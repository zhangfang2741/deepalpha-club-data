# src/deepalpha/models/holdings_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

INSTITUTIONAL_HOLDER_SCHEMA = pl.Schema({
    "symbol":        pl.String,
    "holder":        pl.String,
    "shares":        pl.Int64,
    "date_reported": pl.Date,
    "pct_out":       pl.Float64,
    "value":         pl.Float64,
    "fetched_at":    _UTC,
})

INSIDER_TRANSACTION_SCHEMA = pl.Schema({
    "symbol":      pl.String,
    "insider":     pl.String,
    "shares":      pl.Int64,
    "value":       pl.Float64,
    "transaction": pl.String,
    "date":        pl.Date,
    "fetched_at":  _UTC,
})
