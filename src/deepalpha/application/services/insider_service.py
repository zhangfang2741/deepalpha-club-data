"""内幕交易业务逻辑服务"""
from typing import Protocol

from deepalpha.domain.governance.models import InsiderTrade, CongressTrade


class IInsiderProvider(Protocol):
    async def get_insider_trades(self, symbol: str | None, limit: int, page: int) -> list[InsiderTrade]: ...


class ICongressProvider(Protocol):
    async def get_congress_trades(self, symbol: str | None, limit: int, page: int) -> list[CongressTrade]: ...


class InsiderService:
    def __init__(self, insider: IInsiderProvider, congress: ICongressProvider) -> None:
        self._insider = insider
        self._congress = congress

    async def get_insider_trades(self, symbol: str, limit: int = 20) -> list[InsiderTrade]:
        return await self._insider.get_insider_trades(symbol=symbol.upper(), limit=limit, page=0)

    async def get_congress_trades(self, symbol: str, limit: int = 20) -> list[CongressTrade]:
        return await self._congress.get_congress_trades(symbol=symbol.upper(), limit=limit, page=0)
