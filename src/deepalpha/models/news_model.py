# src/deepalpha/models/news_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

NEWS_ITEM_SCHEMA = pl.Schema({
    "symbol":       pl.String,
    "title":        pl.String,
    "publisher":    pl.String,
    "url":          pl.String,
    "published_at": _UTC,
    "tab":          pl.String,
    "fetched_at":   _UTC,
})
