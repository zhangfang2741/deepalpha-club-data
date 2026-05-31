import pytest
import polars as pl
from pytest_httpx import HTTPXMock
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.directory_loader import FMPDirectoryLoader
from deepalpha.loaders.enums import AssetClass


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_symbols_stocks(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "exchangeShortName": "NASDAQ", "type": "stock"},
    ])
    loader = FMPDirectoryLoader(client)
    df = await loader.get_symbols(AssetClass.STOCK)
    assert isinstance(df, pl.DataFrame)
    assert "symbol" in df.columns
    await client.aclose()


@pytest.mark.asyncio
async def test_get_exchanges_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"exchange": "NASDAQ", "name": "NASDAQ", "country": "US", "currency": "USD"},
    ])
    loader = FMPDirectoryLoader(client)
    df = await loader.get_exchanges()
    assert isinstance(df, pl.DataFrame)
    assert "exchange" in df.columns
    await client.aclose()


@pytest.mark.asyncio
async def test_get_sectors_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"sector": "Technology"},
        {"sector": "Healthcare"},
    ])
    loader = FMPDirectoryLoader(client)
    sectors = await loader.get_sectors()
    assert isinstance(sectors, list)
    assert "Technology" in sectors
    await client.aclose()


@pytest.mark.asyncio
async def test_get_industries_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"industry": "Software"},
        {"industry": "Semiconductors"},
    ])
    loader = FMPDirectoryLoader(client)
    industries = await loader.get_industries()
    assert isinstance(industries, list)
    assert "Software" in industries
    await client.aclose()
