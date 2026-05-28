# src/deepalpha/models/company_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

FAST_INFO_SCHEMA = pl.Schema({
    "symbol":              pl.String,
    "last_price":          pl.Float64,
    "market_cap":          pl.Float64,
    "currency":            pl.String,
    "exchange":            pl.String,
    "quote_type":          pl.String,
    "fifty_day_avg":       pl.Float64,
    "two_hundred_day_avg": pl.Float64,
    "year_high":           pl.Float64,
    "year_low":            pl.Float64,
    "fetched_at":          _UTC,
})

COMPANY_INFO_SCHEMA = pl.Schema({
    "symbol":           pl.String,
    "short_name":       pl.String,
    "sector":           pl.String,
    "industry":         pl.String,
    "country":          pl.String,
    "employees":        pl.Int64,
    "trailing_pe":      pl.Float64,
    "forward_pe":       pl.Float64,
    "price_to_book":    pl.Float64,
    "beta":             pl.Float64,
    "dividend_yield":   pl.Float64,
    "market_cap":       pl.Float64,
    "business_summary": pl.String,
    "fetched_at":       _UTC,
})
