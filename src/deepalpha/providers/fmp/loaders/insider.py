import polars as pl
from deepalpha.loaders.insider import AbstractInsiderTradeLoader
from deepalpha.models.insider import InsiderTrade, InsiderStatistics


class FMPInsiderTradeLoader(AbstractInsiderTradeLoader):
    """FMP 内部人交易数据加载器。"""

    async def get_insider_trades(
        self, symbol: str | None = None, limit: int = 50, page: int = 0
    ) -> pl.DataFrame:
        """获取内部人交易记录。

        Args:
            symbol: 股票代码（可选）
            limit: 分页大小，默认 50
            page: 分页索引，默认 0

        Returns:
            内部人交易记录 DataFrame
        """
        if symbol:
            records = await self._get_list(
                "/stable/search-insider-trades",
                symbol=symbol, limit=limit, page=page,
            )
        else:
            records = await self._get_list(
                "/stable/latest-insider-trade", limit=limit, page=page
            )
        return self._to_df(records, InsiderTrade)

    async def get_insider_statistics(self, symbol: str) -> InsiderStatistics:
        """获取内部人交易统计数据。

        Args:
            symbol: 股票代码

        Returns:
            InsiderStatistics 对象
        """
        data = await self._get(f"/stable/insider-trade-statistics/{symbol}")
        return InsiderStatistics.model_validate(data)
