# src/deepalpha/loaders/yfinance_loader/yfinance_loader.py
"""YFinance data loader — returns raw data for all supported data types."""
import logging
import time
from datetime import date, datetime, timezone
from typing import Any, Callable, Optional

import pandas as pd
import polars as pl
import yfinance as yf

from deepalpha.base.base_source import BaseSource
from deepalpha.loaders.yfinance_loader.yfinance_config import YFinanceConfig
from deepalpha.models.price_model import TICK_SCHEMA

logger = logging.getLogger(__name__)


class YFinanceLoader(BaseSource):
    version = "1.0.0"

    @property
    def name(self) -> str:
        return "yfinance_loader"

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
        dispatch = {
            "price":                  lambda: self._fetch_price(symbols, start_date, end_date, kwargs.get("interval", "1d")),
            "fast_info":              lambda: self._fetch_fast_info(symbols),
            "company_info":           lambda: self._fetch_company_info(symbols),
            "dividends":              lambda: self._fetch_series(symbols, "dividends"),
            "splits":                 lambda: self._fetch_series(symbols, "splits"),
            "income_stmt":            lambda: self._fetch_financials(symbols, "income_stmt", kwargs.get("freq", "annual")),
            "balance_sheet":          lambda: self._fetch_financials(symbols, "balance_sheet", kwargs.get("freq", "annual")),
            "cashflow":               lambda: self._fetch_financials(symbols, "cashflow", kwargs.get("freq", "annual")),
            "analyst_ratings":        lambda: self._fetch_ticker_df(symbols, "recommendations"),
            "price_targets":          lambda: self._fetch_price_targets(symbols),
            "earnings_estimate":      lambda: self._fetch_ticker_df(symbols, "earnings_estimate"),
            "esg":                    lambda: self._fetch_ticker_df(symbols, "sustainability"),
            "institutional_holders":  lambda: self._fetch_ticker_df(symbols, "institutional_holders"),
            "insider_transactions":   lambda: self._fetch_ticker_df(symbols, "insider_transactions"),
            "fund_overview":          lambda: self._fetch_fund_overview(symbols),
            "fund_holdings":          lambda: self._fetch_fund_holdings(symbols),
            "sector":                 lambda: self._fetch_sector(symbols),
            "industry":               lambda: self._fetch_industry(symbols),
            "calendar":               lambda: self._fetch_calendar(symbols),
            "news":                   lambda: self._fetch_news(symbols, kwargs.get("count", 50)),
            "screen":                 lambda: self._fetch_screen(
                                          kwargs.get("query", {}),
                                          kwargs.get("sort_field", "marketcap"),
                                          kwargs.get("sort_asc", False),
                                          kwargs.get("size", 25),
                                          kwargs.get("offset", 0),
                                      ),
        }
        if data_type not in dispatch:
            raise ValueError(f"Unknown data_type: {data_type!r}")
        return dispatch[data_type]()

    def validate(self, df: pl.DataFrame) -> bool:
        return not df.is_empty()

    # ── Price ──────────────────────────────────────────────────────────────

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
        """Pivot flat multi-symbol download (Close_AAPL, Open_AAPL...) to tidy rows."""
        frames = []
        for symbol in symbols:
            suffix = f"_{symbol}"
            sym_cols = {col: col[: -len(suffix)] for col in raw_pd.columns if col.endswith(suffix)}
            if not sym_cols:
                continue
            sym_df = raw_pd[list(sym_cols.keys())].rename(columns=sym_cols).reset_index()
            sym_df["symbol"] = symbol
            frames.append(sym_df)
        if not frames:
            return pl.DataFrame()
        return pl.from_pandas(pd.concat(frames, ignore_index=True))

    # ── Company ────────────────────────────────────────────────────────────

    def _fetch_fast_info(self, symbols: list[str]) -> pl.DataFrame:
        rows = []
        for symbol in symbols:
            try:
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
            except Exception as e:
                logger.warning("fast_info failed for %s: %s", symbol, e)
            time.sleep(self.config.rate_limit)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def _fetch_company_info(self, symbols: list[str]) -> pl.DataFrame:
        rows = []
        for symbol in symbols:
            try:
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
            except Exception as e:
                logger.warning("company_info failed for %s: %s", symbol, e)
            time.sleep(self.config.rate_limit)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    # ── Series (dividends / splits) ────────────────────────────────────────

    def _fetch_series(self, symbols: list[str], attr: str) -> pl.DataFrame:
        frames = []
        for symbol in symbols:
            try:
                series = getattr(yf.Ticker(symbol), attr)
                if series is None or series.empty:
                    continue
                df_pd = series.reset_index()
                df_pd.columns = ["date", "value"]
                df_pd["symbol"] = symbol
                frames.append(pl.from_pandas(df_pd))
            except Exception as e:
                logger.warning("%s failed for %s: %s", attr, symbol, e)
            time.sleep(self.config.rate_limit)
        return pl.concat(frames) if frames else pl.DataFrame()

    # ── Financials ─────────────────────────────────────────────────────────

    def _fetch_financials(self, symbols: list[str], stmt_type: str, freq: str) -> pl.DataFrame:
        attr_map = {
            "income_stmt":  {"annual": "income_stmt",  "quarterly": "quarterly_income_stmt",  "ttm": "ttm_income_stmt"},
            "balance_sheet": {"annual": "balance_sheet", "quarterly": "quarterly_balance_sheet", "ttm": "balance_sheet"},
            "cashflow":     {"annual": "cashflow",      "quarterly": "quarterly_cashflow",      "ttm": "ttm_cashflow"},
        }
        frames = []
        for symbol in symbols:
            try:
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
            except Exception as e:
                logger.warning("financials (%s, %s) failed for %s: %s", stmt_type, freq, symbol, e)
            time.sleep(self.config.rate_limit)
        return pl.concat(frames) if frames else pl.DataFrame()

    # ── Generic ticker attribute → DataFrame ──────────────────────────────

    def _fetch_ticker_df(self, symbols: list[str], attr: str) -> pl.DataFrame:
        frames = []
        for symbol in symbols:
            try:
                raw = getattr(yf.Ticker(symbol), attr)
                if raw is None:
                    continue
                if hasattr(raw, "empty") and raw.empty:
                    continue
                df = pl.from_pandas(raw.reset_index() if hasattr(raw, "reset_index") else raw)
                df = df.with_columns(pl.lit(symbol).alias("symbol"))
                frames.append(df)
            except Exception as e:
                logger.warning("%s failed for %s: %s", attr, symbol, e)
            time.sleep(self.config.rate_limit)
        return pl.concat(frames) if frames else pl.DataFrame()

    # ── Analysis ───────────────────────────────────────────────────────────

    def _fetch_price_targets(self, symbols: list[str]) -> pl.DataFrame:
        rows = []
        for symbol in symbols:
            try:
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
            except Exception as e:
                logger.warning("price_targets failed for %s: %s", symbol, e)
            time.sleep(self.config.rate_limit)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    # ── ETF / Funds ────────────────────────────────────────────────────────

    def _fetch_fund_overview(self, symbols: list[str]) -> pl.DataFrame:
        rows = []
        for symbol in symbols:
            try:
                fd = yf.Ticker(symbol).funds_data
                if fd is None:
                    continue
                overview = fd.fund_overview or {}
                ops = fd.fund_operations

                def _ops(key: str):
                    if ops is not None and key in ops.index:
                        return ops.loc[key].iloc[0]
                    return None

                rows.append({
                    "symbol": symbol,
                    "fund_family": overview.get("fundFamily"),
                    "legal_type": overview.get("legalType"),
                    "category": overview.get("categoryName"),
                    "morning_star_rating": overview.get("morningStarOverallRating"),
                    "net_assets": _ops("totalNetAssets"),
                    "expense_ratio": _ops("annualReportExpenseRatio"),
                    "turnover": _ops("annualHoldingsTurnover"),
                })
            except Exception as e:
                logger.warning("fund_overview failed for %s: %s", symbol, e)
            time.sleep(self.config.rate_limit)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def _fetch_fund_holdings(self, symbols: list[str]) -> pl.DataFrame:
        frames = []
        for symbol in symbols:
            try:
                fd = yf.Ticker(symbol).funds_data
                if fd is None:
                    continue
                holdings = fd.top_holdings
                if holdings is not None and not holdings.empty:
                    df = pl.from_pandas(holdings.reset_index())
                    df = df.with_columns(pl.lit(symbol).alias("symbol"))
                    frames.append(df)
            except Exception as e:
                logger.warning("fund_holdings failed for %s: %s", symbol, e)
            time.sleep(self.config.rate_limit)
        return pl.concat(frames) if frames else pl.DataFrame()

    # ── Sector / Industry ─────────────────────────────────────────────────

    def _fetch_sector(self, sector_keys: list[str]) -> pl.DataFrame:
        rows = []
        for key in sector_keys:
            try:
                s = yf.Sector(key)
                rows.append({
                    "key": key,
                    "name": s.name,
                    "etf_symbol": s.symbol,
                    "market_cap": (s.overview or {}).get("marketCap"),
                    "ytd_return": (s.overview or {}).get("ytdReturn"),
                })
            except Exception as e:
                logger.warning("sector failed for %s: %s", key, e)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def _fetch_industry(self, industry_keys: list[str]) -> pl.DataFrame:
        rows = []
        for key in industry_keys:
            try:
                ind = yf.Industry(key)
                rows.append({
                    "key": key,
                    "name": ind.name,
                    "sector_key": ind.sector_key,
                })
            except Exception as e:
                logger.warning("industry failed for %s: %s", key, e)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    # ── Calendar ───────────────────────────────────────────────────────────

    def _fetch_calendar(self, symbols: list[str]) -> pl.DataFrame:
        rows = []
        for symbol in symbols:
            try:
                cal = yf.Ticker(symbol).calendar
                if not cal:
                    continue
                earnings_dates = cal.get("Earnings Date", [])
                rows.append({
                    "symbol": symbol,
                    "earnings_date": earnings_dates[0] if earnings_dates else None,
                    "eps_estimate_avg": cal.get("Earnings Average"),
                    "eps_estimate_low": cal.get("Earnings Low"),
                    "eps_estimate_high": cal.get("Earnings High"),
                    "revenue_estimate_avg": cal.get("Revenue Average"),
                })
            except Exception as e:
                logger.warning("calendar failed for %s: %s", symbol, e)
            time.sleep(self.config.rate_limit)
        return pl.DataFrame(rows) if rows else pl.DataFrame()

    # ── News ───────────────────────────────────────────────────────────────

    def _fetch_news(self, symbols: list[str], count: int) -> pl.DataFrame:
        frames = []
        for symbol in symbols:
            try:
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
            except Exception as e:
                logger.warning("news failed for %s: %s", symbol, e)
            time.sleep(self.config.rate_limit)
        return pl.concat(frames) if frames else pl.DataFrame()

    # ── Screener ───────────────────────────────────────────────────────────

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

    # ── Streaming ──────────────────────────────────────────────────────────

    def stream(self, symbols: list[str], callback: Callable, async_mode: bool = False) -> None:
        """Real-time tick streaming via WebSocket. Bypasses fetch/adapter pipeline.

        callback receives a pl.DataFrame with TICK_SCHEMA on each tick.
        """
        if async_mode:
            import asyncio
            asyncio.run(self._stream_async(symbols, callback))
        else:
            ws = yf.WebSocket()
            ws.subscribe(symbols)

            def _on_tick(data: dict) -> None:
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

        async def _on_tick(data: dict) -> None:
            df = pl.DataFrame([{
                "symbol": data["id"],
                "price": data["price"],
                "volume": data.get("dayVolume", 0),
                "tick_at": datetime.now(timezone.utc),
            }]).cast(TICK_SCHEMA)
            await callback(df)

        await ws.subscribe(symbols, callback=_on_tick)
        await ws.listen()
