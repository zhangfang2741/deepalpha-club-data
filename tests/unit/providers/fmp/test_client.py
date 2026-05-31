import pytest
from pytest_httpx import HTTPXMock
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.errors import (
    FMPAuthError, FMPNotFoundError, FMPServerError,
)

@pytest.fixture
def config():
    return FMPConfig(api_key="test-key")

@pytest.mark.asyncio
async def test_get_attaches_api_key(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(json={"symbol": "AAPL"})
    async with FMPAsyncClient(config) as client:
        result = await client.get("/stable/quote/AAPL")
    request = httpx_mock.get_request()
    assert "apikey=test-key" in str(request.url)
    assert result == {"symbol": "AAPL"}

@pytest.mark.asyncio
async def test_get_raises_auth_error_on_401(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(status_code=401)
    async with FMPAsyncClient(config) as client:
        with pytest.raises(FMPAuthError):
            await client.get("/stable/quote/AAPL")

@pytest.mark.asyncio
async def test_get_raises_not_found_on_404(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(status_code=404)
    async with FMPAsyncClient(config) as client:
        with pytest.raises(FMPNotFoundError):
            await client.get("/stable/quote/AAPL")

@pytest.mark.asyncio
async def test_get_retries_on_500_then_raises(httpx_mock: HTTPXMock, config):
    cfg = FMPConfig(api_key="test-key", max_retries=1)
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=500)
    async with FMPAsyncClient(cfg) as client:
        with pytest.raises(FMPServerError):
            await client.get("/stable/quote/AAPL")

@pytest.mark.asyncio
async def test_get_returns_list_unchanged(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(json=[{"symbol": "AAPL"}, {"symbol": "MSFT"}])
    async with FMPAsyncClient(config) as client:
        result = await client.get("/stable/quotes-batch")
    assert result == [{"symbol": "AAPL"}, {"symbol": "MSFT"}]

@pytest.mark.asyncio
async def test_get_retries_on_429_with_retry_after(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(
        status_code=429,
        headers={"Retry-After": "0"},
    )
    httpx_mock.add_response(json={"symbol": "AAPL"})
    async with FMPAsyncClient(config) as client:
        result = await client.get("/stable/quote/AAPL")
    assert result == {"symbol": "AAPL"}
