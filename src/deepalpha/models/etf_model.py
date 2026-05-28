# src/deepalpha/models/etf_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

FUND_OVERVIEW_SCHEMA = pl.Schema({
    "symbol":              pl.String,
    "fund_family":         pl.String,
    "legal_type":          pl.String,
    "category":            pl.String,
    "morning_star_rating": pl.Int32,
    "net_assets":          pl.Float64,
    "expense_ratio":       pl.Float64,
    "turnover":            pl.Float64,
    "fetched_at":          _UTC,
})

FUND_HOLDINGS_SCHEMA = pl.Schema({
    "symbol":         pl.String,
    "holding_symbol": pl.String,
    "holding_name":   pl.String,
    "pct":            pl.Float64,
    "fetched_at":     _UTC,
})

SECTOR_WEIGHTS_SCHEMA = pl.Schema({
    "symbol":     pl.String,
    "sector":     pl.String,
    "weight":     pl.Float64,
    "fetched_at": _UTC,
})
