# src/deepalpha/adapters/fmp_adapter.py
"""Adapter for transforming raw FMP API responses to canonical schemas."""
from datetime import datetime, timezone

import polars as pl

from deepalpha.adapters.base_adapter import BaseAdapter
from deepalpha.models.price_model import PRICE_BAR_SCHEMA


class FMPAdapter(BaseAdapter):
    source_name = "fmp"

    def adapt_price(self, raw: pl.DataFrame) -> pl.DataFrame:
        """Map raw FMP price columns to PRICE_BAR_SCHEMA.

        FMP-specific columns (unadjustedClose, change, changePercent) are dropped.
        Missing canonical columns (dividends, splits, repaired) are filled with defaults.
        """
        now = datetime.now(timezone.utc)
        return (
            raw
            .rename({"adjClose": "adj_close"})
            .with_columns([
                pl.lit(0.0).alias("dividends"),
                pl.lit(0.0).alias("splits"),
                pl.lit(False).alias("repaired"),
                pl.lit(now).cast(PRICE_BAR_SCHEMA["fetched_at"]).alias("fetched_at"),
            ])
            .select(PRICE_BAR_SCHEMA.names())
            .cast(PRICE_BAR_SCHEMA)
        )
