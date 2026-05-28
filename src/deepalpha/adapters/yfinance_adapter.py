# src/deepalpha/adapters/yfinance_adapter.py
"""Adapter for transforming raw YFinanceLoader DataFrames to canonical schemas."""
from datetime import datetime, timezone

import polars as pl

from deepalpha.adapters.base_adapter import BaseAdapter
from deepalpha.models.price_model import PRICE_BAR_SCHEMA, DIVIDENDS_SCHEMA, SPLITS_SCHEMA
from deepalpha.models.company_model import FAST_INFO_SCHEMA, COMPANY_INFO_SCHEMA
from deepalpha.models.financials_model import INCOME_STMT_SCHEMA, BALANCE_SHEET_SCHEMA, CASH_FLOW_SCHEMA
from deepalpha.models.analysis_model import (
    ANALYST_RATING_SCHEMA, PRICE_TARGET_SCHEMA, EARNINGS_ESTIMATE_SCHEMA, ESG_SCHEMA,
)
from deepalpha.models.holdings_model import INSTITUTIONAL_HOLDER_SCHEMA, INSIDER_TRANSACTION_SCHEMA
from deepalpha.models.etf_model import FUND_OVERVIEW_SCHEMA, FUND_HOLDINGS_SCHEMA, SECTOR_WEIGHTS_SCHEMA
from deepalpha.models.sector_model import SECTOR_OVERVIEW_SCHEMA, INDUSTRY_OVERVIEW_SCHEMA
from deepalpha.models.calendar_model import EARNINGS_CALENDAR_SCHEMA
from deepalpha.models.news_model import NEWS_ITEM_SCHEMA
from deepalpha.models.universe_model import SCREEN_RESULT_SCHEMA


def _add_fetched_at(df: pl.DataFrame, schema: pl.Schema) -> pl.DataFrame:
    """Inject a UTC-aware fetched_at column cast to the schema's type."""
    now = datetime.now(timezone.utc)
    return df.with_columns(
        pl.lit(now).cast(schema["fetched_at"]).alias("fetched_at")
    )


def _rename_existing(df: pl.DataFrame, rename_map: dict[str, str]) -> pl.DataFrame:
    """Apply rename_map only for columns that exist in df."""
    existing = {k: v for k, v in rename_map.items() if k in df.columns}
    return df.rename(existing) if existing else df


class YFinanceAdapter(BaseAdapter):
    source_name = "yfinance"

    def adapt_price(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map yfinance history() output to PRICE_BAR_SCHEMA.

        Handles optional Repaired? column and PascalCase -> snake_case renaming.
        Loader has already injected the symbol column and reset the DatetimeIndex.
        """
        df = _rename_existing(raw, {
            "Date": "date", "Open": "open", "High": "high",
            "Low": "low", "Close": "close", "Volume": "volume",
            "Dividends": "dividends", "Stock Splits": "splits",
            "Adj Close": "adj_close",
        })
        if "Repaired?" in df.columns:
            df = df.rename({"Repaired?": "repaired"})
        else:
            df = df.with_columns(pl.lit(False).alias("repaired"))
        return (
            _add_fetched_at(df, PRICE_BAR_SCHEMA)
            .select(PRICE_BAR_SCHEMA.names())
            .cast(PRICE_BAR_SCHEMA)
        )

    def adapt_dividends(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_series('dividends') output to DIVIDENDS_SCHEMA."""
        return (
            raw.rename({"value": "amount"})
            .pipe(_add_fetched_at, DIVIDENDS_SCHEMA)
            .select(DIVIDENDS_SCHEMA.names())
            .cast(DIVIDENDS_SCHEMA)
        )

    def adapt_splits(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_series('splits') output to SPLITS_SCHEMA."""
        return (
            raw.rename({"value": "ratio"})
            .pipe(_add_fetched_at, SPLITS_SCHEMA)
            .select(SPLITS_SCHEMA.names())
            .cast(SPLITS_SCHEMA)
        )

    def adapt_fast_info(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_fast_info() output to FAST_INFO_SCHEMA."""
        return (
            _add_fetched_at(raw, FAST_INFO_SCHEMA)
            .select(FAST_INFO_SCHEMA.names())
            .cast(FAST_INFO_SCHEMA)
        )

    def adapt_company_info(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_company_info() output to COMPANY_INFO_SCHEMA."""
        return (
            _add_fetched_at(raw, COMPANY_INFO_SCHEMA)
            .select(COMPANY_INFO_SCHEMA.names())
            .cast(COMPANY_INFO_SCHEMA)
        )

    def adapt_income_stmt(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        """Map transposed income statement to INCOME_STMT_SCHEMA.

        freq parameter overrides the freq column if already in raw.
        """
        df = _rename_existing(raw, {
            "Total Revenue":    "total_revenue",
            "Gross Profit":     "gross_profit",
            "Operating Income": "operating_income",
            "Net Income":       "net_income",
            "EBITDA":           "ebitda",
            "Diluted EPS":      "diluted_eps",
        })
        df = df.with_columns(pl.lit(freq).alias("freq"))
        return (
            _add_fetched_at(df, INCOME_STMT_SCHEMA)
            .select(INCOME_STMT_SCHEMA.names())
            .cast(INCOME_STMT_SCHEMA)
        )

    def adapt_balance_sheet(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        """Map transposed balance sheet to BALANCE_SHEET_SCHEMA."""
        df = _rename_existing(raw, {
            "Total Assets":                              "total_assets",
            "Total Liabilities Net Minority Interest":   "total_liabilities",
            "Stockholders Equity":                       "stockholders_equity",
            "Total Debt":                                "total_debt",
            "Cash And Cash Equivalents":                 "cash_and_equivalents",
            "Net Debt":                                  "net_debt",
        })
        df = df.with_columns(pl.lit(freq).alias("freq"))
        return (
            _add_fetched_at(df, BALANCE_SHEET_SCHEMA)
            .select(BALANCE_SHEET_SCHEMA.names())
            .cast(BALANCE_SHEET_SCHEMA)
        )

    def adapt_cash_flow(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        """Map transposed cash flow statement to CASH_FLOW_SCHEMA."""
        df = _rename_existing(raw, {
            "Operating Cash Flow":  "operating_cash_flow",
            "Investing Cash Flow":  "investing_cash_flow",
            "Financing Cash Flow":  "financing_cash_flow",
            "Free Cash Flow":       "free_cash_flow",
            "Capital Expenditure":  "capital_expenditure",
        })
        df = df.with_columns(pl.lit(freq).alias("freq"))
        return (
            _add_fetched_at(df, CASH_FLOW_SCHEMA)
            .select(CASH_FLOW_SCHEMA.names())
            .cast(CASH_FLOW_SCHEMA)
        )

    def adapt_analyst_ratings(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map ticker.recommendations to ANALYST_RATING_SCHEMA."""
        df = _rename_existing(raw, {
            "Date": "date", "Firm": "firm",
            "To Grade": "to_grade", "From Grade": "from_grade", "Action": "action",
        })
        return (
            _add_fetched_at(df, ANALYST_RATING_SCHEMA)
            .select(ANALYST_RATING_SCHEMA.names())
            .cast(ANALYST_RATING_SCHEMA)
        )

    def adapt_price_targets(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_price_targets() output to PRICE_TARGET_SCHEMA."""
        return (
            _add_fetched_at(raw, PRICE_TARGET_SCHEMA)
            .select(PRICE_TARGET_SCHEMA.names())
            .cast(PRICE_TARGET_SCHEMA)
        )

    def adapt_earnings_estimate(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map ticker.earnings_estimate to EARNINGS_ESTIMATE_SCHEMA."""
        df = _rename_existing(raw, {
            "avg": "avg_eps", "low": "low_eps", "high": "high_eps",
            "numberOfAnalysts": "num_analysts",
        })
        return (
            _add_fetched_at(df, EARNINGS_ESTIMATE_SCHEMA)
            .select(EARNINGS_ESTIMATE_SCHEMA.names())
            .cast(EARNINGS_ESTIMATE_SCHEMA)
        )

    def adapt_esg(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map ticker.sustainability to ESG_SCHEMA."""
        df = _rename_existing(raw, {"controversyLevel": "controversy_level"})
        return (
            _add_fetched_at(df, ESG_SCHEMA)
            .select(ESG_SCHEMA.names())
            .cast(ESG_SCHEMA)
        )

    def adapt_institutional_holders(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map ticker.institutional_holders to INSTITUTIONAL_HOLDER_SCHEMA."""
        df = _rename_existing(raw, {
            "Holder": "holder", "Shares": "shares",
            "Date Reported": "date_reported",
            "% Out": "pct_out", "Value": "value",
        })
        return (
            _add_fetched_at(df, INSTITUTIONAL_HOLDER_SCHEMA)
            .select(INSTITUTIONAL_HOLDER_SCHEMA.names())
            .cast(INSTITUTIONAL_HOLDER_SCHEMA)
        )

    def adapt_insider_transactions(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map ticker.insider_transactions to INSIDER_TRANSACTION_SCHEMA."""
        df = _rename_existing(raw, {
            "Insider": "insider", "Shares": "shares",
            "Value": "value", "Transaction": "transaction",
            "Start Date": "date",
        })
        return (
            _add_fetched_at(df, INSIDER_TRANSACTION_SCHEMA)
            .select(INSIDER_TRANSACTION_SCHEMA.names())
            .cast(INSIDER_TRANSACTION_SCHEMA)
        )

    def adapt_fund_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_fund_overview() output to FUND_OVERVIEW_SCHEMA."""
        return (
            _add_fetched_at(raw, FUND_OVERVIEW_SCHEMA)
            .select(FUND_OVERVIEW_SCHEMA.names())
            .cast(FUND_OVERVIEW_SCHEMA)
        )

    def adapt_fund_holdings(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map ticker.funds_data.top_holdings to FUND_HOLDINGS_SCHEMA."""
        df = _rename_existing(raw, {
            "symbol_x": "holding_symbol",
            "holdingName": "holding_name",
            "holdingPercent": "pct",
        })
        return (
            _add_fetched_at(df, FUND_HOLDINGS_SCHEMA)
            .select(FUND_HOLDINGS_SCHEMA.names())
            .cast(FUND_HOLDINGS_SCHEMA)
        )

    def adapt_sector_weights(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map sector weightings dict to SECTOR_WEIGHTS_SCHEMA."""
        df = _rename_existing(raw, {"sectorKey": "sector", "sectorWeight": "weight"})
        return (
            _add_fetched_at(df, SECTOR_WEIGHTS_SCHEMA)
            .select(SECTOR_WEIGHTS_SCHEMA.names())
            .cast(SECTOR_WEIGHTS_SCHEMA)
        )

    def adapt_sector_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_sector() output to SECTOR_OVERVIEW_SCHEMA."""
        return (
            _add_fetched_at(raw, SECTOR_OVERVIEW_SCHEMA)
            .select(SECTOR_OVERVIEW_SCHEMA.names())
            .cast(SECTOR_OVERVIEW_SCHEMA)
        )

    def adapt_industry_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_industry() output to INDUSTRY_OVERVIEW_SCHEMA."""
        return (
            _add_fetched_at(raw, INDUSTRY_OVERVIEW_SCHEMA)
            .select(INDUSTRY_OVERVIEW_SCHEMA.names())
            .cast(INDUSTRY_OVERVIEW_SCHEMA)
        )

    def adapt_earnings_calendar(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_calendar() output to EARNINGS_CALENDAR_SCHEMA."""
        return (
            _add_fetched_at(raw, EARNINGS_CALENDAR_SCHEMA)
            .select(EARNINGS_CALENDAR_SCHEMA.names())
            .cast(EARNINGS_CALENDAR_SCHEMA)
        )

    def adapt_news(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_news() output to NEWS_ITEM_SCHEMA."""
        return (
            _add_fetched_at(raw, NEWS_ITEM_SCHEMA)
            .select(NEWS_ITEM_SCHEMA.names())
            .cast(NEWS_ITEM_SCHEMA)
        )

    def adapt_screen_results(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map _fetch_screen() output to SCREEN_RESULT_SCHEMA."""
        df = _rename_existing(raw, {
            "shortName":     "short_name",
            "dividendYield": "dividend_yield",
            "trailingPE":    "trailing_pe",
            "marketCap":     "market_cap",
        })
        return (
            _add_fetched_at(df, SCREEN_RESULT_SCHEMA)
            .select(SCREEN_RESULT_SCHEMA.names())
            .cast(SCREEN_RESULT_SCHEMA)
        )
