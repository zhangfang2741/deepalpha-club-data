# Signal Trend Radar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 每日从 SEC EDGAR（8-K / XBRL / Form D）和 Greenhouse/Lever 采集 QQQ 100 公司信号，LLM 提取技术/基础设施/工程主题关键词，加权动量评分后写入 PostgreSQL 每日快照，Next.js `/radar` 页面展示时光机雷达图和排行榜。

**Architecture:** 单体 daily pipeline（`signal_radar/run.py`）并发采集四路信号 + 批量 LLM 提取 + 评分写库；FastAPI 四个只读路由暴露查询接口；Next.js 单页消费 API 渲染 Recharts RadarChart + 排行榜 + 趋势折线图。

**Tech Stack:** asyncpg, httpx, MiniMax API (`https://api.minimax.chat/v1/chat/completions`), SEC EDGAR REST（无需 Key）, Greenhouse/Lever 公开 API（无需 Key）, Recharts, shadcn/ui, Tailwind CSS v4, yaml, xml.etree.ElementTree

---

## File Map

| 路径 | 职责 |
|------|------|
| `src/deepalpha/domain/signal_radar/models.py` | Pydantic domain 模型 |
| `src/deepalpha/domain/signal_radar/protocols.py` | ISignalRadarRepo Protocol |
| `src/deepalpha/infrastructure/db/signal_radar_repo.py` | PostgreSQL repo（pool-based） |
| `src/deepalpha/infrastructure/providers/edgar/cik_resolver.py` | Ticker→CIK 映射 |
| `src/deepalpha/infrastructure/providers/edgar/filing_8k_loader.py` | 8-K 电话会议文本 |
| `src/deepalpha/infrastructure/providers/edgar/xbrl_capex_loader.py` | XBRL Capex 采集 |
| `src/deepalpha/infrastructure/providers/edgar/form_d_loader.py` | Form D 融资文本 |
| `src/deepalpha/infrastructure/providers/greenhouse/job_loader.py` | Greenhouse/Lever JD |
| `src/deepalpha/infrastructure/providers/minimax/theme_extractor.py` | LLM 主题提取 |
| `src/deepalpha/interface/pipeline/signal_radar/scoring.py` | 纯函数评分引擎 |
| `src/deepalpha/interface/pipeline/signal_radar/run.py` | Pipeline 主入口 |
| `src/deepalpha/interface/web/routers/signal_radar.py` | FastAPI 路由 |
| `config/greenhouse_slugs.yaml` | 公司 Greenhouse/Lever slug 配置 |
| `config/qqq_tickers.yaml` | QQQ 100 成分股列表 |
| `frontend/app/(dashboard)/radar/page.tsx` | /radar 时光机页面 |
| `tests/unit/signal_radar/test_models.py` | Domain 模型测试 |
| `tests/unit/signal_radar/test_scoring.py` | 评分引擎测试 |
| `tests/unit/providers/edgar/test_filing_8k_loader.py` | 8-K loader 测试 |
| `tests/unit/providers/edgar/test_xbrl_capex_loader.py` | XBRL loader 测试 |
| `tests/unit/providers/edgar/test_form_d_loader.py` | Form D loader 测试 |
| `tests/unit/providers/greenhouse/test_job_loader.py` | Greenhouse loader 测试 |
| `tests/unit/providers/minimax/test_theme_extractor.py` | Theme extractor 测试 |

**修改：**
- `src/deepalpha/infrastructure/config.py` — 追加 `SignalRadarPipelineConfig`
- `src/deepalpha/interface/web/app.py` — 注册 signal_radar router

---

## Task 1: Domain 模型

**Files:**
- Create: `src/deepalpha/domain/signal_radar/__init__.py`
- Create: `src/deepalpha/domain/signal_radar/models.py`
- Create: `src/deepalpha/domain/signal_radar/protocols.py`
- Test: `tests/unit/signal_radar/test_models.py`

- [ ] **Step 1: 创建目录**

```bash
mkdir -p src/deepalpha/domain/signal_radar \
         src/deepalpha/infrastructure/providers/edgar \
         src/deepalpha/infrastructure/providers/greenhouse \
         src/deepalpha/interface/pipeline/signal_radar \
         tests/unit/signal_radar \
         tests/unit/providers/edgar \
         tests/unit/providers/greenhouse \
         tests/unit/providers/minimax

touch src/deepalpha/domain/signal_radar/__init__.py \
      src/deepalpha/infrastructure/providers/edgar/__init__.py \
      src/deepalpha/infrastructure/providers/greenhouse/__init__.py \
      src/deepalpha/interface/pipeline/signal_radar/__init__.py \
      tests/unit/signal_radar/__init__.py \
      tests/unit/providers/edgar/__init__.py \
      tests/unit/providers/greenhouse/__init__.py \
      tests/unit/providers/minimax/__init__.py
```

- [ ] **Step 2: 写失败测试**

`tests/unit/signal_radar/test_models.py`:
```python
import datetime
import pytest
from pydantic import ValidationError
from deepalpha.domain.signal_radar.models import (
    SignalCategory, ExtractedTheme, DailyThemeScore,
)


def test_signal_category_values():
    assert SignalCategory.tech_concept == "tech_concept"
    assert SignalCategory.infra_component == "infra_component"
    assert SignalCategory.engineering_concept == "engineering_concept"


def test_extracted_theme_confidence_out_of_range():
    with pytest.raises(ValidationError):
        ExtractedTheme(name="HBM3e", category=SignalCategory.infra_component, confidence=1.5)


def test_daily_theme_score_breakdown_defaults_empty():
    score = DailyThemeScore(
        theme_name="MCP",
        category=SignalCategory.tech_concept,
        score_date=datetime.date(2026, 6, 7),
        base_score=10.0,
        momentum=1.5,
        final_score=15.0,
        cumulative_score=15.0,
        company_count=3,
    )
    assert score.signal_breakdown == {}
```

- [ ] **Step 3: 运行确认失败**

```bash
uv run pytest tests/unit/signal_radar/test_models.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 4: 实现 models.py**

`src/deepalpha/domain/signal_radar/models.py`:
```python
"""信号趋势雷达领域模型"""
import datetime
from enum import Enum
from pydantic import BaseModel, Field


class SignalCategory(str, Enum):
    tech_concept = "tech_concept"
    infra_component = "infra_component"
    engineering_concept = "engineering_concept"


class RawSignalItem(BaseModel):
    ticker: str = Field(title="公司 ticker")
    source_type: str = Field(title="来源类型")  # earnings_call|capex|form_d|job_posting
    signal_date: datetime.date = Field(title="信号原始日期")
    doc_id: str = Field(title="原始文件唯一 ID")
    text_snippet: str = Field("", title="原文摘要（最多 2000 字符）")


class ExtractedTheme(BaseModel):
    name: str = Field(title="标准化主题名")
    category: SignalCategory = Field(title="主题类别")
    confidence: float = Field(ge=0.0, le=1.0, title="置信度")


class ThemeSignal(BaseModel):
    theme: ExtractedTheme
    source_type: str
    ticker: str


class DailyThemeScore(BaseModel):
    theme_name: str
    category: SignalCategory
    score_date: datetime.date
    base_score: float
    momentum: float
    final_score: float
    cumulative_score: float
    company_count: int = 0
    signal_breakdown: dict[str, float] = Field(default_factory=dict)
```

- [ ] **Step 5: 实现 protocols.py**

`src/deepalpha/domain/signal_radar/protocols.py`:
```python
"""信号雷达数据层 Protocol"""
import datetime
from typing import Protocol
from deepalpha.domain.signal_radar.models import DailyThemeScore, ExtractedTheme


class ISignalRadarRepo(Protocol):
    async def is_raw_item_processed(self, ticker: str, source_type: str, doc_id: str) -> bool: ...
    async def insert_raw_item(self, ticker: str, source_type: str, signal_date: datetime.date, doc_id: str, text_snippet: str) -> int: ...
    async def insert_extracted_themes(self, raw_item_id: int, themes: list[ExtractedTheme], extract_date: datetime.date) -> None: ...
    async def get_past_base_scores(self, theme_names: list[str], as_of: datetime.date, window_days: int) -> dict[str, float]: ...
    async def get_cumulative_scores(self, theme_names: list[str], as_of: datetime.date) -> dict[str, float]: ...
    async def upsert_daily_scores(self, scores: list[DailyThemeScore]) -> None: ...
    async def log_pipeline_run(self, run_date: datetime.date) -> None: ...
    async def update_pipeline_run(self, run_date: datetime.date, status: str, items_fetched: int, themes_extracted: int, error_detail: str | None) -> None: ...
    async def get_leaderboard(self, date: datetime.date, window_days: int | None, category: str | None, limit: int) -> list[DailyThemeScore]: ...
    async def get_theme_trend(self, theme_name: str, from_date: datetime.date, to_date: datetime.date) -> list[DailyThemeScore]: ...
    async def get_snapshot(self, date: datetime.date, limit: int) -> list[DailyThemeScore]: ...
    async def search_themes(self, q: str, limit: int) -> list[str]: ...
```

- [ ] **Step 6: 运行确认通过**

```bash
uv run pytest tests/unit/signal_radar/test_models.py -v
```
Expected: 3 PASSED

- [ ] **Step 7: Commit**

```bash
git add src/deepalpha/domain/signal_radar/ tests/unit/signal_radar/
git commit -m "feat(signal-radar): add domain models and repo protocol"
```

---

## Task 2: PostgreSQL Repo

**Files:**
- Create: `src/deepalpha/infrastructure/db/signal_radar_repo.py`

- [ ] **Step 1: 实现 repo**

`src/deepalpha/infrastructure/db/signal_radar_repo.py`:
```python
"""
信号趋势雷达 PostgreSQL 数据层

接受外部传入的 asyncpg.Pool，所有表含 created_at/updated_at。
每日只写增量，历史快照永不覆盖（UNIQUE 约束 + upsert）。
"""
import datetime
import json
from typing import Any
import asyncpg
from deepalpha.domain.signal_radar.models import DailyThemeScore, ExtractedTheme, SignalCategory

_DDL = """
CREATE TABLE IF NOT EXISTS signal_raw_items (
    id           BIGSERIAL PRIMARY KEY,
    ticker       VARCHAR(10)  NOT NULL,
    source_type  VARCHAR(20)  NOT NULL,
    signal_date  DATE         NOT NULL,
    doc_id       VARCHAR(200) NOT NULL,
    text_snippet TEXT         NOT NULL DEFAULT '',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (ticker, source_type, doc_id)
);
CREATE INDEX IF NOT EXISTS idx_sri_date ON signal_raw_items (signal_date DESC);

CREATE TABLE IF NOT EXISTS signal_extracted_themes (
    id           BIGSERIAL PRIMARY KEY,
    raw_item_id  BIGINT       NOT NULL REFERENCES signal_raw_items(id),
    theme_name   VARCHAR(100) NOT NULL,
    category     VARCHAR(30)  NOT NULL,
    confidence   FLOAT        NOT NULL,
    extract_date DATE         NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_set_date ON signal_extracted_themes (extract_date, theme_name);

CREATE TABLE IF NOT EXISTS signal_theme_daily_scores (
    id               BIGSERIAL PRIMARY KEY,
    theme_name       VARCHAR(100) NOT NULL,
    category         VARCHAR(30)  NOT NULL,
    score_date       DATE         NOT NULL,
    base_score       FLOAT        NOT NULL,
    momentum         FLOAT        NOT NULL,
    final_score      FLOAT        NOT NULL,
    cumulative_score FLOAT        NOT NULL,
    company_count    INT          NOT NULL DEFAULT 0,
    signal_breakdown JSONB        NOT NULL DEFAULT '{}',
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (theme_name, score_date)
);
CREATE INDEX IF NOT EXISTS idx_stds_date_cum ON signal_theme_daily_scores (score_date DESC, cumulative_score DESC);
CREATE INDEX IF NOT EXISTS idx_stds_name    ON signal_theme_daily_scores (theme_name, score_date DESC);

CREATE TABLE IF NOT EXISTS signal_pipeline_runs (
    id               BIGSERIAL PRIMARY KEY,
    run_date         DATE         NOT NULL UNIQUE,
    status           VARCHAR(20)  NOT NULL DEFAULT 'running',
    items_fetched    INT          NOT NULL DEFAULT 0,
    themes_extracted INT          NOT NULL DEFAULT 0,
    error_detail     TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
"""


class SignalRadarRepo:
    def __init__(self, pool: "asyncpg.Pool[asyncpg.Record]") -> None:
        self._pool = pool

    @classmethod
    async def create(cls, dsn: str) -> "SignalRadarRepo":
        """工厂方法：创建 pool 并初始化表结构。"""
        pool: asyncpg.Pool[asyncpg.Record] = await asyncpg.create_pool(dsn)  # type: ignore[assignment]
        async with pool.acquire() as conn:
            await conn.execute(_DDL)
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    # --- 写入 ---

    async def is_raw_item_processed(self, ticker: str, source_type: str, doc_id: str) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM signal_raw_items WHERE ticker=$1 AND source_type=$2 AND doc_id=$3",
                ticker, source_type, doc_id,
            )
        return row is not None

    async def insert_raw_item(
        self, ticker: str, source_type: str, signal_date: datetime.date, doc_id: str, text_snippet: str
    ) -> int:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO signal_raw_items (ticker, source_type, signal_date, doc_id, text_snippet)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (ticker, source_type, doc_id) DO UPDATE
                    SET text_snippet = EXCLUDED.text_snippet, updated_at = NOW()
                RETURNING id
                """,
                ticker, source_type, signal_date, doc_id, text_snippet[:2000],
            )
        assert row is not None
        return int(row["id"])

    async def insert_extracted_themes(
        self, raw_item_id: int, themes: list[ExtractedTheme], extract_date: datetime.date
    ) -> None:
        if not themes:
            return
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO signal_extracted_themes (raw_item_id, theme_name, category, confidence, extract_date)
                VALUES ($1, $2, $3, $4, $5)
                """,
                [(raw_item_id, t.name, t.category.value, t.confidence, extract_date) for t in themes],
            )

    async def get_past_base_scores(
        self, theme_names: list[str], as_of: datetime.date, window_days: int = 7
    ) -> dict[str, float]:
        if not theme_names:
            return {}
        since = as_of - datetime.timedelta(days=window_days)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT theme_name, AVG(base_score) AS avg
                FROM signal_theme_daily_scores
                WHERE theme_name = ANY($1) AND score_date >= $2 AND score_date < $3
                GROUP BY theme_name
                """,
                theme_names, since, as_of,
            )
        return {r["theme_name"]: float(r["avg"]) for r in rows}

    async def get_cumulative_scores(self, theme_names: list[str], as_of: datetime.date) -> dict[str, float]:
        if not theme_names:
            return {}
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (theme_name) theme_name, cumulative_score
                FROM signal_theme_daily_scores
                WHERE theme_name = ANY($1) AND score_date < $2
                ORDER BY theme_name, score_date DESC
                """,
                theme_names, as_of,
            )
        return {r["theme_name"]: float(r["cumulative_score"]) for r in rows}

    async def upsert_daily_scores(self, scores: list[DailyThemeScore]) -> None:
        if not scores:
            return
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO signal_theme_daily_scores
                    (theme_name, category, score_date, base_score, momentum, final_score, cumulative_score, company_count, signal_breakdown)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                ON CONFLICT (theme_name, score_date) DO UPDATE SET
                    base_score=EXCLUDED.base_score, momentum=EXCLUDED.momentum,
                    final_score=EXCLUDED.final_score, cumulative_score=EXCLUDED.cumulative_score,
                    company_count=EXCLUDED.company_count, signal_breakdown=EXCLUDED.signal_breakdown,
                    updated_at=NOW()
                """,
                [
                    (s.theme_name, s.category.value, s.score_date, s.base_score, s.momentum,
                     s.final_score, s.cumulative_score, s.company_count, json.dumps(s.signal_breakdown))
                    for s in scores
                ],
            )

    async def log_pipeline_run(self, run_date: datetime.date) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO signal_pipeline_runs (run_date, status) VALUES ($1,'running') "
                "ON CONFLICT (run_date) DO UPDATE SET status='running', updated_at=NOW()",
                run_date,
            )

    async def update_pipeline_run(
        self, run_date: datetime.date, status: str, items_fetched: int, themes_extracted: int, error_detail: str | None
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE signal_pipeline_runs SET status=$2, items_fetched=$3, themes_extracted=$4, error_detail=$5, updated_at=NOW() WHERE run_date=$1",
                run_date, status, items_fetched, themes_extracted, error_detail,
            )

    # --- 查询 (API 层使用) ---

    async def get_leaderboard(
        self, date: datetime.date, window_days: int | None, category: str | None, limit: int = 50
    ) -> list[DailyThemeScore]:
        params: list[Any] = []
        if window_days is not None:
            since = date - datetime.timedelta(days=window_days)
            date_clause = "score_date >= $1 AND score_date <= $2"
            params = [since, date]
        else:
            date_clause = "score_date <= $1"
            params = [date]

        cat_clause = ""
        if category and category != "all":
            params.append(category)
            cat_clause = f"AND category = ${len(params)}"

        params.append(limit)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT theme_name, category,
                       MAX(score_date) AS score_date,
                       SUM(base_score) AS base_score,
                       AVG(momentum)   AS momentum,
                       SUM(final_score) AS final_score,
                       SUM(final_score) AS cumulative_score,
                       MAX(company_count) AS company_count,
                       '{{}}'::jsonb AS signal_breakdown
                FROM signal_theme_daily_scores
                WHERE {date_clause} {cat_clause}
                GROUP BY theme_name, category
                HAVING COUNT(*) >= 1
                ORDER BY SUM(final_score) DESC
                LIMIT ${len(params)}
                """,
                *params,
            )
        return [_row_to_score(r) for r in rows]

    async def get_theme_trend(self, theme_name: str, from_date: datetime.date, to_date: datetime.date) -> list[DailyThemeScore]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM signal_theme_daily_scores WHERE theme_name=$1 AND score_date>=$2 AND score_date<=$3 ORDER BY score_date",
                theme_name, from_date, to_date,
            )
        return [_row_to_score(r) for r in rows]

    async def get_snapshot(self, date: datetime.date, limit: int = 20) -> list[DailyThemeScore]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM signal_theme_daily_scores WHERE score_date=$1 ORDER BY final_score DESC LIMIT $2",
                date, limit,
            )
        return [_row_to_score(r) for r in rows]

    async def search_themes(self, q: str, limit: int = 20) -> list[str]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT theme_name FROM signal_theme_daily_scores WHERE theme_name ILIKE $1 ORDER BY theme_name LIMIT $2",
                f"%{q}%", limit,
            )
        return [r["theme_name"] for r in rows]


def _row_to_score(row: asyncpg.Record) -> DailyThemeScore:
    bd = row["signal_breakdown"]
    if isinstance(bd, str):
        bd = json.loads(bd)
    return DailyThemeScore(
        theme_name=row["theme_name"],
        category=SignalCategory(row["category"]),
        score_date=row["score_date"],
        base_score=float(row["base_score"]),
        momentum=float(row["momentum"]),
        final_score=float(row["final_score"]),
        cumulative_score=float(row["cumulative_score"]),
        company_count=int(row["company_count"]),
        signal_breakdown=dict(bd) if bd else {},
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/deepalpha/infrastructure/db/signal_radar_repo.py
git commit -m "feat(signal-radar): add PostgreSQL repo with daily snapshot schema"
```

---

## Task 3: Pipeline 配置 + YAML 文件

**Files:**
- Modify: `src/deepalpha/infrastructure/config.py`
- Create: `config/greenhouse_slugs.yaml`
- Create: `config/qqq_tickers.yaml`

- [ ] **Step 1: 追加 SignalRadarPipelineConfig 到 config.py**

在文件末尾追加（保留现有内容不变）：

```python
class SignalRadarPipelineConfig(BaseSettings):
    """信号趋势雷达 pipeline 全局配置，从环境变量读取。"""

    postgres_host: str = Field(title="PostgreSQL 主机")
    postgres_port: int = Field(5432, title="PostgreSQL 端口")
    postgres_db: str = Field(title="数据库名")
    postgres_user: str = Field(title="数据库用户名")
    postgres_password: str = Field(title="数据库密码")
    postgres_ssl: bool = Field(False, title="是否启用 SSL")

    minimax_api_key: str = Field("", title="MiniMax API Key")

    qqq_tickers_yaml: str = Field("config/qqq_tickers.yaml", title="QQQ 成分股配置路径")
    greenhouse_slugs_yaml: str = Field("config/greenhouse_slugs.yaml", title="Greenhouse slug 配置路径")

    edgar_lookback_days: int = Field(2, title="EDGAR 拉取最近 N 天")
    momentum_window_days: int = Field(7, title="动量计算窗口（天）")
    momentum_cap: float = Field(3.0, title="动量系数上限")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def asyncpg_dsn(self) -> str:
        ssl_param = "?sslmode=require" if self.postgres_ssl else ""
        user = quote(self.postgres_user, safe="")
        password = quote(self.postgres_password, safe="")
        return (
            f"postgresql://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}{ssl_param}"
        )
```

- [ ] **Step 2: 创建 config/qqq_tickers.yaml**

```yaml
# QQQ 纳斯达克100成分股（2026年参考）
tickers:
  - AAPL
  - MSFT
  - NVDA
  - AMZN
  - META
  - GOOGL
  - GOOG
  - TSLA
  - AVGO
  - COST
  - NFLX
  - AMD
  - PEP
  - QCOM
  - ADBE
  - TXN
  - INTU
  - AMGN
  - CMCSA
  - CSCO
  - AMAT
  - HON
  - ISRG
  - ADI
  - MU
  - LRCX
  - KLAC
  - REGN
  - PANW
  - GILD
  - SNPS
  - CDNS
  - PYPL
  - ABNB
  - CRWD
  - MRVL
  - FTNT
  - DXCM
  - CTAS
  - ADSK
  - MELI
  - IDXX
  - NXPI
  - PAYX
  - FAST
  - BIIB
  - GEHC
  - MRNA
  - ON
  - ODFL
  - ZS
  - TEAM
  - VRSK
  - ANSS
  - WDAY
  - DDOG
  - CEG
  - PCAR
  - EBAY
  - ALGN
  - ENPH
```

- [ ] **Step 3: 创建 config/greenhouse_slugs.yaml**

```yaml
# 支持 Greenhouse 或 Lever 公开 API 的 QQQ 公司
# type: greenhouse → GET https://boards.greenhouse.io/embed/job_board/jobs.json?for={slug}
# type: lever      → GET https://api.lever.co/v0/postings/{slug}?mode=json
companies:
  - ticker: NVDA
    slug: nvidia
    type: greenhouse
  - ticker: META
    slug: meta
    type: greenhouse
  - ticker: GOOGL
    slug: google
    type: greenhouse
  - ticker: MSFT
    slug: microsoft
    type: greenhouse
  - ticker: ADBE
    slug: adobe
    type: greenhouse
  - ticker: CRWD
    slug: crowdstrike
    type: greenhouse
  - ticker: PANW
    slug: paloaltonetworks
    type: greenhouse
  - ticker: DDOG
    slug: datadoghq
    type: greenhouse
  - ticker: ZS
    slug: zscaler
    type: greenhouse
  - ticker: WDAY
    slug: workday
    type: greenhouse
  - ticker: TEAM
    slug: atlassian
    type: greenhouse
  - ticker: FTNT
    slug: fortinet
    type: greenhouse
```

- [ ] **Step 4: Commit**

```bash
git add src/deepalpha/infrastructure/config.py \
        config/greenhouse_slugs.yaml config/qqq_tickers.yaml
git commit -m "feat(signal-radar): add pipeline config and ticker/slug yamls"
```

---

## Task 4: CIK 解析器

**Files:**
- Create: `src/deepalpha/infrastructure/providers/edgar/cik_resolver.py`
- Test: `tests/unit/providers/edgar/test_cik_resolver.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/providers/edgar/test_cik_resolver.py`:
```python
import httpx
import pytest
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver


async def test_resolve_known_ticker(httpx_mock):
    httpx_mock.add_response(
        url="https://www.sec.gov/files/company_tickers.json",
        json={
            "0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
            "1": {"cik_str": 789019,  "ticker": "MSFT", "title": "MICROSOFT CORP"},
        },
    )
    async with httpx.AsyncClient() as client:
        resolver = CikResolver(client)
        assert await resolver.resolve("NVDA") == "0001045810"
        assert await resolver.resolve("nvda") == "0001045810"  # 大小写不敏感


async def test_resolve_unknown_returns_none(httpx_mock):
    httpx_mock.add_response(
        url="https://www.sec.gov/files/company_tickers.json",
        json={"0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"}},
    )
    async with httpx.AsyncClient() as client:
        resolver = CikResolver(client)
        assert await resolver.resolve("UNKNOWN") is None
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/edgar/test_cik_resolver.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现 cik_resolver.py**

`src/deepalpha/infrastructure/providers/edgar/cik_resolver.py`:
```python
"""SEC EDGAR Ticker→CIK 映射（无需 API Key）"""
import logging
import httpx

logger = logging.getLogger(__name__)
_URL = "https://www.sec.gov/files/company_tickers.json"
_HEADERS = {"User-Agent": "DeepAlpha contact@deepalpha.club"}


class CikResolver:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._cache: dict[str, str] | None = None

    async def _load(self) -> None:
        if self._cache is not None:
            return
        resp = await self._client.get(_URL, headers=_HEADERS)
        resp.raise_for_status()
        self._cache = {
            v["ticker"].upper(): str(v["cik_str"]).zfill(10)
            for v in resp.json().values()
        }

    async def resolve(self, ticker: str) -> str | None:
        """返回零填充10位 CIK 字符串，ticker 不存在则返回 None。"""
        await self._load()
        assert self._cache is not None
        return self._cache.get(ticker.upper())
```

- [ ] **Step 4: 运行确认通过**

```bash
uv run pytest tests/unit/providers/edgar/test_cik_resolver.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/infrastructure/providers/edgar/cik_resolver.py \
        tests/unit/providers/edgar/test_cik_resolver.py
git commit -m "feat(signal-radar): add SEC EDGAR CIK resolver"
```

---

## Task 5: 8-K 电话会议 Loader

**Files:**
- Create: `src/deepalpha/infrastructure/providers/edgar/filing_8k_loader.py`
- Test: `tests/unit/providers/edgar/test_filing_8k_loader.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/providers/edgar/test_filing_8k_loader.py`:
```python
import datetime
import httpx
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver
from deepalpha.infrastructure.providers.edgar.filing_8k_loader import Filing8KLoader

_TICKERS_JSON = {"0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"}}

_SUBMISSIONS = {
    "filings": {
        "recent": {
            "form":            ["8-K",                   "10-Q"],
            "accessionNumber": ["0001045810-26-000001",  "0001045810-26-000002"],
            "filingDate":      ["2026-06-06",            "2026-06-05"],
            "primaryDocument": ["nvda-20260606.htm",     "nvda-20260605.htm"],
        }
    }
}


async def test_fetch_returns_8k_only(httpx_mock):
    httpx_mock.add_response(url="https://www.sec.gov/files/company_tickers.json", json=_TICKERS_JSON)
    httpx_mock.add_response(url="https://data.sec.gov/submissions/CIK0001045810.json", json=_SUBMISSIONS)
    httpx_mock.add_response(
        url="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000001/nvda-20260606.htm",
        text="We are investing in HBM3e memory and liquid cooling infrastructure.",
    )
    async with httpx.AsyncClient() as client:
        loader = Filing8KLoader(client, CikResolver(client))
        items = await loader.fetch("NVDA", since=datetime.date(2026, 6, 5))
    assert len(items) == 1
    assert items[0].source_type == "earnings_call"
    assert "HBM3e" in items[0].text_snippet


async def test_fetch_unknown_ticker_returns_empty(httpx_mock):
    httpx_mock.add_response(url="https://www.sec.gov/files/company_tickers.json", json=_TICKERS_JSON)
    async with httpx.AsyncClient() as client:
        loader = Filing8KLoader(client, CikResolver(client))
        items = await loader.fetch("UNKNOWN", since=datetime.date(2026, 6, 5))
    assert items == []
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/edgar/test_filing_8k_loader.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现 filing_8k_loader.py**

`src/deepalpha/infrastructure/providers/edgar/filing_8k_loader.py`:
```python
"""SEC EDGAR 8-K 电话会议文本采集器"""
import datetime
import logging
import re
import httpx
from deepalpha.domain.signal_radar.models import RawSignalItem
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver

logger = logging.getLogger(__name__)
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"
_DOC_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{doc}"
_HEADERS = {"User-Agent": "DeepAlpha contact@deepalpha.club"}


class Filing8KLoader:
    def __init__(self, client: httpx.AsyncClient, resolver: CikResolver) -> None:
        self._client = client
        self._resolver = resolver

    async def fetch(self, ticker: str, since: datetime.date) -> list[RawSignalItem]:
        cik10 = await self._resolver.resolve(ticker)
        if not cik10:
            logger.warning("无法解析 CIK: %s", ticker)
            return []
        try:
            resp = await self._client.get(_SUBMISSIONS_URL.format(cik10=cik10), headers=_HEADERS)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("获取 submissions 失败 %s: %s", ticker, exc)
            return []

        recent = resp.json().get("filings", {}).get("recent", {})
        items: list[RawSignalItem] = []
        cik_int = int(cik10)

        for form, acc, date_str, doc in zip(
            recent.get("form", []),
            recent.get("accessionNumber", []),
            recent.get("filingDate", []),
            recent.get("primaryDocument", []),
        ):
            if form != "8-K":
                continue
            filing_date = datetime.date.fromisoformat(date_str)
            if filing_date < since:
                break
            text = await self._fetch_text(cik_int, acc, doc)
            items.append(RawSignalItem(
                ticker=ticker,
                source_type="earnings_call",
                signal_date=filing_date,
                doc_id=acc,
                text_snippet=text[:2000],
            ))
        return items

    async def _fetch_text(self, cik_int: int, acc: str, doc: str) -> str:
        url = _DOC_URL.format(cik_int=cik_int, acc_nodash=acc.replace("-", ""), doc=doc)
        try:
            resp = await self._client.get(url, headers=_HEADERS)
            resp.raise_for_status()
            text = re.sub(r"<[^>]+>", " ", resp.text)
            return re.sub(r"\s+", " ", text).strip()
        except httpx.HTTPError as exc:
            logger.error("获取 8-K 文件失败: %s", exc)
            return ""
```

- [ ] **Step 4: 运行确认通过**

```bash
uv run pytest tests/unit/providers/edgar/test_filing_8k_loader.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/infrastructure/providers/edgar/filing_8k_loader.py \
        tests/unit/providers/edgar/test_filing_8k_loader.py
git commit -m "feat(signal-radar): add SEC EDGAR 8-K loader"
```

---

## Task 6: XBRL Capex Loader

**Files:**
- Create: `src/deepalpha/infrastructure/providers/edgar/xbrl_capex_loader.py`
- Test: `tests/unit/providers/edgar/test_xbrl_capex_loader.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/providers/edgar/test_xbrl_capex_loader.py`:
```python
import datetime
import httpx
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver
from deepalpha.infrastructure.providers.edgar.xbrl_capex_loader import XbrlCapexLoader

_TICKERS_JSON = {"0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"}}

_FACTS = {
    "facts": {
        "us-gaap": {
            "PaymentsToAcquirePropertyPlantAndEquipment": {
                "units": {
                    "USD": [
                        {"end": "2026-04-30", "val": 3_500_000_000, "form": "10-Q", "filed": "2026-06-05", "frame": "CY2026Q1I"}
                    ]
                }
            }
        }
    }
}


async def test_fetch_capex_signal(httpx_mock):
    httpx_mock.add_response(url="https://www.sec.gov/files/company_tickers.json", json=_TICKERS_JSON)
    httpx_mock.add_response(url="https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json", json=_FACTS)
    async with httpx.AsyncClient() as client:
        loader = XbrlCapexLoader(client, CikResolver(client))
        items = await loader.fetch("NVDA", since=datetime.date(2026, 6, 1))
    assert len(items) == 1
    assert items[0].source_type == "capex"
    assert "3,500,000,000" in items[0].text_snippet


async def test_fetch_capex_skips_old_filings(httpx_mock):
    old_facts = {
        "facts": {"us-gaap": {"PaymentsToAcquirePropertyPlantAndEquipment": {
            "units": {"USD": [{"end": "2024-01-31", "val": 1_000_000_000, "form": "10-Q", "filed": "2024-03-01", "frame": "CY2023Q4I"}]}
        }}}
    }
    httpx_mock.add_response(url="https://www.sec.gov/files/company_tickers.json", json=_TICKERS_JSON)
    httpx_mock.add_response(url="https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json", json=old_facts)
    async with httpx.AsyncClient() as client:
        loader = XbrlCapexLoader(client, CikResolver(client))
        items = await loader.fetch("NVDA", since=datetime.date(2026, 6, 1))
    assert items == []
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/edgar/test_xbrl_capex_loader.py -v
```

- [ ] **Step 3: 实现 xbrl_capex_loader.py**

`src/deepalpha/infrastructure/providers/edgar/xbrl_capex_loader.py`:
```python
"""SEC EDGAR XBRL Capex 数据采集器"""
import datetime
import logging
import httpx
from deepalpha.domain.signal_radar.models import RawSignalItem
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver

logger = logging.getLogger(__name__)
_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"
_CONCEPT = "PaymentsToAcquirePropertyPlantAndEquipment"
_HEADERS = {"User-Agent": "DeepAlpha contact@deepalpha.club"}


class XbrlCapexLoader:
    def __init__(self, client: httpx.AsyncClient, resolver: CikResolver) -> None:
        self._client = client
        self._resolver = resolver

    async def fetch(self, ticker: str, since: datetime.date) -> list[RawSignalItem]:
        cik10 = await self._resolver.resolve(ticker)
        if not cik10:
            return []
        try:
            resp = await self._client.get(_FACTS_URL.format(cik10=cik10), headers=_HEADERS)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("获取 XBRL facts 失败 %s: %s", ticker, exc)
            return []

        entries = (
            resp.json().get("facts", {}).get("us-gaap", {})
            .get(_CONCEPT, {}).get("units", {}).get("USD", [])
        )
        items: list[RawSignalItem] = []
        for e in entries:
            filed_str = e.get("filed", "")
            if not filed_str or datetime.date.fromisoformat(filed_str) < since:
                continue
            val = e.get("val", 0)
            end = e.get("end", "")
            frame = e.get("frame", end)
            text = (
                f"{ticker} capital expenditure ({_CONCEPT}): "
                f"{val:,.0f} USD for period ending {end}, "
                f"filed {filed_str} via {e.get('form', '')}."
            )
            items.append(RawSignalItem(
                ticker=ticker,
                source_type="capex",
                signal_date=datetime.date.fromisoformat(filed_str),
                doc_id=f"{ticker}-capex-{frame}",
                text_snippet=text,
            ))
        return items
```

- [ ] **Step 4: 运行确认通过**

```bash
uv run pytest tests/unit/providers/edgar/test_xbrl_capex_loader.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/infrastructure/providers/edgar/xbrl_capex_loader.py \
        tests/unit/providers/edgar/test_xbrl_capex_loader.py
git commit -m "feat(signal-radar): add SEC EDGAR XBRL Capex loader"
```

---

## Task 7: Form D 融资 Loader

**Files:**
- Create: `src/deepalpha/infrastructure/providers/edgar/form_d_loader.py`
- Test: `tests/unit/providers/edgar/test_form_d_loader.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/providers/edgar/test_form_d_loader.py`:
```python
import pytest
from deepalpha.infrastructure.providers.edgar.form_d_loader import _parse_business_desc


def test_parse_business_desc_extracts_text():
    xml = """<?xml version="1.0"?>
<edgarSubmission>
  <offeringData>
    <businessDescription>AI inference platform using MCP protocol and HBM memory</businessDescription>
  </offeringData>
</edgarSubmission>"""
    desc = _parse_business_desc(xml)
    assert "MCP" in desc
    assert "HBM" in desc


def test_parse_business_desc_missing_tag_returns_empty():
    xml = "<edgarSubmission><offeringData></offeringData></edgarSubmission>"
    assert _parse_business_desc(xml) == ""


def test_parse_business_desc_malformed_xml_returns_empty():
    assert _parse_business_desc("not xml at all <<<") == ""
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/edgar/test_form_d_loader.py -v
```

- [ ] **Step 3: 实现 form_d_loader.py**

`src/deepalpha/infrastructure/providers/edgar/form_d_loader.py`:
```python
"""
SEC EDGAR Form D 融资申报采集器

通过 EFTS 全文检索获取科技类创业融资 Form D，
提取 businessDescription 字段作为信号文本。
"""
import datetime
import logging
import xml.etree.ElementTree as ET
import httpx
from deepalpha.domain.signal_radar.models import RawSignalItem

logger = logging.getLogger(__name__)
_EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
_DOC_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/primary_doc.xml"
_HEADERS = {"User-Agent": "DeepAlpha contact@deepalpha.club"}


def _parse_business_desc(xml_text: str) -> str:
    """从 Form D XML 提取 businessDescription 字段文本。"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return ""
    # Form D XML 命名空间可能为空或有前缀，使用无命名空间匹配
    for tag in ["businessDescription", ".//businessDescription"]:
        elem = root.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
    return ""


class FormDLoader:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def fetch(
        self,
        since: datetime.date,
        until: datetime.date,
        max_items: int = 50,
    ) -> list[RawSignalItem]:
        """采集 since~until 期间的 Form D 融资申报。"""
        params = {
            "forms": "D",
            "dateRange": "custom",
            "startdt": since.isoformat(),
            "enddt": until.isoformat(),
            "hits.hits.total": "true",
        }
        try:
            resp = await self._client.get(_EFTS_URL, params=params, headers=_HEADERS)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("EFTS Form D 搜索失败: %s", exc)
            return []

        hits = resp.json().get("hits", {}).get("hits", [])
        items: list[RawSignalItem] = []

        for hit in hits[:max_items]:
            src = hit.get("_source", {})
            acc = src.get("accession_no", "")
            file_date_str = src.get("file_date", "")
            entity = src.get("entity_name", "Unknown")
            if not acc or not file_date_str:
                continue

            # CIK 是 accession number 第一段（10位）
            cik_int = int(acc.split("-")[0])
            acc_nodash = acc.replace("-", "")
            doc_url = _DOC_URL.format(cik_int=cik_int, acc_nodash=acc_nodash)

            try:
                doc_resp = await self._client.get(doc_url, headers=_HEADERS)
                doc_resp.raise_for_status()
                desc = _parse_business_desc(doc_resp.text)
            except httpx.HTTPError:
                desc = ""

            if not desc:
                continue

            text = f"[Form D] {entity}: {desc}"
            items.append(RawSignalItem(
                ticker="__FORM_D__",
                source_type="form_d",
                signal_date=datetime.date.fromisoformat(file_date_str),
                doc_id=acc,
                text_snippet=text[:2000],
            ))

        return items
```

- [ ] **Step 4: 运行确认通过**

```bash
uv run pytest tests/unit/providers/edgar/test_form_d_loader.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/infrastructure/providers/edgar/form_d_loader.py \
        tests/unit/providers/edgar/test_form_d_loader.py
git commit -m "feat(signal-radar): add SEC EDGAR Form D loader"
```

---

## Task 8: Greenhouse/Lever 招聘 Loader

**Files:**
- Create: `src/deepalpha/infrastructure/providers/greenhouse/job_loader.py`
- Test: `tests/unit/providers/greenhouse/test_job_loader.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/providers/greenhouse/test_job_loader.py`:
```python
import datetime
import httpx
from deepalpha.infrastructure.providers.greenhouse.job_loader import JobLoader, CompanySlug


async def test_fetch_greenhouse_jobs(httpx_mock):
    httpx_mock.add_response(
        url="https://boards.greenhouse.io/embed/job_board/jobs.json?for=nvidia",
        json={
            "jobs": [
                {"title": "Senior HBM Memory Architect", "departments": [{"name": "Hardware Engineering"}], "updated_at": "2026-06-06T00:00:00Z"},
                {"title": "AI Inference Optimization Engineer", "departments": [{"name": "Software"}], "updated_at": "2026-06-06T00:00:00Z"},
            ]
        },
    )
    slug = CompanySlug(ticker="NVDA", slug="nvidia", type="greenhouse")
    async with httpx.AsyncClient() as client:
        loader = JobLoader(client)
        items = await loader.fetch(slug, since=datetime.date(2026, 6, 5))
    assert len(items) == 1  # 合并为一条 text_snippet
    assert items[0].source_type == "job_posting"
    assert "HBM Memory Architect" in items[0].text_snippet


async def test_fetch_lever_jobs(httpx_mock):
    httpx_mock.add_response(
        url="https://api.lever.co/v0/postings/crowdstrike?mode=json",
        json=[
            {"text": "AI Security Engineer", "categories": {"department": "Engineering"}, "createdAt": 1749168000000},
        ],
    )
    slug = CompanySlug(ticker="CRWD", slug="crowdstrike", type="lever")
    async with httpx.AsyncClient() as client:
        loader = JobLoader(client)
        items = await loader.fetch(slug, since=datetime.date(2026, 6, 5))
    assert len(items) == 1
    assert "AI Security Engineer" in items[0].text_snippet
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/greenhouse/test_job_loader.py -v
```

- [ ] **Step 3: 实现 job_loader.py**

`src/deepalpha/infrastructure/providers/greenhouse/job_loader.py`:
```python
"""
Greenhouse / Lever 招聘 JD 采集器

通过公开 JSON API 获取职位列表（无需 API Key），
将同一公司所有职位标题聚合为一条信号文本。
"""
import datetime
import logging
from dataclasses import dataclass
import httpx
from deepalpha.domain.signal_radar.models import RawSignalItem

logger = logging.getLogger(__name__)
_GH_URL = "https://boards.greenhouse.io/embed/job_board/jobs.json?for={slug}"
_LEVER_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


@dataclass
class CompanySlug:
    ticker: str
    slug: str
    type: str  # "greenhouse" | "lever"


class JobLoader:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def fetch(self, company: CompanySlug, since: datetime.date) -> list[RawSignalItem]:
        if company.type == "greenhouse":
            return await self._fetch_greenhouse(company, since)
        elif company.type == "lever":
            return await self._fetch_lever(company, since)
        return []

    async def _fetch_greenhouse(self, company: CompanySlug, since: datetime.date) -> list[RawSignalItem]:
        url = _GH_URL.format(slug=company.slug)
        try:
            resp = await self._client.get(url, timeout=10.0)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Greenhouse 请求失败 %s: %s", company.slug, exc)
            return []

        jobs = resp.json().get("jobs", [])
        titles = []
        for job in jobs:
            updated = job.get("updated_at", "")
            if updated and datetime.date.fromisoformat(updated[:10]) < since:
                continue
            dept = ""
            if job.get("departments"):
                dept = job["departments"][0].get("name", "")
            titles.append(f"{job.get('title', '')} [{dept}]")

        if not titles:
            return []
        text = f"[{company.ticker}] Recent job postings: " + "; ".join(titles)
        return [RawSignalItem(
            ticker=company.ticker,
            source_type="job_posting",
            signal_date=since,
            doc_id=f"{company.ticker}-jobs-{since.isoformat()}",
            text_snippet=text[:2000],
        )]

    async def _fetch_lever(self, company: CompanySlug, since: datetime.date) -> list[RawSignalItem]:
        url = _LEVER_URL.format(slug=company.slug)
        try:
            resp = await self._client.get(url, timeout=10.0)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Lever 请求失败 %s: %s", company.slug, exc)
            return []

        postings = resp.json() if isinstance(resp.json(), list) else []
        titles = []
        for p in postings:
            # Lever 时间戳为毫秒 Unix 时间戳
            created_ms = p.get("createdAt", 0)
            created = datetime.date.fromtimestamp(created_ms / 1000)
            if created < since:
                continue
            dept = p.get("categories", {}).get("department", "")
            titles.append(f"{p.get('text', '')} [{dept}]")

        if not titles:
            return []
        text = f"[{company.ticker}] Recent job postings: " + "; ".join(titles)
        return [RawSignalItem(
            ticker=company.ticker,
            source_type="job_posting",
            signal_date=since,
            doc_id=f"{company.ticker}-jobs-{since.isoformat()}",
            text_snippet=text[:2000],
        )]
```

- [ ] **Step 4: 运行确认通过**

```bash
uv run pytest tests/unit/providers/greenhouse/test_job_loader.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/infrastructure/providers/greenhouse/job_loader.py \
        tests/unit/providers/greenhouse/test_job_loader.py
git commit -m "feat(signal-radar): add Greenhouse/Lever job loader"
```

---

## Task 9: MiniMax 主题提取器

**Files:**
- Create: `src/deepalpha/infrastructure/providers/minimax/theme_extractor.py`
- Test: `tests/unit/providers/minimax/test_theme_extractor.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/providers/minimax/test_theme_extractor.py`:
```python
import httpx
from deepalpha.infrastructure.providers.minimax.theme_extractor import ThemeExtractor
from deepalpha.domain.signal_radar.models import SignalCategory

_API_URL = "https://api.minimax.chat/v1/chat/completions"


async def test_extract_themes(httpx_mock):
    httpx_mock.add_response(
        url=_API_URL,
        json={
            "choices": [{
                "message": {
                    "content": '{"themes":[{"name":"HBM3e","category":"infra_component","confidence":0.92},{"name":"MCP","category":"tech_concept","confidence":0.85}]}'
                }
            }]
        },
    )
    async with httpx.AsyncClient() as client:
        extractor = ThemeExtractor(client, api_key="test-key")
        themes = await extractor.extract("We are building HBM3e memory systems with MCP protocol.", "earnings_call")
    assert len(themes) == 2
    assert themes[0].name == "HBM3e"
    assert themes[0].category == SignalCategory.infra_component
    assert themes[1].name == "MCP"


async def test_extract_returns_empty_on_api_error(httpx_mock):
    httpx_mock.add_response(url=_API_URL, status_code=500)
    async with httpx.AsyncClient() as client:
        extractor = ThemeExtractor(client, api_key="test-key")
        themes = await extractor.extract("some text", "capex")
    assert themes == []


async def test_extract_filters_low_confidence(httpx_mock):
    httpx_mock.add_response(
        url=_API_URL,
        json={
            "choices": [{
                "message": {
                    "content": '{"themes":[{"name":"HBM3e","category":"infra_component","confidence":0.92},{"name":"vague","category":"tech_concept","confidence":0.3}]}'
                }
            }]
        },
    )
    async with httpx.AsyncClient() as client:
        extractor = ThemeExtractor(client, api_key="test-key")
        themes = await extractor.extract("text", "earnings_call")
    assert len(themes) == 1
    assert themes[0].name == "HBM3e"
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/minimax/test_theme_extractor.py -v
```

- [ ] **Step 3: 实现 theme_extractor.py**

`src/deepalpha/infrastructure/providers/minimax/theme_extractor.py`:
```python
"""
MiniMax LLM 主题提取器

从信号文本中提取细粒度技术/基础设施/工程概念关键词。
复用 translator.py 中相同的 API 调用模式。
"""
import json
import logging
import httpx
from deepalpha.domain.signal_radar.models import ExtractedTheme, SignalCategory

logger = logging.getLogger(__name__)
_API_URL = "https://api.minimax.chat/v1/chat/completions"
_MODEL = "MiniMax-Text-01"
_MIN_CONFIDENCE = 0.6

_SYSTEM_PROMPT = """你是一个专业的技术信号分析师，从公司文件中提取细粒度的技术/基础设施/工程关键词。

提取规则：
✅ 合格（提取这些）：
- 技术关键词：MCP、Agent Memory、Mixture of Experts、RAG Pipeline、RLHF Pipeline
- 基础设施组件：HBM3e、NVLink、InfiniBand、液冷机柜、定制ASIC、CoWoS封装、光互连
- 新兴工程概念：AI Compiler、Inference Optimization、Post-Training、Speculative Decoding

❌ 不合格（不要提取这些）：
- 行业大词：AI、云计算、数字化转型、机器学习
- 公司名/品牌名：NVIDIA、OpenAI（但产品型号如"H100"可以）
- 财务指标：营收增长、毛利率、EPS

判断标准：
1. 可以出现在工程师招聘 JD 的技能要求中
2. 可以对应到具体 Capex 支出或融资金额
3. 多家公司同期提到（跨公司共现）

输出格式（严格 JSON，不要 markdown 代码块）：
{"themes":[{"name":"标准化名称","category":"tech_concept|infra_component|engineering_concept","confidence":0.0-1.0}]}

每条信号最多提取5个主题，名称使用英文缩写或规范术语。"""


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    if "```" in text:
        start = text.find("```")
        end = text.rfind("```")
        if start != end:
            text = text[start + 3:end]
            if text.startswith("json"):
                text = text[4:]
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


class ThemeExtractor:
    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._api_key = api_key

    async def extract(self, text: str, source_type: str) -> list[ExtractedTheme]:
        """从文本中提取主题，返回置信度 >= 0.6 的结果。"""
        if not text.strip():
            return []
        try:
            resp = await self._client.post(
                _API_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": _MODEL,
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": f"[{source_type}] {text[:2000]}"},
                    ],
                    "temperature": 0.1,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("主题提取 API 失败: %s", exc)
            return []

        try:
            content = resp.json()["choices"][0]["message"]["content"]
            data = _extract_json(content)
            themes = []
            for t in data.get("themes", []):
                try:
                    theme = ExtractedTheme(
                        name=t["name"],
                        category=SignalCategory(t["category"]),
                        confidence=float(t["confidence"]),
                    )
                    if theme.confidence >= _MIN_CONFIDENCE:
                        themes.append(theme)
                except Exception:
                    continue
            return themes
        except Exception as exc:
            logger.error("主题解析失败: %s", exc)
            return []
```

- [ ] **Step 4: 运行确认通过**

```bash
uv run pytest tests/unit/providers/minimax/test_theme_extractor.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/infrastructure/providers/minimax/theme_extractor.py \
        tests/unit/providers/minimax/test_theme_extractor.py
git commit -m "feat(signal-radar): add MiniMax theme extractor"
```

---

## Task 10: 评分引擎（纯函数）

**Files:**
- Create: `src/deepalpha/interface/pipeline/signal_radar/scoring.py`
- Test: `tests/unit/signal_radar/test_scoring.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/signal_radar/test_scoring.py`:
```python
import datetime
from deepalpha.domain.signal_radar.models import ExtractedTheme, SignalCategory, ThemeSignal
from deepalpha.interface.pipeline.signal_radar.scoring import compute_daily_scores

TODAY = datetime.date(2026, 6, 7)

def _theme(name: str, cat: SignalCategory = SignalCategory.tech_concept, conf: float = 0.9) -> ExtractedTheme:
    return ExtractedTheme(name=name, category=cat, confidence=conf)

def _signal(name: str, source: str, ticker: str = "NVDA") -> ThemeSignal:
    return ThemeSignal(theme=_theme(name), source_type=source, ticker=ticker)


def test_base_score_uses_source_weights():
    signals = [
        _signal("HBM3e", "capex"),       # weight=4, conf=0.9 → 3.6
        _signal("HBM3e", "earnings_call"), # weight=3, conf=0.9 → 2.7
    ]
    scores = compute_daily_scores(signals, past_scores={}, prev_cumulative={}, today=TODAY)
    assert len(scores) == 1
    assert abs(scores[0].base_score - 6.3) < 0.01


def test_momentum_caps_at_configured_max():
    signals = [_signal("MCP", "capex")]
    # 过去7天均值极低 → 动量 = 3.6/0.01 = 360，但 cap 为 3.0
    scores = compute_daily_scores(
        signals, past_scores={"MCP": 0.01}, prev_cumulative={}, today=TODAY, momentum_cap=3.0
    )
    assert scores[0].momentum == 3.0


def test_cumulative_adds_to_previous():
    signals = [_signal("MCP", "earnings_call")]  # base = 2.7, momentum=1.0 (no past), final=2.7
    scores = compute_daily_scores(
        signals, past_scores={}, prev_cumulative={"MCP": 100.0}, today=TODAY
    )
    assert scores[0].cumulative_score > 100.0


def test_company_count_tracks_unique_tickers():
    signals = [
        ThemeSignal(theme=_theme("HBM3e"), source_type="capex", ticker="NVDA"),
        ThemeSignal(theme=_theme("HBM3e"), source_type="capex", ticker="AMD"),
        ThemeSignal(theme=_theme("HBM3e"), source_type="capex", ticker="NVDA"),  # 重复
    ]
    scores = compute_daily_scores(signals, past_scores={}, prev_cumulative={}, today=TODAY)
    assert scores[0].company_count == 2
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/signal_radar/test_scoring.py -v
```

- [ ] **Step 3: 实现 scoring.py**

`src/deepalpha/interface/pipeline/signal_radar/scoring.py`:
```python
"""
信号趋势雷达评分引擎（纯函数，无 I/O）

最终分 = 加权基础分 × min(动量系数, cap)
动量系数 = 今日基础分 / max(过去N天均值, 1)
"""
import datetime
from deepalpha.domain.signal_radar.models import DailyThemeScore, SignalCategory, ThemeSignal

_SOURCE_WEIGHTS: dict[str, int] = {
    "earnings_call": 3,
    "capex":         4,
    "form_d":        2,
    "job_posting":   1,
}


def compute_daily_scores(
    signals: list[ThemeSignal],
    past_scores: dict[str, float],      # theme_name → 过去 N 天平均基础分
    prev_cumulative: dict[str, float],  # theme_name → 截至昨日的累计分
    today: datetime.date,
    momentum_cap: float = 3.0,
) -> list[DailyThemeScore]:
    """计算今日所有主题的得分快照列表。"""
    base: dict[str, float] = {}
    breakdown: dict[str, dict[str, float]] = {}
    companies: dict[str, set[str]] = {}
    categories: dict[str, SignalCategory] = {}

    for sig in signals:
        name = sig.theme.name
        weight = _SOURCE_WEIGHTS.get(sig.source_type, 1)
        contribution = weight * sig.theme.confidence

        if name not in base:
            base[name] = 0.0
            breakdown[name] = {}
            companies[name] = set()
            categories[name] = sig.theme.category

        base[name] += contribution
        breakdown[name][sig.source_type] = (
            breakdown[name].get(sig.source_type, 0.0) + contribution
        )
        companies[name].add(sig.ticker)

    results: list[DailyThemeScore] = []
    for name, base_score in base.items():
        avg_past = past_scores.get(name, 0.0)
        momentum = base_score / max(avg_past, 1.0)
        momentum = min(momentum, momentum_cap)
        final = base_score * momentum
        cumulative = prev_cumulative.get(name, 0.0) + final
        results.append(DailyThemeScore(
            theme_name=name,
            category=categories[name],
            score_date=today,
            base_score=round(base_score, 4),
            momentum=round(momentum, 4),
            final_score=round(final, 4),
            cumulative_score=round(cumulative, 4),
            company_count=len(companies[name]),
            signal_breakdown={k: round(v, 4) for k, v in breakdown[name].items()},
        ))
    return sorted(results, key=lambda s: s.final_score, reverse=True)
```

- [ ] **Step 4: 运行确认通过**

```bash
uv run pytest tests/unit/signal_radar/test_scoring.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/interface/pipeline/signal_radar/scoring.py \
        tests/unit/signal_radar/test_scoring.py
git commit -m "feat(signal-radar): add weighted momentum scoring engine"
```

---

## Task 11: Pipeline 主入口

**Files:**
- Create: `src/deepalpha/interface/pipeline/signal_radar/run.py`

- [ ] **Step 1: 实现 run.py**

`src/deepalpha/interface/pipeline/signal_radar/run.py`:
```python
"""
信号趋势雷达 Pipeline

调度建议：每日 UTC 06:00 运行一次（cron: 0 6 * * *）

流程：
  1. 读取 qqq_tickers.yaml 和 greenhouse_slugs.yaml
  2. 并发采集 8-K / XBRL Capex（按 ticker 并发）
  3. 串行采集 Form D（跨公司，单次搜索）
  4. 并发采集 Greenhouse/Lever 招聘
  5. 批量 LLM 提取主题
  6. 计算加权动量评分
  7. 写入 PostgreSQL 每日快照
"""
import asyncio
import datetime
import logging
from pathlib import Path

import httpx
import yaml

from deepalpha.infrastructure.config import SignalRadarPipelineConfig
from deepalpha.infrastructure.db.signal_radar_repo import SignalRadarRepo
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver
from deepalpha.infrastructure.providers.edgar.filing_8k_loader import Filing8KLoader
from deepalpha.infrastructure.providers.edgar.form_d_loader import FormDLoader
from deepalpha.infrastructure.providers.edgar.xbrl_capex_loader import XbrlCapexLoader
from deepalpha.infrastructure.providers.greenhouse.job_loader import CompanySlug, JobLoader
from deepalpha.infrastructure.providers.minimax.theme_extractor import ThemeExtractor
from deepalpha.domain.signal_radar.models import RawSignalItem, ThemeSignal
from deepalpha.interface.pipeline.signal_radar.scoring import compute_daily_scores

logger = logging.getLogger(__name__)


def load_tickers(yaml_path: str) -> list[str]:
    path = Path(yaml_path)
    if not path.exists():
        logger.warning("QQQ tickers 配置不存在: %s", yaml_path)
        return []
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("tickers", [])


def load_slugs(yaml_path: str) -> list[CompanySlug]:
    path = Path(yaml_path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [
        CompanySlug(ticker=c["ticker"], slug=c["slug"], type=c["type"])
        for c in data.get("companies", [])
    ]


async def collect_all_signals(
    tickers: list[str],
    slugs: list[CompanySlug],
    since: datetime.date,
    until: datetime.date,
    client: httpx.AsyncClient,
) -> list[RawSignalItem]:
    resolver = CikResolver(client)
    loader_8k = Filing8KLoader(client, resolver)
    loader_capex = XbrlCapexLoader(client, resolver)
    loader_form_d = FormDLoader(client)
    loader_jobs = JobLoader(client)

    # 8-K 和 XBRL 按 ticker 并发（限制并发数避免 EDGAR 限速）
    sem = asyncio.Semaphore(5)

    async def fetch_ticker(ticker: str) -> list[RawSignalItem]:
        async with sem:
            items_8k = await loader_8k.fetch(ticker, since)
            await asyncio.sleep(0.1)  # EDGAR 礼貌延迟
            items_capex = await loader_capex.fetch(ticker, since)
            return items_8k + items_capex

    ticker_results = await asyncio.gather(*[fetch_ticker(t) for t in tickers])
    all_items: list[RawSignalItem] = [item for sublist in ticker_results for item in sublist]

    # Form D 单次全量搜索
    form_d_items = await loader_form_d.fetch(since=since, until=until)
    all_items.extend(form_d_items)

    # Greenhouse/Lever 并发（公司较少）
    job_results = await asyncio.gather(*[loader_jobs.fetch(slug, since) for slug in slugs])
    all_items.extend([item for sublist in job_results for item in sublist])

    logger.info("采集完成，共 %d 条原始信号", len(all_items))
    return all_items


async def main(config: SignalRadarPipelineConfig | None = None) -> None:
    if config is None:
        config = SignalRadarPipelineConfig()

    today = datetime.date.today()
    since = today - datetime.timedelta(days=config.edgar_lookback_days)

    tickers = load_tickers(config.qqq_tickers_yaml)
    slugs = load_slugs(config.greenhouse_slugs_yaml)
    if not tickers:
        logger.warning("无 QQQ tickers 配置，退出")
        return

    logger.info("开始信号雷达 pipeline，日期: %s，监控 %d 个 ticker", today, len(tickers))

    repo = await SignalRadarRepo.create(config.asyncpg_dsn())
    try:
        await repo.log_pipeline_run(today)
        items_fetched = 0
        themes_extracted = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            all_items = await collect_all_signals(tickers, slugs, since, today, client)
            extractor = ThemeExtractor(client, api_key=config.minimax_api_key)

            # 去重并存储原始信号，提取主题
            all_signals: list[ThemeSignal] = []
            for item in all_items:
                if await repo.is_raw_item_processed(item.ticker, item.source_type, item.doc_id):
                    continue
                raw_id = await repo.insert_raw_item(
                    item.ticker, item.source_type, item.signal_date, item.doc_id, item.text_snippet
                )
                items_fetched += 1
                themes = await extractor.extract(item.text_snippet, item.source_type)
                if themes:
                    await repo.insert_extracted_themes(raw_id, themes, today)
                    themes_extracted += len(themes)
                    for t in themes:
                        all_signals.append(ThemeSignal(theme=t, source_type=item.source_type, ticker=item.ticker))
                await asyncio.sleep(0.05)  # MiniMax 限速保护

        # 计算今日评分
        if all_signals:
            theme_names = list({s.theme.name for s in all_signals})
            past_scores = await repo.get_past_base_scores(
                theme_names, today, config.momentum_window_days
            )
            prev_cumulative = await repo.get_cumulative_scores(theme_names, today)
            daily_scores = compute_daily_scores(
                all_signals, past_scores, prev_cumulative, today, config.momentum_cap
            )
            await repo.upsert_daily_scores(daily_scores)
            logger.info("写入 %d 个主题得分快照", len(daily_scores))

        await repo.update_pipeline_run(today, "success", items_fetched, themes_extracted, None)
        logger.info("Pipeline 完成：%d 条新信号，%d 个主题", items_fetched, themes_extracted)

    except Exception as exc:
        logger.error("Pipeline 失败: %s", exc, exc_info=True)
        await repo.update_pipeline_run(today, "failed", 0, 0, str(exc))
        raise
    finally:
        await repo.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(main())
```

- [ ] **Step 2: 运行 lint 检查**

```bash
uv run ruff check src/deepalpha/interface/pipeline/signal_radar/run.py
```
Expected: 无报错

- [ ] **Step 3: Commit**

```bash
git add src/deepalpha/interface/pipeline/signal_radar/run.py
git commit -m "feat(signal-radar): add daily pipeline main entry"
```

---

## Task 12: FastAPI 路由

**Files:**
- Create: `src/deepalpha/interface/web/routers/signal_radar.py`
- Modify: `src/deepalpha/interface/web/app.py`

- [ ] **Step 1: 实现 signal_radar.py**

`src/deepalpha/interface/web/routers/signal_radar.py`:
```python
"""信号趋势雷达 API 路由"""
import datetime
from typing import Annotated, AsyncGenerator

import asyncpg
from fastapi import APIRouter, Depends, Query

from deepalpha.domain.signal_radar.models import DailyThemeScore
from deepalpha.infrastructure.config import SignalRadarPipelineConfig
from deepalpha.infrastructure.db.signal_radar_repo import SignalRadarRepo

router = APIRouter(prefix="/signal-radar", tags=["signal-radar"])

# 模块级 pool，第一次请求时初始化，之后复用
_pool: asyncpg.Pool | None = None  # type: ignore[type-arg]


async def _get_repo() -> AsyncGenerator[SignalRadarRepo, None]:
    global _pool
    if _pool is None:
        cfg = SignalRadarPipelineConfig()
        repo_instance = await SignalRadarRepo.create(cfg.asyncpg_dsn())
        _pool = repo_instance._pool
    yield SignalRadarRepo(_pool)


RepoDep = Annotated[SignalRadarRepo, Depends(_get_repo)]


@router.get("/leaderboard", response_model=list[DailyThemeScore])
async def get_leaderboard(
    repo: RepoDep,
    date: datetime.date = Query(default_factory=datetime.date.today),
    window: str = Query("30d", description="时间窗口：7d|30d|90d|1y|3y|all"),
    category: str = Query("all", description="tech_concept|infra_component|engineering_concept|all"),
    limit: int = Query(50, ge=1, le=200),
) -> list[DailyThemeScore]:
    window_days = _parse_window(window)
    return await repo.get_leaderboard(date, window_days, category, limit)


@router.get("/trend/{theme_name}", response_model=list[DailyThemeScore])
async def get_trend(
    theme_name: str,
    repo: RepoDep,
    from_date: datetime.date = Query(alias="from", default_factory=lambda: datetime.date.today() - datetime.timedelta(days=30)),
    to_date: datetime.date = Query(alias="to", default_factory=datetime.date.today),
) -> list[DailyThemeScore]:
    return await repo.get_theme_trend(theme_name, from_date, to_date)


@router.get("/snapshot", response_model=list[DailyThemeScore])
async def get_snapshot(
    repo: RepoDep,
    date: datetime.date = Query(default_factory=datetime.date.today),
    limit: int = Query(20, ge=1, le=50),
) -> list[DailyThemeScore]:
    return await repo.get_snapshot(date, limit)


@router.get("/themes", response_model=list[str])
async def search_themes(
    repo: RepoDep,
    q: str = Query("", description="模糊搜索主题名"),
    limit: int = Query(20, ge=1, le=100),
) -> list[str]:
    return await repo.search_themes(q, limit)


def _parse_window(window: str) -> int | None:
    mapping = {"7d": 7, "30d": 30, "90d": 90, "1y": 365, "3y": 1095, "all": None}
    return mapping.get(window, 30)
```

- [ ] **Step 2: 注册 router 到 app.py**

在 `src/deepalpha/interface/web/app.py` 中添加 signal_radar router：

```python
# 导入行加入（在现有 import 列表末尾）：
from deepalpha.interface.web.routers import (
    agent, analyst, calendar, company,
    concept, financial, insider, market, news, signal_radar,
)

# include_router 行加入（在最后一行 agent router 之后）：
app.include_router(signal_radar.router, prefix="/api/v1")
```

- [ ] **Step 3: 验证 app 可启动**

```bash
uv run python -c "from deepalpha.interface.web.app import app; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/deepalpha/interface/web/routers/signal_radar.py \
        src/deepalpha/interface/web/app.py
git commit -m "feat(signal-radar): add FastAPI routes and register router"
```

---

## Task 13: Next.js /radar 前端页面

**Files:**
- Create: `frontend/app/(dashboard)/radar/page.tsx`

- [ ] **Step 1: 确认 Recharts 已安装**

```bash
cd frontend && grep recharts package.json
```
Expected: 包含 `"recharts"` 条目。若无：`pnpm add recharts`

- [ ] **Step 2: 创建 /radar 页面**

`frontend/app/(dashboard)/radar/page.tsx`:
```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend,
} from "recharts";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const WINDOWS = ["7d", "30d", "90d", "1y", "3y", "all"] as const;
const CATEGORIES = ["all", "tech_concept", "infra_component", "engineering_concept"] as const;

type Score = {
  theme_name: string;
  category: string;
  score_date: string;
  final_score: number;
  cumulative_score: number;
  company_count: number;
  signal_breakdown: Record<string, number>;
};

function categoryLabel(c: string) {
  return { tech_concept: "技术概念", infra_component: "基础设施", engineering_concept: "工程概念", all: "全部" }[c] ?? c;
}

function categoryColor(c: string) {
  return { tech_concept: "#6366f1", infra_component: "#f59e0b", engineering_concept: "#10b981" }[c] ?? "#94a3b8";
}

export default function RadarPage() {
  const [window_, setWindow] = useState<string>("30d");
  const [category, setCategory] = useState<string>("all");
  const [date, setDate] = useState<string>(new Date().toISOString().slice(0, 10));
  const [leaderboard, setLeaderboard] = useState<Score[]>([]);
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [trendData, setTrendData] = useState<Record<string, Score[]>>({});
  const [loading, setLoading] = useState(false);

  const fetchLeaderboard = useCallback(async () => {
    setLoading(true);
    try {
      const url = `${BACKEND}/api/v1/signal-radar/leaderboard?date=${date}&window=${window_}&category=${category}&limit=50`;
      const res = await fetch(url);
      const data: Score[] = await res.json();
      setLeaderboard(data);
    } finally {
      setLoading(false);
    }
  }, [date, window_, category]);

  useEffect(() => { fetchLeaderboard(); }, [fetchLeaderboard]);

  const fetchTrend = useCallback(async (themeName: string) => {
    if (trendData[themeName]) return;
    const from = new Date(date);
    from.setDate(from.getDate() - (window_ === "7d" ? 7 : window_ === "30d" ? 30 : window_ === "90d" ? 90 : window_ === "1y" ? 365 : 1095));
    const url = `${BACKEND}/api/v1/signal-radar/trend/${encodeURIComponent(themeName)}?from=${from.toISOString().slice(0, 10)}&to=${date}`;
    const res = await fetch(url);
    const data: Score[] = await res.json();
    setTrendData(prev => ({ ...prev, [themeName]: data }));
  }, [date, window_, trendData]);

  const toggleTheme = (name: string) => {
    if (selectedThemes.includes(name)) {
      setSelectedThemes(prev => prev.filter(t => t !== name));
    } else {
      setSelectedThemes(prev => [...prev, name]);
      fetchTrend(name);
    }
  };

  // RadarChart 数据：Top 8 主题
  const radarData = leaderboard.slice(0, 8).map(s => ({
    subject: s.theme_name,
    score: s.final_score,
    fullMark: Math.max(...leaderboard.slice(0, 8).map(x => x.final_score), 1),
  }));

  // 趋势图数据：合并所有选中主题的时间序列
  const allDates = Array.from(
    new Set(selectedThemes.flatMap(t => (trendData[t] ?? []).map(d => d.score_date)))
  ).sort();
  const trendChartData = allDates.map(d => {
    const point: Record<string, string | number> = { date: d };
    selectedThemes.forEach(t => {
      const row = (trendData[t] ?? []).find(r => r.score_date === d);
      point[t] = row?.final_score ?? 0;
    });
    return point;
  });

  const TREND_COLORS = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">信号趋势雷达</h1>
        <div className="flex gap-3 items-center flex-wrap">
          {/* 时光机日期 */}
          <input
            type="date"
            value={date}
            onChange={e => setDate(e.target.value)}
            className="border rounded px-2 py-1 text-sm"
          />
          {/* 时间窗口 */}
          <div className="flex gap-1">
            {WINDOWS.map(w => (
              <button
                key={w}
                onClick={() => setWindow(w)}
                className={`px-2 py-1 text-xs rounded border ${window_ === w ? "bg-indigo-600 text-white border-indigo-600" : "border-gray-300"}`}
              >
                {w}
              </button>
            ))}
          </div>
          {/* 类别筛选 */}
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="border rounded px-2 py-1 text-sm"
          >
            {CATEGORIES.map(c => <option key={c} value={c}>{categoryLabel(c)}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 雷达图 */}
        <div className="border rounded-lg p-4 bg-white">
          <h2 className="text-sm font-semibold text-gray-500 mb-3">Top 8 主题雷达图</h2>
          {loading ? (
            <div className="h-64 flex items-center justify-center text-gray-400">加载中...</div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, "auto"]} tick={{ fontSize: 9 }} />
                <Radar name="得分" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
              </RadarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* 排行榜 */}
        <div className="border rounded-lg p-4 bg-white">
          <h2 className="text-sm font-semibold text-gray-500 mb-3">
            排行榜 <span className="font-normal text-gray-400">（点击主题查看趋势）</span>
          </h2>
          <div className="overflow-y-auto max-h-72 space-y-1">
            {leaderboard.slice(0, 30).map((s, i) => (
              <div
                key={s.theme_name}
                onClick={() => toggleTheme(s.theme_name)}
                className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer hover:bg-gray-50 ${selectedThemes.includes(s.theme_name) ? "ring-1 ring-indigo-400 bg-indigo-50" : ""}`}
              >
                <span className="text-xs text-gray-400 w-5 text-right">{i + 1}</span>
                <span
                  className="text-xs px-1.5 py-0.5 rounded"
                  style={{ backgroundColor: categoryColor(s.category) + "22", color: categoryColor(s.category) }}
                >
                  {categoryLabel(s.category).slice(0, 2)}
                </span>
                <span className="text-sm font-medium flex-1 truncate">{s.theme_name}</span>
                <span className="text-xs text-gray-500">{s.company_count}家</span>
                <div className="w-20 bg-gray-100 rounded-full h-1.5">
                  <div
                    className="h-1.5 rounded-full"
                    style={{
                      width: `${Math.min((s.final_score / (leaderboard[0]?.final_score || 1)) * 100, 100)}%`,
                      backgroundColor: categoryColor(s.category),
                    }}
                  />
                </div>
                <span className="text-xs font-mono w-14 text-right">{s.final_score.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 趋势折线图 */}
      {selectedThemes.length > 0 && (
        <div className="border rounded-lg p-4 bg-white">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-500">趋势对比</h2>
            <button onClick={() => { setSelectedThemes([]); setTrendData({}); }} className="text-xs text-gray-400 hover:text-gray-600">
              清除
            </button>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendChartData}>
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Legend />
              {selectedThemes.map((t, i) => (
                <Line key={t} type="monotone" dataKey={t} stroke={TREND_COLORS[i % TREND_COLORS.length]} dot={false} strokeWidth={2} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: 验证前端编译**

```bash
cd frontend && pnpm build 2>&1 | tail -20
```
Expected: `✓ Compiled successfully` 或仅有警告（无 error）

- [ ] **Step 4: Commit**

```bash
git add frontend/app/\(dashboard\)/radar/page.tsx
git commit -m "feat(signal-radar): add Next.js /radar time-machine radar page"
```

---

## Task 14: 端到端验证

- [ ] **Step 1: 运行全部单元测试**

```bash
uv run pytest tests/unit/signal_radar/ tests/unit/providers/edgar/ \
             tests/unit/providers/greenhouse/ tests/unit/providers/minimax/ -v
```
Expected: 所有测试 PASSED，无 FAILED

- [ ] **Step 2: 验证 pipeline 可导入**

```bash
uv run python -c "from deepalpha.interface.pipeline.signal_radar.run import main; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: 集成测试（需要真实 .env）**

```bash
uv run pytest -m integration -k signal_radar -v
```
若无集成测试文件，跳过此步。

- [ ] **Step 4: 启动 FastAPI 验证路由**

```bash
uv run fastapi dev src/deepalpha/interface/web/app.py &
curl http://localhost:8000/api/v1/signal-radar/leaderboard | python -m json.tool | head -20
```
Expected: 返回 JSON 数组（空数组或有数据均可）

- [ ] **Step 5: 启动前端验证页面**

```bash
cd frontend && pnpm dev
# 打开 http://localhost:3000/radar
```
Expected: 页面加载，显示时间控件和空排行榜

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat(signal-radar): complete signal trend radar end-to-end implementation"
```
