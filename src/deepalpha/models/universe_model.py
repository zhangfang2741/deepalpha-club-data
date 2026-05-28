# src/deepalpha/models/universe_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

SCREEN_RESULT_SCHEMA = pl.Schema({
    "symbol":         pl.String,
    "short_name":     pl.String,
    "exchange":       pl.String,
    "market_cap":     pl.Float64,
    "trailing_pe":    pl.Float64,
    "dividend_yield": pl.Float64,
    "fetched_at":     _UTC,
})
