import pytest
from pytest_httpx import HTTPXMock

from deepalpha.domain.market.enums import MoverDirection
from deepalpha.models.performance import MarketMover, SectorPE, SectorPerformance
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.performance_loader import FMPMarketPerformanceLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_movers_gainers_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "name": "NVIDIA", "change": 45.0,
        "price": 900.0, "changesPercentage": 5.26, "volume": 30000000,
    }])
    loader = FMPMarketPerformanceLoader(client)
    result = await loader.get_movers(MoverDirection.GAINERS, limit=10)
    assert isinstance(result, list)
    assert isinstance(result[0], MarketMover)
    assert result[0].symbol == "NVDA"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sector_performance_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"sector": "Technology", "changesPercentage": "1.23%"},
        {"sector": "Energy", "changesPercentage": "-0.45%"},
    ])
    loader = FMPMarketPerformanceLoader(client)
    result = await loader.get_sector_performance()
    assert isinstance(result, list)
    assert isinstance(result[0], SectorPerformance)
    assert result[0].sector == "Technology"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sector_pe_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-05-02", "sector": "Technology", "pe": 32.5},
    ])
    loader = FMPMarketPerformanceLoader(client)
    result = await loader.get_sector_pe()
    assert isinstance(result, list)
    assert isinstance(result[0], SectorPE)
    assert result[0].pe == 32.5
    await client.aclose()
