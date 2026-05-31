import datetime

import polars as pl

from deepalpha.loaders.enums import AssetClass, Interval
from deepalpha.loaders.market_loader import AbstractMarketLoader
from deepalpha.models.market import PriceBar, Quote

_INTRADAY_PATHS: dict[Interval, str] = {
    Interval.ONE_MIN:     "intraday-1-min",
    Interval.FIVE_MIN:    "intraday-5-min",
    Interval.FIFTEEN_MIN: "intraday-15-min",
    Interval.THIRTY_MIN:  "intraday-30-min",
    Interval.ONE_HOUR:    "intraday-1-hour",
    Interval.FOUR_HOUR:   "intraday-4-hour",
}

_SNAPSHOT_PATHS: dict[AssetClass, str] = {
    AssetClass.STOCK:       "full-exchange-quotes",
    AssetClass.ETF:         "full-etf-quotes",
    AssetClass.INDEX:       "full-index-quotes",
    AssetClass.CRYPTO:      "full-cryptocurrency-quotes",
    AssetClass.FOREX:       "full-forex-quotes",
    AssetClass.COMMODITY:   "full-commodities-quotes",
    AssetClass.MUTUAL_FUND: "full-mutual-fund-quotes",
}

class FMPMarketLoader(AbstractMarketLoader):
    async def get_quote(self, symbol: str) -> Quote:
        data = await self._get(f"/stable/quote/{symbol}")
        return Quote.model_validate(data)

    async def get_quotes(self, symbols: list[str]) -> pl.DataFrame:
        records = await self._get_list("/stable/quotes-batch", symbols=",".join(symbols))
        return self._to_df(records, Quote)

    async def get_price_history(
        self,
        symbol: str,
        start: datetime.date,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> pl.DataFrame:
        params: dict[str, str] = {"from": str(start)}
        if end:
            params["to"] = str(end)
        if interval in _INTRADAY_PATHS:
            path = f"/stable/{_INTRADAY_PATHS[interval]}/{symbol}"
        elif adjusted:
            path = f"/stable/historical-price-eod-full/{symbol}"
        else:
            path = f"/stable/historical-price-eod-non-split-adjusted/{symbol}"
        records = await self._get_list(path, **params)
        return self._to_df(records, PriceBar)

    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> pl.DataFrame:
        suffix = _SNAPSHOT_PATHS.get(asset_class, "full-exchange-quotes")
        records = await self._get_list(f"/stable/{suffix}")
        return self._to_df(records, Quote)
