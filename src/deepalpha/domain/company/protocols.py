"""company 领域端口协议"""
from typing import Protocol, runtime_checkable

from .models import CompanyProfile


@runtime_checkable
class ICompanyProvider(Protocol):
    """公司数据提供者协议"""

    async def get_profile(self, symbol: str) -> CompanyProfile:
        """获取公司概况"""
        ...

    async def get_peers(self, symbol: str) -> list[str]:
        """获取同业竞争公司"""
        ...
