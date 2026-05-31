from abc import abstractmethod
import datetime
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import Interval

class AbstractEconomicsLoader(BaseLoader):
    @abstractmethod
    async def get_indicator(
        self,
        indicator_name: str,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_MONTH,
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_available_indicators(self) -> list[str]: ...
