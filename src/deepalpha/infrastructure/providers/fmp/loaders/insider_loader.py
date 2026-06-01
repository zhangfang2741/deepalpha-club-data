from deepalpha.infrastructure.providers.base import BaseLoader
from deepalpha.models.insider import InsiderStatistics, InsiderTrade


class FMPInsiderTradeLoader(BaseLoader):
    """FMP 内部人交易数据加载器。"""

    async def get_insider_trades(
        self, symbol: str | None = None, limit: int = 50, page: int = 0
    ) -> list[InsiderTrade]:
        """获取内部人交易记录。

        Args:
            symbol: 股票代码（可选）
            limit: 分页大小，默认 50
            page: 分页索引，默认 0

        Returns:
            InsiderTrade 领域对象列表
        """
        from deepalpha.infrastructure.providers.fmp.errors import FMPNotFoundError
        try:
            if symbol:
                records = await self._get_list(
                    "/stable/insider-trades-search",
                    symbol=symbol, limit=limit, page=page,
                )
            else:
                records = await self._get_list(
                    "/stable/insider-trades-latest", limit=limit, page=page
                )
        except FMPNotFoundError:
            return []
        return self._to_models(records, InsiderTrade)

    async def get_insider_statistics(self, symbol: str) -> list[InsiderStatistics]:
        """获取内部人交易季度统计数据。

        Args:
            symbol: 股票代码

        Returns:
            InsiderStatistics 领域对象列表
        """
        from deepalpha.infrastructure.providers.fmp.errors import FMPNotFoundError
        try:
            records = await self._get_list(f"/stable/insider-trade-statistics/{symbol}")
        except FMPNotFoundError:
            return []
        return self._to_models(records, InsiderStatistics)
