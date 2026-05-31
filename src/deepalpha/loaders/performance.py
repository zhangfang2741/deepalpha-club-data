from abc import abstractmethod
import datetime
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import MoverDirection

class AbstractMarketPerformanceLoader(BaseLoader):
    @abstractmethod
    async def get_movers(
        self, direction: MoverDirection, limit: int = 20
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_sector_performance(self, date: datetime.date | None = None) -> pl.DataFrame: ...
    @abstractmethod
    async def get_sector_pe(self, date: datetime.date | None = None) -> pl.DataFrame: ...
