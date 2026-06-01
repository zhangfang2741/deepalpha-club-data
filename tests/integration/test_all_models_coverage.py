"""全面模型覆盖测试 — 确保每个模型类的所有字段都被测试到。

运行方式：
    uv run --no-active pytest tests/integration/test_all_models_coverage.py -v -m integration -s
"""
import datetime

import pytest

from deepalpha.domain.market.enums import (
    AssetClass,
    CongressChamber,
    IndicatorType,
    MoverDirection,
)
from deepalpha.domain.financial.enums import StatementPeriod
from deepalpha.infrastructure.providers.base import BaseLoader
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.analyst_loader import FMPAnalystLoader
from deepalpha.infrastructure.providers.fmp.loaders.calendar_loader import FMPCalendarLoader
from deepalpha.infrastructure.providers.fmp.loaders.company_loader import FMPCompanyLoader
from deepalpha.infrastructure.providers.fmp.loaders.congress_loader import FMPCongressTradeLoader
from deepalpha.infrastructure.providers.fmp.loaders.directory_loader import FMPDirectoryLoader
from deepalpha.infrastructure.providers.fmp.loaders.economics_loader import FMPEconomicsLoader
from deepalpha.infrastructure.providers.fmp.loaders.filings_loader import FMPSecFilingLoader
from deepalpha.infrastructure.providers.fmp.loaders.financial_loader import FMPFinancialLoader
from deepalpha.infrastructure.providers.fmp.loaders.indicators_loader import FMPTechnicalIndicatorLoader
from deepalpha.infrastructure.providers.fmp.loaders.insider_loader import FMPInsiderTradeLoader
from deepalpha.infrastructure.providers.fmp.loaders.market_loader import FMPMarketLoader
from deepalpha.infrastructure.providers.fmp.loaders.news_loader import FMPNewsLoader
from deepalpha.infrastructure.providers.fmp.loaders.performance_loader import FMPMarketPerformanceLoader


def make_client() -> FMPAsyncClient:
    return FMPAsyncClient(FMPConfig())


# ══════════════════════════════════════════════════════════════════════════════
# ANALYST MODELS — AnalystRating, PriceTarget, Estimate
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_analyst_rating_model():
    """测试 AnalystRating 模型的所有字段"""
    client = make_client()
    result = await FMPAnalystLoader(client).get_ratings("AAPL")
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        for col in ["date", "rating", "rating_recommendation", "rating_score"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nAnalystRating 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_price_target_model():
    """测试 PriceTarget 模型的所有字段"""
    client = make_client()
    result = await FMPAnalystLoader(client).get_price_targets("AAPL")
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["last_month", "last_quarter", "last_year", "all_time"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nPriceTarget 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_estimate_model():
    """测试 Estimate 模型的所有字段"""
    client = make_client()
    result = await FMPAnalystLoader(client).get_estimates("AAPL", period=StatementPeriod.ANNUAL)
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["estimated_revenue_avg", "estimated_eps_avg", "number_analyst_estimated_revenue"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nEstimate 字段验证通过: {list(df.columns)}")


# ══════════════════════════════════════════════════════════════════════════════
# CALENDAR MODELS
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_earnings_event_model():
    """测试 EarningsEvent 模型的所有字段"""
    start, end = datetime.date(2026, 5, 1), datetime.date(2026, 7, 31)
    client = make_client()
    result = await FMPCalendarLoader(client).get_earnings_calendar(start, end)
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        assert "symbol" in df.columns
        for col in ["eps", "eps_estimated", "time", "revenue_estimated"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nEarningsEvent 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dividend_event_model():
    """测试 DividendEvent 模型的所有字段"""
    start, end = datetime.date(2026, 5, 1), datetime.date(2026, 7, 31)
    client = make_client()
    result = await FMPCalendarLoader(client).get_dividend_calendar(start, end)
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["dividend", "record_date", "payment_date"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nDividendEvent 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ipo_event_model():
    """测试 IPOEvent 模型的所有字段"""
    start, end = datetime.date(2026, 5, 1), datetime.date(2026, 12, 31)
    client = make_client()
    result = await FMPCalendarLoader(client).get_ipo_calendar(start, end)
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["company", "exchange", "price_range", "shares"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nIPOEvent 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_split_event_model():
    """测试 SplitEvent 模型的所有字段"""
    from deepalpha.infrastructure.providers.fmp.errors import FMPAuthError
    start, end = datetime.date(2020, 1, 1), datetime.date(2026, 12, 31)
    client = make_client()
    try:
        result = await FMPCalendarLoader(client).get_splits_calendar(start, end)
    except FMPAuthError:
        await client.aclose()
        pytest.skip("splits-calendar 端点需要更高订阅计划")
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["numerator", "denominator"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nSplitEvent 字段验证通过: {list(df.columns)}")


# ══════════════════════════════════════════════════════════════════════════════
# COMPANY MODELS
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_company_profile_model():
    """测试 CompanyProfile 模型的所有字段"""
    client = make_client()
    profile = await FMPCompanyLoader(client).get_profile("AAPL")
    await client.aclose()
    assert profile.symbol == "AAPL"
    assert profile.company_name is not None
    for attr in ["exchange", "industry", "sector", "description", "website",
                 "full_time_employees", "ceo", "country", "ipo_date", "is_actively_trading"]:
        assert hasattr(profile, attr)
    print(f"\nCompanyProfile: {profile.symbol} / {profile.company_name}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_executive_model():
    """测试 Executive 模型的所有字段"""
    client = make_client()
    result = await FMPCompanyLoader(client).get_executives("AAPL")
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["name", "title", "pay", "currency_of_pay", "gender", "year_born"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nExecutive 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_cap_record_model():
    """测试 MarketCapRecord 模型的所有字段"""
    client = make_client()
    result = await FMPCompanyLoader(client).get_market_cap("AAPL")
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["symbol", "date", "market_cap"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nMarketCapRecord 字段验证通过: {list(df.columns)}")


# ══════════════════════════════════════════════════════════════════════════════
# CONGRESS MODEL
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_congress_trade_model():
    """测试 CongressTrade 模型的所有字段"""
    client = make_client()
    result = await FMPCongressTradeLoader(client).get_congress_trades(
        chamber=CongressChamber.SENATE, limit=10
    )
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["symbol", "disclosure_date", "transaction_date", "first_name",
                    "last_name", "office", "district", "owner", "type", "amount",
                    "asset_description", "asset_type", "link"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nCongressTrade 字段验证通过: {list(df.columns)}")


# ══════════════════════════════════════════════════════════════════════════════
# DIRECTORY MODELS
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_symbol_info_model():
    """测试 SymbolInfo 模型的所有字段"""
    client = make_client()
    result = await FMPDirectoryLoader(client).get_symbols(AssetClass.STOCK)
    await client.aclose()
    assert isinstance(result, list)
    assert len(result) > 0
    df = BaseLoader.to_dataframe(result)
    for col in ["symbol", "name", "exchange", "exchange_short_name", "type"]:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nSymbolInfo 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exchange_info_model():
    """测试 ExchangeInfo 模型的所有字段"""
    client = make_client()
    result = await FMPDirectoryLoader(client).get_exchanges()
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["exchange", "name", "country", "currency"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nExchangeInfo 字段验证通过: {list(df.columns)}")


# ══════════════════════════════════════════════════════════════════════════════
# FILINGS MODELS
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sec_filing_model():
    """测试 SecFiling 模型的所有字段"""
    client = make_client()
    result = await FMPSecFilingLoader(client).get_filings(symbol="AAPL", form_type="10-K", limit=5)
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["symbol", "filing_date", "accepted_date", "form_type", "link", "final_link"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nSecFiling 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sec_company_profile_model():
    """测试 SecCompanyProfile 模型的所有字段"""
    client = make_client()
    profile = await FMPSecFilingLoader(client).get_sec_profile("AAPL")
    await client.aclose()
    assert profile.symbol == "AAPL"
    assert profile.cik is not None
    for attr in ["registrant_name", "sic_code", "sic_description", "sic_group"]:
        assert hasattr(profile, attr)
    print(f"\nSecCompanyProfile: {profile.symbol} / CIK: {profile.cik}")


# ══════════════════════════════════════════════════════════════════════════════
# FINANCIAL MODELS
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_income_statement_model():
    """测试 IncomeStatement 模型的所有字段"""
    client = make_client()
    result = await FMPFinancialLoader(client).get_income_statement("AAPL", limit=2)
    await client.aclose()
    assert isinstance(result, list) and len(result) > 0
    df = BaseLoader.to_dataframe(result)
    for col in ["symbol", "date", "period", "revenue", "gross_profit",
                "operating_income", "net_income", "eps", "eps_diluted", "ebitda"]:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nIncomeStatement 字段验证通过")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_balance_sheet_model():
    """测试 BalanceSheet 模型的所有字段"""
    client = make_client()
    result = await FMPFinancialLoader(client).get_balance_sheet("AAPL", limit=2)
    await client.aclose()
    assert isinstance(result, list) and len(result) > 0
    df = BaseLoader.to_dataframe(result)
    for col in ["symbol", "date", "period", "total_assets", "total_liabilities",
                "total_stockholders_equity", "cash_and_cash_equivalents", "total_debt", "net_debt"]:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nBalanceSheet 字段验证通过")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cash_flow_model():
    """测试 CashFlow 模型的所有字段"""
    client = make_client()
    result = await FMPFinancialLoader(client).get_cash_flow_statement("AAPL", limit=2)
    await client.aclose()
    assert isinstance(result, list) and len(result) > 0
    df = BaseLoader.to_dataframe(result)
    for col in ["symbol", "date", "period", "operating_cash_flow",
                "capital_expenditure", "free_cash_flow", "dividends_paid"]:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nCashFlow 字段验证通过")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_financial_ratio_model():
    """测试 FinancialRatio 模型的所有字段"""
    client = make_client()
    result = await FMPFinancialLoader(client).get_financial_ratios("AAPL", limit=2)
    await client.aclose()
    assert isinstance(result, list) and len(result) > 0
    df = BaseLoader.to_dataframe(result)
    for col in ["symbol", "date", "period", "current_ratio", "gross_profit_margin",
                "operating_profit_margin", "net_profit_margin",
                "return_on_equity", "return_on_assets", "debt_equity_ratio"]:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nFinancialRatio 字段验证通过")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_key_metrics_model():
    """测试 KeyMetrics 模型的所有字段"""
    client = make_client()
    result = await FMPFinancialLoader(client).get_key_metrics("AAPL", limit=2)
    await client.aclose()
    assert isinstance(result, list) and len(result) > 0
    df = BaseLoader.to_dataframe(result)
    for col in ["symbol", "date", "period", "pe_ratio", "price_to_book",
                "price_to_sales", "ev_to_ebitda", "free_cash_flow_per_share", "earnings_yield"]:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nKeyMetrics 字段验证通过")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_valuation_model():
    """测试 Valuation 模型的所有字段"""
    client = make_client()
    valuation = await FMPFinancialLoader(client).get_valuation("AAPL")
    await client.aclose()
    assert valuation.symbol == "AAPL"
    assert valuation.dcf is not None and valuation.dcf > 0
    assert hasattr(valuation, "stock_price")
    print(f"\nValuation: dcf=${valuation.dcf:.2f}")


# ══════════════════════════════════════════════════════════════════════════════
# INDICATORS MODEL
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_indicator_row_model():
    """测试 IndicatorRow 模型的所有字段"""
    start, end = datetime.date(2025, 1, 1), datetime.date(2025, 3, 31)
    client = make_client()
    result = await FMPTechnicalIndicatorLoader(client).get_indicator(
        "AAPL", IndicatorType.SMA, period=20, start=start, end=end
    )
    await client.aclose()
    assert isinstance(result, list) and len(result) > 0
    df = BaseLoader.to_dataframe(result)
    for col in ["date", "value", "open", "high", "low", "close", "volume"]:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nIndicatorRow 字段验证通过: {list(df.columns)}")


# ══════════════════════════════════════════════════════════════════════════════
# INSIDER MODELS
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insider_trade_model():
    """测试 InsiderTrade 模型的所有字段"""
    client = make_client()
    result = await FMPInsiderTradeLoader(client).get_insider_trades(symbol="AAPL", limit=10)
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["symbol", "filing_date", "transaction_date", "reporting_name",
                    "security_name", "transaction_type", "acquisition_or_disposition",
                    "securities_transacted", "price", "type_of_owner", "form_type", "url"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nInsiderTrade 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insider_statistics_model():
    """测试 InsiderStatistics 模型的所有字段"""
    client = make_client()
    result = await FMPInsiderTradeLoader(client).get_insider_statistics("AAPL")
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["symbol", "year", "quarter", "acquired_transactions",
                    "disposed_transactions", "total_acquired", "total_disposed",
                    "total_purchases", "total_sales"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nInsiderStatistics 字段验证通过: {list(df.columns)}")


# ══════════════════════════════════════════════════════════════════════════════
# MARKET MODELS
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_quote_model():
    """测试 Quote 模型的所有字段"""
    client = make_client()
    quote = await FMPMarketLoader(client).get_quote("AAPL")
    await client.aclose()
    assert quote.symbol == "AAPL"
    assert quote.price > 0
    for attr in ["name", "change", "changes_percentage", "day_low", "day_high",
                 "year_high", "year_low", "market_cap", "volume", "avg_volume",
                 "open", "previous_close", "eps", "pe", "exchange", "timestamp"]:
        assert hasattr(quote, attr)
    print(f"\nQuote: {quote.symbol} ${quote.price:.2f}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_price_bar_model():
    """测试 PriceBar 模型的所有字段"""
    client = make_client()
    result = await FMPMarketLoader(client).get_price_history(
        "AAPL",
        start=datetime.date(2025, 1, 1),
        end=datetime.date(2025, 1, 10),
    )
    await client.aclose()
    assert isinstance(result, list) and len(result) > 0
    df = BaseLoader.to_dataframe(result)
    for col in ["date", "open", "high", "low", "close", "volume", "adj_close"]:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nPriceBar 字段验证通过: {list(df.columns)}")


# ══════════════════════════════════════════════════════════════════════════════
# NEWS MODEL
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_news_article_model():
    """测试 NewsArticle 模型的所有字段"""
    client = make_client()
    result = await FMPNewsLoader(client).get_news(symbols=["AAPL"], limit=5)
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["title", "url", "published_date", "site", "text", "symbol", "sentiment"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nNewsArticle 字段验证通过: {list(df.columns)}")


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE MODELS
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_mover_model():
    """测试 MarketMover 模型的所有字段"""
    client = make_client()
    result = await FMPMarketPerformanceLoader(client).get_movers(MoverDirection.GAINERS, limit=5)
    await client.aclose()
    assert isinstance(result, list) and len(result) > 0
    df = BaseLoader.to_dataframe(result)
    for col in ["symbol", "name", "change", "price", "changes_percentage", "volume"]:
        assert col in df.columns, f"缺少字段: {col}"
    print(f"\nMarketMover 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sector_performance_model():
    """测试 SectorPerformance 模型的所有字段"""
    client = make_client()
    result = await FMPMarketPerformanceLoader(client).get_sector_performance()
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["sector", "changes_percentage"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nSectorPerformance 字段验证通过: {list(df.columns)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sector_pe_model():
    """测试 SectorPE 模型的所有字段"""
    client = make_client()
    result = await FMPMarketPerformanceLoader(client).get_sector_pe()
    await client.aclose()
    assert isinstance(result, list)
    if len(result) > 0:
        df = BaseLoader.to_dataframe(result)
        for col in ["date", "sector", "pe"]:
            assert col in df.columns, f"缺少字段: {col}"
        print(f"\nSectorPE 字段验证通过: {list(df.columns)}")
