# src/deepalpha/loaders/fmp_loader/fmp_loader.py
"""FMP data loader — returns raw API responses without field mapping."""
import logging
import time
from datetime import date
from typing import Any, Optional

import httpx
import polars as pl

from deepalpha.base.base_source import BaseSource
from deepalpha.loaders.fmp_loader.fmp_config import FMPConfig

logger = logging.getLogger(__name__)


class FMPLoader(BaseSource):
    version = "1.0.0"

    @property
    def name(self) -> str:
        return "fmp_loader"

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
            params: dict[str, str] = {"apikey": self.config.api_key}
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
                logger.warning("Error fetching %s: %s", symbol, e)
                continue

        if not results:
            return pl.DataFrame()

        df = pl.DataFrame(results)
        if "date" in df.columns:
            df = df.with_columns(pl.col("date").str.to_date())
        return df  # raw FMP column names: adjClose, unadjustedClose, changePercent, etc.

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
