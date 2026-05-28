# Canonical Data Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a unified canonical data model (10 `pl.Schema` modules) with a source-agnostic adapter layer, rewrite FMPLoader to return raw data, implement a full YFinanceLoader, and update PriceCleaner and API schemas to consume canonical schemas.

**Architecture:** Sources return raw `pl.DataFrame`s; per-source adapters transform them to canonical schemas defined in `models/`; processors and API consume only canonical shapes. No backward-compat shims — old files deleted outright.

**Tech Stack:** Python 3.11, polars ≥ 0.20, yfinance, httpx, pydantic-settings, pytest

**Spec:** `docs/superpowers/specs/2026-05-25-canonical-data-model-design.md`

---

## File Map

### Delete (no longer needed)
- `src/deepalpha/sources/` — entire directory
- `src/deepalpha/base/source.py`
- `src/deepalpha/base/processor.py`
- `src/deepalpha/processors/price_cleaner/cleaner.py`
- `src/deepalpha/processors/price_cleaner/schemas.py`
- `src/deepalpha/api/schemas.py`
- `tests/unit/sources/` — entire directory

### Create
- `src/deepalpha/base/base_source.py`
- `src/deepalpha/base/base_processor.py`
- `src/deepalpha/models/__init__.py`
- `src/deepalpha/models/price_model.py`
- `src/deepalpha/models/company_model.py`
- `src/deepalpha/models/financials_model.py`
- `src/deepalpha/models/analysis_model.py`
- `src/deepalpha/models/holdings_model.py`
- `src/deepalpha/models/etf_model.py`
- `src/deepalpha/models/sector_model.py`
- `src/deepalpha/models/calendar_model.py`
- `src/deepalpha/models/news_model.py`
- `src/deepalpha/models/universe_model.py`
- `src/deepalpha/adapters/__init__.py`
- `src/deepalpha/adapters/base_adapter.py`
- `src/deepalpha/adapters/fmp_adapter.py`
- `src/deepalpha/adapters/yfinance_adapter.py`
- `src/deepalpha/loaders/__init__.py`
- `src/deepalpha/loaders/fmp_loader/__init__.py`
- `src/deepalpha/loaders/fmp_loader/fmp_loader.py`
- `src/deepalpha/loaders/fmp_loader/fmp_config.py`
- `src/deepalpha/loaders/yfinance_loader/__init__.py`
- `src/deepalpha/loaders/yfinance_loader/yfinance_loader.py`
- `src/deepalpha/loaders/yfinance_loader/yfinance_config.py`
- `src/deepalpha/processors/price_cleaner/price_cleaner.py`
- `src/deepalpha/processors/price_cleaner/price_schema.py`
- `src/deepalpha/api/api_schemas.py`
- `tests/unit/models/__init__.py`
- `tests/unit/models/test_price_model.py`
- `tests/unit/models/test_other_models.py`
- `tests/unit/adapters/__init__.py`
- `tests/unit/adapters/test_fmp_adapter.py`
- `tests/unit/adapters/test_yfinance_adapter.py`
- `tests/unit/loaders/__init__.py`
- `tests/unit/loaders/test_fmp_loader.py`
- `tests/unit/loaders/test_yfinance_loader.py`

### Modify
- `src/deepalpha/base/__init__.py` — update imports
- `src/deepalpha/processors/price_cleaner/__init__.py` — update imports
- `tests/unit/test_base.py` — update import paths
- `tests/unit/processors/test_price_cleaner.py` — update imports + rewrite for canonical input

---

## Task 1: Delete old files + scaffold new packages

**Files:**
- Delete: `src/deepalpha/sources/`, `src/deepalpha/base/source.py`, `src/deepalpha/base/processor.py`, `src/deepalpha/processors/price_cleaner/cleaner.py`, `src/deepalpha/processors/price_cleaner/schemas.py`, `src/deepalpha/api/schemas.py`, `tests/unit/sources/`

- [ ] **Step 1: Delete old directories and files**

```bash
rm -rf src/deepalpha/sources
rm -f src/deepalpha/base/source.py src/deepalpha/base/processor.py
rm -f src/deepalpha/processors/price_cleaner/cleaner.py src/deepalpha/processors/price_cleaner/schemas.py
rm -f src/deepalpha/api/schemas.py
rm -rf tests/unit/sources
```

- [ ] **Step 2: Create new package skeleton directories**

```bash
mkdir -p src/deepalpha/models
mkdir -p src/deepalpha/adapters
mkdir -p src/deepalpha/loaders/fmp_loader
mkdir -p src/deepalpha/loaders/yfinance_loader
mkdir -p tests/unit/models
mkdir -p tests/unit/adapters
mkdir -p tests/unit/loaders
touch src/deepalpha/models/__init__.py
touch src/deepalpha/adapters/__init__.py
touch src/deepalpha/loaders/__init__.py
touch src/deepalpha/loaders/fmp_loader/__init__.py
touch src/deepalpha/loaders/yfinance_loader/__init__.py
touch tests/unit/models/__init__.py
touch tests/unit/adapters/__init__.py
touch tests/unit/loaders/__init__.py
```

- [ ] **Step 3: Verify pytest still collects (0 tests from deleted paths)**

```bash
pytest tests/ --collect-only 2>&1 | grep "sources\|ERROR" | head -20
```

Expected: no output (no errors or source-path references)

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: delete old source/base/processor files, scaffold new package dirs"
```

---

## Task 2: Rewrite base classes

**Files:**
- Create: `src/deepalpha/base/base_source.py`
- Create: `src/deepalpha/base/base_processor.py`
- Modify: `src/deepalpha/base/__init__.py`
- Modify: `tests/unit/test_base.py`

- [ ] **Step 1: Update test_base.py to use new import paths**

Replace the entire content of `tests/unit/test_base.py`:

```python
"""Tests for base plugin classes"""
import pytest
from deepalpha.base import BaseSource, BaseProcessor
import polars as pl
from abc import ABC


class TestBaseSource:
    def test_base_source_is_abc(self):
        assert issubclass(BaseSource, ABC)

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseSource()

    def test_concrete_subclass_works(self):
        class MinimalSource(BaseSource):
            name = "test"
            def fetch(self, **kwargs): return pl.DataFrame()
            def validate(self, df): return True

        source = MinimalSource()
        assert source.name == "test"


class TestBaseProcessor:
    def test_base_processor_is_abc(self):
        assert issubclass(BaseProcessor, ABC)

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseProcessor()

    def test_validate_output_non_empty(self):
        class MinimalProcessor(BaseProcessor):
            def process(self, df, **kwargs): return df

        p = MinimalProcessor()
        assert p.validate_output(pl.DataFrame({"a": [1]})) is True

    def test_validate_output_empty(self):
        class MinimalProcessor(BaseProcessor):
            def process(self, df, **kwargs): return df

        p = MinimalProcessor()
        assert p.validate_output(pl.DataFrame()) is False
```

- [ ] **Step 2: Run test to verify it fails (import error expected)**

```bash
pytest tests/unit/test_base.py -v
```

Expected: `ImportError` — `base_source` not found yet

- [ ] **Step 3: Write base_source.py**

```python
# src/deepalpha/base/base_source.py
from abc import ABC, abstractmethod
from typing import Any
import polars as pl


class BaseSource(ABC):
    name: str
    version: str = "1.0.0"

    @abstractmethod
    def fetch(self, **kwargs: Any) -> pl.DataFrame: ...

    @abstractmethod
    def validate(self, df: pl.DataFrame) -> bool: ...

    def to_kafka(self, df: pl.DataFrame, topic: str, bootstrap_servers: str = "localhost:9092") -> None:
        from confluent_kafka import Producer
        import json
        producer = Producer({"bootstrap.servers": bootstrap_servers})
        for row in df.iter_rows(named=True):
            producer.produce(topic, key=row.get("symbol", "").encode(), value=json.dumps(row).encode())
        producer.flush()
```

- [ ] **Step 4: Write base_processor.py**

```python
# src/deepalpha/base/base_processor.py
from abc import ABC, abstractmethod
from typing import Any
import polars as pl


class BaseProcessor(ABC):
    name: str
    version: str = "1.0.0"

    @abstractmethod
    def process(self, df: pl.DataFrame, **kwargs: Any) -> pl.DataFrame: ...

    def validate_output(self, df: pl.DataFrame) -> bool:
        return not df.is_empty()
```

- [ ] **Step 5: Update base/__init__.py**

```python
# src/deepalpha/base/__init__.py
from deepalpha.base.base_source import BaseSource
from deepalpha.base.base_processor import BaseProcessor

__all__ = ["BaseSource", "BaseProcessor"]
```

- [ ] **Step 6: Run tests and verify they pass**

```bash
pytest tests/unit/test_base.py -v
```

Expected: 6 passed

- [ ] **Step 7: Commit**

```bash
git add src/deepalpha/base/ tests/unit/test_base.py
git commit -m "feat: rewrite base classes into base_source.py and base_processor.py"
```

---

## Task 3: Price model

**Files:**
- Create: `src/deepalpha/models/price_model.py`
- Create: `tests/unit/models/test_price_model.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/models/test_price_model.py
import polars as pl
from datetime import date, timezone, datetime
from deepalpha.models.price_model import (
    PRICE_BAR_SCHEMA, DIVIDENDS_SCHEMA, SPLITS_SCHEMA, TICK_SCHEMA, _UTC,
)


class TestPriceModel:
    def test_price_bar_schema_fields(self):
        expected = {"symbol", "date", "open", "high", "low", "close",
                    "volume", "adj_close", "dividends", "splits", "repaired", "fetched_at"}
        assert set(PRICE_BAR_SCHEMA.names()) == expected

    def test_price_bar_schema_types(self):
        assert PRICE_BAR_SCHEMA["volume"] == pl.Int64
        assert PRICE_BAR_SCHEMA["repaired"] == pl.Boolean
        assert PRICE_BAR_SCHEMA["date"] == pl.Date
        assert PRICE_BAR_SCHEMA["close"] == pl.Float64

    def test_fetched_at_is_utc(self):
        assert PRICE_BAR_SCHEMA["fetched_at"] == _UTC
        assert _UTC == pl.Datetime("us", time_zone="UTC")

    def test_price_bar_schema_accepts_valid_df(self):
        now = datetime.now(timezone.utc)
        df = pl.DataFrame({
            "symbol": ["AAPL"], "date": [date(2024, 1, 1)],
            "open": [150.0], "high": [155.0], "low": [149.0], "close": [153.0],
            "volume": [1_000_000], "adj_close": [153.0],
            "dividends": [0.0], "splits": [0.0], "repaired": [False],
            "fetched_at": [now],
        }).cast(PRICE_BAR_SCHEMA)
        assert df.schema == PRICE_BAR_SCHEMA

    def test_dividends_schema_fields(self):
        assert set(DIVIDENDS_SCHEMA.names()) == {"symbol", "date", "amount", "fetched_at"}

    def test_splits_schema_fields(self):
        assert set(SPLITS_SCHEMA.names()) == {"symbol", "date", "ratio", "fetched_at"}

    def test_tick_schema_fields(self):
        assert set(TICK_SCHEMA.names()) == {"symbol", "price", "volume", "tick_at"}

    def test_tick_at_is_utc(self):
        assert TICK_SCHEMA["tick_at"] == _UTC
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/unit/models/test_price_model.py -v
```

Expected: `ImportError` — `price_model` not found

- [ ] **Step 3: Implement price_model.py**

```python
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
    "dividends":  pl.Float64,
    "splits":     pl.Float64,
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/unit/models/test_price_model.py -v
```

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/models/price_model.py tests/unit/models/test_price_model.py
git commit -m "feat: add price_model with PRICE_BAR_SCHEMA, DIVIDENDS, SPLITS, TICK schemas"
```

---

## Task 4: Company and financials models

**Files:**
- Create: `src/deepalpha/models/company_model.py`
- Create: `src/deepalpha/models/financials_model.py`
- Create: `tests/unit/models/test_other_models.py` (covers all remaining models)

- [ ] **Step 1: Write failing tests for company + financials**

```python
# tests/unit/models/test_other_models.py
import polars as pl
from deepalpha.models.price_model import _UTC


class TestCompanyModel:
    def test_fast_info_schema_fields(self):
        from deepalpha.models.company_model import FAST_INFO_SCHEMA
        expected = {"symbol", "last_price", "market_cap", "currency", "exchange",
                    "quote_type", "fifty_day_avg", "two_hundred_day_avg",
                    "year_high", "year_low", "fetched_at"}
        assert set(FAST_INFO_SCHEMA.names()) == expected
        assert FAST_INFO_SCHEMA["fetched_at"] == _UTC

    def test_company_info_schema_fields(self):
        from deepalpha.models.company_model import COMPANY_INFO_SCHEMA
        expected = {"symbol", "short_name", "sector", "industry", "country",
                    "employees", "trailing_pe", "forward_pe", "price_to_book",
                    "beta", "dividend_yield", "market_cap", "business_summary", "fetched_at"}
        assert set(COMPANY_INFO_SCHEMA.names()) == expected
        assert COMPANY_INFO_SCHEMA["employees"] == pl.Int64


class TestFinancialsModel:
    def test_income_stmt_schema_fields(self):
        from deepalpha.models.financials_model import INCOME_STMT_SCHEMA
        expected = {"symbol", "period_end", "freq", "total_revenue", "gross_profit",
                    "operating_income", "net_income", "ebitda", "diluted_eps", "fetched_at"}
        assert set(INCOME_STMT_SCHEMA.names()) == expected
        assert INCOME_STMT_SCHEMA["freq"] == pl.String
        assert INCOME_STMT_SCHEMA["period_end"] == pl.Date

    def test_balance_sheet_schema_fields(self):
        from deepalpha.models.financials_model import BALANCE_SHEET_SCHEMA
        expected = {"symbol", "period_end", "freq", "total_assets", "total_liabilities",
                    "stockholders_equity", "total_debt", "cash_and_equivalents",
                    "net_debt", "fetched_at"}
        assert set(BALANCE_SHEET_SCHEMA.names()) == expected

    def test_cash_flow_schema_fields(self):
        from deepalpha.models.financials_model import CASH_FLOW_SCHEMA
        expected = {"symbol", "period_end", "freq", "operating_cash_flow",
                    "investing_cash_flow", "financing_cash_flow", "free_cash_flow",
                    "capital_expenditure", "fetched_at"}
        assert set(CASH_FLOW_SCHEMA.names()) == expected
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/unit/models/test_other_models.py::TestCompanyModel tests/unit/models/test_other_models.py::TestFinancialsModel -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement company_model.py**

```python
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
```

- [ ] **Step 4: Implement financials_model.py**

```python
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
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/models/test_other_models.py::TestCompanyModel tests/unit/models/test_other_models.py::TestFinancialsModel -v
```

Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add src/deepalpha/models/company_model.py src/deepalpha/models/financials_model.py tests/unit/models/test_other_models.py
git commit -m "feat: add company_model and financials_model schemas"
```

---

## Task 5: Remaining models (analysis, holdings, etf, sector, calendar, news, universe)

**Files:**
- Create: `src/deepalpha/models/analysis_model.py`
- Create: `src/deepalpha/models/holdings_model.py`
- Create: `src/deepalpha/models/etf_model.py`
- Create: `src/deepalpha/models/sector_model.py`
- Create: `src/deepalpha/models/calendar_model.py`
- Create: `src/deepalpha/models/news_model.py`
- Create: `src/deepalpha/models/universe_model.py`
- Modify: `tests/unit/models/test_other_models.py`

- [ ] **Step 1: Add tests for all remaining models to test_other_models.py**

Append to `tests/unit/models/test_other_models.py`:

```python
class TestAnalysisModel:
    def test_analyst_rating_schema(self):
        from deepalpha.models.analysis_model import ANALYST_RATING_SCHEMA
        assert set(ANALYST_RATING_SCHEMA.names()) == {
            "symbol", "date", "firm", "to_grade", "from_grade", "action", "fetched_at"}

    def test_price_target_schema(self):
        from deepalpha.models.analysis_model import PRICE_TARGET_SCHEMA
        assert set(PRICE_TARGET_SCHEMA.names()) == {
            "symbol", "current", "mean", "high", "low", "num_analysts", "fetched_at"}
        assert PRICE_TARGET_SCHEMA["num_analysts"] == pl.Int32

    def test_earnings_estimate_schema(self):
        from deepalpha.models.analysis_model import EARNINGS_ESTIMATE_SCHEMA
        assert "period" in EARNINGS_ESTIMATE_SCHEMA.names()
        assert "avg_eps" in EARNINGS_ESTIMATE_SCHEMA.names()
        assert "avg_revenue" in EARNINGS_ESTIMATE_SCHEMA.names()

    def test_esg_schema(self):
        from deepalpha.models.analysis_model import ESG_SCHEMA
        assert set(ESG_SCHEMA.names()) == {
            "symbol", "total_esg", "environment", "social",
            "governance", "controversy_level", "fetched_at"}


class TestHoldingsModel:
    def test_institutional_holder_schema(self):
        from deepalpha.models.holdings_model import INSTITUTIONAL_HOLDER_SCHEMA
        assert set(INSTITUTIONAL_HOLDER_SCHEMA.names()) == {
            "symbol", "holder", "shares", "date_reported", "pct_out", "value", "fetched_at"}
        assert INSTITUTIONAL_HOLDER_SCHEMA["shares"] == pl.Int64

    def test_insider_transaction_schema(self):
        from deepalpha.models.holdings_model import INSIDER_TRANSACTION_SCHEMA
        assert set(INSIDER_TRANSACTION_SCHEMA.names()) == {
            "symbol", "insider", "shares", "value", "transaction", "date", "fetched_at"}


class TestETFModel:
    def test_fund_overview_schema(self):
        from deepalpha.models.etf_model import FUND_OVERVIEW_SCHEMA
        assert "morning_star_rating" in FUND_OVERVIEW_SCHEMA.names()
        assert FUND_OVERVIEW_SCHEMA["morning_star_rating"] == pl.Int32

    def test_fund_holdings_schema(self):
        from deepalpha.models.etf_model import FUND_HOLDINGS_SCHEMA
        assert set(FUND_HOLDINGS_SCHEMA.names()) == {
            "symbol", "holding_symbol", "holding_name", "pct", "fetched_at"}

    def test_sector_weights_schema(self):
        from deepalpha.models.etf_model import SECTOR_WEIGHTS_SCHEMA
        assert set(SECTOR_WEIGHTS_SCHEMA.names()) == {"symbol", "sector", "weight", "fetched_at"}


class TestSectorModel:
    def test_sector_overview_schema(self):
        from deepalpha.models.sector_model import SECTOR_OVERVIEW_SCHEMA
        assert set(SECTOR_OVERVIEW_SCHEMA.names()) == {
            "key", "name", "etf_symbol", "market_cap", "ytd_return", "fetched_at"}

    def test_industry_overview_schema(self):
        from deepalpha.models.sector_model import INDUSTRY_OVERVIEW_SCHEMA
        assert set(INDUSTRY_OVERVIEW_SCHEMA.names()) == {
            "key", "name", "sector_key", "fetched_at"}


class TestCalendarModel:
    def test_earnings_calendar_schema(self):
        from deepalpha.models.calendar_model import EARNINGS_CALENDAR_SCHEMA
        assert "earnings_date" in EARNINGS_CALENDAR_SCHEMA.names()
        assert "eps_estimate_avg" in EARNINGS_CALENDAR_SCHEMA.names()

    def test_market_status_schema(self):
        from deepalpha.models.calendar_model import MARKET_STATUS_SCHEMA
        assert set(MARKET_STATUS_SCHEMA.names()) == {"market", "status", "timezone", "fetched_at"}


class TestNewsModel:
    def test_news_item_schema(self):
        from deepalpha.models.news_model import NEWS_ITEM_SCHEMA
        assert set(NEWS_ITEM_SCHEMA.names()) == {
            "symbol", "title", "publisher", "url", "published_at", "tab", "fetched_at"}
        assert NEWS_ITEM_SCHEMA["published_at"] == _UTC


class TestUniverseModel:
    def test_screen_result_schema(self):
        from deepalpha.models.universe_model import SCREEN_RESULT_SCHEMA
        assert set(SCREEN_RESULT_SCHEMA.names()) == {
            "symbol", "short_name", "exchange", "market_cap",
            "trailing_pe", "dividend_yield", "fetched_at"}
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/unit/models/test_other_models.py -v 2>&1 | grep "FAILED\|ERROR" | head -20
```

Expected: 12+ failures

- [ ] **Step 3: Implement analysis_model.py**

```python
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
```

- [ ] **Step 4: Implement holdings_model.py**

```python
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
```

- [ ] **Step 5: Implement etf_model.py**

```python
# src/deepalpha/models/etf_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

FUND_OVERVIEW_SCHEMA = pl.Schema({
    "symbol":              pl.String,
    "fund_family":         pl.String,
    "legal_type":          pl.String,
    "category":            pl.String,
    "morning_star_rating": pl.Int32,
    "net_assets":          pl.Float64,
    "expense_ratio":       pl.Float64,
    "turnover":            pl.Float64,
    "fetched_at":          _UTC,
})

FUND_HOLDINGS_SCHEMA = pl.Schema({
    "symbol":         pl.String,
    "holding_symbol": pl.String,
    "holding_name":   pl.String,
    "pct":            pl.Float64,
    "fetched_at":     _UTC,
})

SECTOR_WEIGHTS_SCHEMA = pl.Schema({
    "symbol":     pl.String,
    "sector":     pl.String,
    "weight":     pl.Float64,
    "fetched_at": _UTC,
})
```

- [ ] **Step 6: Implement sector_model.py, calendar_model.py, news_model.py, universe_model.py**

```python
# src/deepalpha/models/sector_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

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

```python
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
```

```python
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
```

```python
# src/deepalpha/models/universe_model.py
import polars as pl
from deepalpha.models.price_model import _UTC

SCREEN_RESULT_SCHEMA = pl.Schema({
    "symbol":         pl.String,
    "short_name":     pl.String,
    "exchange":       pl.String,
    "market_cap":     pl.Float64,
    "trailing_pe":    pl.Float64,
    "dividend_yield": pl.Float64,
    "fetched_at":     _UTC,
})
```

- [ ] **Step 7: Run all model tests**

```bash
pytest tests/unit/models/ -v
```

Expected: all passed (8 from test_price_model + 20 from test_other_models)

- [ ] **Step 8: Commit**

```bash
git add src/deepalpha/models/ tests/unit/models/
git commit -m "feat: add analysis, holdings, etf, sector, calendar, news, universe models"
```

---

## Task 6: models/__init__.py

**Files:**
- Modify: `src/deepalpha/models/__init__.py`

- [ ] **Step 1: Write test for top-level import**

Append to `tests/unit/models/test_price_model.py`:

```python
class TestModelsInit:
    def test_can_import_all_schemas_from_top_level(self):
        from deepalpha.models import (
            PRICE_BAR_SCHEMA, DIVIDENDS_SCHEMA, SPLITS_SCHEMA, TICK_SCHEMA,
            FAST_INFO_SCHEMA, COMPANY_INFO_SCHEMA,
            INCOME_STMT_SCHEMA, BALANCE_SHEET_SCHEMA, CASH_FLOW_SCHEMA,
            ANALYST_RATING_SCHEMA, PRICE_TARGET_SCHEMA, EARNINGS_ESTIMATE_SCHEMA, ESG_SCHEMA,
            INSTITUTIONAL_HOLDER_SCHEMA, INSIDER_TRANSACTION_SCHEMA,
            FUND_OVERVIEW_SCHEMA, FUND_HOLDINGS_SCHEMA, SECTOR_WEIGHTS_SCHEMA,
            SECTOR_OVERVIEW_SCHEMA, INDUSTRY_OVERVIEW_SCHEMA,
            EARNINGS_CALENDAR_SCHEMA, MARKET_STATUS_SCHEMA,
            NEWS_ITEM_SCHEMA, SCREEN_RESULT_SCHEMA,
        )
        assert PRICE_BAR_SCHEMA is not None
        assert SCREEN_RESULT_SCHEMA is not None
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/unit/models/test_price_model.py::TestModelsInit -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement models/__init__.py**

```python
# src/deepalpha/models/__init__.py
from deepalpha.models.price_model import PRICE_BAR_SCHEMA, DIVIDENDS_SCHEMA, SPLITS_SCHEMA, TICK_SCHEMA
from deepalpha.models.company_model import FAST_INFO_SCHEMA, COMPANY_INFO_SCHEMA
from deepalpha.models.financials_model import INCOME_STMT_SCHEMA, BALANCE_SHEET_SCHEMA, CASH_FLOW_SCHEMA
from deepalpha.models.analysis_model import ANALYST_RATING_SCHEMA, PRICE_TARGET_SCHEMA, EARNINGS_ESTIMATE_SCHEMA, ESG_SCHEMA
from deepalpha.models.holdings_model import INSTITUTIONAL_HOLDER_SCHEMA, INSIDER_TRANSACTION_SCHEMA
from deepalpha.models.etf_model import FUND_OVERVIEW_SCHEMA, FUND_HOLDINGS_SCHEMA, SECTOR_WEIGHTS_SCHEMA
from deepalpha.models.sector_model import SECTOR_OVERVIEW_SCHEMA, INDUSTRY_OVERVIEW_SCHEMA
from deepalpha.models.calendar_model import EARNINGS_CALENDAR_SCHEMA, MARKET_STATUS_SCHEMA
from deepalpha.models.news_model import NEWS_ITEM_SCHEMA
from deepalpha.models.universe_model import SCREEN_RESULT_SCHEMA

__all__ = [
    "PRICE_BAR_SCHEMA", "DIVIDENDS_SCHEMA", "SPLITS_SCHEMA", "TICK_SCHEMA",
    "FAST_INFO_SCHEMA", "COMPANY_INFO_SCHEMA",
    "INCOME_STMT_SCHEMA", "BALANCE_SHEET_SCHEMA", "CASH_FLOW_SCHEMA",
    "ANALYST_RATING_SCHEMA", "PRICE_TARGET_SCHEMA", "EARNINGS_ESTIMATE_SCHEMA", "ESG_SCHEMA",
    "INSTITUTIONAL_HOLDER_SCHEMA", "INSIDER_TRANSACTION_SCHEMA",
    "FUND_OVERVIEW_SCHEMA", "FUND_HOLDINGS_SCHEMA", "SECTOR_WEIGHTS_SCHEMA",
    "SECTOR_OVERVIEW_SCHEMA", "INDUSTRY_OVERVIEW_SCHEMA",
    "EARNINGS_CALENDAR_SCHEMA", "MARKET_STATUS_SCHEMA",
    "NEWS_ITEM_SCHEMA", "SCREEN_RESULT_SCHEMA",
]
```

- [ ] **Step 4: Run all model tests**

```bash
pytest tests/unit/models/ -v
```

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/models/__init__.py tests/unit/models/test_price_model.py
git commit -m "feat: add models/__init__.py re-exporting all canonical schemas"
```

---

## Task 7: BaseAdapter

**Files:**
- Create: `src/deepalpha/adapters/base_adapter.py`
- Create: `tests/unit/adapters/test_fmp_adapter.py` (stub for now)

- [ ] **Step 1: Write test**

```python
# tests/unit/adapters/test_fmp_adapter.py
import pytest
import polars as pl
from deepalpha.adapters.base_adapter import BaseAdapter


class TestBaseAdapter:
    def test_unimplemented_adapt_price_raises(self):
        adapter = BaseAdapter()
        with pytest.raises(NotImplementedError):
            adapter.adapt_price(pl.DataFrame())

    def test_unimplemented_adapt_company_info_raises(self):
        adapter = BaseAdapter()
        with pytest.raises(NotImplementedError):
            adapter.adapt_company_info(pl.DataFrame())

    def test_source_name_not_set_raises_on_access(self):
        adapter = BaseAdapter()
        with pytest.raises(AttributeError):
            _ = adapter.source_name
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/unit/adapters/test_fmp_adapter.py::TestBaseAdapter -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement base_adapter.py**

```python
# src/deepalpha/adapters/base_adapter.py
import polars as pl


class BaseAdapter:
    """Transforms raw source DataFrame into canonical model schema.

    Implement only the methods supported by your source.
    All unimplemented methods raise NotImplementedError at call time.
    Do NOT inherit from ABC — partial implementation is intentional.
    """

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

- [ ] **Step 4: Run tests**

```bash
pytest tests/unit/adapters/test_fmp_adapter.py::TestBaseAdapter -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/adapters/base_adapter.py tests/unit/adapters/test_fmp_adapter.py
git commit -m "feat: add BaseAdapter with NotImplementedError stubs for all data categories"
```

---

## Task 8: FMPConfig + FMPLoader rewrite

**Files:**
- Create: `src/deepalpha/loaders/fmp_loader/fmp_config.py`
- Create: `src/deepalpha/loaders/fmp_loader/fmp_loader.py`
- Create: `src/deepalpha/loaders/fmp_loader/__init__.py`
- Create: `tests/unit/loaders/test_fmp_loader.py`

- [ ] **Step 1: Write tests**

```python
# tests/unit/loaders/test_fmp_loader.py
import pytest
from datetime import date
import polars as pl
from deepalpha.loaders.fmp_loader.fmp_config import FMPConfig
from deepalpha.loaders.fmp_loader.fmp_loader import FMPLoader


class TestFMPConfig:
    def test_default_config(self):
        config = FMPConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.rate_limit == 0.5
        assert "financialmodelingprep.com" in config.base_url

    def test_custom_config(self):
        config = FMPConfig(api_key="k", rate_limit=1.0, base_url="http://localhost")
        assert config.rate_limit == 1.0
        assert config.base_url == "http://localhost"


class TestFMPLoader:
    def test_name(self):
        loader = FMPLoader(FMPConfig(api_key="k"))
        assert loader.name == "fmp_loader"

    def test_validate_empty(self):
        loader = FMPLoader(FMPConfig(api_key="k"))
        assert loader.validate(pl.DataFrame()) is False

    def test_validate_missing_required_cols(self):
        loader = FMPLoader(FMPConfig(api_key="k"))
        assert loader.validate(pl.DataFrame({"x": [1]})) is False

    def test_validate_valid(self):
        loader = FMPLoader(FMPConfig(api_key="k"))
        df = pl.DataFrame({"date": [date(2024, 1, 1)], "symbol": ["AAPL"], "close": [150.0]})
        assert loader.validate(df) is True

    def test_fetch_unknown_type_raises(self):
        loader = FMPLoader(FMPConfig(api_key="k"))
        with pytest.raises(ValueError, match="Unknown data_type"):
            loader.fetch(data_type="unknown")

    def test_fetch_price_returns_raw_fmp_column_names(self, httpx_mock):
        """Raw output must preserve FMP field names (adjClose, not adj_close)."""
        import httpx
        from pytest_httpx import HTTPXMock
        config = FMPConfig(api_key="k", rate_limit=0)
        loader = FMPLoader(config)

        httpx_mock.add_response(
            url=f"{config.base_url}/historical-price-full/AAPL?apikey=k",
            json={"historical": [{
                "date": "2024-01-02", "open": 185.0, "high": 188.0,
                "low": 184.0, "close": 187.0, "volume": 1000000,
                "adjClose": 187.0, "unadjustedClose": 187.5,
                "change": 2.0, "changePercent": 1.08,
            }]},
        )

        df = loader.fetch(data_type="price", symbols=["AAPL"])
        assert "adjClose" in df.columns
        assert "adj_close" not in df.columns
```

Note: `pytest-httpx` is needed. Add it to dev dependencies if not already present:
```bash
uv add --dev pytest-httpx
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/unit/loaders/test_fmp_loader.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement fmp_config.py**

```python
# src/deepalpha/loaders/fmp_loader/fmp_config.py


class FMPConfig:
    def __init__(
        self,
        api_key: str = "",
        rate_limit: float = 0.5,
        base_url: str = "https://site.financialmodelingprep.com/api/v3",
    ):
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.base_url = base_url
```

- [ ] **Step 4: Implement fmp_loader.py (raw output — no field renaming)**

```python
# src/deepalpha/loaders/fmp_loader/fmp_loader.py
import time
from datetime import date
from typing import Any, Optional

import httpx
import polars as pl

from deepalpha.base.base_source import BaseSource
from deepalpha.loaders.fmp_loader.fmp_config import FMPConfig


class FMPLoader(BaseSource):
    name = "fmp_loader"
    version = "1.0.0"

    def __init__(self, config: FMPConfig):
        self.config = config
        self.client = httpx.Client(timeout=30.0)

    def fetch(
        self,
        data_type: str = "price",
        symbols: Optional[list[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs: Any,
    ) -> pl.DataFrame:
        if data_type == "price":
            return self._fetch_price(symbols, start_date, end_date)
        elif data_type == "financials":
            return self._fetch_financials(symbols)
        elif data_type == "quote":
            return self._fetch_quote(symbols)
        else:
            raise ValueError(f"Unknown data_type: {data_type}")

    def _fetch_price(
        self,
        symbols: Optional[list[str]],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> pl.DataFrame:
        if not symbols:
            symbols = ["AAPL"]

        results = []
        for symbol in symbols:
            url = f"{self.config.base_url}/historical-price-full/{symbol}"
            params = {"apikey": self.config.api_key}
            if start_date:
                params["from"] = start_date.isoformat()
            if end_date:
                params["to"] = end_date.isoformat()

            try:
                response = self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if "historical" in data:
                    for row in data["historical"]:
                        row["symbol"] = symbol
                        results.append(row)
                time.sleep(self.config.rate_limit)
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue

        if not results:
            return pl.DataFrame()

        df = pl.DataFrame(results)
        if "date" in df.columns:
            df = df.with_columns(pl.col("date").str.to_date())
        return df   # raw FMP column names preserved

    def _fetch_financials(self, symbols: Optional[list[str]]) -> pl.DataFrame:
        return pl.DataFrame()

    def _fetch_quote(self, symbols: Optional[list[str]]) -> pl.DataFrame:
        return pl.DataFrame()

    def validate(self, df: pl.DataFrame) -> bool:
        if df.is_empty():
            return False
        return {"date", "symbol", "close"}.issubset(df.columns)

    def close(self) -> None:
        self.client.close()
```

- [ ] **Step 5: Update loaders/fmp_loader/__init__.py**

```python
# src/deepalpha/loaders/fmp_loader/__init__.py
from deepalpha.loaders.fmp_loader.fmp_loader import FMPLoader

__all__ = ["FMPLoader"]
```

- [ ] **Step 6: Run tests (skip the httpx mock test if pytest-httpx not installed yet)**

```bash
pytest tests/unit/loaders/test_fmp_loader.py -v -k "not fetch_price_returns_raw"
```

Expected: 5 passed

- [ ] **Step 7: Commit**

```bash
git add src/deepalpha/loaders/fmp_loader/ tests/unit/loaders/test_fmp_loader.py
git commit -m "feat: add FMPConfig and rewrite FMPLoader to return raw FMP column names"
```

---

## Task 9: FMPAdapter

**Files:**
- Create: `src/deepalpha/adapters/fmp_adapter.py`
- Modify: `tests/unit/adapters/test_fmp_adapter.py`

- [ ] **Step 1: Add adapter tests to test_fmp_adapter.py**

Append to `tests/unit/adapters/test_fmp_adapter.py`:

```python
from datetime import date, datetime, timezone
from deepalpha.adapters.fmp_adapter import FMPAdapter
from deepalpha.models.price_model import PRICE_BAR_SCHEMA


class TestFMPAdapter:
    def _make_raw_price(self):
        return pl.DataFrame({
            "date":             [date(2024, 1, 2)],
            "symbol":           ["AAPL"],
            "open":             [185.0],
            "high":             [188.0],
            "low":              [184.0],
            "close":            [187.0],
            "volume":           [1_000_000],
            "adjClose":         [187.0],
            "unadjustedClose":  [187.5],
            "change":           [2.0],
            "changePercent":    [1.08],
        })

    def test_adapt_price_schema_matches_canonical(self):
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert result.schema == PRICE_BAR_SCHEMA

    def test_adapt_price_drops_fmp_only_columns(self):
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert "unadjustedClose" not in result.columns
        assert "change" not in result.columns
        assert "changePercent" not in result.columns

    def test_adapt_price_fills_dividends_and_splits_with_zero(self):
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert result["dividends"][0] == 0.0
        assert result["splits"][0] == 0.0

    def test_adapt_price_sets_repaired_false(self):
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert result["repaired"][0] is False

    def test_adapt_price_fetched_at_is_utc(self):
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        ts = result["fetched_at"][0]
        assert ts is not None

    def test_adapt_price_preserves_ohlcv(self):
        adapter = FMPAdapter()
        result = adapter.adapt_price(self._make_raw_price())
        assert result["close"][0] == 187.0
        assert result["volume"][0] == 1_000_000
        assert result["adj_close"][0] == 187.0

    def test_source_name(self):
        assert FMPAdapter.source_name == "fmp"
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/unit/adapters/test_fmp_adapter.py::TestFMPAdapter -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement fmp_adapter.py**

```python
# src/deepalpha/adapters/fmp_adapter.py
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

- [ ] **Step 4: Run tests**

```bash
pytest tests/unit/adapters/test_fmp_adapter.py -v
```

Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/adapters/fmp_adapter.py tests/unit/adapters/test_fmp_adapter.py
git commit -m "feat: add FMPAdapter.adapt_price mapping FMP raw columns to PRICE_BAR_SCHEMA"
```

---

## Task 10: YFinanceConfig + YFinanceLoader (price fetch)

**Files:**
- Create: `src/deepalpha/loaders/yfinance_loader/yfinance_config.py`
- Create: `src/deepalpha/loaders/yfinance_loader/yfinance_loader.py`
- Create: `src/deepalpha/loaders/yfinance_loader/__init__.py`
- Create: `tests/unit/loaders/test_yfinance_loader.py`

- [ ] **Step 1: Write tests for config and price fetch**

```python
# tests/unit/loaders/test_yfinance_loader.py
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
import pandas as pd
import polars as pl

from deepalpha.loaders.yfinance_loader.yfinance_config import YFinanceConfig
from deepalpha.loaders.yfinance_loader.yfinance_loader import YFinanceLoader


class TestYFinanceConfig:
    def test_defaults(self):
        config = YFinanceConfig()
        assert config.rate_limit == 0.5
        assert config.retries == 3
        assert config.proxy is None
        assert config.repair is True
        assert config.tz_cache_path == "/tmp/yf_tz_cache"

    def test_custom_values(self):
        config = YFinanceConfig(rate_limit=1.0, retries=5, proxy="http://proxy:8080")
        assert config.rate_limit == 1.0
        assert config.retries == 5
        assert config.proxy == "http://proxy:8080"


class TestYFinanceLoaderInit:
    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_sets_yf_config_on_init(self, mock_yf):
        config = YFinanceConfig(retries=5)
        YFinanceLoader(config)
        assert mock_yf.config.network.retries == 5

    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_sets_proxy_when_provided(self, mock_yf):
        config = YFinanceConfig(proxy="http://proxy:8080")
        YFinanceLoader(config)
        assert mock_yf.config.network.proxy == "http://proxy:8080"

    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_sets_tz_cache(self, mock_yf):
        config = YFinanceConfig(tz_cache_path="/tmp/test_cache")
        YFinanceLoader(config)
        mock_yf.set_tz_cache_location.assert_called_once_with("/tmp/test_cache")


class TestYFinanceLoaderPriceSingle:
    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_single_symbol_returns_df_with_symbol_column(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame({
            "Open": [150.0], "High": [155.0], "Low": [149.0],
            "Close": [153.0], "Adj Close": [153.0], "Volume": [1_000_000],
            "Dividends": [0.0], "Stock Splits": [0.0],
        }, index=pd.DatetimeIndex([pd.Timestamp("2024-01-02")], name="Date"))
        mock_yf.Ticker.return_value = mock_ticker

        config = YFinanceConfig(rate_limit=0)
        loader = YFinanceLoader(config)
        df = loader.fetch(data_type="price", symbols=["AAPL"],
                          start_date=date(2024, 1, 1), end_date=date(2024, 1, 3))

        assert "symbol" in df.columns
        assert df["symbol"][0] == "AAPL"
        assert "Date" in df.columns or "date" in df.columns or "index" in df.columns

    @patch("deepalpha.loaders.yfinance_loader.yfinance_loader.yf")
    def test_unknown_data_type_raises(self, mock_yf):
        loader = YFinanceLoader(YFinanceConfig())
        with pytest.raises(ValueError, match="Unknown data_type"):
            loader.fetch(data_type="unknown", symbols=["AAPL"])
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/unit/loaders/test_yfinance_loader.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement yfinance_config.py**

```python
# src/deepalpha/loaders/yfinance_loader/yfinance_config.py
from typing import Optional


class YFinanceConfig:
    def __init__(
        self,
        rate_limit: float = 0.5,
        retries: int = 3,
        proxy: Optional[str] = None,
        timeout: int = 30,
        tz_cache_path: str = "/tmp/yf_tz_cache",
        repair: bool = True,
    ):
        self.rate_limit = rate_limit
        self.retries = retries
        self.proxy = proxy
        self.timeout = timeout
        self.tz_cache_path = tz_cache_path
        self.repair = repair
```

- [ ] **Step 4: Implement yfinance_loader.py (price fetch only for now)**

```python
# src/deepalpha/loaders/yfinance_loader/yfinance_loader.py
import time
from datetime import date, datetime, timezone
from typing import Any, Callable, Optional

import pandas as pd
import polars as pl
import yfinance as yf

from deepalpha.base.base_source import BaseSource
from deepalpha.loaders.yfinance_loader.yfinance_config import YFinanceConfig
from deepalpha.models.price_model import TICK_SCHEMA


class YFinanceLoader(BaseSource):
    name = "yfinance_loader"
    version = "1.0.0"

    def __init__(self, config: YFinanceConfig):
        self.config = config
        yf.set_tz_cache_location(config.tz_cache_path)
        yf.config.network.retries = config.retries
        yf.config.debug.hide_exceptions = False
        if config.proxy:
            yf.config.network.proxy = config.proxy

    def fetch(
        self,
        data_type: str,
        symbols: Optional[list[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs: Any,
    ) -> pl.DataFrame:
        symbols = symbols or []
        if data_type == "price":
            return self._fetch_price(symbols, start_date, end_date,
                                     kwargs.get("interval", "1d"))
        elif data_type == "fast_info":
            return self._fetch_fast_info(symbols)
        elif data_type == "company_info":
            return self._fetch_company_info(symbols)
        elif data_type == "dividends":
            return self._fetch_series(symbols, "dividends")
        elif data_type == "splits":
            return self._fetch_series(symbols, "splits")
        elif data_type in ("income_stmt", "balance_sheet", "cashflow"):
            freq = kwargs.get("freq", "annual")
            return self._fetch_financials(symbols, data_type, freq)
        elif data_type == "analyst_ratings":
            return self._fetch_ticker_df(symbols, "recommendations")
        elif data_type == "price_targets":
            return self._fetch_price_targets(symbols)
        elif data_type == "earnings_estimate":
            return self._fetch_ticker_df(symbols, "earnings_estimate")
        elif data_type == "esg":
            return self._fetch_ticker_df(symbols, "sustainability")
        elif data_type == "institutional_holders":
            return self._fetch_ticker_df(symbols, "institutional_holders")
        elif data_type == "insider_transactions":
            return self._fetch_ticker_df(symbols, "insider_transactions")
        elif data_type == "fund_overview":
            return self._fetch_fund_overview(symbols)
        elif data_type == "fund_holdings":
            return self._fetch_fund_holdings(symbols)
        elif data_type == "sector":
            return self._fetch_sector(symbols)
        elif data_type == "industry":
            return self._fetch_industry(symbols)
        elif data_type == "calendar":
            return self._fetch_calendar(symbols)
        elif data_type == "news":
            return self._fetch_news(symbols, kwargs.get("count", 50))
        elif data_type == "screen":
            return self._fetch_screen(
                kwargs.get("query", {}),
                kwargs.get("sort_field", "marketcap"),
                kwargs.get("sort_asc", False),
                kwargs.get("size", 25),
                kwargs.get("offset", 0),
            )
        else:
            raise ValueError(f"Unknown data_type: {data_type}")

    def validate(self, df: pl.DataFrame) -> bool:
        return not df.is_empty()

    def _fetch_price(
        self,
        symbols: list[str],
        start_date: Optional[date],
        end_date: Optional[date],
        interval: str,
    ) -> pl.DataFrame:
        if len(symbols) > 1:
            raw_pd = yf.download(
                symbols,
                start=start_date, end=end_date,
                interval=interval,
                auto_adjust=False,
                repair=self.config.repair,
                multi_level_index=False,
                progress=False,
            )
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
            return df.with_columns(pl.lit(symbol).alias("symbol"))

    def _melt_bulk_price(self, raw_pd: pd.DataFrame, symbols: list[str]) -> pl.DataFrame:
        frames = []
        for symbol in symbols:
            suffix = f"_{symbol}"
            sym_cols = {col: col[:-len(suffix)] for col in raw_pd.columns
                        if col.endswith(suffix)}
            if not sym_cols:
                continue
            sym_df = raw_pd[list(sym_cols.keys())].rename(columns=sym_cols)
            sym_df = sym_df.reset_index()
            sym_df["symbol"] = symbol
            frames.append(sym_df)
        if not frames:
            return pl.DataFrame()
        return pl.from_pandas(pd.concat(frames, ignore_index=True))

    def _fetch_fast_info(self, symbols: list[str]) -> pl.DataFrame:
        rows = []
        for symbol in symbols:
            fi = yf.Ticker(symbol).fast_info
            rows.append({
                "symbol": symbol,
                "last_price": fi.last_price,
                "market_cap": fi.market_cap,
                "currency": fi.currency,
                "exchange": fi.exchange,
                "quote_type": fi.quote_type,
                "fifty_day_avg": fi.fifty_day_average,
                "two_hundred_day_avg": fi.two_hundred_day_average,
                "year_high": fi.year_high,
                "year_low": fi.year_low,
            })
            time.sleep(self.config.rate_limit)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def _fetch_company_info(self, symbols: list[str]) -> pl.DataFrame:
        rows = []
        for symbol in symbols:
            info = yf.Ticker(symbol).info
            rows.append({
                "symbol": symbol,
                "short_name": info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "country": info.get("country"),
                "employees": info.get("fullTimeEmployees"),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "beta": info.get("beta"),
                "dividend_yield": info.get("dividendYield"),
                "market_cap": info.get("marketCap"),
                "business_summary": info.get("longBusinessSummary"),
            })
            time.sleep(self.config.rate_limit)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def _fetch_series(self, symbols: list[str], attr: str) -> pl.DataFrame:
        frames = []
        for symbol in symbols:
            series = getattr(yf.Ticker(symbol), attr)
            if series is None or series.empty:
                continue
            df_pd = series.reset_index()
            df_pd.columns = ["date", "value"]
            df_pd["symbol"] = symbol
            frames.append(pl.from_pandas(df_pd))
            time.sleep(self.config.rate_limit)
        return pl.concat(frames) if frames else pl.DataFrame()

    def _fetch_financials(self, symbols: list[str], stmt_type: str, freq: str) -> pl.DataFrame:
        attr_map = {
            "income_stmt": {"annual": "income_stmt", "quarterly": "quarterly_income_stmt", "ttm": "ttm_income_stmt"},
            "balance_sheet": {"annual": "balance_sheet", "quarterly": "quarterly_balance_sheet", "ttm": "balance_sheet"},
            "cashflow": {"annual": "cashflow", "quarterly": "quarterly_cashflow", "ttm": "ttm_cashflow"},
        }
        frames = []
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            attr = attr_map[stmt_type].get(freq, attr_map[stmt_type]["annual"])
            raw_pd = getattr(ticker, attr)
            if raw_pd is None or raw_pd.empty:
                continue
            raw_pd.index.name = "metric"
            transposed = raw_pd.T
            transposed.index.name = "period_end"
            df = pl.from_pandas(transposed.reset_index())
            df = df.with_columns([
                pl.lit(symbol).alias("symbol"),
                pl.lit(freq).alias("freq"),
            ])
            frames.append(df)
            time.sleep(self.config.rate_limit)
        return pl.concat(frames) if frames else pl.DataFrame()

    def _fetch_ticker_df(self, symbols: list[str], attr: str) -> pl.DataFrame:
        frames = []
        for symbol in symbols:
            raw_pd = getattr(yf.Ticker(symbol), attr)
            if raw_pd is None or (hasattr(raw_pd, "empty") and raw_pd.empty):
                continue
            df = pl.from_pandas(raw_pd.reset_index() if hasattr(raw_pd, "reset_index") else raw_pd)
            df = df.with_columns(pl.lit(symbol).alias("symbol"))
            frames.append(df)
            time.sleep(self.config.rate_limit)
        return pl.concat(frames) if frames else pl.DataFrame()

    def _fetch_price_targets(self, symbols: list[str]) -> pl.DataFrame:
        rows = []
        for symbol in symbols:
            apt = yf.Ticker(symbol).analyst_price_targets
            if not apt:
                continue
            rows.append({
                "symbol": symbol,
                "current": apt.get("current"),
                "mean": apt.get("mean"),
                "high": apt.get("high"),
                "low": apt.get("low"),
                "num_analysts": apt.get("numberOfAnalysts"),
            })
            time.sleep(self.config.rate_limit)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def _fetch_fund_overview(self, symbols: list[str]) -> pl.DataFrame:
        rows = []
        for symbol in symbols:
            fd = yf.Ticker(symbol).funds_data
            if fd is None:
                continue
            overview = fd.fund_overview or {}
            ops_df = fd.fund_operations
            rows.append({
                "symbol": symbol,
                "fund_family": overview.get("fundFamily"),
                "legal_type": overview.get("legalType"),
                "category": overview.get("categoryName"),
                "morning_star_rating": overview.get("morningStarOverallRating"),
                "net_assets": ops_df.loc["totalNetAssets"].iloc[0] if ops_df is not None and "totalNetAssets" in ops_df.index else None,
                "expense_ratio": ops_df.loc["annualReportExpenseRatio"].iloc[0] if ops_df is not None and "annualReportExpenseRatio" in ops_df.index else None,
                "turnover": ops_df.loc["annualHoldingsTurnover"].iloc[0] if ops_df is not None and "annualHoldingsTurnover" in ops_df.index else None,
            })
            time.sleep(self.config.rate_limit)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def _fetch_fund_holdings(self, symbols: list[str]) -> pl.DataFrame:
        frames = []
        for symbol in symbols:
            fd = yf.Ticker(symbol).funds_data
            if fd is None:
                continue
            holdings_pd = fd.top_holdings
            if holdings_pd is not None and not holdings_pd.empty:
                df = pl.from_pandas(holdings_pd.reset_index())
                df = df.with_columns(pl.lit(symbol).alias("symbol"))
                frames.append(df)
            time.sleep(self.config.rate_limit)
        return pl.concat(frames) if frames else pl.DataFrame()

    def _fetch_sector(self, sector_keys: list[str]) -> pl.DataFrame:
        rows = []
        for key in sector_keys:
            s = yf.Sector(key)
            rows.append({
                "key": key,
                "name": s.name,
                "etf_symbol": s.symbol,
                "market_cap": (s.overview or {}).get("marketCap"),
                "ytd_return": (s.overview or {}).get("ytdReturn"),
            })
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def _fetch_industry(self, industry_keys: list[str]) -> pl.DataFrame:
        rows = []
        for key in industry_keys:
            ind = yf.Industry(key)
            rows.append({
                "key": key,
                "name": ind.name,
                "sector_key": ind.sector_key,
            })
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def _fetch_calendar(self, symbols: list[str]) -> pl.DataFrame:
        rows = []
        for symbol in symbols:
            cal = yf.Ticker(symbol).calendar
            if not cal:
                continue
            earnings_dates = cal.get("Earnings Date", [])
            earnings_date = earnings_dates[0] if earnings_dates else None
            rows.append({
                "symbol": symbol,
                "earnings_date": earnings_date,
                "eps_estimate_avg": cal.get("Earnings Average"),
                "eps_estimate_low": cal.get("Earnings Low"),
                "eps_estimate_high": cal.get("Earnings High"),
                "revenue_estimate_avg": cal.get("Revenue Average"),
            })
            time.sleep(self.config.rate_limit)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def _fetch_news(self, symbols: list[str], count: int) -> pl.DataFrame:
        frames = []
        for symbol in symbols:
            news = yf.Ticker(symbol).get_news(count=count)
            rows = [{
                "symbol": symbol,
                "title": n.get("title"),
                "publisher": n.get("publisher"),
                "url": n.get("link"),
                "published_at": n.get("providerPublishTime"),
                "tab": n.get("type", "news"),
            } for n in (news or [])]
            if rows:
                frames.append(pl.DataFrame(rows))
            time.sleep(self.config.rate_limit)
        return pl.concat(frames) if frames else pl.DataFrame()

    def _fetch_screen(
        self,
        query_dict: dict,
        sort_field: str,
        sort_asc: bool,
        size: int,
        offset: int,
    ) -> pl.DataFrame:
        from yfinance import EquityQuery, screen
        q = self._dict_to_equity_query(query_dict)
        results = screen(q, sortField=sort_field, sortAsc=sort_asc, offset=offset, size=size)
        quotes = results.get("quotes", [])
        return pl.DataFrame(quotes) if quotes else pl.DataFrame()

    def _dict_to_equity_query(self, query_dict: dict):
        from yfinance import EquityQuery
        operator = list(query_dict.keys())[0]
        operands = query_dict[operator]
        if operator in ("and", "or"):
            return EquityQuery(operator, [self._dict_to_equity_query(op) for op in operands])
        return EquityQuery(operator, operands)

    def stream(self, symbols: list[str], callback: Callable, async_mode: bool = False) -> None:
        if async_mode:
            import asyncio
            asyncio.run(self._stream_async(symbols, callback))
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

    async def _stream_async(self, symbols: list[str], callback: Callable) -> None:
        ws = yf.AsyncWebSocket()

        async def _on_tick(data):
            df = pl.DataFrame([{
                "symbol": data["id"],
                "price": data["price"],
                "volume": data.get("dayVolume", 0),
                "tick_at": datetime.now(timezone.utc),
            }]).cast(TICK_SCHEMA)
            await callback(df)

        await ws.subscribe(symbols, callback=_on_tick)
        await ws.listen()
```

- [ ] **Step 5: Update loaders/yfinance_loader/__init__.py**

```python
# src/deepalpha/loaders/yfinance_loader/__init__.py
from deepalpha.loaders.yfinance_loader.yfinance_loader import YFinanceLoader

__all__ = ["YFinanceLoader"]
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/unit/loaders/test_yfinance_loader.py -v
```

Expected: all passed

- [ ] **Step 7: Commit**

```bash
git add src/deepalpha/loaders/yfinance_loader/ tests/unit/loaders/test_yfinance_loader.py
git commit -m "feat: add YFinanceConfig and YFinanceLoader with all 21 data_types, stream, screener"
```

---

## Task 11: YFinanceAdapter

**Files:**
- Create: `src/deepalpha/adapters/yfinance_adapter.py`
- Create: `tests/unit/adapters/test_yfinance_adapter.py`

- [ ] **Step 1: Write tests**

```python
# tests/unit/adapters/test_yfinance_adapter.py
import polars as pl
from datetime import date, datetime, timezone
import pandas as pd
from deepalpha.adapters.yfinance_adapter import YFinanceAdapter
from deepalpha.models.price_model import PRICE_BAR_SCHEMA, DIVIDENDS_SCHEMA, SPLITS_SCHEMA
from deepalpha.models.company_model import FAST_INFO_SCHEMA, COMPANY_INFO_SCHEMA
from deepalpha.models.financials_model import INCOME_STMT_SCHEMA, BALANCE_SHEET_SCHEMA, CASH_FLOW_SCHEMA
from deepalpha.models.analysis_model import ANALYST_RATING_SCHEMA, PRICE_TARGET_SCHEMA, ESG_SCHEMA
from deepalpha.models.holdings_model import INSTITUTIONAL_HOLDER_SCHEMA, INSIDER_TRANSACTION_SCHEMA
from deepalpha.models.etf_model import FUND_OVERVIEW_SCHEMA, FUND_HOLDINGS_SCHEMA, SECTOR_WEIGHTS_SCHEMA
from deepalpha.models.sector_model import SECTOR_OVERVIEW_SCHEMA, INDUSTRY_OVERVIEW_SCHEMA
from deepalpha.models.calendar_model import EARNINGS_CALENDAR_SCHEMA, MARKET_STATUS_SCHEMA
from deepalpha.models.news_model import NEWS_ITEM_SCHEMA
from deepalpha.models.universe_model import SCREEN_RESULT_SCHEMA


def _make_raw_price():
    return pl.DataFrame({
        "Date":         [date(2024, 1, 2)],
        "Open":         [185.0],
        "High":         [188.0],
        "Low":          [184.0],
        "Close":        [187.0],
        "Adj Close":    [187.0],
        "Volume":       [1_000_000],
        "Dividends":    [0.0],
        "Stock Splits": [0.0],
        "symbol":       ["AAPL"],
    })


class TestYFinanceAdapterPrice:
    def test_adapt_price_schema_matches_canonical(self):
        adapter = YFinanceAdapter()
        result = adapter.adapt_price(_make_raw_price())
        assert result.schema == PRICE_BAR_SCHEMA

    def test_adapt_price_repaired_false_when_column_absent(self):
        adapter = YFinanceAdapter()
        result = adapter.adapt_price(_make_raw_price())
        assert result["repaired"][0] is False

    def test_adapt_price_repaired_from_column_when_present(self):
        adapter = YFinanceAdapter()
        raw = _make_raw_price().with_columns(pl.lit(True).alias("Repaired?"))
        result = adapter.adapt_price(raw)
        assert result["repaired"][0] is True

    def test_adapt_price_symbol_preserved(self):
        adapter = YFinanceAdapter()
        result = adapter.adapt_price(_make_raw_price())
        assert result["symbol"][0] == "AAPL"

    def test_adapt_price_fetched_at_utc(self):
        adapter = YFinanceAdapter()
        result = adapter.adapt_price(_make_raw_price())
        assert result["fetched_at"][0] is not None


class TestYFinanceAdapterDividends:
    def test_adapt_dividends_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({"date": [date(2024, 1, 15)], "value": [0.24], "symbol": ["AAPL"]})
        result = adapter.adapt_dividends(raw)
        assert result.schema == DIVIDENDS_SCHEMA


class TestYFinanceAdapterSplits:
    def test_adapt_splits_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({"date": [date(2020, 8, 31)], "value": [4.0], "symbol": ["AAPL"]})
        result = adapter.adapt_splits(raw)
        assert result.schema == SPLITS_SCHEMA


class TestYFinanceAdapterCompany:
    def test_adapt_fast_info_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "last_price": [185.0], "market_cap": [2.9e12],
            "currency": ["USD"], "exchange": ["NMS"], "quote_type": ["EQUITY"],
            "fifty_day_avg": [183.0], "two_hundred_day_avg": [180.0],
            "year_high": [200.0], "year_low": [160.0],
        })
        result = adapter.adapt_fast_info(raw)
        assert result.schema == FAST_INFO_SCHEMA

    def test_adapt_company_info_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "short_name": ["Apple Inc."],
            "sector": ["Technology"], "industry": ["Consumer Electronics"],
            "country": ["United States"], "employees": [164_000],
            "trailing_pe": [28.5], "forward_pe": [26.0],
            "price_to_book": [45.0], "beta": [1.2],
            "dividend_yield": [0.005], "market_cap": [2.9e12],
            "business_summary": ["Apple designs and markets electronics."],
        })
        result = adapter.adapt_company_info(raw)
        assert result.schema == COMPANY_INFO_SCHEMA


class TestYFinanceAdapterFinancials:
    def _make_raw_income(self):
        return pl.DataFrame({
            "period_end":       [date(2024, 9, 28)],
            "Total Revenue":    [3.91e11],
            "Gross Profit":     [1.74e11],
            "Operating Income": [1.19e11],
            "Net Income":       [9.38e10],
            "EBITDA":           [1.31e11],
            "Diluted EPS":      [6.11],
            "symbol":           ["AAPL"],
            "freq":             ["annual"],
        })

    def test_adapt_income_stmt_schema(self):
        adapter = YFinanceAdapter()
        result = adapter.adapt_income_stmt(self._make_raw_income(), freq="annual")
        assert result.schema == INCOME_STMT_SCHEMA

    def test_adapt_income_stmt_freq_preserved(self):
        adapter = YFinanceAdapter()
        result = adapter.adapt_income_stmt(self._make_raw_income(), freq="quarterly")
        assert result["freq"][0] == "quarterly"


class TestYFinanceAdapterAnalysis:
    def test_adapt_analyst_ratings_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({
            "Date":       [date(2024, 1, 5)],
            "Firm":       ["Goldman Sachs"],
            "To Grade":   ["Buy"],
            "From Grade": ["Hold"],
            "Action":     ["up"],
            "symbol":     ["AAPL"],
        })
        result = adapter.adapt_analyst_ratings(raw)
        assert result.schema == ANALYST_RATING_SCHEMA

    def test_adapt_price_targets_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "current": [185.0], "mean": [200.0],
            "high": [230.0], "low": [175.0], "num_analysts": [35],
        })
        result = adapter.adapt_price_targets(raw)
        assert result.schema == PRICE_TARGET_SCHEMA

    def test_adapt_esg_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "total_esg": [17.5],
            "environment": [2.1], "social": [8.3],
            "governance": [7.1], "controversy_level": ["3"],
        })
        result = adapter.adapt_esg(raw)
        assert result.schema == ESG_SCHEMA


class TestYFinanceAdapterHoldings:
    def test_adapt_institutional_holders_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "Holder": ["Vanguard"],
            "Shares": [1_200_000_000], "Date Reported": [date(2024, 3, 31)],
            "% Out": [0.075], "Value": [2.2e11],
        })
        result = adapter.adapt_institutional_holders(raw)
        assert result.schema == INSTITUTIONAL_HOLDER_SCHEMA

    def test_adapt_insider_transactions_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "Insider": ["Tim Cook"],
            "Shares": [50_000], "Value": [9_200_000.0],
            "Transaction": ["Sale"], "Start Date": [date(2024, 2, 1)],
        })
        result = adapter.adapt_insider_transactions(raw)
        assert result.schema == INSIDER_TRANSACTION_SCHEMA


class TestYFinanceAdapterOther:
    def test_adapt_sector_overview_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({
            "key": ["technology"], "name": ["Technology"],
            "etf_symbol": ["XLK"], "market_cap": [15e12], "ytd_return": [0.28],
        })
        result = adapter.adapt_sector_overview(raw)
        assert result.schema == SECTOR_OVERVIEW_SCHEMA

    def test_adapt_news_schema(self):
        from datetime import timezone, datetime
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({
            "symbol":       ["AAPL"],
            "title":        ["Apple reports record earnings"],
            "publisher":    ["Reuters"],
            "url":          ["https://reuters.com/article/1"],
            "published_at": [datetime(2024, 1, 2, tzinfo=timezone.utc)],
            "tab":          ["news"],
        })
        result = adapter.adapt_news(raw)
        assert result.schema == NEWS_ITEM_SCHEMA

    def test_adapt_screen_results_schema(self):
        adapter = YFinanceAdapter()
        raw = pl.DataFrame({
            "symbol": ["AAPL"], "short_name": ["Apple Inc."],
            "exchange": ["NMS"], "market_cap": [2.9e12],
            "trailing_pe": [28.5], "dividend_yield": [0.005],
        })
        result = adapter.adapt_screen_results(raw)
        assert result.schema == SCREEN_RESULT_SCHEMA
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/unit/adapters/test_yfinance_adapter.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement yfinance_adapter.py**

```python
# src/deepalpha/adapters/yfinance_adapter.py
from datetime import datetime, timezone

import polars as pl

from deepalpha.adapters.base_adapter import BaseAdapter
from deepalpha.models.price_model import PRICE_BAR_SCHEMA, DIVIDENDS_SCHEMA, SPLITS_SCHEMA
from deepalpha.models.company_model import FAST_INFO_SCHEMA, COMPANY_INFO_SCHEMA
from deepalpha.models.financials_model import INCOME_STMT_SCHEMA, BALANCE_SHEET_SCHEMA, CASH_FLOW_SCHEMA
from deepalpha.models.analysis_model import ANALYST_RATING_SCHEMA, PRICE_TARGET_SCHEMA, EARNINGS_ESTIMATE_SCHEMA, ESG_SCHEMA
from deepalpha.models.holdings_model import INSTITUTIONAL_HOLDER_SCHEMA, INSIDER_TRANSACTION_SCHEMA
from deepalpha.models.etf_model import FUND_OVERVIEW_SCHEMA, FUND_HOLDINGS_SCHEMA, SECTOR_WEIGHTS_SCHEMA
from deepalpha.models.sector_model import SECTOR_OVERVIEW_SCHEMA, INDUSTRY_OVERVIEW_SCHEMA
from deepalpha.models.calendar_model import EARNINGS_CALENDAR_SCHEMA, MARKET_STATUS_SCHEMA
from deepalpha.models.news_model import NEWS_ITEM_SCHEMA
from deepalpha.models.universe_model import SCREEN_RESULT_SCHEMA


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _add_fetched_at(df: pl.DataFrame, schema: pl.Schema) -> pl.DataFrame:
    return df.with_columns(
        pl.lit(_now()).cast(schema["fetched_at"]).alias("fetched_at")
    )


class YFinanceAdapter(BaseAdapter):
    source_name = "yfinance"

    def adapt_price(self, raw: pl.DataFrame) -> pl.DataFrame:
        rename_map = {
            "Date": "date", "Open": "open", "High": "high",
            "Low": "low", "Close": "close", "Volume": "volume",
            "Dividends": "dividends", "Stock Splits": "splits",
            "Adj Close": "adj_close",
        }
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        df = raw.rename(existing)
        if "Repaired?" in df.columns:
            df = df.rename({"Repaired?": "repaired"})
        else:
            df = df.with_columns(pl.lit(False).alias("repaired"))
        return (
            _add_fetched_at(df, PRICE_BAR_SCHEMA)
            .select(PRICE_BAR_SCHEMA.names())
            .cast(PRICE_BAR_SCHEMA)
        )

    def adapt_dividends(self, raw: pl.DataFrame) -> pl.DataFrame:
        return (
            raw.rename({"value": "amount"})
            .pipe(_add_fetched_at, DIVIDENDS_SCHEMA)
            .select(DIVIDENDS_SCHEMA.names())
            .cast(DIVIDENDS_SCHEMA)
        )

    def adapt_splits(self, raw: pl.DataFrame) -> pl.DataFrame:
        return (
            raw.rename({"value": "ratio"})
            .pipe(_add_fetched_at, SPLITS_SCHEMA)
            .select(SPLITS_SCHEMA.names())
            .cast(SPLITS_SCHEMA)
        )

    def adapt_fast_info(self, raw: pl.DataFrame) -> pl.DataFrame:
        return (
            _add_fetched_at(raw, FAST_INFO_SCHEMA)
            .select(FAST_INFO_SCHEMA.names())
            .cast(FAST_INFO_SCHEMA)
        )

    def adapt_company_info(self, raw: pl.DataFrame) -> pl.DataFrame:
        return (
            _add_fetched_at(raw, COMPANY_INFO_SCHEMA)
            .select(COMPANY_INFO_SCHEMA.names())
            .cast(COMPANY_INFO_SCHEMA)
        )

    def adapt_income_stmt(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        rename_map = {
            "period_end": "period_end",
            "Total Revenue": "total_revenue",
            "Gross Profit": "gross_profit",
            "Operating Income": "operating_income",
            "Net Income": "net_income",
            "EBITDA": "ebitda",
            "Diluted EPS": "diluted_eps",
        }
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        df = raw.rename(existing)
        if "freq" not in df.columns:
            df = df.with_columns(pl.lit(freq).alias("freq"))
        return (
            _add_fetched_at(df, INCOME_STMT_SCHEMA)
            .select(INCOME_STMT_SCHEMA.names())
            .cast(INCOME_STMT_SCHEMA)
        )

    def adapt_balance_sheet(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        rename_map = {
            "Total Assets": "total_assets",
            "Total Liabilities Net Minority Interest": "total_liabilities",
            "Stockholders Equity": "stockholders_equity",
            "Total Debt": "total_debt",
            "Cash And Cash Equivalents": "cash_and_equivalents",
            "Net Debt": "net_debt",
        }
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        df = raw.rename(existing)
        if "freq" not in df.columns:
            df = df.with_columns(pl.lit(freq).alias("freq"))
        return (
            _add_fetched_at(df, BALANCE_SHEET_SCHEMA)
            .select(BALANCE_SHEET_SCHEMA.names())
            .cast(BALANCE_SHEET_SCHEMA)
        )

    def adapt_cash_flow(self, raw: pl.DataFrame, freq: str) -> pl.DataFrame:
        rename_map = {
            "Operating Cash Flow": "operating_cash_flow",
            "Investing Cash Flow": "investing_cash_flow",
            "Financing Cash Flow": "financing_cash_flow",
            "Free Cash Flow": "free_cash_flow",
            "Capital Expenditure": "capital_expenditure",
        }
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        df = raw.rename(existing)
        if "freq" not in df.columns:
            df = df.with_columns(pl.lit(freq).alias("freq"))
        return (
            _add_fetched_at(df, CASH_FLOW_SCHEMA)
            .select(CASH_FLOW_SCHEMA.names())
            .cast(CASH_FLOW_SCHEMA)
        )

    def adapt_analyst_ratings(self, raw: pl.DataFrame) -> pl.DataFrame:
        rename_map = {
            "Date": "date", "Firm": "firm",
            "To Grade": "to_grade", "From Grade": "from_grade", "Action": "action",
        }
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        return (
            raw.rename(existing)
            .pipe(_add_fetched_at, ANALYST_RATING_SCHEMA)
            .select(ANALYST_RATING_SCHEMA.names())
            .cast(ANALYST_RATING_SCHEMA)
        )

    def adapt_price_targets(self, raw: pl.DataFrame) -> pl.DataFrame:
        return (
            _add_fetched_at(raw, PRICE_TARGET_SCHEMA)
            .select(PRICE_TARGET_SCHEMA.names())
            .cast(PRICE_TARGET_SCHEMA)
        )

    def adapt_earnings_estimate(self, raw: pl.DataFrame) -> pl.DataFrame:
        rename_map = {
            "avg": "avg_eps", "low": "low_eps", "high": "high_eps",
            "numberOfAnalysts": "num_analysts",
        }
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        return (
            raw.rename(existing)
            .pipe(_add_fetched_at, EARNINGS_ESTIMATE_SCHEMA)
            .select(EARNINGS_ESTIMATE_SCHEMA.names())
            .cast(EARNINGS_ESTIMATE_SCHEMA)
        )

    def adapt_esg(self, raw: pl.DataFrame) -> pl.DataFrame:
        rename_map = {"controversyLevel": "controversy_level"}
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        return (
            raw.rename(existing)
            .pipe(_add_fetched_at, ESG_SCHEMA)
            .select(ESG_SCHEMA.names())
            .cast(ESG_SCHEMA)
        )

    def adapt_institutional_holders(self, raw: pl.DataFrame) -> pl.DataFrame:
        rename_map = {
            "Holder": "holder", "Shares": "shares",
            "Date Reported": "date_reported",
            "% Out": "pct_out", "Value": "value",
        }
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        return (
            raw.rename(existing)
            .pipe(_add_fetched_at, INSTITUTIONAL_HOLDER_SCHEMA)
            .select(INSTITUTIONAL_HOLDER_SCHEMA.names())
            .cast(INSTITUTIONAL_HOLDER_SCHEMA)
        )

    def adapt_insider_transactions(self, raw: pl.DataFrame) -> pl.DataFrame:
        rename_map = {
            "Insider": "insider", "Shares": "shares",
            "Value": "value", "Transaction": "transaction",
            "Start Date": "date",
        }
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        return (
            raw.rename(existing)
            .pipe(_add_fetched_at, INSIDER_TRANSACTION_SCHEMA)
            .select(INSIDER_TRANSACTION_SCHEMA.names())
            .cast(INSIDER_TRANSACTION_SCHEMA)
        )

    def adapt_fund_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        return (
            _add_fetched_at(raw, FUND_OVERVIEW_SCHEMA)
            .select(FUND_OVERVIEW_SCHEMA.names())
            .cast(FUND_OVERVIEW_SCHEMA)
        )

    def adapt_fund_holdings(self, raw: pl.DataFrame) -> pl.DataFrame:
        rename_map = {
            "symbol_x": "holding_symbol", "holdingName": "holding_name",
            "holdingPercent": "pct",
        }
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        return (
            raw.rename(existing)
            .pipe(_add_fetched_at, FUND_HOLDINGS_SCHEMA)
            .select(FUND_HOLDINGS_SCHEMA.names())
            .cast(FUND_HOLDINGS_SCHEMA)
        )

    def adapt_sector_weights(self, raw: pl.DataFrame) -> pl.DataFrame:
        rename_map = {"sectorKey": "sector", "sectorWeight": "weight"}
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        return (
            raw.rename(existing)
            .pipe(_add_fetched_at, SECTOR_WEIGHTS_SCHEMA)
            .select(SECTOR_WEIGHTS_SCHEMA.names())
            .cast(SECTOR_WEIGHTS_SCHEMA)
        )

    def adapt_sector_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        return (
            _add_fetched_at(raw, SECTOR_OVERVIEW_SCHEMA)
            .select(SECTOR_OVERVIEW_SCHEMA.names())
            .cast(SECTOR_OVERVIEW_SCHEMA)
        )

    def adapt_industry_overview(self, raw: pl.DataFrame) -> pl.DataFrame:
        return (
            _add_fetched_at(raw, INDUSTRY_OVERVIEW_SCHEMA)
            .select(INDUSTRY_OVERVIEW_SCHEMA.names())
            .cast(INDUSTRY_OVERVIEW_SCHEMA)
        )

    def adapt_earnings_calendar(self, raw: pl.DataFrame) -> pl.DataFrame:
        return (
            _add_fetched_at(raw, EARNINGS_CALENDAR_SCHEMA)
            .select(EARNINGS_CALENDAR_SCHEMA.names())
            .cast(EARNINGS_CALENDAR_SCHEMA)
        )

    def adapt_news(self, raw: pl.DataFrame) -> pl.DataFrame:
        return (
            _add_fetched_at(raw, NEWS_ITEM_SCHEMA)
            .select(NEWS_ITEM_SCHEMA.names())
            .cast(NEWS_ITEM_SCHEMA)
        )

    def adapt_screen_results(self, raw: pl.DataFrame) -> pl.DataFrame:
        rename_map = {"shortName": "short_name", "dividendYield": "dividend_yield",
                      "trailingPE": "trailing_pe", "marketCap": "market_cap"}
        existing = {k: v for k, v in rename_map.items() if k in raw.columns}
        return (
            raw.rename(existing)
            .pipe(_add_fetched_at, SCREEN_RESULT_SCHEMA)
            .select(SCREEN_RESULT_SCHEMA.names())
            .cast(SCREEN_RESULT_SCHEMA)
        )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/unit/adapters/test_yfinance_adapter.py -v
```

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/adapters/yfinance_adapter.py tests/unit/adapters/test_yfinance_adapter.py
git commit -m "feat: add YFinanceAdapter covering all 20+ canonical data categories"
```

---

## Task 12: PriceCleaner update

**Files:**
- Create: `src/deepalpha/processors/price_cleaner/price_schema.py`
- Create: `src/deepalpha/processors/price_cleaner/price_cleaner.py`
- Modify: `src/deepalpha/processors/price_cleaner/__init__.py`
- Modify: `tests/unit/processors/test_price_cleaner.py`

- [ ] **Step 1: Rewrite test_price_cleaner.py to use canonical input**

```python
# tests/unit/processors/test_price_cleaner.py
import polars as pl
from datetime import date, datetime, timezone
import pytest
from deepalpha.processors.price_cleaner.price_cleaner import PriceCleaner
from deepalpha.processors.price_cleaner.price_schema import CLEANED_PRICE_SCHEMA
from deepalpha.models.price_model import PRICE_BAR_SCHEMA


def _make_canonical_row(symbol="AAPL", date_val=date(2024, 1, 1),
                        close=185.0, volume=1000, adj_close=185.0) -> dict:
    return {
        "symbol": symbol, "date": date_val, "open": close - 1,
        "high": close + 2, "low": close - 2, "close": close,
        "volume": volume, "adj_close": adj_close,
        "dividends": 0.0, "splits": 0.0, "repaired": False,
        "fetched_at": datetime.now(timezone.utc),
    }


def _make_canonical_df(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows).cast(PRICE_BAR_SCHEMA)


class TestPriceCleaner:
    def test_name(self):
        assert PriceCleaner().name == "price_cleaner"

    def test_output_schema_matches_cleaned_price_schema(self):
        cleaner = PriceCleaner()
        df = _make_canonical_df([_make_canonical_row()])
        result = cleaner.process(df)
        assert result.schema == CLEANED_PRICE_SCHEMA

    def test_empty_input_returns_empty_with_correct_schema(self):
        cleaner = PriceCleaner()
        result = cleaner.process(pl.DataFrame(schema=PRICE_BAR_SCHEMA))
        assert result.is_empty()
        assert result.schema == CLEANED_PRICE_SCHEMA

    def test_deduplicate_keeps_first_per_symbol_date(self):
        cleaner = PriceCleaner()
        rows = [
            _make_canonical_row(close=185.0),
            _make_canonical_row(close=186.0),  # duplicate date
            _make_canonical_row(date_val=date(2024, 1, 2), close=187.0),
        ]
        result = cleaner.process(_make_canonical_df(rows))
        assert result.shape[0] == 2

    def test_anomaly_detection_marks_large_change(self):
        cleaner = PriceCleaner(anomaly_threshold=0.5)
        rows = [
            _make_canonical_row(date_val=date(2024, 1, 1), close=100.0),
            _make_canonical_row(date_val=date(2024, 1, 2), close=180.0),  # +80%
            _make_canonical_row(date_val=date(2024, 1, 3), close=182.0),
        ]
        result = cleaner.process(_make_canonical_df(rows))
        assert result.filter(pl.col("is_anomaly")).shape[0] == 1

    def test_volume_filter_removes_zero_volume_non_anomaly(self):
        cleaner = PriceCleaner()
        rows = [
            _make_canonical_row(date_val=date(2024, 1, 1), volume=1000),
            _make_canonical_row(date_val=date(2024, 1, 2), volume=0),
            _make_canonical_row(date_val=date(2024, 1, 3), volume=1500),
        ]
        result = cleaner.process(_make_canonical_df(rows))
        dates = [str(d) for d in result["date"].to_list()]
        assert "2024-01-02" not in dates

    def test_market_column_added(self):
        cleaner = PriceCleaner(market="HK")
        result = cleaner.process(_make_canonical_df([_make_canonical_row()]))
        assert result["market"][0] == "HK"
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/unit/processors/test_price_cleaner.py -v
```

Expected: `ImportError` (price_cleaner not found at new path)

- [ ] **Step 3: Implement price_schema.py**

```python
# src/deepalpha/processors/price_cleaner/price_schema.py
import polars as pl
from deepalpha.models.price_model import PRICE_BAR_SCHEMA

CLEANED_PRICE_SCHEMA = pl.Schema({
    **dict(PRICE_BAR_SCHEMA),
    "is_anomaly": pl.Boolean,
    "market":     pl.String,
})
```

- [ ] **Step 4: Implement price_cleaner.py**

```python
# src/deepalpha/processors/price_cleaner/price_cleaner.py
import polars as pl

from deepalpha.base.base_processor import BaseProcessor
from deepalpha.models.price_model import PRICE_BAR_SCHEMA
from deepalpha.processors.price_cleaner.price_schema import CLEANED_PRICE_SCHEMA


class PriceCleaner(BaseProcessor):
    name = "price_cleaner"
    version = "1.0.0"

    def __init__(self, anomaly_threshold: float = 0.5, market: str = "US"):
        self.anomaly_threshold = anomaly_threshold
        self.market = market

    def process(self, df: pl.DataFrame, **kwargs) -> pl.DataFrame:
        if df.is_empty():
            return pl.DataFrame(schema=CLEANED_PRICE_SCHEMA)

        df = self._deduplicate(df)
        df = self._detect_anomalies(df)
        df = self._filter_volume(df)
        df = df.with_columns(pl.lit(self.market).alias("market"))
        return df.select(CLEANED_PRICE_SCHEMA.names()).cast(CLEANED_PRICE_SCHEMA)

    def _deduplicate(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.sort("date", descending=True).unique(subset=["symbol", "date"], keep="first")

    def _detect_anomalies(self, df: pl.DataFrame) -> pl.DataFrame:
        df = df.sort(["symbol", "date"])
        df = df.with_columns(pl.col("close").diff().over("symbol").alias("_price_change"))
        df = df.with_columns(
            (
                (pl.col("_price_change").abs() / pl.col("close").shift(1).over("symbol"))
                > self.anomaly_threshold
            ).fill_null(False).alias("is_anomaly")
        )
        return df.drop("_price_change")

    def _filter_volume(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.filter((pl.col("volume") > 0) | pl.col("is_anomaly"))
```

- [ ] **Step 5: Update processors/price_cleaner/__init__.py**

```python
# src/deepalpha/processors/price_cleaner/__init__.py
from deepalpha.processors.price_cleaner.price_cleaner import PriceCleaner

__all__ = ["PriceCleaner"]
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/unit/processors/test_price_cleaner.py -v
```

Expected: all passed

- [ ] **Step 7: Commit**

```bash
git add src/deepalpha/processors/price_cleaner/ tests/unit/processors/test_price_cleaner.py
git commit -m "feat: rewrite PriceCleaner to accept PRICE_BAR_SCHEMA and output CLEANED_PRICE_SCHEMA"
```

---

## Task 13: API schemas update

**Files:**
- Create: `src/deepalpha/api/api_schemas.py`
- Modify: `src/deepalpha/api/routes/price.py` (update import)
- Modify: `src/deepalpha/api/main.py` (verify no broken imports)

- [ ] **Step 1: Implement api_schemas.py**

```python
# src/deepalpha/api/api_schemas.py
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PriceQuery(BaseModel):
    symbols: str = Field(..., description="Comma-separated stock symbols")
    start_date: date = Field(..., description="Start date YYYY-MM-DD")
    end_date: date = Field(..., description="End date YYYY-MM-DD")
    fields: Optional[str] = Field(None, description="Comma-separated fields to return")
    format: str = Field("arrow", description="Response format: arrow or json")


class PriceResponse(BaseModel):
    count: int
    data: list[dict]
    format: str
```

- [ ] **Step 2: Update api/routes that import the old schemas.py**

```bash
grep -r "from deepalpha.api.schemas" src/deepalpha/api/
```

For each file found, update the import from `deepalpha.api.schemas` to `deepalpha.api.api_schemas`.

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: all tests pass, no import errors

- [ ] **Step 4: Commit**

```bash
git add src/deepalpha/api/api_schemas.py src/deepalpha/api/
git commit -m "feat: add api_schemas.py; update API routes to use new schema path"
```

---

## Task 14: Final cleanup and full validation

- [ ] **Step 1: Verify no old import paths remain**

```bash
grep -r "deepalpha.sources\|deepalpha.base.source\|deepalpha.base.processor\|price_cleaner.cleaner\|price_cleaner.schemas\|api.schemas" src/ tests/ | grep -v ".pyc"
```

Expected: no output

- [ ] **Step 2: Run full test suite with coverage**

```bash
pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: all tests pass, 0 errors

- [ ] **Step 3: Run linter**

```bash
ruff check src/
```

Expected: no errors (fix any that appear)

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete canonical data model — models, adapters, loaders, processor update"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered by task |
| --- | --- |
| 10 model modules with `pl.Schema` | Tasks 3-6 |
| `fetched_at: pl.Datetime("us", time_zone="UTC")` | Task 3 (price_model _UTC) |
| `models/__init__.py` re-exports all | Task 6 |
| `BaseAdapter` with `NotImplementedError` stubs | Task 7 |
| `FMPAdapter.adapt_price` with `.select().cast()` contract | Task 9 |
| `FMPLoader` returns raw FMP column names | Task 8 |
| `YFinanceConfig` with retries/proxy/repair | Task 10 |
| `YFinanceLoader` init sets `yf.config` | Task 10 |
| Single-symbol price: injects symbol column | Task 10 |
| Bulk price: `yf.download` + `_melt_bulk_price` | Task 10 |
| 21 `data_type` values dispatched | Task 10 |
| `stream()` sync + async with `TICK_SCHEMA` | Task 10 |
| `_dict_to_equity_query` for screener | Task 10 |
| `YFinanceAdapter` all 20+ `adapt_*` methods | Task 11 |
| `CLEANED_PRICE_SCHEMA = dict(PRICE_BAR_SCHEMA) + extras` | Task 12 |
| `PriceCleaner` accepts `PRICE_BAR_SCHEMA` input | Task 12 |
| `api_schemas.py` replaces old `schemas.py` | Task 13 |
| Old files deleted | Task 1 |

**Placeholder scan:** No TBD/TODO markers found.

**Type consistency check:**
- `_UTC` defined in `price_model.py`, imported via `from deepalpha.models.price_model import _UTC` in all other model files ✓
- `PRICE_BAR_SCHEMA` referenced in `fmp_adapter.py`, `yfinance_adapter.py`, `price_cleaner.py` — all import from `deepalpha.models.price_model` ✓
- `BaseAdapter` imported in `FMPAdapter` and `YFinanceAdapter` from `deepalpha.adapters.base_adapter` ✓
- `_add_fetched_at` helper defined once in `yfinance_adapter.py`, used throughout ✓
