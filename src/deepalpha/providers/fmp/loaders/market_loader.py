"""FMP 市场数据加载器实现"""

import datetime
from typing import Any

import polars as pl

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
        """获取单只股票实时报价。

        Args:
            symbol: 股票代码

        Returns:
            Quote 对象
        """
        data = await self._get("/stable/quote", symbol=symbol)
        return Quote.model_validate(data)

    async def get_quotes(self, symbols: list[str]) -> pl.DataFrame:
        """批量获取股票报价。

        FMP stable API 无批量端点，逐个查询后合并。

        Args:
            symbols: 股票代码列表

        Returns:
            包含报价数据的 Polars DataFrame
        """
        records = []
        for sym in symbols:
            result = await self._get_list("/stable/quote", symbol=sym)
            records.extend(result)
        return self._to_df(records, Quote)

    async def get_price_history(
        self,
        symbol: str,
        start: datetime.date,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> pl.DataFrame:
        """获取历史价格数据。

        Args:
            symbol: 股票代码
            start: 开始日期
            end: 结束日期（可选）
            interval: K线周期（默认日线）
            adjusted: 是否复权（仅日线有效）

        Returns:
            包含历史价格数据的 Polars DataFrame
        """
        params: dict[str, Any] = {"symbol": symbol, "from": str(start)}
        if end:
            params["to"] = str(end)
        if interval in _INTRADAY_PATHS:
            path = f"/stable/{_INTRADAY_PATHS[interval]}"
        else:
            path = "/stable/historical-price-eod/full"
        records = await self._get_list(path, **params)
        return self._to_df(records, PriceBar)

    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> pl.DataFrame:
        """获取全市场快照。

        FMP Start 无全市场快照端点，返回空 DataFrame。

        Args:
            asset_class: 资产类别

        Returns:
            空 Polars DataFrame
        """
        return pl.DataFrame()
