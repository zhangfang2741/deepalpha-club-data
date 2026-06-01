"""市场行情业务逻辑服务"""
import datetime

from deepalpha.domain.market.enums import Interval
from deepalpha.domain.market.models import PriceBar, Quote
from deepalpha.domain.market.protocols import IMarketProvider


class MarketService:
    def __init__(self, provider: IMarketProvider) -> None:
        self._provider = provider

    async def get_quote(self, symbol: str) -> Quote:
        return await self._provider.get_quote(symbol)

    async def get_price_history(
        self, symbol: str,
        start: datetime.date,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY,
    ) -> list[PriceBar]:
        return await self._provider.get_price_history(symbol, start, end, interval)
