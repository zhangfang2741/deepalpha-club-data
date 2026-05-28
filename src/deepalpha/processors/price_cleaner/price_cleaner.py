# src/deepalpha/processors/price_cleaner/price_cleaner.py
"""Price data cleaner — deduplication, anomaly detection, volume filtering."""
import polars as pl

from deepalpha.base.base_processor import BaseProcessor
from deepalpha.models.price_model import PRICE_BAR_SCHEMA
from deepalpha.processors.price_cleaner.price_schema import CLEANED_PRICE_SCHEMA


class PriceCleaner(BaseProcessor):
    version = "1.0.0"

    @property
    def name(self) -> str:
        return "price_cleaner"

    def __init__(self, anomaly_threshold: float = 0.5, market: str = "US"):
        self.anomaly_threshold = anomaly_threshold
        self.market = market

    def process(self, df: pl.DataFrame, **kwargs) -> pl.DataFrame:
        """Clean canonical price data.

        Input must conform to PRICE_BAR_SCHEMA.
        Output conforms to CLEANED_PRICE_SCHEMA (PRICE_BAR_SCHEMA + is_anomaly + market).
        """
        if df.is_empty():
            return pl.DataFrame(schema=CLEANED_PRICE_SCHEMA)

        df = self._deduplicate(df)
        df = self._detect_anomalies(df)
        df = self._filter_volume(df)
        df = df.with_columns(pl.lit(self.market).alias("market"))
        return df.select(CLEANED_PRICE_SCHEMA.names()).cast(CLEANED_PRICE_SCHEMA)

    def _deduplicate(self, df: pl.DataFrame) -> pl.DataFrame:
        """Keep the first record per symbol+date after sorting descending."""
        return df.sort("date", descending=True).unique(subset=["symbol", "date"], keep="first")

    def _detect_anomalies(self, df: pl.DataFrame) -> pl.DataFrame:
        """Mark rows where |price_change / prev_close| > threshold as anomalies."""
        df = df.sort(["symbol", "date"])
        df = df.with_columns(pl.col("close").diff().over("symbol").alias("_price_change"))
        df = df.with_columns(
            (
                (pl.col("_price_change").abs() / pl.col("close").shift(1).over("symbol"))
                > self.anomaly_threshold
            ).fill_null(False).alias("is_anomaly")
        )
        return df.drop("_price_change")

    def _filter_volume(self, df: pl.DataFrame) -> pl.DataFrame:
        """Remove zero-volume rows that are not flagged as anomalies."""
        return df.filter((pl.col("volume") > 0) | pl.col("is_anomaly"))
