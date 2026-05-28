# tests/unit/models/test_other_models.py
import polars as pl
from deepalpha.models.price_model import _UTC


class TestCompanyModel:
    def test_fast_info_schema_fields(self):
        from deepalpha.models.company_model import FAST_INFO_SCHEMA
        expected = {"symbol", "last_price", "market_cap", "currency", "exchange",
                    "quote_type", "fifty_day_avg", "two_hundred_day_avg",
                    "year_high", "year_low", "fetched_at"}
        assert set(FAST_INFO_SCHEMA.names()) == expected
        assert FAST_INFO_SCHEMA["fetched_at"] == _UTC

    def test_company_info_schema_fields(self):
        from deepalpha.models.company_model import COMPANY_INFO_SCHEMA
        expected = {"symbol", "short_name", "sector", "industry", "country",
                    "employees", "trailing_pe", "forward_pe", "price_to_book",
                    "beta", "dividend_yield", "market_cap", "business_summary", "fetched_at"}
        assert set(COMPANY_INFO_SCHEMA.names()) == expected
        assert COMPANY_INFO_SCHEMA["employees"] == pl.Int64


class TestFinancialsModel:
    def test_income_stmt_schema_fields(self):
        from deepalpha.models.financials_model import INCOME_STMT_SCHEMA
        expected = {"symbol", "period_end", "freq", "total_revenue", "gross_profit",
                    "operating_income", "net_income", "ebitda", "diluted_eps", "fetched_at"}
        assert set(INCOME_STMT_SCHEMA.names()) == expected
        assert INCOME_STMT_SCHEMA["freq"] == pl.String
        assert INCOME_STMT_SCHEMA["period_end"] == pl.Date

    def test_balance_sheet_schema_fields(self):
        from deepalpha.models.financials_model import BALANCE_SHEET_SCHEMA
        expected = {"symbol", "period_end", "freq", "total_assets", "total_liabilities",
                    "stockholders_equity", "total_debt", "cash_and_equivalents",
                    "net_debt", "fetched_at"}
        assert set(BALANCE_SHEET_SCHEMA.names()) == expected

    def test_cash_flow_schema_fields(self):
        from deepalpha.models.financials_model import CASH_FLOW_SCHEMA
        expected = {"symbol", "period_end", "freq", "operating_cash_flow",
                    "investing_cash_flow", "financing_cash_flow", "free_cash_flow",
                    "capital_expenditure", "fetched_at"}
        assert set(CASH_FLOW_SCHEMA.names()) == expected


class TestAnalysisModel:
    def test_analyst_rating_schema(self):
        from deepalpha.models.analysis_model import ANALYST_RATING_SCHEMA
        assert set(ANALYST_RATING_SCHEMA.names()) == {
            "symbol", "date", "firm", "to_grade", "from_grade", "action", "fetched_at"}

    def test_price_target_schema(self):
        from deepalpha.models.analysis_model import PRICE_TARGET_SCHEMA
        assert set(PRICE_TARGET_SCHEMA.names()) == {
            "symbol", "current", "mean", "high", "low", "num_analysts", "fetched_at"}
        assert PRICE_TARGET_SCHEMA["num_analysts"] == pl.Int32

    def test_earnings_estimate_schema(self):
        from deepalpha.models.analysis_model import EARNINGS_ESTIMATE_SCHEMA
        assert "period" in EARNINGS_ESTIMATE_SCHEMA.names()
        assert "avg_eps" in EARNINGS_ESTIMATE_SCHEMA.names()
        assert "avg_revenue" in EARNINGS_ESTIMATE_SCHEMA.names()

    def test_esg_schema(self):
        from deepalpha.models.analysis_model import ESG_SCHEMA
        assert set(ESG_SCHEMA.names()) == {
            "symbol", "total_esg", "environment", "social",
            "governance", "controversy_level", "fetched_at"}


class TestHoldingsModel:
    def test_institutional_holder_schema(self):
        from deepalpha.models.holdings_model import INSTITUTIONAL_HOLDER_SCHEMA
        assert set(INSTITUTIONAL_HOLDER_SCHEMA.names()) == {
            "symbol", "holder", "shares", "date_reported", "pct_out", "value", "fetched_at"}
        assert INSTITUTIONAL_HOLDER_SCHEMA["shares"] == pl.Int64

    def test_insider_transaction_schema(self):
        from deepalpha.models.holdings_model import INSIDER_TRANSACTION_SCHEMA
        assert set(INSIDER_TRANSACTION_SCHEMA.names()) == {
            "symbol", "insider", "shares", "value", "transaction", "date", "fetched_at"}


class TestETFModel:
    def test_fund_overview_schema(self):
        from deepalpha.models.etf_model import FUND_OVERVIEW_SCHEMA
        assert "morning_star_rating" in FUND_OVERVIEW_SCHEMA.names()
        assert FUND_OVERVIEW_SCHEMA["morning_star_rating"] == pl.Int32

    def test_fund_holdings_schema(self):
        from deepalpha.models.etf_model import FUND_HOLDINGS_SCHEMA
        assert set(FUND_HOLDINGS_SCHEMA.names()) == {
            "symbol", "holding_symbol", "holding_name", "pct", "fetched_at"}

    def test_sector_weights_schema(self):
        from deepalpha.models.etf_model import SECTOR_WEIGHTS_SCHEMA
        assert set(SECTOR_WEIGHTS_SCHEMA.names()) == {"symbol", "sector", "weight", "fetched_at"}


class TestSectorModel:
    def test_sector_overview_schema(self):
        from deepalpha.models.sector_model import SECTOR_OVERVIEW_SCHEMA
        assert set(SECTOR_OVERVIEW_SCHEMA.names()) == {
            "key", "name", "etf_symbol", "market_cap", "ytd_return", "fetched_at"}

    def test_industry_overview_schema(self):
        from deepalpha.models.sector_model import INDUSTRY_OVERVIEW_SCHEMA
        assert set(INDUSTRY_OVERVIEW_SCHEMA.names()) == {
            "key", "name", "sector_key", "fetched_at"}


class TestCalendarModel:
    def test_earnings_calendar_schema(self):
        from deepalpha.models.calendar_model import EARNINGS_CALENDAR_SCHEMA
        assert "earnings_date" in EARNINGS_CALENDAR_SCHEMA.names()
        assert "eps_estimate_avg" in EARNINGS_CALENDAR_SCHEMA.names()

    def test_market_status_schema(self):
        from deepalpha.models.calendar_model import MARKET_STATUS_SCHEMA
        assert set(MARKET_STATUS_SCHEMA.names()) == {"market", "status", "timezone", "fetched_at"}


class TestNewsModel:
    def test_news_item_schema(self):
        from deepalpha.models.news_model import NEWS_ITEM_SCHEMA
        assert set(NEWS_ITEM_SCHEMA.names()) == {
            "symbol", "title", "publisher", "url", "published_at", "tab", "fetched_at"}
        assert NEWS_ITEM_SCHEMA["published_at"] == _UTC


class TestUniverseModel:
    def test_screen_result_schema(self):
        from deepalpha.models.universe_model import SCREEN_RESULT_SCHEMA
        assert set(SCREEN_RESULT_SCHEMA.names()) == {
            "symbol", "short_name", "exchange", "market_cap",
            "trailing_pe", "dividend_yield", "fetched_at"}
