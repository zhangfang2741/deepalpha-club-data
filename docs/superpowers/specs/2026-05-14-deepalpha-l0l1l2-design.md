# DeepAlpha L0/L1/L2 架构设计方案

**版本**: v1.0
**日期**: 2026-05-14
**状态**: Approved

## 1. 设计目标

为 DeepAlpha 量化研究平台搭建完整的 L0/L1/L2 层级框架，采用**功能插件化架构**，确保：
- 每层职责单一，可独立测试和扩展
- 与技术规格文档的层级命名对应
- 支持批量和实时流处理双轨

## 2. 整体架构

```
deepalpha/
├── plugins/                     # 插件目录
│   ├── sources/                 # L0 数据源插件
│   ├── processors/              # L1/L2 处理插件
│   └── api/                     # Data API Service 插件
├── frontend/                    # 前端目录 (React)
│   ├── admin/                   # 管理后台
│   │   ├── config/              # 配置管理
│   │   ├── users/               # 用户管理
│   │   └── monitoring/          # 监控面板
│   └── src/
├── tests/
├── docker/
├── pyproject.toml
└── README.md
```

### 层级职责

| 层级 | 职责 | 技术栈 |
|------|------|--------|
| L0 (Sources) | 数据源抓取 | FMP API, FRED API, 自建爬虫 |
| L1 (Ingestion) | 批量调度 + 流接入 | Airflow, Kafka producers |
| L2 (Processing) | 数据清洗 + NLP处理 | Polars, Faust, FinBERT |
| L3 (Storage) | 结构化/非结构化存储 | Parquet+DuckDB, Elasticsearch |

## 3. 插件目录结构

每个插件是独立目录，包含：

```
<plugin_name>/
├── __init__.py
├── loader.py      # 或 processor.py
├── config.py
├── schemas.py
└── test_*.py
```

### 3.1 Sources 插件 (L0)

| 插件 | 数据内容 | 更新频率 |
|------|----------|----------|
| fmp_loader | 行情/财务/预期/内幕交易/13F | 每日批处理 |
| fred_loader | 宏观/供应链/BDI/GSCPI | 每日批处理 |
| stocktwits_crawler | 社交情绪 Bullish/Bearish | 20秒轮询 |
| reddit_crawler | WSB 讨论热度/情绪 | 30秒轮询 |
| sec_crawler | 8-K/10-Q/Form4 全文 | 事件驱动 |
| fed_crawler | FOMC 纪要/主席讲话 | 事件驱动 |
| trends_crawler | Google Trends 搜索热度 | 每日 |
| appstore_crawler | App Store 评分变动 | 每日 |

### 3.2 Processors 插件 (L1/L2)

| 插件 | 处理内容 | 输入→输出 |
|------|----------|-----------|
| price_cleaner | 日线行情去重/异常检测/PIT校正 | parquet→parquet |
| fundamental_cleaner | 财务三表 PIT 校正/空值告警 | parquet→parquet |
| macro_processor | 宏观数据清洗格式化 | parquet→parquet |
| sentiment_processor | FinBERT 情绪分类/权重计算 | kafka→ES |

## 4. 插件接口规范

### 4.1 Source 插件接口

```python
class BaseSource(ABC):
    @abstractmethod
    def fetch(self, **kwargs) -> pl.DataFrame:
        """抓取数据"""
        pass

    @abstractmethod
    def validate(self, df: pl.DataFrame) -> bool:
        """数据校验"""
        pass

    def to_kafka(self, df: pl.DataFrame, topic: str):
        """推送数据到 Kafka"""
        pass
```

### 4.2 Processor 插件接口

```python
class BaseProcessor(ABC):
    @abstractmethod
    def process(self, df: pl.DataFrame, **kwargs) -> pl.DataFrame:
        """清洗处理"""
        pass
```

## 5. 数据流设计

### 5.1 清洗工作流 (Batch Processing)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    批量数据清洗流程                                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐               │
│  │ FMP API  │───▶│ Airflow DAG │───▶│   L0 Raw    │───▶│  Price       │               │
│  │ $15/月   │    │ daily_price │    │   Parquet   │    │  Cleaner     │               │
│  └──────────┘    └──────────────┘    └─────────────┘    └──────┬───────┘               │
│                                                                  │                       │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────▼───────┐               │
│  │ FRED API │───▶│ Airflow DAG │───▶│   L0 Raw     │───▶│ Fundamental  │              │
│  │ 免费      │    │ daily_fund  │    │   Parquet   │    │  Cleaner     │               │
│  └──────────┘    └──────────────┘    └─────────────┘    └──────┬───────┘               │
│                                                                  │                       │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────▼───────┐               │
│  │ FMP News │───▶│ Kafka Topic │───▶│ raw.news    │───▶│ Sentiment     │───▶ ES Index   │
│  │          │    │ raw.news    │    │ (7天保留)   │    │ Processor     │   financial_   │
│  └──────────┘    └──────────────┘    └─────────────┘    └───────────────┘   news         │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

**工作流步骤详解：**

#### Step 1: L0 数据抓取
| 来源 | 触发方式 | 输出 |
|------|----------|------|
| FMP 行情 | Airflow daily_price DAG (06:00 EST) | Parquet → L0_raw/price/ |
| FMP 财务 | Airflow daily_fundamental DAG (06:00 EST) | Parquet → L0_raw/financials/ |
| FMP 新闻 | Kafka Producer → raw.news topic | Kafka Message |
| FRED 宏观 | Airflow daily_macro DAG (06:00 EST) | Parquet → L0_raw/macro/ |

#### Step 2: L1 数据接入
| 组件 | 职责 | 配置 |
|------|------|------|
| Airflow | DAG 调度、重试、可视化 | LocalExecutor, 3次重试, 间隔5分钟 |
| Kafka Producer | 实时数据推送 | FMP请求间隔0.5秒防限流 |

#### Step 3: L2 数据清洗

**Price Cleaner 清洗规则：**
```
输入: L0_raw/price/
     ├── 去重: 同 symbol + date 取最新一条
     ├── 异常检测: 单日涨跌幅 > 50% → 标记到 anomaly 分区
     ├── 成交量过滤: volume = 0 的非交易日记录剔除
     └── 输出: warehouse/price/ (按 market/date 分区)
```

**Fundamental Cleaner 清洗规则：**
```
输入: L0_raw/financials/
     ├── PIT校正: 使用 announce_date (非 report_date)
     ├── 有效性检查: announce_date > report_date
     ├── 空值统计: 空值率 > 5% → 触发告警
     └── 输出: warehouse/financials/ (按 market/symbol 分区)
```

**Sentiment Processor 处理规则：**
```
输入: raw.stocktwits / raw.news
     ├── FinBERT 推理: sentiment_scores (positive/negative/neutral)
     ├── 情绪打分: sentiment_score (-1 ~ 1)
     ├── StockTwits特殊: 自带标签 + 用户粉丝权重 (log压缩)
     └── 输出: ES Index (social_sentiment / financial_news)
```

#### Step 4: L3 数据存储
| 存储 | 路径/Index | 分区键 |
|------|------------|--------|
| Parquet (行情) | warehouse/price/ | market, date |
| Parquet (财务) | warehouse/financials/ | market, symbol |
| Parquet (因子) | warehouse/factors/ | date |
| Parquet (宏观) | warehouse/macro/ | series_id |
| Elasticsearch | financial_news | symbol, published_at |
| Elasticsearch | social_sentiment | symbol, created_at |

### 5.2 实时数据流 (Streaming)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  实时数据流                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  StockTwits API  ────▶  StockTwitsCrawler  ────▶  raw.stocktwits  ──────────────┐ │
│  (20秒轮询)                                               (7天)                    │ │
│                                                                     ▼             │
│  Reddit API  ──────▶  RedditCrawler  ──────▶  raw.stocktwits  ──────────────┼───▶ │
│  (30秒轮询)                                               (7天)                    │ │
│                                                                     ▼             │
│  SEC EDGAR  ──────▶  SECCrawler  ─────────▶  raw.sec_filings  ──────────┼───▶ │
│  (事件驱动)                                                (30天)               │ │
│                                                                     ▼             │
│  Fed RSS  ───────▶  FedCrawler  ─────────▶  raw.macro_events  ────────┼───▶ │
│  (事件驱动)                                                (30天)               │ │
│                                                                     ▼             │
│                                                        ┌─────────────────────────┤ │
│                                                        │   Faust Workers         │ │
│                                                        │   ├── SentimentProcessor│ │
│                                                        │   │   └── FinBERT NLP    │ │
│                                                        │   ├── TextParser        │ │
│                                                        │   └── EventProcessor    │ │
│                                                        └───────────┬─────────────┘ │
│                                                                        ▼             │
│                                                    processed.sentiment  ────▶ ES  │
│                                                    (7天保留)                        │
│                                                                        ▼             │
│                                                               dlq.failed  ────▶ 人工 │
│                                                               (30天保留)              │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Kafka Topic 设计

| Topic | 生产者 | 消费者 | 保留 |
|-------|--------|--------|------|
| raw.news | FMPNewsCrawler | SentimentProcessor | 7天 |
| raw.stocktwits | StockTwitsCrawler | SentimentProcessor | 7天 |
| raw.sec_filings | SECCrawler | TextParser | 30天 |
| raw.macro_events | FedRSSCrawler | EventProcessor | 30天 |
| processed.sentiment | Faust | FactorEngine | 7天 |
| dlq.failed | 所有 Worker | 人工处理 | 30天 |

## 6. 配置管理

统一 `config.yaml`：

```yaml
sources:
  fmp:
    api_key: "${FMP_API_KEY}"
    rate_limit: 0.5
  stocktwits:
    poll_interval: 20

kafka:
  bootstrap_servers: "localhost:9092"
  topics:
    news: "raw.news"
    stocktwits: "raw.stocktwits"
    sec_filings: "raw.sec_filings"
    macro_events: "raw.macro_events"

storage:
  parquet_path: "warehouse/"
  es_hosts: ["localhost:9200"]
```

## 10. Docker 服务编排

| 服务 | 端口 | 内存 |
|------|------|------|
| Airflow Webserver | 8080 | ~500MB |
| PostgreSQL | 5432 | ~200MB |
| Elasticsearch | 9200 | ~1GB |
| Kibana | 5601 | ~400MB |
| Kafka | 9092 | ~500MB |
| Zookeeper | 2181 | ~200MB |
| Data API | 8000 | ~300MB |
| Faust Worker | 本地 | ~1.5GB |

## 8. 前端 - 管理后台

### 8.1 定位

管理后台用于配置数据源参数、用户管理、监控数据流状态。后续可扩展至因子编辑器和回测展示。

### 8.2 技术栈

| 组件 | 选型 |
|------|------|
| 框架 | React 18 + TypeScript |
| 状态管理 | Zustand |
| UI 库 | TailwindCSS + shadcn/ui |
| 构建工具 | Vite |
| API 调用 | React Query |

### 8.3 目录结构

```
frontend/admin/
├── src/
│   ├── components/          # 通用组件
│   │   ├── ui/              # shadcn/ui 组件
│   │   └── layout/           # 布局组件
│   ├── pages/
│   │   ├── Config/           # 配置管理页面
│   │   ├── Users/            # 用户管理页面
│   │   └── Monitoring/        # 监控面板
│   ├── hooks/                # 自定义 hooks
│   ├── api/                  # API 调用封装
│   └── stores/               # Zustand stores
├── public/
├── package.json
└── vite.config.ts
```

### 8.4 管理后台功能

| 页面 | 功能 |
|------|------|
| 配置管理 | 数据源 API Key 配置、Kafka Topic 配置、轮询间隔配置 |
| 用户管理 | 用户 CRUD、租户空间分配 |
| 监控面板 | Kafka Lag、ES 写入量、数据更新状态 |

### 8.5 配置管理页面设计

配置项通过前端编辑后，持久化到 `config.yaml` 或数据库，支持：
- FMP API Key 管理
- 爬虫轮询间隔调整
- Kafka Topic 配置
- ES Index 管理

### 8.6 自建统一入口

在管理后台中添加统一监控导航页，聚合所有服务入口：

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DeepAlpha 统一监控中心                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   Airflow   │  │  Kafka UI   │  │   Kibana    │                │
│  │   DAG 监控   │  │  Topic/Lag  │  │  ES 可视化   │                │
│  │  localhost  │  │  localhost  │  │ localhost   │                │
│  │    :8080    │  │    :8090    │  │   :5601     │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  Prometheus │  │   Grafana   │  │  Data API   │                │
│  │   指标采集   │  │   图表展示   │  │   :8000     │                │
│  │  localhost  │  │  localhost  │  │             │                │
│  │    :9090    │  │    :3000    │  │             │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**监控矩阵：**

| 服务 | 工具 | 端口 | 监控内容 |
|------|------|------|----------|
| Airflow | Airflow UI | 8080 | DAG 状态、任务执行、XCom |
| Kafka | Kafka UI | 8090 | Topic、Consumer Lag、消息量 |
| Elasticsearch | Kibana | 5601 | 索引、文档数、写入延迟 |
| Faust Streams | Grafana | 3000 | 吞吐量、延迟、错误率 |
| 系统 | Prometheus | 9090 | CPU、内存、磁盘 |

**Grafana Dashboard 面板：**

```
Faust Stream Monitor
├── 消费吞吐量 (messages/sec)
├── Consumer Lag (按 topic 分组)
├── FinBERT 推理延迟 (p50/p95/p99)
├── 错误率 (按 worker 分组)
└── Kafka Lag 趋势图
```

## 11. 技术选型理由

| 组件 | 选型 | 原因 |
|------|------|------|
| 数据处理 | Python + Polars | 比 Pandas 快 5-10x，内存效率高 |
| 流处理 | Faust | Python 原生，与栈统一，无 JVM |
| 批调度 | Apache Airflow | 生态成熟，DAG 可视化，重试完善 |
| 结构化存储 | Parquet + DuckDB | 列式压缩，零运维，回测友好 |
| 非结构化存储 | Elasticsearch | 全文检索，实时写入 |
| API 框架 | FastAPI | 异步高性能，自动生成 OpenAPI |

## 12. 实施计划

Phase 1: 框架搭建
- 创建目录结构和 pyproject.toml
- 实现 BaseSource/BaseProcessor 基类
- 配置 Docker Compose

Phase 2: L0 数据源
- 实现 fmp_loader
- 实现 fred_loader
- 实现 crawlers

Phase 3: L1/L2 处理
- 实现 Airflow DAGs
- 实现 Kafka producers
- 实现 cleaners
- 实现 Faust workers + FinBERT

Phase 4: 前端管理后台
- 创建 React 项目结构
- 实现配置管理页面
- 实现用户管理页面
- 实现监控面板

## 13. 设计决策

| 决策点 | 选择 | 放弃方案 |
|--------|------|----------|
| 架构风格 | 功能插件化 | 层级模块化 |
| 结构化存储 | Parquet + DuckDB | HBase |
| 流处理框架 | Faust | Flink/Spark |
| 数据处理 | Polars | Pandas |