"""company 领域端口协议"""
import datetime
from typing import Protocol, runtime_checkable

from .models import CompanyProfile, Executive, MarketCapRecord


@runtime_checkable
class ICompanyProvider(Protocol):
    """公司数据提供者协议"""

    async def get_profile(self, symbol: str) -> CompanyProfile:
        """获取公司概况"""
        ...

    async def get_executives(self, symbol: str) -> list[Executive]:
        """获取公司高管名单"""
        ...

    async def get_peers(self, symbol: str) -> list[str]:
        """获取同业竞争公司"""
        ...

    async def get_market_cap(
        self,
        symbol: str,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[MarketCapRecord]:
        """获取市值历史数据"""
        ...
