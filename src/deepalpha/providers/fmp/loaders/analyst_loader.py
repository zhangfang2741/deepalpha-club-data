"""FMP 分析师数据加载器实现"""

from typing import Any

from deepalpha.loaders.analyst_loader import AbstractAnalystLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.analyst import AnalystRating, Estimate, PriceTarget


class FMPAnalystLoader(AbstractAnalystLoader):
    """FMP 分析师数据加载器。

    实现 AbstractAnalystLoader 接口，通过 FMP stable API 获取分析师数据。
    所有端点使用 ?symbol=X 查询参数格式。
    """

    async def get_ratings(self, symbol: str) -> list[AnalystRating]:
        """获取分析师评级。

        Args:
            symbol: 股票代码

        Returns:
            AnalystRating 领域对象列表
        """
        records = await self._get_list("/stable/ratings-snapshot", symbol=symbol)
        return self._to_models(records, AnalystRating)

    async def get_price_targets(self, symbol: str) -> list[PriceTarget]:
        """获取价格目标。

        Args:
            symbol: 股票代码

        Returns:
            PriceTarget 领域对象列表
        """
        data = await self._get("/stable/price-target-summary", symbol=symbol)
        return self._to_models([data], PriceTarget)

    async def get_estimates(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL
    ) -> list[Estimate]:
        """获取分析师预测。

        Args:
            symbol: 股票代码
            period: 财报周期（默认为年度）

        Returns:
            Estimate 领域对象列表
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value}
        records = await self._get_list("/stable/analyst-estimates", **params)
        return self._to_models(records, Estimate)
