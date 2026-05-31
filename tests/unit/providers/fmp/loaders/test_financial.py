"""FMP 财务数据加载器测试"""

import pytest
import polars as pl
from pytest_httpx import HTTPXMock
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.financial import FMPFinancialLoader
from deepalpha.models.financial import Valuation
from deepalpha.loaders.enums import StatementPeriod


@pytest.fixture
def client():
    """创建 FMP 客户端"""
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


_INCOME_ROW = {
    "symbol": "AAPL",
    "date": "2023-09-30",
    "period": "annual",
    "revenue": 383285000000,
    "grossProfit": 169148000000,
    "operatingIncome": 114301000000,
    "netIncome": 96995000000,
    "eps": 6.13,
    "epsDiluted": 6.12,
    "ebitda": 130000000000,
}


@pytest.mark.asyncio
async def test_get_income_statement_annual(httpx_mock: HTTPXMock, client):
    """测试获取年度收入声明"""
    httpx_mock.add_response(json=[_INCOME_ROW])
    loader = FMPFinancialLoader(client)
    df = await loader.get_income_statement("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "revenue" in df.columns
    assert df["symbol"][0] == "AAPL"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_income_statement_ttm(httpx_mock: HTTPXMock, client):
    """测试获取 TTM 收入声明"""
    httpx_mock.add_response(json=[_INCOME_ROW])
    loader = FMPFinancialLoader(client)
    df = await loader.get_income_statement("AAPL", period=StatementPeriod.TTM)
    assert isinstance(df, pl.DataFrame)
    await client.aclose()


@pytest.mark.asyncio
async def test_get_balance_sheet_returns_dataframe(httpx_mock: HTTPXMock, client):
    """测试获取资产负债表"""
    httpx_mock.add_response(
        json=[
            {
                "symbol": "AAPL",
                "date": "2023-09-30",
                "period": "annual",
                "totalAssets": 352583000000,
                "totalLiabilities": 290437000000,
                "totalStockholdersEquity": 62146000000,
                "cashAndCashEquivalents": 29965000000,
                "totalDebt": 110000000000,
                "netDebt": 80000000000,
            }
        ]
    )
    loader = FMPFinancialLoader(client)
    df = await loader.get_balance_sheet("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "total_assets" in df.columns
    await client.aclose()


@pytest.mark.asyncio
async def test_get_valuation_returns_object(httpx_mock: HTTPXMock, client):
    """测试获取估值数据"""
    httpx_mock.add_response(
        json={"symbol": "AAPL", "dcf": 195.23, "stockPrice": 189.84}
    )
    loader = FMPFinancialLoader(client)
    val = await loader.get_valuation("AAPL")
    assert isinstance(val, Valuation)
    assert val.symbol == "AAPL"
    assert val.dcf == 195.23
    await client.aclose()


@pytest.mark.asyncio
async def test_get_cash_flow_returns_dataframe(httpx_mock: HTTPXMock, client):
    """测试获取现金流声明"""
    httpx_mock.add_response(
        json=[
            {
                "symbol": "AAPL",
                "date": "2023-09-30",
                "period": "annual",
                "operatingCashFlow": 110000000000,
                "capitalExpenditure": -10000000000,
                "freeCashFlow": 100000000000,
                "dividendsPaid": -15000000000,
            }
        ]
    )
    loader = FMPFinancialLoader(client)
    df = await loader.get_cash_flow_statement("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "operating_cash_flow" in df.columns
    await client.aclose()
