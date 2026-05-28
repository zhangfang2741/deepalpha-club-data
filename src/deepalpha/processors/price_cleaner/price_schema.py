# src/deepalpha/processors/price_cleaner/price_schema.py
"""Schema for cleaned price data — extends PRICE_BAR_SCHEMA with audit columns."""
import polars as pl
from deepalpha.models.price_model import PRICE_BAR_SCHEMA

CLEANED_PRICE_SCHEMA = pl.Schema({
    **dict(PRICE_BAR_SCHEMA),
    "is_anomaly": pl.Boolean,
    "market":     pl.String,
})
