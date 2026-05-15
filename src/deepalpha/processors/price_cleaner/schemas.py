"""Price cleaner schemas"""
import polars as pl


def get_cleaned_price_schema() -> pl.Schema:
    """Schema for cleaned price data"""
    return pl.Schema({
        "date": pl.Date,
        "symbol": pl.String,
        "open": pl.Float64,
        "high": pl.Float64,
        "low": pl.Float64,
        "close": pl.Float64,
        "volume": pl.Int64,
        "adj_close": pl.Float64,
        "change_percent": pl.Float64,
        "is_anomaly": pl.Boolean,
        "market": pl.String,
    })