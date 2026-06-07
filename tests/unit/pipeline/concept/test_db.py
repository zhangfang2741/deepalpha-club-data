import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from deepalpha.domain.concept.models import ConceptEtfMap, ConceptStock
from deepalpha.infrastructure.db.concept_repo import ConceptRepo as ConceptDb


def _make_mock_pool(mock_conn: AsyncMock) -> MagicMock:
    """构造模拟 asyncpg Pool，acquire() 返回给定 conn。"""
    pool = MagicMock()
    pool.close = AsyncMock()
    acm = MagicMock()
    acm.__aenter__ = AsyncMock(return_value=mock_conn)
    acm.__aexit__ = AsyncMock(return_value=False)
    pool.acquire.return_value = acm
    return pool


@pytest.mark.asyncio
async def test_upsert_etf_map_calls_executemany():
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()  # CREATE TABLE 调用
    mock_conn.executemany = AsyncMock()
    mock_pool = _make_mock_pool(mock_conn)

    records = [
        ConceptEtfMap(
            concept="Artificial Intelligence",
            etf_symbol="BOTZ",
            etf_name="Global X Robotics & AI",
            aum_million=2500.0,
            etfdb_slug="artificial-intelligence-etfs",
            updated_at=datetime.date(2026, 5, 31),
        )
    ]

    with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        async with ConceptDb("postgresql://test") as db:
            await db.upsert_etf_map(records)

    mock_conn.executemany.assert_called_once()
    call_args = mock_conn.executemany.call_args
    rows = call_args[0][1]
    assert rows[0][0] == "Artificial Intelligence"
    assert rows[0][1] == "BOTZ"


@pytest.mark.asyncio
async def test_upsert_stocks_serializes_etfs_as_comma_string():
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.executemany = AsyncMock()
    mock_pool = _make_mock_pool(mock_conn)

    records = [
        ConceptStock(
            date=datetime.date(2026, 5, 31),
            concept="AI",
            symbol="NVDA",
            etf_count=3,
            total_weight=15.5,
            etfs=["BOTZ", "AIQ", "IRBO"],
        )
    ]

    with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        async with ConceptDb("postgresql://test") as db:
            await db.upsert_stocks(datetime.date(2026, 5, 31), records)

    call_args = mock_conn.executemany.call_args
    rows = call_args[0][1]
    assert rows[0][6] == "BOTZ,AIQ,IRBO"  # etfs 字段序列化为逗号分隔字符串


@pytest.mark.asyncio
async def test_load_etf_map_parses_rows():
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {
            "concept": "AI", "etf_symbol": "BOTZ", "etf_name": "Global X",
            "aum_million": 2500.0, "etfdb_slug": "ai-etfs",
            "updated_at": datetime.date(2026, 5, 1),
            "concept_name_zh": None, "etf_name_zh": None, "description_zh": None,
        },
    ])
    mock_pool = _make_mock_pool(mock_conn)

    with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        async with ConceptDb("postgresql://test") as db:
            result = await db.load_etf_map()

    assert len(result) == 1
    assert result[0].concept == "AI"
    assert result[0].etf_symbol == "BOTZ"
