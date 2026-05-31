import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import CongressChamber
from deepalpha.models.congress import CongressTrade
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.congress_loader import FMPCongressTradeLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

_TRADE_ROW = {
    "symbol": "NVDA", "disclosureDate": "2024-04-15", "transactionDate": "2024-04-10",
    "firstName": "John", "lastName": "Smith", "office": "John Smith",
    "district": "AR", "owner": "Self",
    "type": "Purchase", "amount": "$1,001 - $15,000",
    "assetDescription": "NVIDIA Corp", "assetType": "Stock",
    "link": "https://efdsearch.senate.gov/",
}

@pytest.mark.asyncio
async def test_get_senate_trades_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_TRADE_ROW])
    loader = FMPCongressTradeLoader(client)
    result = await loader.get_congress_trades(chamber=CongressChamber.SENATE)
    assert isinstance(result, list)
    assert isinstance(result[0], CongressTrade)
    assert result[0].office == "John Smith"
    assert result[0].first_name == "John"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_house_trades_by_symbol_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{**_TRADE_ROW, "firstName": "Jane", "lastName": "Doe", "office": "Jane Doe"}])
    loader = FMPCongressTradeLoader(client)
    result = await loader.get_congress_trades(symbol="NVDA", chamber=CongressChamber.HOUSE)
    assert isinstance(result, list)
    assert result[0].symbol == "NVDA"
    await client.aclose()
