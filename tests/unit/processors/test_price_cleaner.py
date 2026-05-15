"""Tests for price cleaner plugin"""
import polars as pl
from datetime import date
from deepalpha.processors.price_cleaner import PriceCleaner


class TestPriceCleaner:
    """Test PriceCleaner processor"""

    def test_init(self):
        """Cleaner initialization"""
        cleaner = PriceCleaner(anomaly_threshold=0.5, market="US")
        assert cleaner.name == "price_cleaner"
        assert cleaner.anomaly_threshold == 0.5
        assert cleaner.market == "US"

    def test_default_init(self):
        """Default configuration"""
        cleaner = PriceCleaner()
        assert cleaner.anomaly_threshold == 0.5
        assert cleaner.market == "US"

    def test_deduplicate(self):
        """Remove duplicate symbol+date records"""
        cleaner = PriceCleaner()
        df = pl.DataFrame({
            "date": ["2024-01-01", "2024-01-01", "2024-01-02"],
            "symbol": ["AAPL", "AAPL", "AAPL"],
            "close": [185.0, 186.0, 187.0],
            "volume": [1000, 2000, 1500],
        }).with_columns(pl.col("date").str.to_date())

        result = cleaner.process(df)
        assert result.shape[0] == 2  # Two unique dates

    def test_anomaly_detection(self):
        """Mark price changes > 50% as anomaly"""
        cleaner = PriceCleaner(anomaly_threshold=0.5)
        df = pl.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "symbol": ["AAPL", "AAPL", "AAPL"],
            "close": [100.0, 180.0, 185.0],  # 80% change on Jan 2
            "volume": [1000, 1000, 1000],
        }).with_columns(pl.col("date").str.to_date())

        result = cleaner.process(df)
        anomalies = result.filter(pl.col("is_anomaly"))
        assert anomalies.shape[0] == 1

    def test_empty_input(self):
        """Handle empty DataFrame"""
        cleaner = PriceCleaner()
        result = cleaner.process(pl.DataFrame())
        assert result.is_empty()
        assert "is_anomaly" in result.columns
        assert "market" in result.columns

    def test_validate_output(self):
        """Test output validation"""
        cleaner = PriceCleaner()
        df = pl.DataFrame({
            "date": [date(2024, 1, 1)],
            "symbol": ["AAPL"],
            "close": [185.0],
            "volume": [1000],
        })
        result = cleaner.process(df)
        assert cleaner.validate_output(result) is True

    def test_volume_filter(self):
        """Keep zero volume only for anomaly records"""
        cleaner = PriceCleaner()
        df = pl.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "symbol": ["AAPL", "AAPL", "AAPL"],
            "close": [185.0, 186.0, 187.0],
            "volume": [1000, 0, 1500],  # Jan 2 has zero volume
        }).with_columns(pl.col("date").str.to_date())

        result = cleaner.process(df)
        # Jan 2 should be filtered out (zero volume, not anomaly)
        assert "2024-01-02" not in result["date"].to_list()