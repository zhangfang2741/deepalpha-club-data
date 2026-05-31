"""FMP 市场数据加载器实现"""

import datetime
from typing import Any

from deepalpha.loaders.enums import AssetClass, Interval
from deepalpha.loaders.market_loader import AbstractMarketLoader
from deepalpha.models.market import PriceBar, Quote

_INTRADAY_PATHS: dict[Interval, str] = {
    Interval.ONE_MIN:     "historical-chart/1min",
    Interval.FIVE_MIN:    "historical-chart/5min",
    Interval.FIFTEEN_MIN: "historical-chart/15min",
    Interval.THIRTY_MIN:  "historical-chart/30min",
    Interval.ONE_HOUR:    "historical-chart/1hour",
    Interval.FOUR_HOUR:   "historical-chart/4hour",
}


class FMPMarketLoader(AbstractMarketLoader):
    """FMP 市场数据加载器。

    实现 AbstractMarketLoader 接口，通过 FMP stable API 获取市场数据。
    所有端点使用 ?symbol=X 查询参数格式。
    """

    async def get_quote(self, symbol: str) -> Quote:
        data = await self._get("/stable/quote", symbol=symbol)
        return Quote.model_validate(data)

    async def get_quotes(self, symbols: list[str]) -> list[Quote]:
        result: list[Quote] = []
        for sym in symbols:
            records = await self._get_list("/stable/quote", symbol=sym)
            result.extend(self._to_models(records, Quote))
        return result

    async def get_price_history(
        self,
        symbol: str,
        start: datetime.date,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> list[PriceBar]:
        params: dict[str, Any] = {"symbol": symbol, "from": str(start)}
        if end:
            params["to"] = str(end)
        if interval in _INTRADAY_PATHS:
            path = f"/stable/{_INTRADAY_PATHS[interval]}"
        else:
            path = "/stable/historical-price-eod/full"
        records = await self._get_list(path, **params)
        return self._to_models(records, PriceBar)

    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> list[Quote]:
        return []
