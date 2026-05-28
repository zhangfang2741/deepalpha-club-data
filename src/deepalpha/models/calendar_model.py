# src/deepalpha/models/calendar_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

EARNINGS_CALENDAR_SCHEMA = pl.Schema({
    "symbol":               pl.String,
    "earnings_date":        pl.Date,
    "eps_estimate_avg":     pl.Float64,
    "eps_estimate_low":     pl.Float64,
    "eps_estimate_high":    pl.Float64,
    "revenue_estimate_avg": pl.Float64,
    "fetched_at":           _UTC,
})

MARKET_STATUS_SCHEMA = pl.Schema({
    "market":     pl.String,
    "status":     pl.String,
    "timezone":   pl.String,
    "fetched_at": _UTC,
})
