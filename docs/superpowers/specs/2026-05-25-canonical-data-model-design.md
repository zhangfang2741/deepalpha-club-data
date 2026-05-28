# Canonical Data Model Design

**Date:** 2026-05-25  
**Status:** Approved

---

## Goal

Define a unified canonical data model for all fetchers in the deepalpha data pipeline. Every data source (FMP, yfinance, future sources) produces raw data; a per-source **adapter** transforms it into the canonical schema. Downstream processors, storage, and API all consume canonical-shaped `polars.DataFrame`s.

---

## Background

The project currently has:

- `FMPLoader` — fetches price data from Financial Modeling Prep API, returns raw `pl.DataFrame`
- `PriceCleaner` — processor that cleans price data
- `FMPLoader` currently does field renaming inside itself (should move to adapter)
- No yfinance loader exists yet (yfinance is already a dependency)
- No unified data model — each source defines its own schema independently

The reference design is inspired by the yfinance API structure (`docs/temp/yfinance_api_reference.md`), which organizes data into well-defined categories: price, company info, financial statements, analysis, holdings, ETF/funds, sector/industry, calendar, and news.

---

## Architecture

### Three-Layer Design

```text
┌─────────────────────────────────────────────────────┐
│                   Sources (fetchers)                 │
│  FMPLoader.fetch()  →  raw pl.DataFrame              │
│  YFinanceLoader.fetch() → raw pl.DataFrame           │
└────────────────────────┬────────────────────────────┘
                         │ raw_df
┌────────────────────────▼────────────────────────────┐
│                 Adapters (new layer)                 │
│  FMPAdapter.adapt_*(raw_df) → canonical_df           │
│  YFinanceAdapter.adapt_*(raw_df) → canonical_df      │
└────────────────────────┬────────────────────────────┘
                         │ canonical pl.DataFrame
┌────────────────────────▼────────────────────────────┐
│              Models (canonical schemas)              │
│  deepalpha/models/{price,financials,company,...}.py  │
│  Each module exports pl.Schema constants             │
└────────────────────────┬────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Parquet/DuckDB           Kafka topics
       (storage decided externally)
```

### Core Principles

1. **`BaseSource` is unchanged** — `fetch()` continues to return raw `pl.DataFrame`; sources do not know about canonical schemas.
2. **New `BaseAdapter` ABC** — defines `adapt_*(raw_df) -> pl.DataFrame` per data category; each source implements one adapter.
3. **`models/` is the single source of truth** — all `pl.Schema` constants live here; adapters, processors, and API all import from here.
4. **Models define schema only** — column names and types. Storage partitioning, Kafka topic mapping, and Parquet paths are decided outside the model layer.
5. **Adapter contract**: every `adapt_*` method ends with `.select(SCHEMA.names()).cast(SCHEMA)` to guarantee the output strictly matches the canonical schema.

---

## Directory Structure

```text
src/deepalpha/
├── models/                         ← NEW
│   ├── __init__.py                 # re-exports all schemas
│   ├── price_model.py              # PRICE_BAR_SCHEMA, DIVIDENDS_SCHEMA, SPLITS_SCHEMA, TICK_SCHEMA
│   ├── company_model.py            # FAST_INFO_SCHEMA, COMPANY_INFO_SCHEMA
│   ├── financials_model.py         # INCOME_STMT_SCHEMA, BALANCE_SHEET_SCHEMA, CASH_FLOW_SCHEMA
│   ├── analysis_model.py           # ANALYST_RATING_SCHEMA, PRICE_TARGET_SCHEMA, EARNINGS_ESTIMATE_SCHEMA, ESG_SCHEMA
│   ├── holdings_model.py           # INSTITUTIONAL_HOLDER_SCHEMA, INSIDER_TRANSACTION_SCHEMA
│   ├── etf_model.py                # FUND_OVERVIEW_SCHEMA, FUND_HOLDINGS_SCHEMA, SECTOR_WEIGHTS_SCHEMA
│   ├── sector_model.py             # SECTOR_OVERVIEW_SCHEMA, INDUSTRY_OVERVIEW_SCHEMA
│   ├── calendar_model.py           # EARNINGS_CALENDAR_SCHEMA, MARKET_STATUS_SCHEMA
│   ├── news_model.py               # NEWS_ITEM_SCHEMA
│   └── universe_model.py           # SCREEN_RESULT_SCHEMA
├── adapters/                       ← NEW
│   ├── __init__.py
│   ├── base_adapter.py             # BaseAdapter base class
│   ├── fmp_adapter.py              # FMPAdapter
│   └── yfinance_adapter.py         # YFinanceAdapter
├── loaders/                        ← NEW (replaces sources/)
│   ├── fmp_loader/
│   │   ├── __init__.py
│   │   ├── fmp_loader.py           # FMPLoader — returns raw df, no field mapping
│   │   └── fmp_config.py           # FMPConfig
│   └── yfinance_loader/            ← NEW
│       ├── __init__.py
│       ├── yfinance_loader.py      # YFinanceLoader
│       └── yfinance_config.py      # YFinanceConfig
├── base/
│   ├── base_source.py              # BaseSource ABC
│   └── base_processor.py           # BaseProcessor ABC
├── processors/
│   └── price_cleaner/
│       ├── price_cleaner.py        # PriceCleaner
│       └── price_schema.py         # CLEANED_PRICE_SCHEMA (extends PRICE_BAR_SCHEMA)
└── api/
    └── api_schemas.py              # Pydantic API schemas; field names reference models/
```

---

## Canonical Schemas

All schemas include `symbol: pl.String` and `fetched_at: pl.Datetime` as universal fields.

### `models/price_model.py`

```python
import polars as pl

_UTC = pl.Datetime("us", time_zone="UTC")

PRICE_BAR_SCHEMA = pl.Schema({
    "symbol":      pl.String,
    "date":        pl.Date,
    "open":        pl.Float64,
    "high":        pl.Float64,
    "low":         pl.Float64,
    "close":       pl.Float64,
    "volume":      pl.Int64,
    "adj_close":   pl.Float64,
    "dividends":   pl.Float64,   # always 0.0 from FMP (separate endpoint); inline from yfinance
    "splits":      pl.Float64,   # always 0.0 from FMP (separate endpoint); inline from yfinance
    "repaired":    pl.Boolean,
    "fetched_at":  _UTC,
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
```

**Design note on `repaired`:** FMP does not have a repair concept; adapter sets `False`. yfinance only includes `Repaired?` when `repair=True`; adapter handles the optional column.

**Design note on `adj_close`:** yfinance loader uses `auto_adjust=False` so both `Close` (unadjusted) and `Adj Close` are available, keeping parity with FMP's `close` / `adj_close` separation.

---

### `models/company_model.py`

```python
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
    "fetched_at":          pl.Datetime,
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
    "fetched_at":       pl.Datetime,
})
```

---

### `models/financials_model.py`

Financial statements use tidy format (one row per reporting period) rather than yfinance's wide format (rows = metrics). The `freq` column distinguishes `"annual"`, `"quarterly"`, and `"ttm"`.

```python
INCOME_STMT_SCHEMA = pl.Schema({
    "symbol":           pl.String,
    "period_end":       pl.Date,
    "freq":             pl.String,   # "annual" | "quarterly" | "ttm"
    "total_revenue":    pl.Float64,
    "gross_profit":     pl.Float64,
    "operating_income": pl.Float64,
    "net_income":       pl.Float64,
    "ebitda":           pl.Float64,
    "diluted_eps":      pl.Float64,
    "fetched_at":       pl.Datetime,
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
    "fetched_at":           pl.Datetime,
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
    "fetched_at":          pl.Datetime,
})
```

---

### `models/analysis_model.py`

```python
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
    "fetched_at":   pl.Datetime,
})

EARNINGS_ESTIMATE_SCHEMA = pl.Schema({
    "symbol":       pl.String,
    "period":       pl.String,   # "0q" | "1q" | "0y" | "1y"
    "avg_eps":      pl.Float64,
    "low_eps":      pl.Float64,
    "high_eps":     pl.Float64,
    "avg_revenue":  pl.Float64,
    "growth":       pl.Float64,
    "num_analysts": pl.Int32,
    "fetched_at":   pl.Datetime,
})

ESG_SCHEMA = pl.Schema({
    "symbol":            pl.String,
    "total_esg":         pl.Float64,
    "environment":       pl.Float64,
    "social":            pl.Float64,
    "governance":        pl.Float64,
    "controversy_level": pl.String,
    "fetched_at":        pl.Datetime,
})
```

---

### `models/holdings_model.py`

```python
INSTITUTIONAL_HOLDER_SCHEMA = pl.Schema({
    "symbol":        pl.String,
    "holder":        pl.String,
    "shares":        pl.Int64,
    "date_reported": pl.Date,
    "pct_out":       pl.Float64,
    "value":         pl.Float64,
    "fetched_at":    pl.Datetime,
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
```

---

### `models/etf_model.py`

```python
FUND_OVERVIEW_SCHEMA = pl.Schema({
    "symbol":              pl.String,
    "fund_family":         pl.String,
    "legal_type":          pl.String,
    "category":            pl.String,
    "morning_star_rating": pl.Int32,
    "net_assets":          pl.Float64,
    "expense_ratio":       pl.Float64,
    "turnover":            pl.Float64,
    "fetched_at":          pl.Datetime,
})

FUND_HOLDINGS_SCHEMA = pl.Schema({
    "symbol":         pl.String,
    "holding_symbol": pl.String,
    "holding_name":   pl.String,
    "pct":            pl.Float64,
    "fetched_at":     pl.Datetime,
})

SECTOR_WEIGHTS_SCHEMA = pl.Schema({
    "symbol":     pl.String,
    "sector":     pl.String,
    "weight":     pl.Float64,
    "fetched_at": _UTC,
})
```

---

### `models/sector_model.py`

```python
SECTOR_OVERVIEW_SCHEMA = pl.Schema({
    "key":        pl.String,
    "name":       pl.String,
    "etf_symbol": pl.String,
    "market_cap": pl.Float64,
    "ytd_return": pl.Float64,
    "fetched_at": _UTC,
})

INDUSTRY_OVERVIEW_SCHEMA = pl.Schema({
    "key":        pl.String,
    "name":       pl.String,
    "sector_key": pl.String,
    "fetched_at": _UTC,
})
```

---

### `models/calendar_model.py`

```python
EARNINGS_CALENDAR_SCHEMA = pl.Schema({
    "symbol":               pl.String,
    "earnings_date":        pl.Date,
    "eps_estimate_avg":     pl.Float64,
    "eps_estimate_low":     pl.Float64,
    "eps_estimate_high":    pl.Float64,
    "revenue_estimate_avg": pl.Float64,
    "fetched_at":           pl.Datetime,
})

MARKET_STATUS_SCHEMA = pl.Schema({
    "market":     pl.String,
    "status":     pl.String,   # "open" | "closed" | "pre" | "post"
    "timezone":   pl.String,
    "fetched_at": _UTC,
})
```

---

### `models/news_model.py`

```python
NEWS_ITEM_SCHEMA = pl.Schema({
    "symbol":       pl.String,
    "title":        pl.String,
    "publisher":    pl.String,
    "url":          pl.String,
    "published_at": pl.Datetime,
    "tab":          pl.String,   # "news" | "press releases"
    "fetched_at":   pl.Datetime,
})
```

---

### `models/universe_model.py`

```python
SCREEN_RESULT_SCHEMA = pl.Schema({
    "symbol":         pl.String,
    "short_name":     pl.String,
    "exchange":       pl.String,
    "market_cap":     pl.Float64,
    "trailing_pe":    pl.Float64,
    "dividend_yield": pl.Float64,
    "fetched_at":     pl.Datetime,
})
```

---

## Adapters

### `adapters/base_adapter.py` — BaseAdapter

```python
import polars as pl

class BaseAdapter:
    """Transforms raw source DataFrame into canonical model schema.

    Each source implements one adapter. Only implement the methods
    supported by your source; unimplemented methods raise NotImplementedError
    at call time. Do NOT inherit from ABC — partial implementation is intentional.
    """
    source_name: str

    def adapt_price(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_dividends(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_splits(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_fast_info(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_company_info(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_income_stmt(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_balance_sheet(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_cash_flow(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_analyst_ratings(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_price_targets(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_earnings_estimate(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_esg(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_institutional_holders(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_insider_transactions(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_fund_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_fund_holdings(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_sector_weights(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_sector_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_industry_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_earnings_calendar(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_news(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError

    def adapt_screen_results(self, raw: pl.DataFrame) -> pl.DataFrame:
        raise NotImplementedError
```

**Contract:** Every `adapt_*` implementation must end with:

```python
return df.select(TARGET_SCHEMA.names()).cast(TARGET_SCHEMA)
```

This drops extra columns and enforces types, guaranteeing the output strictly matches the canonical schema.

---

### `adapters/fmp_adapter.py` — FMPAdapter

FMPAdapter implements price and financials (the only real endpoints in FMPLoader today). Fields absent from FMP's price response (`dividends`, `splits`, `repaired`) are filled with defaults.

```python
from datetime import datetime, timezone
import polars as pl
from deepalpha.adapters.base_adapter import BaseAdapter
from deepalpha.models.price_model import PRICE_BAR_SCHEMA

class FMPAdapter(BaseAdapter):
    source_name = "fmp"

    def adapt_price(self, raw: pl.DataFrame) -> pl.DataFrame:
        now = datetime.now(timezone.utc)
        return (
            raw
            .rename({"adjClose": "adj_close"})
            .with_columns([
                pl.lit(0.0).alias("dividends"),
                pl.lit(0.0).alias("splits"),
                pl.lit(False).alias("repaired"),
                pl.lit(now).cast(PRICE_BAR_SCHEMA["fetched_at"]).alias("fetched_at"),
            ])
            .select(PRICE_BAR_SCHEMA.names())
            .cast(PRICE_BAR_SCHEMA)
        )
```

Fields dropped by `.select()`: `unadjustedClose`, `change`, `changePercent` (not in canonical schema).

---

### `adapters/yfinance_adapter.py` — YFinanceAdapter

YFinanceAdapter handles the full surface of yfinance's data types. Key transformation patterns:

- **Column rename:** yfinance uses `Open/High/Low/Close` (PascalCase) and `Stock Splits` (with space) → canonical uses snake_case
- **Index reset + symbol injection:** `YFinanceLoader` already resets the DatetimeIndex and injects the `symbol` column into the raw df before handing it to the adapter. Adapter signatures are therefore identical to `BaseAdapter` — no extra parameters needed.
- **`Repaired?` optional column:** only present when `repair=True`; adapter fills with `False` if absent
- **`adj_close`:** loader uses `auto_adjust=False`, so `Adj Close` is always present alongside `Close`
- **Wide → tidy for financials:** yfinance returns financials as a wide DataFrame (rows=metrics, columns=dates); adapter transposes to tidy (rows=periods)

```python
from deepalpha.adapters.base_adapter import BaseAdapter
from deepalpha.models.price_model import PRICE_BAR_SCHEMA

class YFinanceAdapter(BaseAdapter):
    source_name = "yfinance"

    def adapt_price(self, raw: pl.DataFrame) -> pl.DataFrame:
        now = datetime.now(timezone.utc)
        df = raw.rename({
            "Date": "date", "Open": "open", "High": "high",
            "Low": "low", "Close": "close", "Volume": "volume",
            "Dividends": "dividends", "Stock Splits": "splits",
            "Adj Close": "adj_close",
        })
        if "Repaired?" in df.columns:
            df = df.rename({"Repaired?": "repaired"})
        else:
            df = df.with_columns(pl.lit(False).alias("repaired"))
        return (
            df
            .with_columns(
                pl.lit(now).cast(PRICE_BAR_SCHEMA["fetched_at"]).alias("fetched_at")
            )
            .select(PRICE_BAR_SCHEMA.names())
            .cast(PRICE_BAR_SCHEMA)
        )
```

`symbol` is already in `raw` because `YFinanceLoader` injects it before returning.

---

## YFinanceLoader

### `loaders/yfinance_loader/yfinance_config.py`

```python
from typing import Optional
from pydantic_settings import BaseSettings

class YFinanceConfig(BaseSettings):
    rate_limit: float = 0.5        # seconds between per-symbol requests
    retries: int = 3               # automatic retry count (exponential backoff)
    proxy: Optional[str] = None    # HTTP proxy, e.g. "http://proxy:8080"
    timeout: int = 30
    tz_cache_path: str = "/tmp/yf_tz_cache"
    repair: bool = True            # enable price repair by default

    model_config = {"env_prefix": "YF_"}
```

### `loaders/yfinance_loader/yfinance_loader.py`

#### Initialization

```python
import yfinance as yf

def __init__(self, config: YFinanceConfig):
    self.config = config
    yf.set_tz_cache_location(config.tz_cache_path)
    yf.config.network.retries = config.retries
    yf.config.debug.hide_exceptions = False   # surface errors instead of silent failure
    if config.proxy:
        yf.config.network.proxy = config.proxy
```

#### `data_type` dispatch table

| `data_type` | yfinance interface | Notes |
| --- | --- | --- |
| `price` | `yf.download()` for multi-symbol; `ticker.history()` for single | `auto_adjust=False`, `repair=config.repair` |
| `fast_info` | `ticker.fast_info` | lightweight; no rate limit concern |
| `company_info` | `ticker.info` | slow; cache locally if possible |
| `dividends` | `ticker.dividends` | returns Series; adapter converts |
| `splits` | `ticker.splits` | returns Series; adapter converts |
| `income_stmt` | `ticker.income_stmt` / `quarterly_income_stmt` / `ttm_income_stmt` | `freq` kwarg selects variant |
| `balance_sheet` | `ticker.balance_sheet` / `quarterly_balance_sheet` | same pattern as income_stmt |
| `cashflow` | `ticker.cashflow` / `quarterly_cashflow` / `ttm_cashflow` | same pattern as income_stmt |
| `analyst_ratings` | `ticker.recommendations` | DataFrame with Firm, To Grade, Action |
| `price_targets` | `ticker.analyst_price_targets` | returns dict; adapter wraps in DataFrame |
| `earnings_estimate` | `ticker.earnings_estimate` | periods: 0q, 1q, 0y, 1y |
| `esg` | `ticker.sustainability` | |
| `institutional_holders` | `ticker.institutional_holders` | |
| `insider_transactions` | `ticker.insider_transactions` | |
| `fund_overview` | `ticker.funds_data.fund_overview` + `fund_operations` | produces `FUND_OVERVIEW_SCHEMA` |
| `fund_holdings` | `ticker.funds_data.top_holdings` + `sector_weightings` | produces `FUND_HOLDINGS_SCHEMA` + `SECTOR_WEIGHTS_SCHEMA` |
| `sector` | `yf.Sector(key)` | `symbols` treated as sector keys |
| `industry` | `yf.Industry(key)` | `symbols` treated as industry keys |
| `calendar` | `ticker.calendar` | returns dict; adapter converts |
| `news` | `ticker.get_news(count=50)` | |
| `screen` | `yf.screen(EquityQuery, ...)` | `symbols` unused; `kwargs` carries query dict |

#### Bulk price fetch strategy

The loader always injects `symbol` into the returned raw df so adapter signatures stay uniform.

```python
def _fetch_price(self, symbols, start_date, end_date, interval, **kwargs):
    if len(symbols) > 1:
        # yf.download uses Yahoo's batch endpoint — fewer requests, less blocking risk
        raw_pd = yf.download(
            symbols,
            start=start_date, end=end_date,
            interval=interval,
            auto_adjust=False,
            repair=self.config.repair,
            multi_level_index=False,   # flatten to "Close_AAPL" format
            progress=False,
        )
        # _melt_bulk_price pivots "Close_AAPL" columns → tidy rows with symbol column
        return self._melt_bulk_price(raw_pd, symbols)
    else:
        symbol = symbols[0]
        ticker = yf.Ticker(symbol)
        raw_pd = ticker.history(
            start=start_date, end=end_date,
            interval=interval,
            auto_adjust=False,
            repair=self.config.repair,
        )
        df = pl.from_pandas(raw_pd.reset_index())
        return df.with_columns(pl.lit(symbol).alias("symbol"))   # inject symbol
```

`_melt_bulk_price` pivots the flat multi-symbol pandas DataFrame (columns `Close_AAPL`, `Open_AAPL`, …) into tidy format where each row has a `symbol` column. Implementation: reset index, melt on date, parse `{field}_{symbol}` column names, pivot back to wide-per-symbol.

#### Rate limiting

Per-symbol requests sleep `config.rate_limit` seconds after each call. Bulk `yf.download()` calls are exempt (Yahoo's batch endpoint handles throttling internally).

#### WebSocket streaming (real-time)

`YFinanceLoader` exposes a separate `stream()` method outside of `fetch()`:

```python
def stream(self, symbols: list[str], callback, async_mode: bool = False) -> None:
    """Real-time tick streaming. Does not go through fetch/adapter pipeline.

    callback receives a pl.DataFrame with TICK_SCHEMA on each tick.
    """
    if async_mode:
        self._stream_async(symbols, callback)
    else:
        ws = yf.WebSocket()
        ws.subscribe(symbols)
        def _on_tick(data):
            df = pl.DataFrame([{
                "symbol": data["id"],
                "price": data["price"],
                "volume": data.get("dayVolume", 0),
                "tick_at": datetime.now(timezone.utc),
            }]).cast(TICK_SCHEMA)
            callback(df)
        ws.listen(_on_tick)

async def _stream_async(self, symbols, callback):
    ws = yf.AsyncWebSocket()
    async def _on_tick(data):
        df = pl.DataFrame([{
            "symbol":  data["id"],
            "price":   data["price"],
            "volume":  data.get("dayVolume", 0),
            "tick_at": datetime.now(timezone.utc),
        }]).cast(TICK_SCHEMA)
        await callback(df)
    await ws.subscribe(symbols, callback=_on_tick)
    await ws.listen()
```

#### Screener support

```python
def _fetch_screen(self, query_dict: dict, sort_field: str = "marketcap",
                  sort_asc: bool = False, size: int = 25, offset: int = 0):
    from yfinance import EquityQuery, screen
    q = self._dict_to_equity_query(query_dict)
    results = screen(q, sortField=sort_field, sortAsc=sort_asc,
                     offset=offset, size=size)
    return pl.DataFrame(results.get("quotes", []))
```

`_dict_to_equity_query` recursively converts a dict like `{"and": [{"gt": ["marketcap", 1e9]}, ...]}` into nested `EquityQuery` objects.

---

## Migration from Old Code

No backward compatibility. Delete old files and rewrite from scratch per the new structure.

### Files to delete

- `src/deepalpha/sources/` — entire directory (replaced by `loaders/`)
- `src/deepalpha/base/source.py` → replaced by `base/base_source.py`
- `src/deepalpha/base/processor.py` → replaced by `base/base_processor.py`
- `src/deepalpha/processors/price_cleaner/cleaner.py` → replaced by `price_cleaner.py`
- `src/deepalpha/processors/price_cleaner/schemas.py` → replaced by `price_schema.py`
- `src/deepalpha/api/schemas.py` → replaced by `api_schemas.py`

### `loaders/fmp_loader/fmp_loader.py` (rewrite)

`_fetch_price()` returns the raw FMP API response with no field renaming or selecting. All transformation moves to `FMPAdapter`.

```python
return df   # raw FMP column names: adjClose, unadjustedClose, changePercent, ...
```

### `processors/price_cleaner/price_schema.py` (new file)

`PriceCleaner` outputs `PRICE_BAR_SCHEMA` fields plus `is_anomaly` and `market`. Use `dict()` to extend the schema:

```python
from deepalpha.models.price_model import PRICE_BAR_SCHEMA
import polars as pl

CLEANED_PRICE_SCHEMA = pl.Schema({
    **dict(PRICE_BAR_SCHEMA),
    "is_anomaly": pl.Boolean,
    "market":     pl.String,
})
```

`PriceCleaner.process()` input must conform to `PRICE_BAR_SCHEMA` (i.e., come from an adapter). Output conforms to `CLEANED_PRICE_SCHEMA`.

---

## FMP vs yfinance — Recommended Data Source by Category

| Category | Primary Source | Reason |
| --- | --- | --- |
| Price OHLCV | Either (FMP preferred for production) | FMP more stable for bulk historical |
| Company fast_info | yfinance | Lightweight, no quota concern |
| Company full info | yfinance | More complete field coverage |
| Financial statements | FMP | More complete, structured response |
| Analysis / ESG / Estimates | yfinance | Only source with these endpoints |
| Holdings / Insider | yfinance | Only source with these endpoints |
| ETF / Funds | yfinance | Only source with these endpoints |
| Sector / Industry | yfinance | Only source with these endpoints |
| Calendar / News | yfinance | Only source with these endpoints |
| Universe screening | yfinance (`EquityQuery`) | Built-in screener |
| Real-time ticks | yfinance (`WebSocket`) | Only source with streaming |

---

## Usage Example (End-to-End)

```python
from deepalpha.loaders.yfinance_loader.yfinance_loader import YFinanceLoader
from deepalpha.loaders.yfinance_loader.yfinance_config import YFinanceConfig
from deepalpha.adapters.yfinance_adapter import YFinanceAdapter

loader = YFinanceLoader(YFinanceConfig())
adapter = YFinanceAdapter()

# Fetch raw price data
raw_df = loader.fetch(data_type="price", symbols=["AAPL", "MSFT"],
                      start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

# Adapt to canonical schema
canonical_df = adapter.adapt_price(raw_df, symbol="AAPL")

# canonical_df.schema == PRICE_BAR_SCHEMA  ← guaranteed
# Write to Parquet, push to Kafka, pass to PriceCleaner — all read PRICE_BAR_SCHEMA
```

---

## Testing Strategy

- **Unit tests for each adapter method**: provide a manually constructed raw DataFrame mimicking the source's output, assert the output schema equals the target canonical schema.
- **Schema validation helper**: `assert df.schema == TARGET_SCHEMA` after every `adapt_*` call.
- **yfinance tests use mocked `yf.Ticker` / `yf.download`** to avoid network calls in CI.
- **FMP tests use `httpx.MockTransport`** (already the pattern in `test_fmp_loader.py`).
- **Rate limiting**: tested by asserting `time.sleep` is called with `config.rate_limit` in per-symbol loops.
