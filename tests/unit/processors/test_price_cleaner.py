# tests/unit/processors/test_price_cleaner.py
import polars as pl
from datetime import date, datetime, timezone
import pytest
from deepalpha.processors.price_cleaner.price_cleaner import PriceCleaner
from deepalpha.processors.price_cleaner.price_schema import CLEANED_PRICE_SCHEMA
from deepalpha.models.price_model import PRICE_BAR_SCHEMA


def _make_canonical_row(symbol="AAPL", date_val=date(2024, 1, 1),
                        close=185.0, volume=1000, adj_close=185.0) -> dict:
    return {
        "symbol": symbol, "date": date_val, "open": close - 1,
        "high": close + 2, "low": close - 2, "close": close,
        "volume": volume, "adj_close": adj_close,
        "dividends": 0.0, "splits": 0.0, "repaired": False,
        "fetched_at": datetime.now(timezone.utc),
    }


def _make_canonical_df(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows).cast(PRICE_BAR_SCHEMA)


class TestPriceCleaner:
    def test_name(self):
        """PriceCleaner name is 'price_cleaner'."""
        assert PriceCleaner().name == "price_cleaner"

    def test_output_schema_matches_cleaned_price_schema(self):
        """process() output schema must equal CLEANED_PRICE_SCHEMA."""
        cleaner = PriceCleaner()
        df = _make_canonical_df([_make_canonical_row()])
        result = cleaner.process(df)
        assert result.schema == CLEANED_PRICE_SCHEMA

    def test_empty_input_returns_empty_with_correct_schema(self):
        """Empty PRICE_BAR_SCHEMA input yields empty CLEANED_PRICE_SCHEMA output."""
        cleaner = PriceCleaner()
        result = cleaner.process(pl.DataFrame(schema=PRICE_BAR_SCHEMA))
        assert result.is_empty()
        assert result.schema == CLEANED_PRICE_SCHEMA

    def test_deduplicate_keeps_first_per_symbol_date(self):
        """Duplicate symbol+date rows are deduplicated to one."""
        cleaner = PriceCleaner()
        rows = [
            _make_canonical_row(close=185.0),
            _make_canonical_row(close=186.0),  # duplicate date
            _make_canonical_row(date_val=date(2024, 1, 2), close=187.0),
        ]
        result = cleaner.process(_make_canonical_df(rows))
        assert result.shape[0] == 2

    def test_anomaly_detection_marks_large_change(self):
        """Price change > threshold is marked is_anomaly=True."""
        cleaner = PriceCleaner(anomaly_threshold=0.5)
        rows = [
            _make_canonical_row(date_val=date(2024, 1, 1), close=100.0),
            _make_canonical_row(date_val=date(2024, 1, 2), close=180.0),  # +80%
            _make_canonical_row(date_val=date(2024, 1, 3), close=182.0),
        ]
        result = cleaner.process(_make_canonical_df(rows))
        assert result.filter(pl.col("is_anomaly")).shape[0] == 1

    def test_volume_filter_removes_zero_volume_non_anomaly(self):
        """Zero-volume non-anomaly rows are removed."""
        cleaner = PriceCleaner()
        rows = [
            _make_canonical_row(date_val=date(2024, 1, 1), volume=1000),
            _make_canonical_row(date_val=date(2024, 1, 2), volume=0),
            _make_canonical_row(date_val=date(2024, 1, 3), volume=1500),
        ]
        result = cleaner.process(_make_canonical_df(rows))
        dates = [str(d) for d in result["date"].to_list()]
        assert "2024-01-02" not in dates

    def test_market_column_added(self):
        """market column is added with configured market value."""
        cleaner = PriceCleaner(market="HK")
        result = cleaner.process(_make_canonical_df([_make_canonical_row()]))
        assert result["market"][0] == "HK"

    def test_default_market_is_us(self):
        """Default market is 'US'."""
        result = PriceCleaner().process(_make_canonical_df([_make_canonical_row()]))
        assert result["market"][0] == "US"
