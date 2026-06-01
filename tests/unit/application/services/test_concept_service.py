import datetime
import pytest
from unittest.mock import AsyncMock

from deepalpha.application.services.concept_service import ConceptService
from deepalpha.domain.concept.models import ConceptStock, ConceptSummary


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.get_latest_stocks = AsyncMock(return_value=[
        ConceptStock(
            date=datetime.date(2026, 6, 1), concept="AI", symbol="NVDA",
            etf_count=5, total_weight=10.0, etfs=["BOTZ"],
        )
    ])
    repo.get_all_summaries = AsyncMock(return_value=[
        ConceptSummary(
            concept="AI", etf_count=4, stock_count=10,
            top_symbols=["NVDA"], last_updated=datetime.date(2026, 6, 1),
        )
    ])
    repo.get_stocks_history = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get_concept = AsyncMock(return_value=None)
    cache.set_concept = AsyncMock()
    cache.get_list = AsyncMock(return_value=None)
    cache.set_list = AsyncMock()
    return cache


@pytest.mark.asyncio
async def test_get_concept_cache_miss_queries_repo_and_fills_cache(mock_repo, mock_cache):
    svc = ConceptService(mock_repo, mock_cache)
    result = await svc.get_concept("AI")
    mock_repo.get_latest_stocks.assert_called_once_with("AI")
    mock_cache.set_concept.assert_called_once()
    assert len(result) == 1
    assert result[0].symbol == "NVDA"


@pytest.mark.asyncio
async def test_get_concept_cache_hit_skips_repo(mock_repo, mock_cache):
    cached = [ConceptStock(
        date=datetime.date(2026, 6, 1), concept="AI", symbol="MSFT",
        etf_count=3, total_weight=8.0, etfs=["AIQ"],
    )]
    mock_cache.get_concept = AsyncMock(return_value=cached)
    svc = ConceptService(mock_repo, mock_cache)
    result = await svc.get_concept("AI")
    mock_repo.get_latest_stocks.assert_not_called()
    assert result[0].symbol == "MSFT"


@pytest.mark.asyncio
async def test_list_summaries_cache_miss_queries_repo(mock_repo, mock_cache):
    svc = ConceptService(mock_repo, mock_cache)
    result = await svc.list_summaries()
    mock_repo.get_all_summaries.assert_called_once()
    mock_cache.set_list.assert_called_once()
    assert len(result) == 1
