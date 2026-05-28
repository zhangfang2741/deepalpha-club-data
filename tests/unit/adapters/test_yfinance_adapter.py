# tests/unit/adapters/test_yfinance_adapter.py
import polars as pl
from datetime import date, datetime, timezone
from deepalpha.adapters.yfinance_adapter import YFinanceAdapter
from deepalpha.models.price_model import PRICE_BAR_SCHEMA, DIVIDENDS_SCHEMA, SPLITS_SCHEMA
from deepalpha.models.company_model import FAST_INFO_SCHEMA, COMPANY_INFO_SCHEMA
from deepalpha.models.financials_model import INCOME_STMT_SCHEMA, BALANCE_SHEET_SCHEMA, CASH_FLOW_SCHEMA
from deepalpha.models.analysis_model import ANALYST_RATING_SCHEMA, PRICE_TARGET_SCHEMA, ESG_SCHEMA
from deepalpha.models.holdings_model import INSTITUTIONAL_HOLDER_SCHEMA, INSIDER_TRANSACTION_SCHEMA
from deepalpha.models.etf_model import FUND_OVERVIEW_SCHEMA, FUND_HOLDINGS_SCHEMA, SECTOR_WEIGHTS_SCHEMA
from deepalpha.models.sector_model import SECTOR_OVERVIEW_SCHEMA, INDUSTRY_OVERVIEW_SCHEMA
from deepalpha.models.calendar_model import EARNINGS_CALENDAR_SCHEMA
from deepalpha.models.news_model import NEWS_ITEM_SCHEMA
from deepalpha.models.universe_model import SCREEN_RESULT_SCHEMA


def _make_raw_price():
    return pl.DataFrame({
        "Date":         [date(2024, 1, 2)],
        "Open":         [185.0],
        "High":         [188.0],
        "Low":          [184.0],
        "Close":        [187.0],
        "Adj Close":    [187.0],
        "Volume":       [1_000_000],
        "Dividends":    [0.0],
        "Stock Splits": [0.0],
        "symbol":       ["AAPL"],
    })


class TestYFinanceAdapterPrice:
    def test_adapt_price_schema_matches_canonical(self):
        """Output schema must exactly equal PRICE_BAR_SCHEMA."""
        result = YFinanceAdapter().adapt_price(_make_raw_price())
        assert result.schema == PRICE_BAR_SCHEMA

    def test_adapt_price_repaired_false_when_column_absent(self):
        """repaired defaults to False when Repaired? column is absent."""
        result = YFinanceAdapter().adapt_price(_make_raw_price())
        assert result["repaired"][0] is False

    def test_adapt_price_repaired_from_column_when_present(self):
        """repaired reads from Repaired? column when present."""
        raw = _make_raw_price().with_columns(pl.lit(True).alias("Repaired?"))
        result = YFinanceAdapter().adapt_price(raw)
        assert result["repaired"][0] is True

    def test_adapt_price_symbol_preserved(self):
        """symbol column from loader is preserved."""
        result = YFinanceAdapter().adapt_price(_make_raw_price())
        assert result["symbol"][0] == "AAPL"

    def test_adapt_price_fetched_at_utc(self):
        """fetched_at is timezone-aware UTC."""
        result = YFinanceAdapter().adapt_price(_make_raw_price())
        assert result["fetched_at"].dtype == PRICE_BAR_SCHEMA["fetched_at"]


class TestYFinanceAdapterDividends:
    def test_adapt_dividends_schema(self):
        """adapt_dividends output matches DIVIDENDS_SCHEMA."""
        raw = pl.DataFrame({"date": [date(2024, 1, 15)], "value": [0.24], "symbol": ["AAPL"]})
        result = YFinanceAdapter().adapt_dividends(raw)
        assert result.schema == DIVIDENDS_SCHEMA


class TestYFinanceAdapterSplits:
    def test_adapt_splits_schema(self):
        """adapt_splits output matches SPLITS_SCHEMA."""
        raw = pl.DataFrame({"date": [date(2020, 8, 31)], "value": [4.0], "symbol": ["AAPL"]})
        result = YFinanceAdapter().adapt_splits(raw)
        assert result.schema == SPLITS_SCHEMA


class TestYFinanceAdapterCompany:
    def test_adapt_fast_info_schema(self):
        """adapt_fast_info output matches FAST_INFO_SCHEMA."""
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "last_price": [185.0], "market_cap": [2.9e12],
            "currency": ["USD"], "exchange": ["NMS"], "quote_type": ["EQUITY"],
            "fifty_day_avg": [183.0], "two_hundred_day_avg": [180.0],
            "year_high": [200.0], "year_low": [160.0],
        })
        result = YFinanceAdapter().adapt_fast_info(raw)
        assert result.schema == FAST_INFO_SCHEMA

    def test_adapt_company_info_schema(self):
        """adapt_company_info output matches COMPANY_INFO_SCHEMA."""
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "short_name": ["Apple Inc."],
            "sector": ["Technology"], "industry": ["Consumer Electronics"],
            "country": ["United States"], "employees": [164_000],
            "trailing_pe": [28.5], "forward_pe": [26.0],
            "price_to_book": [45.0], "beta": [1.2],
            "dividend_yield": [0.005], "market_cap": [2.9e12],
            "business_summary": ["Apple designs electronics."],
        })
        result = YFinanceAdapter().adapt_company_info(raw)
        assert result.schema == COMPANY_INFO_SCHEMA


class TestYFinanceAdapterFinancials:
    def _make_raw_income(self):
        return pl.DataFrame({
            "period_end":       [date(2024, 9, 28)],
            "Total Revenue":    [3.91e11],
            "Gross Profit":     [1.74e11],
            "Operating Income": [1.19e11],
            "Net Income":       [9.38e10],
            "EBITDA":           [1.31e11],
            "Diluted EPS":      [6.11],
            "symbol":           ["AAPL"],
            "freq":             ["annual"],
        })

    def test_adapt_income_stmt_schema(self):
        """adapt_income_stmt output matches INCOME_STMT_SCHEMA."""
        result = YFinanceAdapter().adapt_income_stmt(self._make_raw_income(), freq="annual")
        assert result.schema == INCOME_STMT_SCHEMA

    def test_adapt_income_stmt_freq_preserved(self):
        """adapt_income_stmt preserves freq from raw data."""
        result = YFinanceAdapter().adapt_income_stmt(self._make_raw_income(), freq="quarterly")
        assert result["freq"][0] == "quarterly"

    def test_adapt_balance_sheet_schema(self):
        """adapt_balance_sheet output matches BALANCE_SHEET_SCHEMA."""
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "period_end": [date(2024, 9, 28)], "freq": ["annual"],
            "Total Assets": [3.64e11], "Total Liabilities Net Minority Interest": [3.08e11],
            "Stockholders Equity": [5.67e10], "Total Debt": [1.04e11],
            "Cash And Cash Equivalents": [2.93e10], "Net Debt": [7.49e10],
        })
        result = YFinanceAdapter().adapt_balance_sheet(raw, freq="annual")
        assert result.schema == BALANCE_SHEET_SCHEMA

    def test_adapt_cash_flow_schema(self):
        """adapt_cash_flow output matches CASH_FLOW_SCHEMA."""
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "period_end": [date(2024, 9, 28)], "freq": ["annual"],
            "Operating Cash Flow": [1.18e11], "Investing Cash Flow": [-2.0e10],
            "Financing Cash Flow": [-1.0e11], "Free Cash Flow": [1.08e11],
            "Capital Expenditure": [-9.95e9],
        })
        result = YFinanceAdapter().adapt_cash_flow(raw, freq="annual")
        assert result.schema == CASH_FLOW_SCHEMA


class TestYFinanceAdapterAnalysis:
    def test_adapt_analyst_ratings_schema(self):
        """adapt_analyst_ratings output matches ANALYST_RATING_SCHEMA."""
        raw = pl.DataFrame({
            "Date":       [date(2024, 1, 5)],
            "Firm":       ["Goldman Sachs"],
            "To Grade":   ["Buy"],
            "From Grade": ["Hold"],
            "Action":     ["up"],
            "symbol":     ["AAPL"],
        })
        result = YFinanceAdapter().adapt_analyst_ratings(raw)
        assert result.schema == ANALYST_RATING_SCHEMA

    def test_adapt_price_targets_schema(self):
        """adapt_price_targets output matches PRICE_TARGET_SCHEMA."""
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "current": [185.0], "mean": [200.0],
            "high": [230.0], "low": [175.0], "num_analysts": [35],
        })
        result = YFinanceAdapter().adapt_price_targets(raw)
        assert result.schema == PRICE_TARGET_SCHEMA

    def test_adapt_esg_schema(self):
        """adapt_esg output matches ESG_SCHEMA."""
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "total_esg": [17.5],
            "environment": [2.1], "social": [8.3],
            "governance": [7.1], "controversy_level": ["3"],
        })
        result = YFinanceAdapter().adapt_esg(raw)
        assert result.schema == ESG_SCHEMA


class TestYFinanceAdapterHoldings:
    def test_adapt_institutional_holders_schema(self):
        """adapt_institutional_holders output matches INSTITUTIONAL_HOLDER_SCHEMA."""
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "Holder": ["Vanguard"],
            "Shares": [1_200_000_000], "Date Reported": [date(2024, 3, 31)],
            "% Out": [0.075], "Value": [2.2e11],
        })
        result = YFinanceAdapter().adapt_institutional_holders(raw)
        assert result.schema == INSTITUTIONAL_HOLDER_SCHEMA

    def test_adapt_insider_transactions_schema(self):
        """adapt_insider_transactions output matches INSIDER_TRANSACTION_SCHEMA."""
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "Insider": ["Tim Cook"],
            "Shares": [50_000], "Value": [9_200_000.0],
            "Transaction": ["Sale"], "Start Date": [date(2024, 2, 1)],
        })
        result = YFinanceAdapter().adapt_insider_transactions(raw)
        assert result.schema == INSIDER_TRANSACTION_SCHEMA


class TestYFinanceAdapterOther:
    def test_adapt_sector_overview_schema(self):
        """adapt_sector_overview output matches SECTOR_OVERVIEW_SCHEMA."""
        raw = pl.DataFrame({
            "key": ["technology"], "name": ["Technology"],
            "etf_symbol": ["XLK"], "market_cap": [15e12], "ytd_return": [0.28],
        })
        result = YFinanceAdapter().adapt_sector_overview(raw)
        assert result.schema == SECTOR_OVERVIEW_SCHEMA

    def test_adapt_news_schema(self):
        """adapt_news output matches NEWS_ITEM_SCHEMA."""
        raw = pl.DataFrame({
            "symbol":       ["AAPL"],
            "title":        ["Apple reports record earnings"],
            "publisher":    ["Reuters"],
            "url":          ["https://reuters.com/article/1"],
            "published_at": [datetime(2024, 1, 2, tzinfo=timezone.utc)],
            "tab":          ["news"],
        })
        result = YFinanceAdapter().adapt_news(raw)
        assert result.schema == NEWS_ITEM_SCHEMA

    def test_adapt_screen_results_schema(self):
        """adapt_screen_results output matches SCREEN_RESULT_SCHEMA."""
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "short_name": ["Apple Inc."],
            "exchange": ["NMS"], "market_cap": [2.9e12],
            "trailing_pe": [28.5], "dividend_yield": [0.005],
        })
        result = YFinanceAdapter().adapt_screen_results(raw)
        assert result.schema == SCREEN_RESULT_SCHEMA
