"""FMP 市场表现数据加载器实现"""

import datetime

import polars as pl

from deepalpha.loaders.enums import MoverDirection
from deepalpha.loaders.performance_loader import AbstractMarketPerformanceLoader
from deepalpha.models.performance import MarketMover, SectorPE, SectorPerformance

_MOVER_PATHS: dict[MoverDirection, str] = {
    MoverDirection.GAINERS: "biggest-gainers",
    MoverDirection.LOSERS:  "biggest-losers",
    MoverDirection.ACTIVE:  "most-actives",
}


class FMPMarketPerformanceLoader(AbstractMarketPerformanceLoader):
    """FMP 市场表现加载器。

    实现 AbstractMarketPerformanceLoader 接口，通过 FMP stable API 获取市场表现数据。
    FMP Start 仅支持当日快照，历史数据需要 premium 订阅。
    """

    async def get_movers(
        self, direction: MoverDirection, limit: int = 20
    ) -> pl.DataFrame:
        """获取市场涨跌幅排行数据。

        Args:
            direction: 排行类型（涨幅榜/跌幅榜/成交量榜）
            limit: 排行数据条数，默认 20

        Returns:
            市场涨跌幅排行 DataFrame
        """
        path = _MOVER_PATHS[direction]
        records = await self._get_list(f"/stable/{path}", limit=limit)
        return self._to_df(records, MarketMover)

    async def get_sector_performance(self, date: datetime.date | None = None) -> pl.DataFrame:
        """获取板块表现数据。

        FMP Start 仅支持当日快照，历史数据需 premium。
        date 参数被忽略，始终返回最新快照。

        Args:
            date: 查询日期（可选，当前不支持历史数据）

        Returns:
            板块表现数据 DataFrame
        """
        records = await self._get_list("/stable/sector-performance-snapshot")
        return self._to_df(records, SectorPerformance)

    async def get_sector_pe(self, date: datetime.date | None = None) -> pl.DataFrame:
        """获取板块市盈率数据。

        FMP Start 仅支持当日快照，历史数据需 premium。
        date 参数被忽略，始终返回最新快照。

        Args:
            date: 查询日期（可选，当前不支持历史数据）

        Returns:
            板块市盈率数据 DataFrame
        """
        records = await self._get_list("/stable/sector-pe-snapshot")
        return self._to_df(records, SectorPE)
