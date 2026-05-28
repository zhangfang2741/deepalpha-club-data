# src/deepalpha/models/price_model.py
import polars as pl

_UTC = pl.Datetime("us", time_zone="UTC")

PRICE_BAR_SCHEMA = pl.Schema({
    "symbol":     pl.String,
    "date":       pl.Date,
    "open":       pl.Float64,
    "high":       pl.Float64,
    "low":        pl.Float64,
    "close":      pl.Float64,
    "volume":     pl.Int64,
    "adj_close":  pl.Float64,
    "dividends":  pl.Float64,   # always 0.0 from FMP (separate endpoint); inline from yfinance
    "splits":     pl.Float64,   # always 0.0 from FMP (separate endpoint); inline from yfinance
    "repaired":   pl.Boolean,
    "fetched_at": _UTC,
})

DIVIDENDS_SCHEMA = pl.Schema({
    "symbol":     pl.String,
    "date":       pl.Date,
    "amount":     pl.Float64,
    "fetched_at": _UTC,
})

SPLITS_SCHEMA = pl.Schema({
    "symbol":     pl.String,
    "date":       pl.Date,
    "ratio":      pl.Float64,
    "fetched_at": _UTC,
})

TICK_SCHEMA = pl.Schema({
    "symbol":  pl.String,
    "price":   pl.Float64,
    "volume":  pl.Int64,
    "tick_at": _UTC,
})
