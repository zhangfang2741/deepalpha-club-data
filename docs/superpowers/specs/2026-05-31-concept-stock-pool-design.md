# 美股概念股池系统设计文档

**日期**：2026-05-31
**状态**：已批准
**参考文档**：`docs/美股概念股池方案总结.docx`

---

## 1. 背景与目标

在 `deepalpha` 包内构建一套自动化的美股概念股池系统，以业界公认的 ETFdb 分类体系作为概念定义的权威来源，通过 ETF 持仓作为概念成分股的代理指标，每日自动构建并更新美股概念股池（覆盖 50+ 概念）。

核心信条：ETF 本身由专业指数公司（Indxx、Solactive、MSCI 等）按严格方法论编制，其持仓比任何手动维护列表更具代表性和时效性。

---

## 2. 整体架构

### 分层结构

```
src/deepalpha/
├── models/
│   └── concept.py                  # ConceptEtfMap、ConceptStock、ConceptSummary
│
├── providers/
│   └── finnhub/                    # 镜像 providers/fmp/ 结构
│       ├── __init__.py
│       ├── config.py               # FinnhubConfig（FINNHUB_API_KEY）
│       └── client.py               # FinnhubClient（httpx async，限速 60次/分钟）
│
└── pipeline/
    └── concept/
        ├── __init__.py
        ├── config.py               # ConceptPipelineConfig（DB/Valkey/Finnhub 配置）
        ├── etfdb_scraper.py        # ETFdb HTML 抓取（httpx + lxml）
        ├── finnhub_loader.py       # ETF 持仓拉取 + AUM 过滤逻辑
        ├── db.py                   # asyncpg DB 层（ConceptDb）
        ├── cache.py                # Valkey 缓存层（ConceptCache）
        ├── tasks/
        │   ├── __init__.py
        │   ├── build_concept_map.py    # 月度任务入口
        │   └── update_holdings.py     # 日度任务入口
        └── api/
            ├── __init__.py
            └── router.py           # FastAPI router
```

### 数据流

```
【月度任务】
ETFdb.com ──(httpx+lxml)──► etfdb_scraper
                                │ ~70 个主题分类 + 各分类 ETF symbol 列表
                                ▼
                         Finnhub /stock/profile2（拉 AUM）
                                │ 过滤 AUM < 1亿（100M USD）
                                ▼
                      PostgreSQL: concept_etf_map
                         (ON CONFLICT DO UPDATE，幂等写入)

【日度任务（美东收盘后，新加坡时间 04:30）】
concept_etf_map ──读取──► finnhub_loader
                                │ Finnhub /etf/holdings 逐 ETF 拉持仓
                                │ 失败 → ETF 官网 CSV 兜底
                                ▼
                         按 concept 合并，计算 etf_count / total_weight
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
          PostgreSQL                     Valkey
       concept_stocks               concept:{name}  TTL=2天
    (ON CONFLICT DO UPDATE)         concept:__list__ TTL=2天

【查询】
FastAPI ──► Valkey（命中直接返回）
              │ 未命中
              ▼
           PostgreSQL 最新日期数据
```

---

## 3. 数据模型

### 3.1 PostgreSQL 表结构

```sql
-- 月度维护：概念 → ETF 映射
CREATE TABLE concept_etf_map (
    concept        VARCHAR(100) NOT NULL,
    etf_symbol     VARCHAR(20)  NOT NULL,
    etf_name       VARCHAR(200),
    aum_million    FLOAT,
    etfdb_slug     VARCHAR(100),
    updated_at     DATE         NOT NULL,
    PRIMARY KEY (concept, etf_symbol)
);

-- 日度更新：概念成分股快照
CREATE TABLE concept_stocks (
    date           DATE         NOT NULL,
    concept        VARCHAR(100) NOT NULL,
    symbol         VARCHAR(20)  NOT NULL,
    name           VARCHAR(200),
    etf_count      INT          NOT NULL,
    total_weight   FLOAT        NOT NULL,
    etfs           TEXT,                   -- 持有 ETF 列表，逗号分隔
    PRIMARY KEY (date, concept, symbol)
);
```

### 3.2 Pydantic 模型（`models/concept.py`）

```python
class ConceptEtfMap(BaseModel):
    concept: str
    etf_symbol: str
    etf_name: str | None
    aum_million: float | None
    etfdb_slug: str | None
    updated_at: date

class ConceptStock(BaseModel):
    date: date
    concept: str
    symbol: str
    name: str | None
    etf_count: int
    total_weight: float
    etfs: list[str]          # 从逗号分隔字符串解析

class ConceptSummary(BaseModel):
    concept: str
    etf_count: int           # 该概念下 ETF 数量
    stock_count: int         # 成分股数量（最新日期）
    top_symbols: list[str]   # etf_count 最高的前 5 只股票
    last_updated: date
```

---

## 4. 采集层设计

### 4.1 ETFdb 抓取（`etfdb_scraper.py`）

两步抓取，使用 httpx + lxml（项目已有依赖），请求间隔 2 秒，User-Agent 轮换：

1. `GET https://etfdb.com/etfs/themes/` → 解析所有主题分类 slug + 分类名
2. 对每个 slug，`GET https://etfdb.com/type/{slug}/#etfs` → 解析该分类下 ETF symbol 列表

输出：`list[ConceptEtfCandidate]`，待 AUM 过滤。

### 4.2 Finnhub 客户端（`providers/finnhub/client.py`）

镜像 `providers/fmp/client.py`，httpx 异步，内置令牌桶限速（60次/分钟，间隔 1.1 秒）：

```
GET /api/v1/stock/profile2?symbol={etf}&token={key}   # → aum（百万美元）
GET /api/v1/etf/holdings?symbol={etf}&token={key}      # → holdings 列表
```

Finnhub holdings 响应映射到 `FinnhubHolding(symbol, name, percent)`。

### 4.3 容错设计

- Finnhub 返回空或报错 → 自动回落 ETF 官网 CSV（Global X、iShares 等每日发布持仓 CSV）
- PostgreSQL 写入使用 `ON CONFLICT DO UPDATE`，任务重跑幂等
- Valkey TTL 2 天，防止 DB 故障时缓存过期导致服务不可用

---

## 5. DB 层设计（`db.py`）

`ConceptDb` 封装所有 asyncpg 操作，入参出参全用 Pydantic 模型校验：

```python
class ConceptDb:
    async def upsert_etf_map(self, records: list[ConceptEtfMap]) -> None: ...
    async def load_etf_map(self) -> list[ConceptEtfMap]: ...
    async def upsert_stocks(self, date: date, records: list[ConceptStock]) -> None: ...
    async def get_latest_stocks(self, concept: str) -> list[ConceptStock]: ...
    async def get_all_concept_summaries(self) -> list[ConceptSummary]: ...
    async def get_stocks_history(self, concept: str, start: date, end: date) -> list[ConceptStock]: ...
```

连接配置通过 `ConceptPipelineConfig`（pydantic-settings）从环境变量读取，Neon PostgreSQL 需启用 SSL（`ssl='require'`）。

---

## 6. 缓存层设计（`cache.py`）

`ConceptCache` 封装 valkey-py 操作：

```python
class ConceptCache:
    async def get_concept(self, name: str) -> list[ConceptStock] | None: ...
    async def set_concept(self, name: str, stocks: list[ConceptStock]) -> None: ...
    async def get_list(self) -> list[ConceptSummary] | None: ...
    async def set_list(self, summaries: list[ConceptSummary]) -> None: ...
    async def refresh_all(self, db: ConceptDb) -> None: ...  # 日度任务结束后调用
```

Valkey key 设计：

| Key | Value | TTL |
|-----|-------|-----|
| `concept:__list__` | JSON `list[ConceptSummary]` | 172800 秒（2天）|
| `concept:{name}` | JSON `list[ConceptStock]` | 172800 秒（2天）|

---

## 7. FastAPI 接口（`api/router.py`）

```
GET /concept/list
    响应：list[ConceptSummary]
    包含：所有概念名、ETF 数量、成分股数、top5 成分、最后更新日
    缓存：先查 Valkey concept:__list__，未命中查 DB 并回填缓存

GET /concept/{name}?min_etf_count=1
    响应：{ concept, date, stocks: list[ConceptStock] }
    过滤：etf_count >= min_etf_count（默认=1）
    缓存：先查 Valkey concept:{name}，未命中查 DB 最新日期数据并回填

GET /concept/{name}/history?start=YYYY-MM-DD&end=YYYY-MM-DD
    响应：list[ConceptStock]
    说明：历史快照，仅查 DB，不走缓存
```

---

## 8. 调度任务

### 月度任务：`build_concept_map.py`

```
调度：每月 1 日 02:00（新加坡时间）

流程：
1. etfdb_scraper 抓取全部主题分类 → list[ConceptEtfCandidate]
2. 批量调用 FinnhubClient.get_etf_profile() 拉取 AUM
3. 过滤 aum_million < 100
4. ConceptDb.upsert_etf_map() 写入
5. 打印统计：X 个概念，Y 只 ETF 通过过滤
```

### 日度任务：`update_holdings.py`

```
调度：每个交易日 04:30（新加坡时间，对应美东 16:30 收盘后）

流程：
1. ConceptDb.load_etf_map() 读取所有 concept→etf 映射
2. 遍历每只 ETF，FinnhubClient.get_holdings()
   - 失败 → CSV 兜底；仍失败 → 记录警告跳过
3. 按 concept 合并：计算 etf_count / total_weight / etfs 字段
4. ConceptDb.upsert_stocks(date=today) 写入 concept_stocks
5. ConceptCache.refresh_all() 刷新全部 Valkey key
```

---

## 9. 环境变量

在项目 `.env` 中新增以下配置（参考 `deepalpha-club-ai/.env`）：

```env
# PostgreSQL（Neon，需 SSL）
POSTGRES_HOST=ep-cold-silence-apl6e8tx.c-7.us-east-1.aws.neon.tech
POSTGRES_PORT=5432
POSTGRES_DB=neondb
POSTGRES_USER=neondb_owner
POSTGRES_PASSWORD=npg_xhAfdp2IEKG3
POSTGRES_SSL=true

# Valkey（Upstash，需 SSL）
VALKEY_HOST=grand-doberman-114359.upstash.io
VALKEY_PORT=6379
VALKEY_PASSWORD=gQAAAAAAAb63AAIgcDExY2VjN2FjNDZhYTQ0ZmZkOTNhNDA2YjExYTU3ZWE3ZQ
VALKEY_SSL=true

# Finnhub
FINNHUB_API_KEY=d22pa8pr01qi437f6jh0d22pa8pr01qi437f6jhg
```

---

## 10. 新增依赖

在 `pyproject.toml` 的 `dependencies` 中新增：

```toml
"asyncpg>=0.29.0",    # PostgreSQL 异步驱动（Neon 兼容）
"valkey>=6.0.0",      # Valkey/Redis 客户端（兼容 redis-py API）
```

---

## 11. 外部依赖成本

| 依赖 | 用途 | 费用 | 限制 |
|------|------|------|------|
| ETFdb.com | 概念分类 + ETF 列表 | 免费（HTML 抓取）| 每月 1 次，间隔 2 秒 |
| Finnhub 免费版 | ETF 持仓 + AUM | 免费 | 60次/分钟 |
| ETF 官网 CSV | 持仓兜底 | 免费 | URL 偶尔变更 |
| FMP API | 行情补充（可选） | Starter 已有 | 无额外成本 |
| Neon PostgreSQL | 持久化存储 | 已有 | — |
| Upstash Valkey | 缓存层 | 已有 | — |

采集层完全免费，50+ ETF 每日持仓更新约需 1 分钟（Finnhub 限速内）。
