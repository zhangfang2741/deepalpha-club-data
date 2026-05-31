import polars as pl
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import MoverDirection
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.performance_loader import FMPMarketPerformanceLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_movers_gainers(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "name": "NVIDIA", "change": 45.0,
        "price": 900.0, "changesPercentage": 5.26, "volume": 30000000,
    }])
    loader = FMPMarketPerformanceLoader(client)
    df = await loader.get_movers(MoverDirection.GAINERS, limit=10)
    assert isinstance(df, pl.DataFrame)
    assert "symbol" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sector_performance_snapshot(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"sector": "Technology", "changesPercentage": "1.23%"},
        {"sector": "Energy", "changesPercentage": "-0.45%"},
    ])
    loader = FMPMarketPerformanceLoader(client)
    df = await loader.get_sector_performance()
    assert isinstance(df, pl.DataFrame)
    assert "sector" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sector_pe_snapshot(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-05-02", "sector": "Technology", "pe": 32.5},
    ])
    loader = FMPMarketPerformanceLoader(client)
    df = await loader.get_sector_pe()
    assert isinstance(df, pl.DataFrame)
    assert "pe" in df.columns
    await client.aclose()
