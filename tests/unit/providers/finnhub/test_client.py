import pytest
from pytest_httpx import HTTPXMock

from deepalpha.infrastructure.providers.finnhub.client import FinnhubClient
from deepalpha.infrastructure.providers.finnhub.config import FinnhubConfig


@pytest.fixture
def config():
    return FinnhubConfig(finnhub_api_key="test-key")


@pytest.mark.asyncio
async def test_get_etf_profile_attaches_token(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(json={"name": "Global X Robotics", "mktCap": 2500000000.0})
    async with FinnhubClient(config) as client:
        result = await client.get_etf_profile("BOTZ")
    request = httpx_mock.get_request()
    assert "token=test-key" in str(request.url)
    assert result["name"] == "Global X Robotics"


@pytest.mark.asyncio
async def test_get_etf_holdings_returns_list(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(json={
        "symbol": "BOTZ",
        "holdings": [
            {"symbol": "NVDA", "name": "NVIDIA Corp", "percent": 8.5},
            {"symbol": "ISRG", "name": "Intuitive Surgical", "percent": 5.2},
        ]
    })
    async with FinnhubClient(config) as client:
        result = await client.get_etf_holdings("BOTZ")
    assert len(result) == 2
    assert result[0]["symbol"] == "NVDA"
    assert result[0]["percent"] == 8.5


@pytest.mark.asyncio
async def test_get_etf_holdings_empty_on_no_holdings_key(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(json={"symbol": "BOTZ"})
    async with FinnhubClient(config) as client:
        result = await client.get_etf_holdings("BOTZ")
    assert result == []


@pytest.mark.asyncio
async def test_raises_on_http_error(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(status_code=429)
    async with FinnhubClient(config) as client:
        with pytest.raises(Exception):
            await client.get_etf_profile("BOTZ")
