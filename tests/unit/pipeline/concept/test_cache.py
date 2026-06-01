import datetime
import json
import pytest
from unittest.mock import AsyncMock, patch

from deepalpha.domain.concept.models import ConceptStock, ConceptSummary
from deepalpha.infrastructure.cache.concept_cache import ConceptCache


@pytest.fixture
def mock_valkey():
    """返回一个模拟的 valkey.asyncio.Valkey 实例。"""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def cache(mock_valkey):
    with patch("deepalpha.infrastructure.cache.concept_cache.valkey_asyncio.Valkey", return_value=mock_valkey):
        return ConceptCache(host="localhost", port=6379, password="", ssl=False)


@pytest.mark.asyncio
async def test_get_concept_returns_none_on_cache_miss(cache, mock_valkey):
    mock_valkey.get.return_value = None
    result = await cache.get_concept("AI")
    assert result is None


@pytest.mark.asyncio
async def test_get_concept_deserializes_cached_data(cache, mock_valkey):
    stock = ConceptStock(
        date=datetime.date(2026, 5, 31),
        concept="AI",
        symbol="NVDA",
        etf_count=3,
        total_weight=15.5,
        etfs=["BOTZ", "AIQ", "IRBO"],
    )
    mock_valkey.get.return_value = json.dumps([stock.model_dump(mode="json")])
    result = await cache.get_concept("AI")
    assert result is not None
    assert len(result) == 1
    assert result[0].symbol == "NVDA"
    assert result[0].etfs == ["BOTZ", "AIQ", "IRBO"]


@pytest.mark.asyncio
async def test_set_concept_serializes_with_ttl(cache, mock_valkey):
    stocks = [
        ConceptStock(date=datetime.date(2026, 5, 31), concept="AI", symbol="NVDA",
                     etf_count=3, total_weight=15.5, etfs=["BOTZ"])
    ]
    await cache.set_concept("AI", stocks)
    mock_valkey.set.assert_called_once()
    call_args = mock_valkey.set.call_args
    assert call_args[0][0] == "concept:AI"
    assert call_args[1]["ex"] == 172800


@pytest.mark.asyncio
async def test_get_list_returns_none_on_cache_miss(cache, mock_valkey):
    mock_valkey.get.return_value = None
    result = await cache.get_list()
    assert result is None


@pytest.mark.asyncio
async def test_set_list_uses_correct_key(cache, mock_valkey):
    summaries = [
        ConceptSummary(concept="AI", etf_count=4, stock_count=120,
                       top_symbols=["NVDA"], last_updated=datetime.date(2026, 5, 31))
    ]
    await cache.set_list(summaries)
    call_args = mock_valkey.set.call_args
    assert call_args[0][0] == "concept:__list__"
