import pytest
from pytest_httpx import HTTPXMock

from deepalpha.domain.governance.models import InsiderStatistics, InsiderTrade
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.insider_loader import FMPInsiderTradeLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

_TRADE_ROW = {
    "symbol": "AAPL", "filingDate": "2024-05-01", "transactionDate": "2024-04-29",
    "reportingName": "Tim Cook", "securityName": "Common Stock",
    "transactionType": "S-Sale", "acquisitionOrDisposition": "D",
    "securitiesTransacted": 100000, "price": 185.0,
    "typeOfOwner": "officer", "formType": "4",
    "url": "https://www.sec.gov/",
}

@pytest.mark.asyncio
async def test_get_insider_trades_all_market(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_TRADE_ROW])
    loader = FMPInsiderTradeLoader(client)
    result = await loader.get_insider_trades()
    assert isinstance(result, list)
    assert isinstance(result[0], InsiderTrade)
    assert result[0].reporting_name == "Tim Cook"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_insider_trades_by_symbol(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_TRADE_ROW])
    loader = FMPInsiderTradeLoader(client)
    result = await loader.get_insider_trades(symbol="AAPL", limit=10)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].symbol == "AAPL"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_insider_trades_not_found_returns_empty_list(httpx_mock: HTTPXMock, client):
    from deepalpha.infrastructure.providers.fmp.errors import FMPNotFoundError
    httpx_mock.add_exception(FMPNotFoundError("not found"))
    loader = FMPInsiderTradeLoader(client)
    result = await loader.get_insider_trades(symbol="UNKN")
    assert result == []
    await client.aclose()

@pytest.mark.asyncio
async def test_get_insider_statistics(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {
            "symbol": "AAPL", "year": 2026, "quarter": 1,
            "acquiredTransactions": 5, "disposedTransactions": 20,
            "totalAcquired": 50000.0, "totalDisposed": 200000.0,
            "totalPurchases": 1, "totalSales": 15,
        },
    ])
    loader = FMPInsiderTradeLoader(client)
    result = await loader.get_insider_statistics("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], InsiderStatistics)
    assert result[0].acquired_transactions == 5
    await client.aclose()
