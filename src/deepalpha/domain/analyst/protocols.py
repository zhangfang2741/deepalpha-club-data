"""analyst 领域端口协议"""
from typing import Protocol, runtime_checkable

from deepalpha.domain.financial.enums import StatementPeriod
from .models import AnalystRating, Estimate, PriceTarget


@runtime_checkable
class IAnalystProvider(Protocol):
    """分析师数据提供者协议"""

    async def get_ratings(self, symbol: str) -> list[AnalystRating]:
        """获取分析师评级数据"""
        ...

    async def get_price_targets(self, symbol: str) -> list[PriceTarget]:
        """获取分析师价格目标列表"""
        ...

    async def get_estimates(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
    ) -> list[Estimate]:
        """获取分析师预测数据"""
        ...
