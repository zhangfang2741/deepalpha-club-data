from abc import abstractmethod
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import StatementPeriod

class AbstractAnalystLoader(BaseLoader):
    @abstractmethod
    async def get_ratings(self, symbol: str) -> pl.DataFrame: ...
    @abstractmethod
    async def get_price_targets(self, symbol: str) -> pl.DataFrame: ...
    @abstractmethod
    async def get_estimates(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL
    ) -> pl.DataFrame: ...
