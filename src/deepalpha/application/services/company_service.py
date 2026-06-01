"""公司信息业务逻辑服务"""
from typing import Protocol

from deepalpha.domain.company.models import CompanyProfile, Executive


class ICompanyProvider(Protocol):
    async def get_profile(self, symbol: str) -> CompanyProfile: ...
    async def get_executives(self, symbol: str) -> list[Executive]: ...
    async def get_peers(self, symbol: str) -> list[str]: ...


class CompanyService:
    def __init__(self, provider: ICompanyProvider) -> None:
        self._provider = provider

    async def get_profile(self, symbol: str) -> CompanyProfile:
        return await self._provider.get_profile(symbol)

    async def get_executives(self, symbol: str) -> list[Executive]:
        return await self._provider.get_executives(symbol)

    async def get_peers(self, symbol: str) -> list[str]:
        return await self._provider.get_peers(symbol)
