"""全面模型覆盖测试 — 确保每个模型类的所有字段都被测试到。

运行方式：
    uv run --no-active pytest tests/integration/test_all_models_coverage.py -v -m integration -s
"""
import datetime

import pytest

from deepalpha import FMPDataHub
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import (
    AssetClass,
    CongressChamber,
    IndicatorType,
    Interval,
    MoverDirection,
    StatementPeriod,
)


# ══════════════════════════════════════════════════════════════════════════════
# ANALYST MODELS — AnalystRating, PriceTarget, Estimate
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_analyst_rating_model():
    """测试 AnalystRating 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.analyst.get_ratings("AAPL")
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        expected_cols = ["date", "rating", "rating_recommendation", "rating_score"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nAnalystRating 字段验证通过: {list(df.columns)}")
        print(df.head(1).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_price_target_model():
    """测试 PriceTarget 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.analyst.get_price_targets("AAPL")
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        expected_cols = ["last_month", "last_quarter", "last_year", "all_time"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nPriceTarget 字段验证通过: {list(df.columns)}")
        print(df.__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_estimate_model():
    """测试 Estimate 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.analyst.get_estimates("AAPL", period=StatementPeriod.ANNUAL)
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        assert "date" in df.columns
        expected_cols = ["estimated_revenue_avg", "estimated_eps_avg", "number_analyst_estimated_revenue"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nEstimate 字段验证通过: {list(df.columns)}")
        print(df.head(3).__str__())


# ══════════════════════════════════════════════════════════════════════════════
# CALENDAR MODELS — EarningsEvent, DividendEvent, IPOEvent, SplitEvent
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_earnings_event_model():
    """测试 EarningsEvent 模型的所有字段"""
    start, end = datetime.date(2026, 5, 1), datetime.date(2026, 7, 31)
    async with FMPDataHub() as hub:
        result = await hub.calendar.get_earnings_calendar(start, end)
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        assert "date" in df.columns
        expected_cols = ["eps", "eps_estimated", "time", "revenue_estimated"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nEarningsEvent 字段验证通过: {list(df.columns)}")
        print(df.head(3).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dividend_event_model():
    """测试 DividendEvent 模型的所有字段"""
    start, end = datetime.date(2026, 5, 1), datetime.date(2026, 7, 31)
    async with FMPDataHub() as hub:
        result = await hub.calendar.get_dividend_calendar(start, end)
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        assert "date" in df.columns
        expected_cols = ["dividend", "record_date", "payment_date"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nDividendEvent 字段验证通过: {list(df.columns)}")
        print(df.head(3).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ipo_event_model():
    """测试 IPOEvent 模型的所有字段"""
    start, end = datetime.date(2026, 5, 1), datetime.date(2026, 12, 31)
    async with FMPDataHub() as hub:
        result = await hub.calendar.get_ipo_calendar(start, end)
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        assert "date" in df.columns
        expected_cols = ["company", "exchange", "price_range", "shares"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nIPOEvent 字段验证通过: {list(df.columns)}")
        print(df.head(3).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_split_event_model():
    """测试 SplitEvent 模型的所有字段"""
    start, end = datetime.date(2020, 1, 1), datetime.date(2026, 12, 31)
    async with FMPDataHub() as hub:
        result = await hub.calendar.get_splits_calendar(start, end)
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        assert "date" in df.columns
        expected_cols = ["numerator", "denominator"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nSplitEvent 字段验证通过: {list(df.columns)}")
        print(df.head(3).__str__())


# ══════════════════════════════════════════════════════════════════════════════
# COMPANY MODELS — CompanyProfile, Executive, MarketCapRecord
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_company_profile_model():
    """测试 CompanyProfile 模型的所有字段"""
    async with FMPDataHub() as hub:
        profile = await hub.company.get_profile("AAPL")
    assert profile.symbol == "AAPL"
    assert profile.company_name is not None
    assert profile.exchange is not None
    assert profile.industry is not None
    assert profile.sector is not None
    assert hasattr(profile, "description")
    assert hasattr(profile, "website")
    assert hasattr(profile, "full_time_employees")
    assert hasattr(profile, "ceo")
    assert hasattr(profile, "country")
    assert hasattr(profile, "ipo_date")
    assert hasattr(profile, "is_actively_trading")
    print(f"\nCompanyProfile 字段验证通过:")
    print(f"  symbol: {profile.symbol}, company_name: {profile.company_name}")
    print(f"  exchange: {profile.exchange}, industry: {profile.industry}, sector: {profile.sector}")
    print(f"  ceo: {profile.ceo}, employees: {profile.full_time_employees}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_executive_model():
    """测试 Executive 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.company.get_executives("AAPL")
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "name" in df.columns
        assert "title" in df.columns
        expected_cols = ["pay", "currency_of_pay", "gender", "year_born"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nExecutive 字段验证通过: {list(df.columns)}")
        print(df.select(["name", "title", "pay"]).head(5).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_cap_record_model():
    """测试 MarketCapRecord 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.company.get_market_cap("AAPL")
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        assert "date" in df.columns
        assert "market_cap" in df.columns
        assert df["symbol"].item() == "AAPL"
        print(f"\nMarketCapRecord 字段验证通过: {list(df.columns)}")
        print(df.head(3).__str__())


# ══════════════════════════════════════════════════════════════════════════════
# CONGRESS MODEL — CongressTrade
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_congress_trade_model():
    """测试 CongressTrade 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.congress.get_congress_trades(chamber=CongressChamber.SENATE, limit=10)
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        expected_cols = [
            "disclosure_date", "transaction_date", "first_name", "last_name",
            "office", "district", "owner", "type", "amount",
            "asset_description", "asset_type", "link"
        ]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nCongressTrade 字段验证通过: {list(df.columns)}")
        print(df.select(["office", "symbol", "type", "amount"]).head(5).__str__())


# ══════════════════════════════════════════════════════════════════════════════
# DIRECTORY MODELS — SymbolInfo, ExchangeInfo
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_symbol_info_model():
    """测试 SymbolInfo 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.directory.get_symbols(AssetClass.STOCK)
    assert isinstance(result, list)
    assert len(result) > 0
    df = BaseLoader.to_dataframe(result)
    assert "symbol" in df.columns
    expected_cols = ["name", "exchange", "exchange_short_name", "type"]
    for col in expected_cols:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nSymbolInfo 字段验证通过: {list(df.columns)}")
    print(df.head(3).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exchange_info_model():
    """测试 ExchangeInfo 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.directory.get_exchanges()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "exchange" in df.columns
        expected_cols = ["name", "country", "currency"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nExchangeInfo 字段验证通过: {list(df.columns)}")
        print(df.head(5).__str__())


# ══════════════════════════════════════════════════════════════════════════════
# FILINGS MODELS — SecFiling, SecCompanyProfile
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sec_filing_model():
    """测试 SecFiling 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.filings.get_filings(symbol="AAPL", form_type="10-K", limit=5)
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        expected_cols = ["filing_date", "accepted_date", "form_type", "link", "final_link"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nSecFiling 字段验证通过: {list(df.columns)}")
        print(df.select(["filing_date", "form_type", "link"]).head(3).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sec_company_profile_model():
    """测试 SecCompanyProfile 模型的所有字段"""
    async with FMPDataHub() as hub:
        profile = await hub.filings.get_sec_profile("AAPL")
    assert profile.symbol == "AAPL"
    assert profile.cik is not None
    assert profile.registrant_name is not None
    assert hasattr(profile, "sic_code")
    assert hasattr(profile, "sic_description")
    assert hasattr(profile, "sic_group")
    print(f"\nSecCompanyProfile 字段验证通过:")
    print(f"  symbol: {profile.symbol}, cik: {profile.cik}")
    print(f"  registrant_name: {profile.registrant_name}, sic_code: {profile.sic_code}")
    print(f"  sic_description: {profile.sic_description}")


# ══════════════════════════════════════════════════════════════════════════════
# FINANCIAL MODELS — IncomeStatement, BalanceSheet, CashFlow, FinancialRatio,
#                    KeyMetrics, Valuation
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_income_statement_model():
    """测试 IncomeStatement 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.financial.get_income_statement("AAPL", limit=2)
    assert isinstance(result, list)
    assert len(result) > 0
    df = BaseLoader.to_dataframe(result)
    assert "symbol" in df.columns
    assert "date" in df.columns
    assert "period" in df.columns
    expected_cols = ["revenue", "gross_profit", "operating_income", "net_income", "eps", "eps_diluted", "ebitda"]
    for col in expected_cols:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nIncomeStatement 字段验证通过: {list(df.columns)}")
    print(df.select(["date", "period", "revenue", "net_income"]).head(2).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_balance_sheet_model():
    """测试 BalanceSheet 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.financial.get_balance_sheet("AAPL", limit=2)
    assert isinstance(result, list)
    assert len(result) > 0
    df = BaseLoader.to_dataframe(result)
    assert "symbol" in df.columns
    assert "date" in df.columns
    assert "period" in df.columns
    expected_cols = [
        "total_assets", "total_liabilities", "total_stockholders_equity",
        "cash_and_cash_equivalents", "total_debt", "net_debt"
    ]
    for col in expected_cols:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nBalanceSheet 字段验证通过: {list(df.columns)}")
    print(df.select(["date", "total_assets", "total_liabilities", "total_stockholders_equity"]).head(2).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cash_flow_model():
    """测试 CashFlow 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.financial.get_cash_flow_statement("AAPL", limit=2)
    assert isinstance(result, list)
    assert len(result) > 0
    df = BaseLoader.to_dataframe(result)
    assert "symbol" in df.columns
    assert "date" in df.columns
    assert "period" in df.columns
    expected_cols = ["operating_cash_flow", "capital_expenditure", "free_cash_flow", "dividends_paid"]
    for col in expected_cols:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nCashFlow 字段验证通过: {list(df.columns)}")
    print(df.select(["date", "operating_cash_flow", "free_cash_flow"]).head(2).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_financial_ratio_model():
    """测试 FinancialRatio 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.financial.get_financial_ratios("AAPL", limit=2)
    assert isinstance(result, list)
    assert len(result) > 0
    df = BaseLoader.to_dataframe(result)
    assert "symbol" in df.columns
    assert "date" in df.columns
    assert "period" in df.columns
    expected_cols = [
        "current_ratio", "gross_profit_margin", "operating_profit_margin",
        "net_profit_margin", "return_on_equity", "return_on_assets", "debt_equity_ratio"
    ]
    for col in expected_cols:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nFinancialRatio 字段验证通过: {list(df.columns)}")
    print(df.select(["date", "gross_profit_margin", "return_on_equity"]).head(2).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_key_metrics_model():
    """测试 KeyMetrics 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.financial.get_key_metrics("AAPL", limit=2)
    assert isinstance(result, list)
    assert len(result) > 0
    df = BaseLoader.to_dataframe(result)
    assert "symbol" in df.columns
    assert "date" in df.columns
    assert "period" in df.columns
    expected_cols = [
        "pe_ratio", "price_to_book", "price_to_sales", "ev_to_ebitda",
        "free_cash_flow_per_share", "earnings_yield"
    ]
    for col in expected_cols:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nKeyMetrics 字段验证通过: {list(df.columns)}")
    print(df.select(["date", "pe_ratio", "price_to_book"]).head(2).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_valuation_model():
    """测试 Valuation 模型的所有字段"""
    async with FMPDataHub() as hub:
        valuation = await hub.financial.get_valuation("AAPL")
    assert valuation.symbol == "AAPL"
    assert valuation.dcf is not None and valuation.dcf > 0
    assert valuation.stock_price is not None and valuation.stock_price > 0
    print(f"\nValuation 字段验证通过:")
    print(f"  symbol: {valuation.symbol}, dcf: ${valuation.dcf:.2f}, stock_price: ${valuation.stock_price:.2f}")


# ══════════════════════════════════════════════════════════════════════════════
# INDICATORS MODEL — IndicatorRow
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_indicator_row_model():
    """测试 IndicatorRow 模型的所有字段"""
    start, end = datetime.date(2025, 1, 1), datetime.date(2025, 3, 31)
    async with FMPDataHub() as hub:
        result = await hub.indicators.get_indicator("AAPL", IndicatorType.SMA, period=20, start=start, end=end)
    assert isinstance(result, list)
    assert len(result) > 0
    df = BaseLoader.to_dataframe(result)
    assert "date" in df.columns
    assert "value" in df.columns
    expected_cols = ["open", "high", "low", "close", "volume"]
    for col in expected_cols:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nIndicatorRow 字段验证通过: {list(df.columns)}")
    print(df.head(3).__str__())


# ══════════════════════════════════════════════════════════════════════════════
# INSIDER MODELS — InsiderTrade, InsiderStatistics
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insider_trade_model():
    """测试 InsiderTrade 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.insider.get_insider_trades(symbol="AAPL", limit=10)
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        expected_cols = [
            "filing_date", "transaction_date", "reporting_name", "security_name",
            "transaction_type", "acquisition_or_disposition", "securities_transacted",
            "price", "type_of_owner", "form_type", "url"
        ]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nInsiderTrade 字段验证通过: {list(df.columns)}")
        print(df.select(["reporting_name", "securities_transacted", "price"]).head(5).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insider_statistics_model():
    """测试 InsiderStatistics 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.insider.get_insider_statistics("AAPL")
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        expected_cols = [
            "year", "quarter", "acquired_transactions", "disposed_transactions",
            "total_acquired", "total_disposed", "total_purchases", "total_sales"
        ]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nInsiderStatistics 字段验证通过: {list(df.columns)}")
        print(df.select(["year", "quarter", "acquired_transactions", "disposed_transactions"]).head(4).__str__())


# ══════════════════════════════════════════════════════════════════════════════
# MARKET MODELS — Quote, PriceBar
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_quote_model():
    """测试 Quote 模型的所有字段"""
    async with FMPDataHub() as hub:
        quote = await hub.market.get_quote("AAPL")
    assert quote.symbol == "AAPL"
    assert quote.price > 0
    assert hasattr(quote, "name")
    assert hasattr(quote, "change")
    assert hasattr(quote, "changes_percentage")
    assert hasattr(quote, "day_low")
    assert hasattr(quote, "day_high")
    assert hasattr(quote, "year_high")
    assert hasattr(quote, "year_low")
    assert hasattr(quote, "market_cap")
    assert hasattr(quote, "volume")
    assert hasattr(quote, "avg_volume")
    assert hasattr(quote, "open")
    assert hasattr(quote, "previous_close")
    assert hasattr(quote, "eps")
    assert hasattr(quote, "pe")
    assert hasattr(quote, "exchange")
    assert hasattr(quote, "timestamp")
    print(f"\nQuote 字段验证通过:")
    print(f"  symbol: {quote.symbol}, price: ${quote.price:.2f}")
    print(f"  change: {quote.change:.2f}, changes_percentage: {quote.changes_percentage:.2f}%")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_price_bar_model():
    """测试 PriceBar 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.market.get_price_history(
            "AAPL",
            start=datetime.date(2025, 1, 1),
            end=datetime.date(2025, 1, 10)
        )
    assert isinstance(result, list)
    assert len(result) > 0
    df = BaseLoader.to_dataframe(result)
    assert "date" in df.columns
    assert "open" in df.columns
    assert "high" in df.columns
    assert "low" in df.columns
    assert "close" in df.columns
    assert "volume" in df.columns
    assert "adj_close" in df.columns
    print(f"\nPriceBar 字段验证通过: {list(df.columns)}")
    print(df.head(3).__str__())


# ══════════════════════════════════════════════════════════════════════════════
# NEWS MODEL — NewsArticle
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_news_article_model():
    """测试 NewsArticle 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.news.get_news(symbols=["AAPL"], limit=5)
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "title" in df.columns
        assert "url" in df.columns
        expected_cols = ["published_date", "site", "text", "symbol", "sentiment"]
        for col in expected_cols:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nNewsArticle 字段验证通过: {list(df.columns)}")
        print(df.select(["published_date", "site", "title"]).head(3).__str__())


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE MODELS — MarketMover, SectorPerformance, SectorPE
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_mover_model():
    """测试 MarketMover 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.performance.get_movers(MoverDirection.GAINERS, limit=5)
    assert isinstance(result, list)
    assert len(result) > 0
    df = BaseLoader.to_dataframe(result)
    assert "symbol" in df.columns
    assert "name" in df.columns
    expected_cols = ["change", "price", "changes_percentage", "volume"]
    for col in expected_cols:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nMarketMover 字段验证通过: {list(df.columns)}")
    print(df.select(["symbol", "name", "price", "changes_percentage"]).head(5).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sector_performance_model():
    """测试 SectorPerformance 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.performance.get_sector_performance()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "sector" in df.columns
        assert "changes_percentage" in df.columns
        print(f"\nSectorPerformance 字段验证通过: {list(df.columns)}")
        print(df.__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sector_pe_model():
    """测试 SectorPE 模型的所有字段"""
    async with FMPDataHub() as hub:
        result = await hub.performance.get_sector_pe()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "date" in df.columns
        assert "sector" in df.columns
        assert "pe" in df.columns
        print(f"\nSectorPE 字段验证通过: {list(df.columns)}")
        print(df.__str__())
