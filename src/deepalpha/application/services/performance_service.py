"""市场表现业务逻辑服务"""
from typing import Protocol

from deepalpha.domain.market.models import MarketMover, SectorPerformance
from deepalpha.domain.market.enums import MoverDirection


class IPerformanceProvider(Protocol):
    async def get_movers(self, direction: MoverDirection, limit: int = 20) -> list[MarketMover]: ...
    async def get_sector_performance(self) -> list[SectorPerformance]: ...


class PerformanceService:
    def __init__(self, provider: IPerformanceProvider) -> None:
        self._provider = provider

    async def get_gainers(self, limit: int = 10) -> list[MarketMover]:
        return await self._provider.get_movers(MoverDirection.GAINER, limit=limit)

    async def get_losers(self, limit: int = 10) -> list[MarketMover]:
        return await self._provider.get_movers(MoverDirection.LOSER, limit=limit)

    async def get_sector_performance(self) -> list[SectorPerformance]:
        return await self._provider.get_sector_performance()
