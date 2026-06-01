"""market 领域端口协议"""
import datetime
from typing import Protocol, runtime_checkable

from .enums import AssetClass, Interval
from .models import PriceBar, Quote


@runtime_checkable
class IMarketProvider(Protocol):
    """市场数据提供者协议"""

    async def get_quote(self, symbol: str) -> Quote:
        """获取单个股票实时行情"""
        ...

    async def get_quotes(self, symbols: list[str]) -> list[Quote]:
        """批量获取股票实时行情"""
        ...

    async def get_price_history(
        self,
        symbol: str,
        start: datetime.date,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> list[PriceBar]:
        """获取股票价格历史数据"""
        ...

    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> list[Quote]:
        """获取市场快照（涨跌榜、最活跃等）"""
        ...
