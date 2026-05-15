"""Tests for FMP loader plugin"""
import pytest
from datetime import date
import polars as pl
from deepalpha.sources.fmp_loader import FMPLoader
from deepalpha.sources.fmp_loader.config import FMPConfig


class TestFMPConfig:
    """Test FMP configuration"""

    def test_default_config(self):
        """Default configuration values"""
        config = FMPConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.rate_limit == 0.5
        assert "financialmodelingprep.com" in config.base_url


class TestFMPLoader:
    """Test FMP loader plugin"""

    def test_init(self):
        """Loader initialization"""
        config = FMPConfig(api_key="test-key")
        loader = FMPLoader(config)
        assert loader.name == "fmp_loader"
        assert loader.config.api_key == "test-key"

    def test_validate_empty_dataframe(self):
        """Reject empty DataFrame"""
        config = FMPConfig(api_key="test-key")
        loader = FMPLoader(config)
        df = loader.validate(pl.DataFrame())
        assert df is False

    def test_validate_missing_columns(self):
        """Reject DataFrame missing required columns"""
        config = FMPConfig(api_key="test-key")
        loader = FMPLoader(config)
        df = pl.DataFrame({"a": [1, 2, 3]})
        result = loader.validate(df)
        assert result is False

    def test_validate_valid_dataframe(self):
        """Accept valid DataFrame"""
        config = FMPConfig(api_key="test-key")
        loader = FMPLoader(config)
        df = pl.DataFrame({
            "date": [date(2024, 1, 1)],
            "symbol": ["AAPL"],
            "close": [185.0],
        })
        result = loader.validate(df)
        assert result is True

    def test_fetch_unknown_data_type(self):
        """Raise error for unknown data type"""
        config = FMPConfig(api_key="test-key")
        loader = FMPLoader(config)
        with pytest.raises(ValueError, match="Unknown data_type"):
            loader.fetch(data_type="unknown")