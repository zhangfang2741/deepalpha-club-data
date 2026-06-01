"""FMP 市场表现数据加载器实现"""

import datetime

from deepalpha.domain.market.enums import MoverDirection
from deepalpha.infrastructure.providers.base import BaseLoader
from deepalpha.domain.market.models import MarketMover, SectorPE, SectorPerformance

_MOVER_PATHS: dict[MoverDirection, str] = {
    MoverDirection.GAINERS: "biggest-gainers",
    MoverDirection.LOSERS:  "biggest-losers",
    MoverDirection.ACTIVE:  "most-actives",
}


class FMPMarketPerformanceLoader(BaseLoader):
    """FMP 市场表现加载器。

    实现 AbstractMarketPerformanceLoader 接口，通过 FMP stable API 获取市场表现数据。
    FMP Start 仅支持当日快照，历史数据需要 premium 订阅。
    """

    async def get_movers(
        self, direction: MoverDirection, limit: int = 20
    ) -> list[MarketMover]:
        """获取市场涨跌幅排行数据。

        Args:
            direction: 排行类型（涨幅榜/跌幅榜/成交量榜）
            limit: 排行数据条数，默认 20

        Returns:
            MarketMover 领域对象列表
        """
        path = _MOVER_PATHS[direction]
        records = await self._get_list(f"/stable/{path}", limit=limit)
        return self._to_models(records, MarketMover)

    async def get_sector_performance(self, date: datetime.date | None = None) -> list[SectorPerformance]:
        """获取板块表现数据。

        date=None 时使用今日日期，FMP Start 不支持历史日期（premium only）。

        Args:
            date: 查询日期，默认为今日

        Returns:
            SectorPerformance 领域对象列表
        """
        query_date = date or datetime.date.today()
        records = await self._get_list(
            "/stable/sector-performance-snapshot", date=str(query_date)
        )
        return self._to_models(records, SectorPerformance)

    async def get_sector_pe(self, date: datetime.date | None = None) -> list[SectorPE]:
        """获取板块市盈率数据。

        date=None 时使用今日日期，FMP Start 不支持历史日期（premium only）。

        Args:
            date: 查询日期，默认为今日

        Returns:
            SectorPE 领域对象列表
        """
        query_date = date or datetime.date.today()
        records = await self._get_list(
            "/stable/sector-pe-snapshot", date=str(query_date)
        )
        return self._to_models(records, SectorPE)
