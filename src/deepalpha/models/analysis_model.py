# src/deepalpha/models/analysis_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

ANALYST_RATING_SCHEMA = pl.Schema({
    "symbol":     pl.String,
    "date":       pl.Date,
    "firm":       pl.String,
    "to_grade":   pl.String,
    "from_grade": pl.String,
    "action":     pl.String,
    "fetched_at": _UTC,
})

PRICE_TARGET_SCHEMA = pl.Schema({
    "symbol":       pl.String,
    "current":      pl.Float64,
    "mean":         pl.Float64,
    "high":         pl.Float64,
    "low":          pl.Float64,
    "num_analysts": pl.Int32,
    "fetched_at":   _UTC,
})

EARNINGS_ESTIMATE_SCHEMA = pl.Schema({
    "symbol":       pl.String,
    "period":       pl.String,
    "avg_eps":      pl.Float64,
    "low_eps":      pl.Float64,
    "high_eps":     pl.Float64,
    "avg_revenue":  pl.Float64,
    "growth":       pl.Float64,
    "num_analysts": pl.Int32,
    "fetched_at":   _UTC,
})

ESG_SCHEMA = pl.Schema({
    "symbol":            pl.String,
    "total_esg":         pl.Float64,
    "environment":       pl.Float64,
    "social":            pl.Float64,
    "governance":        pl.Float64,
    "controversy_level": pl.String,
    "fetched_at":        _UTC,
})
