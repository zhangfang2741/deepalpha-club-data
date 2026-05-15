"""Price data cleaner implementation"""
import polars as pl

from deepalpha.base.processor import BaseProcessor
from deepalpha.processors.price_cleaner.schemas import get_cleaned_price_schema


class PriceCleaner(BaseProcessor):
    """Price data cleaner for L2 processing.

    Applies cleaning rules:
    - Deduplication: same symbol+date, keep latest
    - Anomaly detection: price change > 50%
    - Volume filter: remove zero-volume non-trading days
    """

    name = "price_cleaner"
    version = "1.0.0"

    def __init__(
        self,
        anomaly_threshold: float = 0.5,
        market: str = "US",
    ):
        """Initialize price cleaner.

        Args:
            anomaly_threshold: Price change threshold for anomaly detection (default 50%)
            market: Market identifier for partitioning
        """
        self.anomaly_threshold = anomaly_threshold
        self.market = market

    def process(self, df: pl.DataFrame, **kwargs) -> pl.DataFrame:
        """Clean price data.

        Args:
            df: Input DataFrame with raw price data
            **kwargs: Additional processing parameters

        Returns:
            polars.DataFrame: Cleaned price data
        """
        if df.is_empty():
            return pl.DataFrame(schema=get_cleaned_price_schema())

        # Ensure date column is Date type
        if "date" in df.columns and df["date"].dtype != pl.Date:
            df = df.with_columns(
                pl.col("date").str.to_date().alias("date")
            )

        # Step 1: Deduplication - keep latest record per symbol+date
        df = self._deduplicate(df)

        # Step 2: Anomaly detection
        df = self._detect_anomalies(df)

        # Step 3: Volume filter
        df = self._filter_volume(df)

        # Add market column
        df = df.with_columns(pl.lit(self.market).alias("market"))

        return df

    def _deduplicate(self, df: pl.DataFrame) -> pl.DataFrame:
        """Remove duplicate records, keep latest per symbol+date"""
        if df.is_empty():
            return df
        return df.sort("date", descending=True).unique(
            subset=["symbol", "date"],
            keep="first",
        )

    def _detect_anomalies(self, df: pl.DataFrame) -> pl.DataFrame:
        """Mark records with price change > threshold as anomaly"""
        if df.is_empty():
            return df

        df = df.sort(["symbol", "date"])

        df = df.with_columns([
            pl.col("close").diff().over("symbol").alias("price_change"),
        ])

        df = df.with_columns([
            (
                (pl.col("price_change").abs() / pl.col("close").shift(1).over("symbol"))
                > self.anomaly_threshold
            ).alias("is_anomaly")
        ])

        # Clean up intermediate column and nulls from diff/shift
        df = df.drop("price_change")
        df = df.with_columns(pl.col("is_anomaly").fill_null(False))

        return df

    def _filter_volume(self, df: pl.DataFrame) -> pl.DataFrame:
        """Remove zero-volume records for non-trading days"""
        if df.is_empty():
            return df
        # Keep records where volume > 0 OR is_anomaly is True
        return df.filter(
            (pl.col("volume") > 0) | pl.col("is_anomaly")
        )