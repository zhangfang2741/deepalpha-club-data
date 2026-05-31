import pytest
import polars as pl
from pytest_httpx import HTTPXMock
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.insider import FMPInsiderTradeLoader
from deepalpha.models.insider import InsiderStatistics

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_insider_trades_all_market(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "filingDate": "2024-05-01", "transactionDate": "2024-04-29",
        "reportingName": "Tim Cook", "typeOfSecurity": "Common Stock",
        "acquitionOrDisposition": "D", "shares": 100000, "price": 185.0,
    }])
    loader = FMPInsiderTradeLoader(client)
    df = await loader.get_insider_trades()
    assert isinstance(df, pl.DataFrame)
    assert "reporting_name" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_insider_trades_by_symbol(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "filingDate": "2024-05-01", "transactionDate": "2024-04-29",
        "reportingName": "Tim Cook", "typeOfSecurity": "Common Stock",
        "acquitionOrDisposition": "D", "shares": 100000, "price": 185.0,
    }])
    loader = FMPInsiderTradeLoader(client)
    df = await loader.get_insider_trades(symbol="AAPL", limit=10)
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 1
    await client.aclose()

@pytest.mark.asyncio
async def test_get_insider_statistics(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json={
        "symbol": "AAPL", "totalBought": 5, "totalSold": 20,
        "totalBoughtAmount": 900000.0, "totalSoldAmount": 3700000.0,
    })
    loader = FMPInsiderTradeLoader(client)
    stats = await loader.get_insider_statistics("AAPL")
    assert isinstance(stats, InsiderStatistics)
    assert stats.total_sold == 20
    await client.aclose()
