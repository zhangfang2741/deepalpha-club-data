# src/deepalpha/models/sector_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

SECTOR_OVERVIEW_SCHEMA = pl.Schema({
    "key":        pl.String,
    "name":       pl.String,
    "etf_symbol": pl.String,
    "market_cap": pl.Float64,
    "ytd_return": pl.Float64,
    "fetched_at": _UTC,
})

INDUSTRY_OVERVIEW_SCHEMA = pl.Schema({
    "key":        pl.String,
    "name":       pl.String,
    "sector_key": pl.String,
    "fetched_at": _UTC,
})
