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
