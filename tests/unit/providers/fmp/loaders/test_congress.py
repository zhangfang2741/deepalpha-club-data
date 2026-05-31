import polars as pl
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import CongressChamber
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.congress_loader import FMPCongressTradeLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_senate_trades_latest(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "filingDate": "2024-04-15", "transactionDate": "2024-04-10",
        "representative": "John Smith", "district": None,
        "type": "Purchase", "amount": "$1,001 - $15,000", "assetDescription": "NVIDIA Corp",
    }])
    loader = FMPCongressTradeLoader(client)
    df = await loader.get_congress_trades(chamber=CongressChamber.SENATE)
    assert isinstance(df, pl.DataFrame)
    assert "representative" in df.columns
    await client.aclose()


@pytest.mark.asyncio
async def test_get_house_trades_by_symbol(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "filingDate": "2024-04-15", "transactionDate": "2024-04-10",
        "representative": "Jane Doe", "district": "CA-18",
        "type": "Sale", "amount": "$15,001 - $50,000", "assetDescription": "NVIDIA Corp",
    }])
    loader = FMPCongressTradeLoader(client)
    df = await loader.get_congress_trades(symbol="NVDA", chamber=CongressChamber.HOUSE)
    assert isinstance(df, pl.DataFrame)
    assert df["symbol"][0] == "NVDA"
    await client.aclose()
