# tests/unit/loaders/test_yfinance_loader.py
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
import pandas as pd
import polars as pl

from deepalpha.loaders.yfinance_loader.yfinance_config import YFinanceConfig
from deepalpha.loaders.yfinance_loader.yfinance_loader import YFinanceLoader


class TestYFinanceConfig:
    def test_defaults(self):
        """Default config values."""
        config = YFinanceConfig()
        assert config.rate_limit == 0.5
        assert config.retries == 3
        assert config.proxy is None
        assert config.repair is True
        assert config.tz_cache_path == "/tmp/yf_tz_cache"

    def test_custom_values(self):
        """Custom config values are stored."""
        config = YFinanceConfig(rate_limit=1.0, retries=5, proxy="http://proxy:8080")
        assert config.rate_limit == 1.0
        assert config.retries == 5
        assert config.proxy == "http://proxy:8080"


class TestYFinanceLoaderInit:
    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_sets_yf_retries_on_init(self, mock_yf):
        """Loader sets yf.config.network.retries from config."""
        config = YFinanceConfig(retries=5)
        YFinanceLoader(config)
        assert mock_yf.config.network.retries == 5

    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_sets_proxy_when_provided(self, mock_yf):
        """Loader sets yf.config.network.proxy when proxy is configured."""
        config = YFinanceConfig(proxy="http://proxy:8080")
        YFinanceLoader(config)
        assert mock_yf.config.network.proxy == "http://proxy:8080"

    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_sets_tz_cache(self, mock_yf):
        """Loader calls yf.set_tz_cache_location with configured path."""
        config = YFinanceConfig(tz_cache_path="/tmp/test_cache")
        YFinanceLoader(config)
        mock_yf.set_tz_cache_location.assert_called_once_with("/tmp/test_cache")

    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_disables_hide_exceptions(self, mock_yf):
        """Loader disables hide_exceptions so errors surface."""
        config = YFinanceConfig()
        YFinanceLoader(config)
        assert mock_yf.config.debug.hide_exceptions is False


class TestYFinanceLoaderPriceSingle:
    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_single_symbol_injects_symbol_column(self, mock_yf):
        """Single-symbol price fetch injects 'symbol' into returned df."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame({
            "Open": [150.0], "High": [155.0], "Low": [149.0],
            "Close": [153.0], "Adj Close": [153.0], "Volume": [1_000_000],
            "Dividends": [0.0], "Stock Splits": [0.0],
        }, index=pd.DatetimeIndex([pd.Timestamp("2024-01-02")], name="Date"))
        mock_yf.Ticker.return_value = mock_ticker

        config = YFinanceConfig(rate_limit=0)
        loader = YFinanceLoader(config)
        df = loader.fetch(data_type="price", symbols=["AAPL"],
                          start_date=date(2024, 1, 1), end_date=date(2024, 1, 3))

        assert "symbol" in df.columns
        assert df["symbol"][0] == "AAPL"

    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_unknown_data_type_raises(self, mock_yf):
        """Unknown data_type raises ValueError."""
        loader = YFinanceLoader(YFinanceConfig())
        with pytest.raises(ValueError, match="Unknown data_type"):
            loader.fetch(data_type="unknown", symbols=["AAPL"])

    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_validate_non_empty(self, mock_yf):
        """Non-empty df passes validation."""
        loader = YFinanceLoader(YFinanceConfig())
        assert loader.validate(pl.DataFrame({"a": [1]})) is True

    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_validate_empty(self, mock_yf):
        """Empty df fails validation."""
        loader = YFinanceLoader(YFinanceConfig())
        assert loader.validate(pl.DataFrame()) is False
