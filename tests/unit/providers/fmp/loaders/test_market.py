import datetime

import pytest
from pytest_httpx import HTTPXMock

from deepalpha.domain.market.enums import AssetClass
from deepalpha.domain.market.models import PriceBar, Quote
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.market_loader import FMPMarketLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_quote_returns_quote(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "price": 189.84, "change": 2.31,
        "changePercentage": 1.23, "volume": 45000000,
    }])
    loader = FMPMarketLoader(client)
    quote = await loader.get_quote("AAPL")
    assert isinstance(quote, Quote)
    assert quote.symbol == "AAPL"
    assert quote.price == 189.84
    assert quote.changes_percentage == 1.23
    await client.aclose()

@pytest.mark.asyncio
async def test_get_quotes_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"symbol": "AAPL", "price": 189.84, "change": 2.31, "changePercentage": 1.23, "volume": 1000},
    ])
    httpx_mock.add_response(json=[
        {"symbol": "MSFT", "price": 420.10, "change": 1.05, "changePercentage": 0.25, "volume": 2000},
    ])
    loader = FMPMarketLoader(client)
    result = await loader.get_quotes(["AAPL", "MSFT"])
    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], Quote)
    assert result[0].symbol == "AAPL"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_price_history_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-01-05", "open": 185.0, "high": 190.0, "low": 184.0, "close": 189.0, "volume": 50000000},
        {"date": "2024-01-04", "open": 182.0, "high": 186.0, "low": 181.0, "close": 185.0, "volume": 48000000},
    ])
    loader = FMPMarketLoader(client)
    result = await loader.get_price_history("AAPL", start=datetime.date(2024, 1, 1))
    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], PriceBar)
    assert result[0].close == 189.0
    await client.aclose()

@pytest.mark.asyncio
async def test_get_market_snapshot_returns_empty_list(client):
    loader = FMPMarketLoader(client)
    result = await loader.get_market_snapshot(AssetClass.STOCK)
    assert isinstance(result, list)
    assert result == []
    await client.aclose()
