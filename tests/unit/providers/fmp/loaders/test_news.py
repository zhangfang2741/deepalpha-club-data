import pytest
from pytest_httpx import HTTPXMock

from deepalpha.domain.news.models import NewsArticle
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.news_loader import FMPNewsLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_stock_news_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "title": "Apple Reports Record Revenue", "url": "https://example.com/aapl",
        "publishedDate": "2024-05-02T18:00:00.000Z", "site": "Reuters",
        "text": "Apple Inc. reported...", "symbol": "AAPL", "sentiment": "Positive",
    }])
    loader = FMPNewsLoader(client)
    result = await loader.get_news(symbols=["AAPL"])
    assert isinstance(result, list)
    assert isinstance(result[0], NewsArticle)
    assert result[0].symbol == "AAPL"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_general_news_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "title": "Market Update", "link": "https://fmp.com/article/1",
        "date": "2024-05-02T12:00:00.000Z", "content": "Markets were mixed today...",
    }])
    loader = FMPNewsLoader(client)
    result = await loader.get_news()
    assert isinstance(result, list)
    assert isinstance(result[0], NewsArticle)
    await client.aclose()
