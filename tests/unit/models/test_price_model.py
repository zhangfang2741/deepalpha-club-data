# tests/unit/models/test_price_model.py
import polars as pl
from datetime import date, timezone, datetime
from deepalpha.models.price_model import (
    PRICE_BAR_SCHEMA, DIVIDENDS_SCHEMA, SPLITS_SCHEMA, TICK_SCHEMA, _UTC,
)


class TestPriceModel:
    def test_price_bar_schema_fields(self):
        expected = {"symbol", "date", "open", "high", "low", "close",
                    "volume", "adj_close", "dividends", "splits", "repaired", "fetched_at"}
        assert set(PRICE_BAR_SCHEMA.names()) == expected

    def test_price_bar_schema_types(self):
        assert PRICE_BAR_SCHEMA["volume"] == pl.Int64
        assert PRICE_BAR_SCHEMA["repaired"] == pl.Boolean
        assert PRICE_BAR_SCHEMA["date"] == pl.Date
        assert PRICE_BAR_SCHEMA["close"] == pl.Float64

    def test_fetched_at_is_utc(self):
        assert PRICE_BAR_SCHEMA["fetched_at"] == _UTC
        assert _UTC == pl.Datetime("us", time_zone="UTC")

    def test_price_bar_schema_accepts_valid_df(self):
        now = datetime.now(timezone.utc)
        df = pl.DataFrame({
            "symbol": ["AAPL"], "date": [date(2024, 1, 1)],
            "open": [150.0], "high": [155.0], "low": [149.0], "close": [153.0],
            "volume": [1_000_000], "adj_close": [153.0],
            "dividends": [0.0], "splits": [0.0], "repaired": [False],
            "fetched_at": [now],
        }).cast(PRICE_BAR_SCHEMA)
        assert df.schema == PRICE_BAR_SCHEMA

    def test_dividends_schema_fields(self):
        assert set(DIVIDENDS_SCHEMA.names()) == {"symbol", "date", "amount", "fetched_at"}

    def test_splits_schema_fields(self):
        assert set(SPLITS_SCHEMA.names()) == {"symbol", "date", "ratio", "fetched_at"}

    def test_tick_schema_fields(self):
        assert set(TICK_SCHEMA.names()) == {"symbol", "price", "volume", "tick_at"}

    def test_tick_at_is_utc(self):
        assert TICK_SCHEMA["tick_at"] == _UTC


class TestModelsInit:
    def test_can_import_all_schemas_from_top_level(self):
        from deepalpha.models import (
            PRICE_BAR_SCHEMA, DIVIDENDS_SCHEMA, SPLITS_SCHEMA, TICK_SCHEMA,
            FAST_INFO_SCHEMA, COMPANY_INFO_SCHEMA,
            INCOME_STMT_SCHEMA, BALANCE_SHEET_SCHEMA, CASH_FLOW_SCHEMA,
            ANALYST_RATING_SCHEMA, PRICE_TARGET_SCHEMA, EARNINGS_ESTIMATE_SCHEMA, ESG_SCHEMA,
            INSTITUTIONAL_HOLDER_SCHEMA, INSIDER_TRANSACTION_SCHEMA,
            FUND_OVERVIEW_SCHEMA, FUND_HOLDINGS_SCHEMA, SECTOR_WEIGHTS_SCHEMA,
            SECTOR_OVERVIEW_SCHEMA, INDUSTRY_OVERVIEW_SCHEMA,
            EARNINGS_CALENDAR_SCHEMA, MARKET_STATUS_SCHEMA,
            NEWS_ITEM_SCHEMA, SCREEN_RESULT_SCHEMA,
        )
        assert PRICE_BAR_SCHEMA is not None
        assert SCREEN_RESULT_SCHEMA is not None
