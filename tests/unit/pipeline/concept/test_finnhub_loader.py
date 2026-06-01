import datetime
import pytest
from unittest.mock import AsyncMock

from deepalpha.models.concept import ConceptEtfMap
from deepalpha.pipeline.concept.etfdb_scraper import ConceptEtfCandidate
from deepalpha.pipeline.concept.finnhub_loader import filter_etfs_by_aum, aggregate_holdings


@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.get_etf_profile = AsyncMock(return_value={"name": "Global X Robotics", "mktCap": 2_500_000_000.0})
    client.get_etf_holdings = AsyncMock(return_value=[
        {"symbol": "NVDA", "name": "NVIDIA Corp", "percent": 8.5},
        {"symbol": "ISRG", "name": "Intuitive Surgical", "percent": 5.2},
    ])
    return client


@pytest.mark.asyncio
async def test_filter_etfs_by_aum_passes_large_etf(mock_client):
    candidates = [ConceptEtfCandidate(concept="Robotics", etf_symbol="BOTZ", etfdb_slug="robotics-etfs")]
    result = await filter_etfs_by_aum(candidates, mock_client, aum_threshold_million=100.0)
    assert len(result) == 1
    assert result[0].etf_symbol == "BOTZ"
    assert result[0].aum_million == pytest.approx(2500.0)


@pytest.mark.asyncio
async def test_filter_etfs_by_aum_blocks_small_etf(mock_client):
    # AUM = $50M，低于 $100M 阈值
    mock_client.get_etf_profile = AsyncMock(return_value={"name": "Tiny ETF", "mktCap": 50_000_000.0})
    candidates = [ConceptEtfCandidate(concept="Robotics", etf_symbol="TINY", etfdb_slug="robotics-etfs")]
    result = await filter_etfs_by_aum(candidates, mock_client, aum_threshold_million=100.0)
    assert result == []


@pytest.mark.asyncio
async def test_aggregate_holdings_calculates_etf_count_and_total_weight():
    today = datetime.date(2026, 5, 31)
    etf_maps = [
        ConceptEtfMap(concept="AI", etf_symbol="BOTZ", updated_at=today),
        ConceptEtfMap(concept="AI", etf_symbol="AIQ", updated_at=today),
    ]
    holdings_by_etf = {
        "BOTZ": [{"symbol": "NVDA", "name": "NVIDIA", "percent": 8.5}],
        "AIQ": [{"symbol": "NVDA", "name": "NVIDIA", "percent": 6.0}, {"symbol": "AMD", "name": "AMD", "percent": 4.0}],
    }
    result = await aggregate_holdings(etf_maps, holdings_by_etf, date=today)

    nvda = next(s for s in result if s.symbol == "NVDA")
    assert nvda.etf_count == 2
    assert nvda.total_weight == pytest.approx(14.5)
    assert set(nvda.etfs) == {"BOTZ", "AIQ"}

    amd = next(s for s in result if s.symbol == "AMD")
    assert amd.etf_count == 1
    assert amd.total_weight == pytest.approx(4.0)
