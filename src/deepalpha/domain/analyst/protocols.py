"""analyst 领域端口协议"""
from typing import Protocol, runtime_checkable

from .models import AnalystRating, PriceTarget


@runtime_checkable
class IAnalystProvider(Protocol):
    """分析师数据提供者协议"""

    async def get_ratings(self, symbol: str) -> list[AnalystRating]:
        """获取分析师评级数据"""
        ...

    async def get_price_target(self, symbol: str) -> PriceTarget | None:
        """获取分析师价格目标"""
        ...
