# 信号趋势雷达（Signal Trend Radar）设计文档

**日期**：2026-06-07
**状态**：已批准，待实现

---

## 1. 概述

信号趋势雷达是一个每日运行的 pipeline，从 QQQ 纳斯达克100成分股的电话会议、Capex、创业融资、招聘等公开信号源中，提取细粒度的技术/基础设施/工程主题关键词，计算每日加权得分与动量，持续累加历史快照，并通过前端雷达图+排行榜可视化展示，支持时光机维度回溯任意历史时刻的主题热度。

目标是发现"可被资本验证的结构性主题"，如 HBM3e、MCP、Post-Training Pipeline、液冷机柜等，而非泛化的行业描述。

---

## 2. 整体架构

### 2.1 目录结构

```
src/deepalpha/
├── domain/signal_radar/
│   ├── __init__.py
│   ├── models.py          # SignalCategory, RawSignalItem, ExtractedTheme, DailyThemeScore
│   └── protocols.py       # ISignalRadarRepo
│
├── infrastructure/
│   ├── providers/
│   │   ├── edgar/
│   │   │   ├── __init__.py
│   │   │   ├── filing_8k_loader.py     # SEC EDGAR 8-K 电话会议文本
│   │   │   ├── form_d_loader.py        # SEC EDGAR Form D 融资申报
│   │   │   └── xbrl_capex_loader.py    # SEC EDGAR XBRL Capex 数据
│   │   └── greenhouse/
│   │       ├── __init__.py
│   │       └── job_loader.py           # Greenhouse / Lever 公开 API 招聘帖
│   ├── db/
│   │   └── signal_radar_repo.py        # PostgreSQL 实现 ISignalRadarRepo
│   └── providers/minimax/
│       └── theme_extractor.py          # LLM 主题提取（复用已有 MiniMax client）
│
└── interface/
    ├── pipeline/signal_radar/
    │   ├── __init__.py
    │   └── run.py                      # 每日 cron pipeline 主入口
    └── web/routers/
        └── signal_radar.py             # FastAPI 路由
```

### 2.2 每日数据流

```
① 拉取 QQQ 100 ticker 列表（yfinance）
② 并发采集 4 路信号源
   ├─ SEC EDGAR 8-K      → 电话会议文本
   ├─ SEC EDGAR XBRL     → Capex 数字
   ├─ SEC EDGAR Form D   → 融资披露文本
   └─ Greenhouse / Lever → 招聘 JD 文本
③ LLM 批量提取主题关键词（MiniMax）
④ 去同义化标准化（LLM prompt 内完成）
⑤ 计算当日加权基础分
⑥ 计算动量系数（与过去7日均值对比）
⑦ 最终分 = 基础分 × min(动量系数, 3.0)
⑧ 写入 PostgreSQL 每日快照
⑨ FastAPI /api/signal-radar/* 路由暴露
⑩ Next.js /radar 页面渲染
```

---

## 3. 信号源详情

| 信号源 | 数据接口 | 内容 | 评分权重 |
|--------|---------|------|---------|
| 电话会议 | SEC EDGAR 8-K filing（8-K Item 2.02/7.01，附件文本） | 管理层对技术投入的表述 | 3 |
| Capex | SEC EDGAR XBRL（us-gaap:PaymentsToAcquirePropertyPlantAndEquipment） | 资本支出金额及相关描述 | 4 |
| 创业融资 | SEC EDGAR Form D（全量，筛选 QQQ 公司关联的 VC 基金投资领域） | 融资摘要文本及行业描述 | 2 |
| 招聘 | Greenhouse boards API（`boards.greenhouse.io/{slug}/jobs`）+ Lever（`api.lever.co/v0/postings/{slug}`） | JD 标题 + 正文 | 1 |

**QQQ 成分股来源**：每日运行时通过 yfinance 拉取当前 QQQ 持仓的 ticker 列表（约 100 只），作为监控范围。

---

## 4. 主题提取

### 4.1 提取范围（三类）

| 类别 | category 值 | 示例 |
|------|------------|------|
| 技术/能力关键词 | `tech_concept` | MCP、Agent Memory、Mixture of Experts、RAG Pipeline、Speculative Decoding |
| 基础设施组件 | `infra_component` | HBM3e、NVLink、InfiniBand、液冷机柜、定制 ASIC、CoWoS 封装、GB200 |
| 新兴工程概念 | `engineering_concept` | AI Compiler、Inference Optimization、Post-Training、RLHF Pipeline、KV Cache |

### 4.2 提取合格判断标准（Prompt 约束）

- 合格：可以被招聘 JD 里的岗位要求验证（如 "HBM 内存架构"）
- 合格：可以被 Capex 支出或融资金额对应（如 "液冷数据中心"）
- 合格：多家公司同期同时提到（如 "MCP 协议支持"）
- 不合格：行业大词（"AI"、"云计算"、"数字化转型"）
- 不合格：公司名、产品品牌（取 "H100" 可以，"NVIDIA" 不要）
- 不合格：财务指标（"营收增长"、"毛利率"）

### 4.3 LLM 输出格式

每条信号文本（截断到约 2000 字符）调用 MiniMax，返回 JSON：

```json
{
  "themes": [
    {"name": "HBM3e", "category": "infra_component", "confidence": 0.92},
    {"name": "MCP", "category": "tech_concept", "confidence": 0.85},
    {"name": "Post-Training Pipeline", "category": "engineering_concept", "confidence": 0.80}
  ]
}
```

约束：
- 每条信号最多 5 个主题
- 输出英文缩写或规范术语（LLM 自行标准化，如 "Model Context Protocol" → "MCP"）
- 置信度低于 0.6 的主题丢弃

### 4.4 去同义化策略（第一阶段）

由 LLM Prompt 内完成，Prompt 中提供示例对照表引导输出规范名称。后续升级路径：引入 embedding 聚类，相似度 > 0.85 自动合并为同一主题。

---

## 5. 评分引擎

### 5.1 评分公式

```
信号源权重：
  earnings_call  = 3
  capex          = 4
  form_d         = 2
  job_posting    = 1

当日基础分(主题 T) =
  Σ (该信号提到 T 的次数 × 信号来源权重 × LLM 置信度)

动量系数 = 今日基础分 / max(过去7日基础分均值, 1.0)
动量系数上限 = 3.0（防止冷门主题单日爆发虚高）

当日最终分 = 基础分 × min(动量系数, 3.0)

累计分(截至日期 D) = Σ 历史所有日期的当日最终分（纯累加，不衰减）
```

### 5.2 主题聚合规则

- 同一天同一主题来自多家公司 → 分数叠加（跨公司共现是强信号）
- 主题名完全一致才合并（由 LLM 负责输出标准化名称）
- 累计出现 ≥ 3 次才进入排行榜展示（过滤低频噪音）

---

## 6. 数据库表结构

所有表包含 `created_at`、`updated_at` 字段，pipeline 每日只写入当日增量，历史快照永不覆盖。

```sql
-- 原始信号条目（去重 key: ticker + source_type + doc_id）
CREATE TABLE signal_raw_items (
    id              BIGSERIAL PRIMARY KEY,
    ticker          VARCHAR(10)   NOT NULL,
    source_type     VARCHAR(20)   NOT NULL,   -- earnings_call | capex | form_d | job_posting
    signal_date     DATE          NOT NULL,
    doc_id          VARCHAR(100)  NOT NULL,
    text_snippet    TEXT,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE (ticker, source_type, doc_id)
);
CREATE INDEX ON signal_raw_items (signal_date DESC, ticker);

-- LLM 提取的主题条目（每条信号可提取多个主题）
CREATE TABLE signal_extracted_themes (
    id              BIGSERIAL PRIMARY KEY,
    raw_item_id     BIGINT        NOT NULL REFERENCES signal_raw_items(id),
    theme_name      VARCHAR(100)  NOT NULL,
    category        VARCHAR(30)   NOT NULL,   -- tech_concept | infra_component | engineering_concept
    confidence      FLOAT         NOT NULL,
    extract_date    DATE          NOT NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX ON signal_extracted_themes (extract_date, theme_name);
CREATE INDEX ON signal_extracted_themes (theme_name, extract_date DESC);

-- 主题每日得分快照（时光机核心表）
CREATE TABLE signal_theme_daily_scores (
    id                BIGSERIAL PRIMARY KEY,
    theme_name        VARCHAR(100)  NOT NULL,
    category          VARCHAR(30)   NOT NULL,
    score_date        DATE          NOT NULL,
    base_score        FLOAT         NOT NULL,
    momentum          FLOAT         NOT NULL,
    final_score       FLOAT         NOT NULL,
    cumulative_score  FLOAT         NOT NULL,   -- 截至当日历史累计
    company_count     INT           NOT NULL DEFAULT 0,
    signal_breakdown  JSONB         NOT NULL DEFAULT '{}',
    -- {"earnings_call": 12.0, "capex": 8.0, "form_d": 4.0, "job_posting": 2.0}
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE (theme_name, score_date)
);
CREATE INDEX ON signal_theme_daily_scores (score_date DESC, cumulative_score DESC);
CREATE INDEX ON signal_theme_daily_scores (theme_name, score_date DESC);

-- Pipeline 每日运行日志
CREATE TABLE signal_pipeline_runs (
    id               BIGSERIAL PRIMARY KEY,
    run_date         DATE          NOT NULL UNIQUE,
    status           VARCHAR(20)   NOT NULL,   -- running | success | failed
    items_fetched    INT           DEFAULT 0,
    themes_extracted INT           DEFAULT 0,
    error_detail     TEXT,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
```

---

## 7. API 接口

新增路由文件：`src/deepalpha/interface/web/routers/signal_radar.py`

```
GET /api/signal-radar/leaderboard
  ?date=2026-06-07    # 时光机：指定查询日期，默认今日
  &window=30d         # 累计分窗口：1M | 1Y | 3Y | all
                      # window 控制 SUM(final_score) 的时间范围（从 date 往前推）
                      # 不影响每日快照的存储，只影响排行榜的排序分值
  &category=all       # tech_concept | infra_component | engineering_concept | all
  &limit=50
→ 按指定窗口内 SUM(final_score) 倒序返回主题排行榜

GET /api/signal-radar/trend/{theme_name}
  ?from=2026-01-01&to=2026-06-07
→ 返回某主题的每日得分时间序列（折线图数据）

GET /api/signal-radar/snapshot
  ?date=2026-06-07
→ 返回指定日期的 Top 20 主题（雷达图数据源）

GET /api/signal-radar/themes
  ?q=HBM
→ 模糊搜索主题名（自动补全）
```

---

## 8. 前端页面（`/radar`）

技术栈：Next.js App Router + Recharts（现有依赖）+ shadcn/ui

### 8.1 页面布局

```
┌────────────────────────────────────────────────────────────┐
│  时间维度：[今日] [1M] [1Y] [3Y] [自定义日期 DatePicker]     │  ← 时光机控件
│  分类筛选：[全部] [技术概念] [基础设施] [工程概念]             │
├─────────────────────┬──────────────────────────────────────┤
│                     │  排行榜                               │
│   趋势雷达图         │  #1  HBM3e          ████ 2847        │
│  (RadarChart)       │  #2  MCP            ███  1923        │
│   Top 8 主题         │  #3  液冷机柜        ██   1456        │
│   按 category 着色   │  #4  Post-Training  ██   1203        │
│                     │  ...                                  │
│                     │  点击主题 → 加载折线趋势图              │
├─────────────────────┴──────────────────────────────────────┤
│  主题趋势折线图（点击排行榜主题后展示，支持多主题叠加对比）       │
│  X轴: 日期   Y轴: final_score   可多选主题叠加               │
└────────────────────────────────────────────────────────────┘
```

### 8.2 时光机交互

- 切换日期/窗口 → 雷达图、排行榜同步刷新
- 点击排行榜主题 → 折线图加载该主题历史趋势
- 多选主题 → 折线图叠加对比
- category 筛选 → 三个区域同步刷新，雷达图各维度着色对应类别

---

## 9. Pipeline 配置

新增 `SignalRadarPipelineConfig`（继承 `BaseSettings`，与现有 config 体系一致）：

```python
class SignalRadarPipelineConfig(BaseSettings):
    # PostgreSQL（复用现有字段）
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_ssl: bool = False

    # MiniMax（复用现有 key）
    minimax_api_key: str = ""

    # 监控范围
    qqq_ticker: str = "QQQ"           # 用于 yfinance 拉取成分股
    max_companies: int = 100

    # 采集参数
    edgar_lookback_days: int = 2       # 拉取最近 N 天的新文件
    greenhouse_slugs_yaml: str = "config/greenhouse_slugs.yaml"

    # 评分参数
    momentum_window_days: int = 7
    momentum_cap: float = 3.0
    min_theme_occurrences: int = 3     # 进入排行榜的最低累计次数

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

调度：每日 UTC 06:00 运行（美股盘前，覆盖前一交易日的 EDGAR 文件）。

---

## 10. 错误处理与幂等性

- `signal_raw_items` 和 `signal_theme_daily_scores` 均使用 `UNIQUE` + `ON CONFLICT DO NOTHING / DO UPDATE` 保证幂等
- 每路信号源采集失败 → 记录日志，跳过该源，不影响其他源
- LLM 提取失败 → 跳过该条信号，记录 `error_detail` 到 `signal_pipeline_runs`
- Pipeline 崩溃重跑 → 幂等，不会重复写入已处理的文档

---

## 11. 实现优先级（分阶段）

| 阶段 | 内容 | 验证标准 |
|------|------|---------|
| P0 | PostgreSQL 建表 + pipeline 骨架 + 一路信号（8-K）跑通 | 能写入 `signal_raw_items` 和 `signal_theme_daily_scores` |
| P1 | 接入其余三路信号源（XBRL / Form D / Greenhouse） | 四路信号均可采集并提取主题 |
| P2 | FastAPI 路由 + Next.js `/radar` 页面 MVP | 排行榜和雷达图可渲染 |
| P3 | 时光机交互 + 多主题折线对比 + category 筛选 | 前端完整交互 |
