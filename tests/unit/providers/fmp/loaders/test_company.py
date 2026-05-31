import datetime

import pytest
from pytest_httpx import HTTPXMock

from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.company_loader import FMPCompanyLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_profile_returns_company_profile(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "companyName": "Apple Inc.", "sector": "Technology",
        "industry": "Consumer Electronics", "exchange": "NASDAQ",
        "marketCap": 2800000000000, "description": "Apple Inc. designs...",
    }])
    loader = FMPCompanyLoader(client)
    profile = await loader.get_profile("AAPL")
    assert isinstance(profile, CompanyProfile)
    assert profile.symbol == "AAPL"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_executives_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "title": "CEO", "name": "Tim Cook", "pay": 99420000,
        "currencyPay": "USD", "gender": "male", "yearBorn": 1960,
    }])
    loader = FMPCompanyLoader(client)
    result = await loader.get_executives("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], Executive)
    assert result[0].name == "Tim Cook"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_peers_returns_list_of_strings(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"symbol": "MSFT"}, {"symbol": "GOOGL"}, {"symbol": "AMZN"},
    ])
    loader = FMPCompanyLoader(client)
    peers = await loader.get_peers("AAPL")
    assert isinstance(peers, list)
    assert "MSFT" in peers
    await client.aclose()


@pytest.mark.asyncio
async def test_get_market_cap_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-05-01", "marketCap": 2800000000000,
    }])
    loader = FMPCompanyLoader(client)
    result = await loader.get_market_cap("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], MarketCapRecord)
    assert result[0].market_cap == 2800000000000
    await client.aclose()
