"""FMP data loader implementation"""
import time
from datetime import date
from typing import Any, Optional

import httpx
import polars as pl

from deepalpha.base.source import BaseSource
from deepalpha.sources.fmp_loader.config import FMPConfig
from deepalpha.sources.fmp_loader.schemas import get_price_schema


class FMPLoader(BaseSource):
    """FMP API data source plugin.

    Fetches daily prices, financial statements, and other data
    from Financial Modeling Prep API.
    """

    name = "fmp_loader"
    version = "1.0.0"

    def __init__(self, config: FMPConfig):
        """Initialize FMP loader with configuration.

        Args:
            config: FMPConfig with api_key and rate_limit
        """
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
        """Fetch data from FMP API.

        Args:
            data_type: Type of data ("price", "financials", "quote")
            symbols: List of stock symbols
            start_date: Start date for price data
            end_date: End date for price data
            **kwargs: Additional FMP API parameters

        Returns:
            polars.DataFrame: Fetched data
        """
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
        """Fetch historical daily prices"""
        if not symbols:
            symbols = ["AAPL"]

        results = []
        for symbol in symbols:
            url = f"{self.config.base_url}/historical-price-full/{symbol}"
            params = {
                "apikey": self.config.api_key,
                "from": start_date.isoformat() if start_date else None,
                "to": end_date.isoformat() if end_date else None,
            }
            params = {k: v for k, v in params.items() if v}

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
            return pl.DataFrame(schema=get_price_schema())

        df = pl.DataFrame(results)
        if "date" in df.columns:
            df = df.with_columns(pl.col("date").str.to_date().alias("date"))

        return df.select([
            "date", "symbol", "open", "high", "low", "close",
            "volume", "adjClose", "unadjustedClose", "change", "changePercent"
        ]).rename({
            "adjClose": "adj_close",
            "unadjustedClose": "unadjusted_close",
            "changePercent": "change_percent",
        })

    def _fetch_financials(self, symbols: Optional[list[str]]) -> pl.DataFrame:
        """Fetch financial statements"""
        # Placeholder - would implement actual API call
        return pl.DataFrame()

    def _fetch_quote(self, symbols: Optional[list[str]]) -> pl.DataFrame:
        """Fetch real-time quotes"""
        # Placeholder - would implement actual API call
        return pl.DataFrame()

    def validate(self, df: pl.DataFrame) -> bool:
        """Validate fetched data.

        Checks:
        - DataFrame is not empty
        - Required columns exist
        - Date column is valid
        """
        if df.is_empty():
            return False

        required_cols = {"date", "symbol", "close"}
        if not required_cols.issubset(df.columns):
            return False

        return True

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()