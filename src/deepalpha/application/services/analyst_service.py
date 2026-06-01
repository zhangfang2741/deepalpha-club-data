"""分析师数据业务逻辑服务"""
from deepalpha.domain.analyst.models import AnalystRating, Estimate, PriceTarget
from deepalpha.domain.analyst.protocols import IAnalystProvider
from deepalpha.domain.financial.enums import StatementPeriod


class AnalystService:
    def __init__(self, provider: IAnalystProvider) -> None:
        self._provider = provider

    async def get_ratings(self, symbol: str) -> list[AnalystRating]:
        return await self._provider.get_ratings(symbol)

    async def get_price_targets(self, symbol: str) -> list[PriceTarget]:
        return await self._provider.get_price_targets(symbol)

    async def get_estimates(self, symbol: str) -> list[Estimate]:
        return await self._provider.get_estimates(symbol, period=StatementPeriod.ANNUAL)
