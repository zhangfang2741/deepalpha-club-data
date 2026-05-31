import polars as pl
from deepalpha.loaders.analyst_loader import AbstractAnalystLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.analyst import AnalystRating, PriceTarget, Estimate


class FMPAnalystLoader(AbstractAnalystLoader):
    """FMP 分析师数据加载器。"""

    async def get_ratings(self, symbol: str) -> pl.DataFrame:
        """获取分析师评级。

        Args:
            symbol: 股票代码

        Returns:
            分析师评级 DataFrame
        """
        records = await self._get_list(f"/stable/historical-ratings/{symbol}")
        return self._to_df(records, AnalystRating)

    async def get_price_targets(self, symbol: str) -> pl.DataFrame:
        """获取价格目标。

        Args:
            symbol: 股票代码

        Returns:
            价格目标 DataFrame
        """
        data = await self._get(f"/stable/price-target-summary/{symbol}")
        return self._to_df([data], PriceTarget)

    async def get_estimates(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL
    ) -> pl.DataFrame:
        """获取分析师预测。

        Args:
            symbol: 股票代码
            period: 财报周期（默认为年度）

        Returns:
            分析师预测 DataFrame
        """
        params = {} if period == StatementPeriod.TTM else {"period": period.value}
        records = await self._get_list(f"/stable/financial-estimates/{symbol}", **params)
        return self._to_df(records, Estimate)
