import polars as pl
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import AssetClass
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.news_loader import FMPNewsLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

_ARTICLE = {
    "title": "Apple reports record earnings",
    "url": "https://example.com/apple",
    "publishedDate": "2024-05-02T18:00:00.000Z",
    "site": "Reuters",
    "text": "Apple Inc reported...",
    "symbol": "AAPL",
}

@pytest.mark.asyncio
async def test_get_news_by_symbols(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_ARTICLE])
    loader = FMPNewsLoader(client)
    df = await loader.get_news(symbols=["AAPL"], limit=5)
    assert isinstance(df, pl.DataFrame)
    assert "title" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_news_general(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_ARTICLE])
    loader = FMPNewsLoader(client)
    df = await loader.get_news(limit=10)
    assert isinstance(df, pl.DataFrame)
    await client.aclose()

@pytest.mark.asyncio
async def test_get_news_crypto(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_ARTICLE])
    loader = FMPNewsLoader(client)
    df = await loader.get_news(asset_class=AssetClass.CRYPTO, limit=5)
    assert isinstance(df, pl.DataFrame)
    await client.aclose()
