from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.models.insider import InsiderStatistics, InsiderTrade


class AbstractInsiderTradeLoader(BaseLoader):
    @abstractmethod
    async def get_insider_trades(
        self, symbol: str | None = None, limit: int = 50, page: int = 0
    ) -> list[InsiderTrade]: ...
    @abstractmethod
    async def get_insider_statistics(self, symbol: str) -> list[InsiderStatistics]: ...
