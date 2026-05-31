import datetime
import pytest
import polars as pl
from pytest_httpx import HTTPXMock
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.company import FMPCompanyLoader
from deepalpha.models.company import CompanyProfile


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_profile_returns_object(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "companyName": "Apple Inc.", "exchange": "NASDAQ",
        "industry": "Consumer Electronics", "sector": "Technology",
        "description": "Apple Inc. designs...", "website": "https://apple.com",
        "fullTimeEmployees": 164000, "ceo": "Tim Cook", "country": "US",
        "ipoDate": "1980-12-12", "isActivelyTrading": True,
    }])
    loader = FMPCompanyLoader(client)
    profile = await loader.get_profile("AAPL")
    assert isinstance(profile, CompanyProfile)
    assert profile.symbol == "AAPL"
    assert profile.company_name == "Apple Inc."
    await client.aclose()


@pytest.mark.asyncio
async def test_get_executives_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"name": "Tim Cook", "title": "CEO", "pay": 99420000, "currencyOfPay": "USD"},
    ])
    loader = FMPCompanyLoader(client)
    df = await loader.get_executives("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "name" in df.columns
    await client.aclose()


@pytest.mark.asyncio
async def test_get_peers_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{"peersList": ["MSFT", "GOOGL", "AMZN"]}])
    loader = FMPCompanyLoader(client)
    peers = await loader.get_peers("AAPL")
    assert isinstance(peers, list)
    assert "MSFT" in peers
    await client.aclose()


@pytest.mark.asyncio
async def test_get_market_cap_current(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-05-02", "marketCap": 2950000000000,
    }])
    loader = FMPCompanyLoader(client)
    df = await loader.get_market_cap("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "market_cap" in df.columns
    await client.aclose()
