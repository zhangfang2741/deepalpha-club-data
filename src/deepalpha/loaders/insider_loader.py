from abc import abstractmethod
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.models.insider import InsiderStatistics

class AbstractInsiderTradeLoader(BaseLoader):
    @abstractmethod
    async def get_insider_trades(
        self, symbol: str | None = None, limit: int = 50, page: int = 0
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_insider_statistics(self, symbol: str) -> InsiderStatistics: ...
