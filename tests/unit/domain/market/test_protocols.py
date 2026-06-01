"""market 领域 Protocol 满足测试"""
import datetime

from deepalpha.domain.market.protocols import IMarketProvider
from deepalpha.domain.market.models import Quote, PriceBar
from deepalpha.domain.market.enums import Interval, AssetClass


class _MockMarketProvider:
    async def get_quote(self, symbol: str) -> Quote: ...
    async def get_quotes(self, symbols: list[str]) -> list[Quote]: ...
    async def get_price_history(
        self,
        symbol: str,
        start: datetime.date,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> list[PriceBar]: ...
    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> list[Quote]: ...


def test_mock_market_provider_satisfies_protocol():
    assert isinstance(_MockMarketProvider(), IMarketProvider)
