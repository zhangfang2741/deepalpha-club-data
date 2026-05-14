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

### 5.1 批量数据流 (L0→L1→L2→L3)

```
[Sources] → [Airflow DAGs] → [Cleaners] → [Parquet/DuckDB]
   ↓
[Kafka Producers]
```

- FMP/FRED Loader: 每日 06:00 触发，推送数据到 Kafka 和清洗队列
- Airflow DAGs: daily_price / daily_fundamental / daily_macro / daily_alternative

### 5.2 实时数据流 (L0→L1→L2→L3)

```
[Crawlers] → [Kafka Producers] → [Faust Workers] → [ES]
                              ↓
                        [FinBERT NLP]
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

## 7. Docker 服务编排

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

## 8. 技术选型理由

| 组件 | 选型 | 原因 |
|------|------|------|
| 数据处理 | Python + Polars | 比 Pandas 快 5-10x，内存效率高 |
| 流处理 | Faust | Python 原生，与栈统一，无 JVM |
| 批调度 | Apache Airflow | 生态成熟，DAG 可视化，重试完善 |
| 结构化存储 | Parquet + DuckDB | 列式压缩，零运维，回测友好 |
| 非结构化存储 | Elasticsearch | 全文检索，实时写入 |
| API 框架 | FastAPI | 异步高性能，自动生成 OpenAPI |

## 9. 实施计划

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

## 10. 设计决策

| 决策点 | 选择 | 放弃方案 |
|--------|------|----------|
| 架构风格 | 功能插件化 | 层级模块化 |
| 结构化存储 | Parquet + DuckDB | HBase |
| 流处理框架 | Faust | Flink/Spark |
| 数据处理 | Polars | Pandas |