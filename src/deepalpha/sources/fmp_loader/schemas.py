"""FMP data schemas"""
import polars as pl


def get_price_schema() -> pl.Schema:
    """Schema for daily price data"""
    return pl.Schema({
        "date": pl.Date,
        "symbol": pl.String,
        "open": pl.Float64,
        "high": pl.Float64,
        "low": pl.Float64,
        "close": pl.Float64,
        "volume": pl.Int64,
        "adj_close": pl.Float64,
        "unadjusted_close": pl.Float64,
        "change": pl.Float64,
        "change_percent": pl.Float64,
    })


def get_financials_schema() -> pl.Schema:
    """Schema for financial statement data"""
    return pl.Schema({
        "symbol": pl.String,
        "date": pl.Date,
        "report_date": pl.Date,
        "announce_date": pl.Date,
        "revenue": pl.Float64,
        "net_income": pl.Float64,
        "eps": pl.Float64,
        "roe": pl.Float64,
        "roa": pl.Float64,
    })