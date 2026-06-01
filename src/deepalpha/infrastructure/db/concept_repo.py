"""
概念股池 PostgreSQL 数据层（infrastructure 适配器）

实现 IConceptRepo 协议，使用 asyncpg 进行异步读写，
所有写入操作均为幂等（ON CONFLICT DO UPDATE）。
"""

import datetime
from collections import defaultdict
from typing import Any

import asyncpg

from deepalpha.domain.concept.models import ConceptEtfMap, ConceptStock, ConceptSummary

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS concept_etf_map (
    concept          VARCHAR(100) NOT NULL,
    etf_symbol       VARCHAR(20)  NOT NULL,
    etf_name         VARCHAR(200),
    aum_million      FLOAT,
    etfdb_slug       VARCHAR(100),
    updated_at       DATE         NOT NULL,
    concept_name_zh  VARCHAR(100),
    etf_name_zh      VARCHAR(200),
    description_zh   TEXT,
    PRIMARY KEY (concept, etf_symbol)
);

CREATE TABLE IF NOT EXISTS concept_stocks (
    date           DATE         NOT NULL,
    concept        VARCHAR(100) NOT NULL,
    symbol         VARCHAR(20)  NOT NULL,
    name           VARCHAR(200),
    etf_count      INT          NOT NULL,
    total_weight   FLOAT        NOT NULL,
    etfs           TEXT,
    PRIMARY KEY (date, concept, symbol)
);
"""


class ConceptRepo:
    """asyncpg-based PostgreSQL 数据层，实现 IConceptRepo 协议。

    管理 concept_etf_map 和 concept_stocks 两张表。
    """

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None  # type: ignore[type-arg]

    async def initialize(self) -> None:
        """创建所需数据表（幂等）。复用外部连接池时应在启动时显式调用。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(_CREATE_TABLES_SQL)
            # 幂等添加新列（已存在时静默忽略）
            for col, typedef in [
                ("concept_name_zh", "VARCHAR(100)"),
                ("etf_name_zh", "VARCHAR(200)"),
                ("description_zh", "TEXT"),
            ]:
                await conn.execute(
                    f"ALTER TABLE concept_etf_map ADD COLUMN IF NOT EXISTS {col} {typedef}"
                )

    async def __aenter__(self) -> "ConceptRepo":
        self._pool = await asyncpg.create_pool(self._dsn)
        await self.initialize()
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._pool:
            await self._pool.close()

    async def replace_etf_map(self, records: list[ConceptEtfMap]) -> None:
        """全量替换 concept_etf_map：清空旧数据后重新写入。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("TRUNCATE TABLE concept_etf_map")
                if records:
                    await conn.executemany(
                        """
                        INSERT INTO concept_etf_map
                            (concept, etf_symbol, etf_name, aum_million, etfdb_slug, updated_at,
                             concept_name_zh, etf_name_zh, description_zh)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        """,
                        [(r.concept, r.etf_symbol, r.etf_name, r.aum_million, r.etfdb_slug, r.updated_at,
                          r.concept_name_zh, r.etf_name_zh, r.description_zh) for r in records],
                    )

    async def upsert_etf_map(self, records: list[ConceptEtfMap]) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO concept_etf_map (concept, etf_symbol, etf_name, aum_million, etfdb_slug, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (concept, etf_symbol) DO UPDATE
                SET etf_name = EXCLUDED.etf_name,
                    aum_million = EXCLUDED.aum_million,
                    etfdb_slug = EXCLUDED.etfdb_slug,
                    updated_at = EXCLUDED.updated_at
                """,
                [(r.concept, r.etf_symbol, r.etf_name, r.aum_million, r.etfdb_slug, r.updated_at) for r in records],
            )

    async def load_etf_map(self) -> list[ConceptEtfMap]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT concept, etf_symbol, etf_name, aum_million, etfdb_slug, updated_at,
                          concept_name_zh, etf_name_zh, description_zh
                   FROM concept_etf_map"""
            )
        return [
            ConceptEtfMap(
                concept=r["concept"],
                etf_symbol=r["etf_symbol"],
                etf_name=r["etf_name"],
                aum_million=r["aum_million"],
                etfdb_slug=r["etfdb_slug"],
                updated_at=r["updated_at"],
                concept_name_zh=r["concept_name_zh"],
                etf_name_zh=r["etf_name_zh"],
                description_zh=r["description_zh"],
            )
            for r in rows
        ]

    async def get_etfs_by_concept(self, concept: str) -> list[ConceptEtfMap]:
        """获取某概念下所有 ETF（含中文翻译）。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT concept, etf_symbol, etf_name, aum_million, etfdb_slug, updated_at,
                          concept_name_zh, etf_name_zh, description_zh
                   FROM concept_etf_map WHERE concept = $1
                   ORDER BY aum_million DESC NULLS LAST""",
                concept,
            )
        return [
            ConceptEtfMap(
                concept=r["concept"],
                etf_symbol=r["etf_symbol"],
                etf_name=r["etf_name"],
                aum_million=r["aum_million"],
                etfdb_slug=r["etfdb_slug"],
                updated_at=r["updated_at"],
                concept_name_zh=r["concept_name_zh"],
                etf_name_zh=r["etf_name_zh"],
                description_zh=r["description_zh"],
            )
            for r in rows
        ]

    async def upsert_stocks(self, date: datetime.date, records: list[ConceptStock]) -> None:
        """将概念成分股批量写入数据库。

        Args:
            date: 数据日期，作为主键的一部分
            records: 概念成分股记录列表
        """
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO concept_stocks (date, concept, symbol, name, etf_count, total_weight, etfs)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (date, concept, symbol) DO UPDATE
                SET name = EXCLUDED.name,
                    etf_count = EXCLUDED.etf_count,
                    total_weight = EXCLUDED.total_weight,
                    etfs = EXCLUDED.etfs
                """,
                [(date, r.concept, r.symbol, r.name, r.etf_count, r.total_weight, ",".join(r.etfs)) for r in records],
            )

    async def get_latest_stocks(self, concept: str) -> list[ConceptStock]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT date, concept, symbol, name, etf_count, total_weight, etfs
                FROM concept_stocks
                WHERE concept = $1
                  AND date = (SELECT MAX(date) FROM concept_stocks WHERE concept = $1)
                ORDER BY etf_count DESC, total_weight DESC
                """,
                concept,
            )
        return [_row_to_stock(r) for r in rows]

    async def get_all_summaries(self) -> list[ConceptSummary]:
        """获取所有概念的摘要信息（对齐 IConceptRepo 协议，原名 get_all_concept_summaries）。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            etf_rows = await conn.fetch(
                """SELECT concept, COUNT(*) as cnt,
                          MAX(concept_name_zh) as concept_name_zh
                   FROM concept_etf_map GROUP BY concept"""
            )
            etf_counts = {r["concept"]: r["cnt"] for r in etf_rows}
            concept_name_zh_map = {r["concept"]: r["concept_name_zh"] for r in etf_rows}

            stock_rows = await conn.fetch(
                """
                WITH latest AS (
                    SELECT concept, MAX(date) as max_date FROM concept_stocks GROUP BY concept
                )
                SELECT cs.concept, cs.date, cs.symbol, cs.etf_count
                FROM concept_stocks cs
                JOIN latest l ON cs.concept = l.concept AND cs.date = l.max_date
                ORDER BY cs.concept, cs.etf_count DESC, cs.total_weight DESC
                """
            )

        concept_data: dict[str, dict[str, Any]] = defaultdict(lambda: {"date": None, "symbols": []})
        for r in stock_rows:
            concept_data[r["concept"]]["date"] = r["date"]
            concept_data[r["concept"]]["symbols"].append(r["symbol"])

        return [
            ConceptSummary(
                concept=concept,
                concept_name_zh=concept_name_zh_map.get(concept),
                etf_count=etf_counts.get(concept, 0),
                stock_count=len(data["symbols"]),
                top_symbols=data["symbols"][:5],
                last_updated=data["date"],
            )
            for concept, data in concept_data.items()
        ]

    async def get_stocks_history(
        self, concept: str, start: datetime.date, end: datetime.date
    ) -> list[ConceptStock]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT date, concept, symbol, name, etf_count, total_weight, etfs
                FROM concept_stocks
                WHERE concept = $1 AND date >= $2 AND date <= $3
                ORDER BY date DESC, etf_count DESC
                """,
                concept, start, end,
            )
        return [_row_to_stock(r) for r in rows]


def _row_to_stock(row: Any) -> ConceptStock:
    return ConceptStock(
        date=row["date"],
        concept=row["concept"],
        symbol=row["symbol"],
        name=row["name"],
        etf_count=row["etf_count"],
        total_weight=row["total_weight"],
        etfs=row["etfs"].split(",") if row["etfs"] else [],
    )
