"""FMP 财务数据加载器测试"""

import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.financial import (
    BalanceSheet,
    CashFlow,
    FinancialRatio,
    IncomeStatement,
    KeyMetrics,
    Valuation,
)
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.financial_loader import FMPFinancialLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


_INCOME_ROW = {
    "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
    "revenue": 383285000000, "grossProfit": 169148000000,
    "operatingIncome": 114301000000, "netIncome": 96995000000,
    "eps": 6.13, "epsDiluted": 6.12, "ebitda": 130000000000,
}


@pytest.mark.asyncio
async def test_get_income_statement_annual(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_INCOME_ROW])
    loader = FMPFinancialLoader(client)
    result = await loader.get_income_statement("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], IncomeStatement)
    assert result[0].symbol == "AAPL"
    assert result[0].revenue == 383285000000
    await client.aclose()


@pytest.mark.asyncio
async def test_get_income_statement_ttm(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_INCOME_ROW])
    loader = FMPFinancialLoader(client)
    result = await loader.get_income_statement("AAPL", period=StatementPeriod.TTM)
    assert isinstance(result, list)
    assert len(result) == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_get_balance_sheet_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
        "totalAssets": 352755000000, "totalLiabilities": 290437000000,
        "totalStockholdersEquity": 62146000000,
    }])
    loader = FMPFinancialLoader(client)
    result = await loader.get_balance_sheet("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], BalanceSheet)
    assert result[0].total_assets == 352755000000
    await client.aclose()


@pytest.mark.asyncio
async def test_get_cash_flow_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
        "netIncome": 96995000000, "operatingCashFlow": 113000000000,
        "capitalExpenditure": -10959000000, "freeCashFlow": 99584000000,
    }])
    loader = FMPFinancialLoader(client)
    result = await loader.get_cash_flow_statement("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], CashFlow)
    await client.aclose()


@pytest.mark.asyncio
async def test_get_financial_ratios_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
        "peRatio": 29.5, "priceToBookRatio": 47.2, "currentRatio": 1.07,
    }])
    loader = FMPFinancialLoader(client)
    result = await loader.get_financial_ratios("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], FinancialRatio)
    await client.aclose()


@pytest.mark.asyncio
async def test_get_key_metrics_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
        "revenuePerShare": 24.32, "netIncomePerShare": 6.13, "marketCap": 2800000000000,
    }])
    loader = FMPFinancialLoader(client)
    result = await loader.get_key_metrics("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], KeyMetrics)
    await client.aclose()


@pytest.mark.asyncio
async def test_get_valuation_returns_valuation_object(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "dcf": 182.5, "stockPrice": 189.84,
    }])
    loader = FMPFinancialLoader(client)
    result = await loader.get_valuation("AAPL")
    assert isinstance(result, Valuation)
    assert result.symbol == "AAPL"
    await client.aclose()
