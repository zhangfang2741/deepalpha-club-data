# src/deepalpha/adapters/base_adapter.py
"""Base adapter class for transforming raw source DataFrames to canonical schemas."""
import polars as pl


class BaseAdapter:
    """Transforms raw source DataFrame into canonical model schema.

    Each source implements one adapter. Only implement the methods supported
    by your source; unimplemented methods raise NotImplementedError at call time.
    Do NOT inherit from ABC — partial implementation is intentional.
    """

    def adapt_price(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_dividends(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_splits(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_fast_info(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_company_info(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_income_stmt(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_balance_sheet(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_cash_flow(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_analyst_ratings(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_price_targets(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_earnings_estimate(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_esg(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_institutional_holders(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_insider_transactions(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_fund_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_fund_holdings(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_sector_weights(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_sector_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_industry_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_earnings_calendar(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_news(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_screen_results(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError
