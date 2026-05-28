# src/deepalpha/models/financials_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

INCOME_STMT_SCHEMA = pl.Schema({
    "symbol":           pl.String,
    "period_end":       pl.Date,
    "freq":             pl.String,
    "total_revenue":    pl.Float64,
    "gross_profit":     pl.Float64,
    "operating_income": pl.Float64,
    "net_income":       pl.Float64,
    "ebitda":           pl.Float64,
    "diluted_eps":      pl.Float64,
    "fetched_at":       _UTC,
})

BALANCE_SHEET_SCHEMA = pl.Schema({
    "symbol":               pl.String,
    "period_end":           pl.Date,
    "freq":                 pl.String,
    "total_assets":         pl.Float64,
    "total_liabilities":    pl.Float64,
    "stockholders_equity":  pl.Float64,
    "total_debt":           pl.Float64,
    "cash_and_equivalents": pl.Float64,
    "net_debt":             pl.Float64,
    "fetched_at":           _UTC,
})

CASH_FLOW_SCHEMA = pl.Schema({
    "symbol":              pl.String,
    "period_end":          pl.Date,
    "freq":                pl.String,
    "operating_cash_flow": pl.Float64,
    "investing_cash_flow": pl.Float64,
    "financing_cash_flow": pl.Float64,
    "free_cash_flow":      pl.Float64,
    "capital_expenditure": pl.Float64,
    "fetched_at":          _UTC,
})
