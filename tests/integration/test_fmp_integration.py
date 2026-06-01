"""集成测试 — 需要真实 FMP_API_KEY 环境变量，仅在 CI 中按需运行。

运行方式：
    uv run --no-active pytest tests/integration/ -v -m integration -s
"""
import datetime

import polars as pl
import pytest

from deepalpha.domain.market.enums import (
    AssetClass,
    CongressChamber,
    IndicatorType,
    Interval,
    MoverDirection,
)
from deepalpha.domain.financial.enums import StatementPeriod
from deepalpha.infrastructure.providers.base import BaseLoader
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.market_loader import FMPMarketLoader
from deepalpha.infrastructure.providers.fmp.loaders.financial_loader import FMPFinancialLoader
from deepalpha.infrastructure.providers.fmp.loaders.analyst_loader import FMPAnalystLoader
from deepalpha.infrastructure.providers.fmp.loaders.calendar_loader import FMPCalendarLoader
from deepalpha.infrastructure.providers.fmp.loaders.news_loader import FMPNewsLoader
from deepalpha.infrastructure.providers.fmp.loaders.indicators_loader import FMPTechnicalIndicatorLoader
from deepalpha.infrastructure.providers.fmp.loaders.economics_loader import FMPEconomicsLoader
from deepalpha.infrastructure.providers.fmp.loaders.insider_loader import FMPInsiderTradeLoader
from deepalpha.infrastructure.providers.fmp.loaders.filings_loader import FMPSecFilingLoader
from deepalpha.infrastructure.providers.fmp.loaders.performance_loader import FMPMarketPerformanceLoader
from deepalpha.infrastructure.providers.fmp.loaders.congress_loader import FMPCongressTradeLoader
from deepalpha.infrastructure.providers.fmp.loaders.directory_loader import FMPDirectoryLoader
from deepalpha.infrastructure.providers.fmp.loaders.company_loader import FMPCompanyLoader


def make_client() -> FMPAsyncClient:
    return FMPAsyncClient(FMPConfig())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_quote_real_aapl():
    client = make_client()
    loader = FMPMarketLoader(client)
    quote = await loader.get_quote("AAPL")
    await client.aclose()
    assert quote.symbol == "AAPL"
    assert quote.price > 0
    print(f"\nAAPL: ${quote.price:.2f}  变化: {quote.changes_percentage:.4f}%")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_price_history():
    client = make_client()
    loader = FMPMarketLoader(client)
    bars = await loader.get_price_history(
        "NVDA",
        start=datetime.date(2025, 1, 1),
        end=datetime.date(2025, 3, 31),
    )
    await client.aclose()
    assert isinstance(bars, list)
    assert len(bars) > 0
    df = BaseLoader.to_dataframe(bars)
    assert "close" in df.columns
    print(f"\nNVDA 历史行情: {len(bars)} 行")
    print(df.head(3).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_sector_performance_real():
    client = make_client()
    loader = FMPMarketPerformanceLoader(client)
    sectors = await loader.get_sector_performance()
    await client.aclose()
    assert isinstance(sectors, list)
    print(f"\n板块表现: {len(sectors)} 行")
    if len(sectors) > 0:
        df = BaseLoader.to_dataframe(sectors)
        assert "sector" in df.columns


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nvda_financial_data():
    client = make_client()
    loader = FMPFinancialLoader(client)

    income_stmts = await loader.get_income_statement("NVDA", limit=4)
    assert isinstance(income_stmts, list)
    assert len(income_stmts) > 0
    income_df = BaseLoader.to_dataframe(income_stmts)
    assert "revenue" in income_df.columns
    print("\n=== NVDA 利润表（年度）===")
    print(income_df.select(["date", "revenue", "gross_profit", "net_income"]).__str__())

    balance_sheets = await loader.get_balance_sheet("NVDA", limit=4)
    assert isinstance(balance_sheets, list)

    cashflows = await loader.get_cash_flow_statement("NVDA", limit=4)
    assert isinstance(cashflows, list)

    ratios = await loader.get_financial_ratios("NVDA", limit=4)
    assert isinstance(ratios, list)

    metrics = await loader.get_key_metrics("NVDA", limit=4)
    assert isinstance(metrics, list)

    valuation = await loader.get_valuation("NVDA")
    assert valuation.dcf is not None and valuation.dcf > 0

    income_q = await loader.get_income_statement(
        "NVDA", period=StatementPeriod.QUARTER, limit=2
    )
    assert isinstance(income_q, list)
    await client.aclose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_quotes_batch():
    client = make_client()
    loader = FMPMarketLoader(client)
    quotes = await loader.get_quotes(["AAPL", "MSFT", "NVDA"])
    await client.aclose()
    assert isinstance(quotes, list)
    assert len(quotes) == 3
    df = BaseLoader.to_dataframe(quotes)
    assert "symbol" in df.columns
    print(f"\n批量报价:")
    print(df.select(["symbol", "price"]).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_price_history_intraday():
    client = make_client()
    loader = FMPMarketLoader(client)
    bars = await loader.get_price_history(
        "AAPL",
        start=datetime.date(2026, 5, 28),
        end=datetime.date(2026, 5, 30),
        interval=Interval.ONE_HOUR,
    )
    await client.aclose()
    assert isinstance(bars, list)
    print(f"\nAAPL 小时行情: {len(bars)} 行")
    if len(bars) > 0:
        df = BaseLoader.to_dataframe(bars)
        assert "close" in df.columns


@pytest.mark.integration
@pytest.mark.asyncio
async def test_aapl_analyst_data():
    client = make_client()
    loader = FMPAnalystLoader(client)
    ratings = await loader.get_ratings("AAPL")
    targets = await loader.get_price_targets("AAPL")
    estimates = await loader.get_estimates("AAPL")
    await client.aclose()
    assert isinstance(ratings, list)
    assert isinstance(targets, list)
    assert isinstance(estimates, list)
    print(f"\n=== AAPL 分析师评级 === {len(ratings)} 行")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_calendar_data():
    start = datetime.date(2026, 5, 1)
    end = datetime.date(2026, 7, 31)
    client = make_client()
    loader = FMPCalendarLoader(client)
    earnings = await loader.get_earnings_calendar(start, end)
    dividends = await loader.get_dividend_calendar(start, end)
    ipos = await loader.get_ipo_calendar(start, end)
    splits = await loader.get_splits_calendar(start, end)
    await client.aclose()
    assert isinstance(earnings, list)
    assert isinstance(dividends, list)
    assert isinstance(ipos, list)
    assert isinstance(splits, list)
    print(f"\n财报日历: {len(earnings)} 行  股息日历: {len(dividends)} 行")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_aapl_company_data():
    client = make_client()
    loader = FMPCompanyLoader(client)
    profile = await loader.get_profile("AAPL")
    executives = await loader.get_executives("AAPL")
    peers = await loader.get_peers("AAPL")
    market_caps = await loader.get_market_cap("AAPL")
    await client.aclose()
    assert profile.symbol == "AAPL"
    assert isinstance(executives, list)
    assert isinstance(peers, list)
    assert isinstance(market_caps, list)
    print(f"\n=== AAPL 公司概况 === {profile.company_name}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_congress_trades():
    client = make_client()
    loader = FMPCongressTradeLoader(client)
    senate_trades = await loader.get_congress_trades(chamber=CongressChamber.SENATE, limit=20)
    house_trades = await loader.get_congress_trades(chamber=CongressChamber.HOUSE, limit=20)
    await client.aclose()
    assert isinstance(senate_trades, list)
    assert isinstance(house_trades, list)
    print(f"\n参议院: {len(senate_trades)} 条  众议院: {len(house_trades)} 条")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_directory_data():
    client = make_client()
    loader = FMPDirectoryLoader(client)
    symbols = await loader.get_symbols(AssetClass.STOCK)
    exchanges = await loader.get_exchanges()
    sectors = await loader.get_sectors()
    industries = await loader.get_industries()
    await client.aclose()
    assert isinstance(symbols, list)
    assert len(symbols) > 0
    assert isinstance(exchanges, list)
    assert isinstance(sectors, list)
    assert isinstance(industries, list)
    print(f"\n股票代码: {len(symbols)} 只  交易所: {len(exchanges)} 个")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_economics_data():
    client = make_client()
    loader = FMPEconomicsLoader(client)
    available = await loader.get_available_indicators()
    assert "CPI" in available
    cpi_rows = await loader.get_indicator(
        "CPI",
        start=datetime.date(2024, 1, 1),
        end=datetime.date(2025, 12, 31),
    )
    await client.aclose()
    assert isinstance(cpi_rows, list)
    print(f"\n=== 可用经济指标 === {available}")
    print(f"CPI 数据: {len(cpi_rows)} 行")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_aapl_filings_data():
    client = make_client()
    loader = FMPSecFilingLoader(client)
    filings_10k = await loader.get_filings(symbol="AAPL", form_type="10-K", limit=5)
    sec_profile = await loader.get_sec_profile("AAPL")
    await client.aclose()
    assert isinstance(filings_10k, list)
    assert sec_profile.symbol == "AAPL"
    print(f"\nAAPL 10-K: {len(filings_10k)} 份  CIK: {sec_profile.cik}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nvda_technical_indicators():
    start = datetime.date(2025, 1, 1)
    end = datetime.date(2025, 12, 31)
    client = make_client()
    loader = FMPTechnicalIndicatorLoader(client)
    sma_rows = await loader.get_indicator("NVDA", IndicatorType.SMA, period=20, start=start, end=end)
    rsi_rows = await loader.get_indicator("NVDA", IndicatorType.RSI, period=14, start=start, end=end)
    await client.aclose()
    assert isinstance(sma_rows, list)
    assert len(sma_rows) > 0
    df = BaseLoader.to_dataframe(sma_rows)
    assert "value" in df.columns
    print(f"\nNVDA SMA(20): {len(sma_rows)} 行  RSI(14): {len(rsi_rows)} 行")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insider_trades():
    client = make_client()
    loader = FMPInsiderTradeLoader(client)
    latest_trades = await loader.get_insider_trades(limit=20)
    aapl_trades = await loader.get_insider_trades(symbol="AAPL", limit=10)
    nvda_stats = await loader.get_insider_statistics("NVDA")
    await client.aclose()
    assert isinstance(latest_trades, list)
    assert isinstance(aapl_trades, list)
    assert isinstance(nvda_stats, list)
    print(f"\n全市场内部人交易: {len(latest_trades)} 条  AAPL: {len(aapl_trades)} 条")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_news_data():
    client = make_client()
    loader = FMPNewsLoader(client)
    stock_news = await loader.get_news(symbols=["AAPL", "MSFT"], limit=10)
    general_news = await loader.get_news(limit=10)
    crypto_news = await loader.get_news(asset_class=AssetClass.CRYPTO, limit=10)
    await client.aclose()
    assert isinstance(stock_news, list)
    assert isinstance(general_news, list)
    assert isinstance(crypto_news, list)
    print(f"\n股票新闻: {len(stock_news)} 条  通用新闻: {len(general_news)} 条")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_performance_data():
    client = make_client()
    loader = FMPMarketPerformanceLoader(client)
    gainers = await loader.get_movers(MoverDirection.GAINERS, limit=10)
    losers = await loader.get_movers(MoverDirection.LOSERS, limit=10)
    actives = await loader.get_movers(MoverDirection.ACTIVE, limit=10)
    sector_perfs = await loader.get_sector_performance()
    sector_pes = await loader.get_sector_pe()
    await client.aclose()
    assert isinstance(gainers, list)
    assert isinstance(losers, list)
    assert isinstance(actives, list)
    assert isinstance(sector_perfs, list)
    assert isinstance(sector_pes, list)
    print(f"\n涨幅榜: {len(gainers)} 只  板块表现: {len(sector_perfs)} 个")
