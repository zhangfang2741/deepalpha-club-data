import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import MoverDirection
from deepalpha.models.performance import MarketMover, SectorPE, SectorPerformance


class AbstractMarketPerformanceLoader(BaseLoader):
    @abstractmethod
    async def get_movers(
        self, direction: MoverDirection, limit: int = 20
    ) -> list[MarketMover]: ...
    @abstractmethod
    async def get_sector_performance(self, date: datetime.date | None = None) -> list[SectorPerformance]: ...
    @abstractmethod
    async def get_sector_pe(self, date: datetime.date | None = None) -> list[SectorPE]: ...
