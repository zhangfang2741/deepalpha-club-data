import pytest
import polars as pl
from pytest_httpx import HTTPXMock
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.analyst import FMPAnalystLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_ratings_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-01-01",
        "rating": "S+", "ratingRecommendation": "Strong Buy", "ratingScore": 1,
    }])
    loader = FMPAnalystLoader(client)
    df = await loader.get_ratings("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "rating" in df.columns
    await client.aclose()


@pytest.mark.asyncio
async def test_get_price_targets_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json={
        "symbol": "AAPL", "lastMonth": 198.0, "lastQuarter": 195.0,
        "lastYear": 185.0, "allTime": 175.0,
    })
    loader = FMPAnalystLoader(client)
    df = await loader.get_price_targets("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "last_month" in df.columns
    await client.aclose()


@pytest.mark.asyncio
async def test_get_estimates_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-09-30",
        "estimatedRevenueAvg": 390000000000, "estimatedEpsAvg": 6.50,
        "numberAnalystEstimatedRevenue": 28,
    }])
    loader = FMPAnalystLoader(client)
    df = await loader.get_estimates("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "estimated_revenue_avg" in df.columns
    await client.aclose()
