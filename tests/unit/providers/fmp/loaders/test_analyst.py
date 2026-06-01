import pytest
from pytest_httpx import HTTPXMock

from deepalpha.domain.analyst.models import AnalystRating, Estimate, PriceTarget
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.analyst_loader import FMPAnalystLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_ratings_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-01-01",
        "rating": "S+", "ratingRecommendation": "Strong Buy", "ratingScore": 1,
    }])
    loader = FMPAnalystLoader(client)
    result = await loader.get_ratings("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], AnalystRating)
    assert result[0].rating == "S+"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_price_targets_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json={
        "symbol": "AAPL", "lastMonth": 198.0, "lastQuarter": 195.0,
        "lastYear": 185.0, "allTime": 175.0,
    })
    loader = FMPAnalystLoader(client)
    result = await loader.get_price_targets("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], PriceTarget)
    assert result[0].last_month == 198.0
    await client.aclose()


@pytest.mark.asyncio
async def test_get_estimates_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-09-30",
        "estimatedRevenueAvg": 390000000000, "estimatedEpsAvg": 6.50,
        "numberAnalystEstimatedRevenue": 28,
    }])
    loader = FMPAnalystLoader(client)
    result = await loader.get_estimates("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], Estimate)
    assert result[0].estimated_eps_avg == 6.50
    await client.aclose()
