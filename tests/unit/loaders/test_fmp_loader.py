# tests/unit/loaders/test_fmp_loader.py
import pytest
from datetime import date
import polars as pl
from deepalpha.loaders.fmp_loader.fmp_config import FMPConfig
from deepalpha.loaders.fmp_loader.fmp_loader import FMPLoader


class TestFMPConfig:
    def test_default_config(self):
        """Default configuration has expected values."""
        config = FMPConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.rate_limit == 0.5
        assert "financialmodelingprep.com" in config.base_url

    def test_custom_config(self):
        """Custom values are stored correctly."""
        config = FMPConfig(api_key="k", rate_limit=1.0, base_url="http://localhost")
        assert config.rate_limit == 1.0
        assert config.base_url == "http://localhost"


class TestFMPLoader:
    def test_name(self):
        """Loader name is fmp_loader."""
        loader = FMPLoader(FMPConfig(api_key="k"))
        assert loader.name == "fmp_loader"

    def test_validate_empty(self):
        """Empty DataFrame fails validation."""
        loader = FMPLoader(FMPConfig(api_key="k"))
        assert loader.validate(pl.DataFrame()) is False

    def test_validate_missing_required_cols(self):
        """DataFrame without required columns fails validation."""
        loader = FMPLoader(FMPConfig(api_key="k"))
        assert loader.validate(pl.DataFrame({"x": [1]})) is False

    def test_validate_valid(self):
        """DataFrame with date, symbol, close passes validation."""
        loader = FMPLoader(FMPConfig(api_key="k"))
        df = pl.DataFrame({"date": [date(2024, 1, 1)], "symbol": ["AAPL"], "close": [150.0]})
        assert loader.validate(df) is True

    def test_fetch_unknown_type_raises(self):
        """Unknown data_type raises ValueError."""
        loader = FMPLoader(FMPConfig(api_key="k"))
        with pytest.raises(ValueError, match="Unknown data_type"):
            loader.fetch(data_type="unknown")
