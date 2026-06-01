"""分析师数据业务逻辑服务"""
from deepalpha.domain.analyst.models import AnalystRating, PriceTarget
from deepalpha.domain.analyst.protocols import IAnalystProvider


class AnalystService:
    def __init__(self, provider: IAnalystProvider) -> None:
        self._provider = provider

    async def get_ratings(self, symbol: str) -> list[AnalystRating]:
        return await self._provider.get_ratings(symbol)

    async def get_price_targets(self, symbol: str) -> list[PriceTarget]:
        return await self._provider.get_price_targets(symbol)
