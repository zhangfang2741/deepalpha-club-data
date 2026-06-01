import pytest
from pytest_httpx import HTTPXMock

from deepalpha.domain.market.enums import AssetClass
from deepalpha.models.directory import ExchangeInfo, SymbolInfo
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.directory_loader import FMPDirectoryLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_symbols_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ",
        "exchangeShortName": "NASDAQ", "type": "stock",
    }])
    loader = FMPDirectoryLoader(client)
    result = await loader.get_symbols(AssetClass.STOCK)
    assert isinstance(result, list)
    assert isinstance(result[0], SymbolInfo)
    assert result[0].symbol == "AAPL"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_exchanges_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "exchange": "NASDAQ", "name": "National Association of Securities Dealers Automated Quotations",
    }])
    loader = FMPDirectoryLoader(client)
    result = await loader.get_exchanges()
    assert isinstance(result, list)
    assert isinstance(result[0], ExchangeInfo)
    assert result[0].exchange == "NASDAQ"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sectors_returns_list_of_strings(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{"sector": "Technology"}, {"sector": "Healthcare"}])
    loader = FMPDirectoryLoader(client)
    sectors = await loader.get_sectors()
    assert isinstance(sectors, list)
    assert "Technology" in sectors
    await client.aclose()

@pytest.mark.asyncio
async def test_get_industries_returns_list_of_strings(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{"industry": "Semiconductors"}])
    loader = FMPDirectoryLoader(client)
    industries = await loader.get_industries()
    assert "Semiconductors" in industries
    await client.aclose()
