# tests/unit/adapters/test_fmp_adapter.py
import pytest
import polars as pl
from deepalpha.adapters.base_adapter import BaseAdapter


class TestBaseAdapter:
    def test_unimplemented_adapt_price_raises(self):
        """adapt_price raises NotImplementedError when not overridden."""
        adapter = BaseAdapter()
        with pytest.raises(NotImplementedError):
            adapter.adapt_price(pl.DataFrame())

    def test_unimplemented_adapt_company_info_raises(self):
        """adapt_company_info raises NotImplementedError when not overridden."""
        adapter = BaseAdapter()
        with pytest.raises(NotImplementedError):
            adapter.adapt_company_info(pl.DataFrame())

    def test_can_instantiate_without_source_name(self):
        """BaseAdapter is a plain class, not ABC — can be instantiated."""
        adapter = BaseAdapter()
        assert adapter is not None


from datetime import date
from deepalpha.adapters.fmp_adapter import FMPAdapter
from deepalpha.models.price_model import PRICE_BAR_SCHEMA


class TestFMPAdapter:
    def _make_raw_price(self):
        """Simulate raw FMP API response (with FMP field names)."""
        return pl.DataFrame({
            "date":             [date(2024, 1, 2)],
            "symbol":           ["AAPL"],
            "open":             [185.0],
            "high":             [188.0],
            "low":              [184.0],
            "close":            [187.0],
            "volume":           [1_000_000],
            "adjClose":         [187.0],
            "unadjustedClose":  [187.5],
            "change":           [2.0],
            "changePercent":    [1.08],
        })

    def test_adapt_price_schema_matches_canonical(self):
        """Output schema must exactly match PRICE_BAR_SCHEMA."""
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert result.schema == PRICE_BAR_SCHEMA

    def test_adapt_price_drops_fmp_only_columns(self):
        """FMP-specific columns (unadjustedClose, change, changePercent) are dropped."""
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert "unadjustedClose" not in result.columns
        assert "change" not in result.columns
        assert "changePercent" not in result.columns

    def test_adapt_price_fills_dividends_and_splits_with_zero(self):
        """dividends and splits default to 0.0 for FMP price data."""
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert result["dividends"][0] == 0.0
        assert result["splits"][0] == 0.0

    def test_adapt_price_sets_repaired_false(self):
        """FMP has no repair concept; repaired is always False."""
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert result["repaired"][0] is False

    def test_adapt_price_fetched_at_is_utc_aware(self):
        """fetched_at is timezone-aware UTC."""
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert result["fetched_at"].dtype == PRICE_BAR_SCHEMA["fetched_at"]

    def test_adapt_price_preserves_ohlcv(self):
        """OHLCV values and adj_close are correctly mapped."""
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert result["close"][0] == 187.0
        assert result["volume"][0] == 1_000_000
        assert result["adj_close"][0] == 187.0

    def test_source_name(self):
        """FMPAdapter identifies itself as 'fmp'."""
        assert FMPAdapter.source_name == "fmp"
