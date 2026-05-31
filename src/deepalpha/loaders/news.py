from abc import abstractmethod
import datetime
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass

class AbstractNewsLoader(BaseLoader):
    @abstractmethod
    async def get_news(
        self,
        symbols: list[str] | None = None,
        asset_class: AssetClass | None = None,
        limit: int = 20,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> pl.DataFrame: ...
