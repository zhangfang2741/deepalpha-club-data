from abc import abstractmethod
import datetime
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass, Interval
from deepalpha.models.market import Quote

class AbstractMarketLoader(BaseLoader):
    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote: ...
    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> pl.DataFrame: ...
    @abstractmethod
    async def get_price_history(
        self, symbol: str, start: datetime.date, end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY, adjusted: bool = True,
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> pl.DataFrame: ...
