"""FMP 财务数据加载器实现"""

import polars as pl
from deepalpha.loaders.financial_loader import AbstractFinancialLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.financial import (
    IncomeStatement,
    BalanceSheet,
    CashFlow,
    FinancialRatio,
    KeyMetrics,
    Valuation,
)


# TTM 端点映射：(标准端点, TTM端点)
_TTM_PATHS: dict[str, tuple[str, str]] = {
    "income": ("income-statement", "income-statements-ttm"),
    "balance": ("balance-sheet-statement", "balance-sheet-statements-ttm"),
    "cashflow": ("cashflow-statement", "cashflow-statements-ttm"),
    "ratios": ("metrics-ratios", "metrics-ratios-ttm"),
    "metrics": ("key-metrics", "key-metrics-ttm"),
}


def _resolve_path(key: str, period: StatementPeriod) -> tuple[str, dict]:
    """根据报告期解析端点和参数。

    Args:
        key: 数据类型 key（income/balance/cashflow/ratios/metrics）
        period: 报告期（ANNUAL/QUARTER/TTM）

    Returns:
        (端点名称, 额外参数字典) 元组
    """
    normal, ttm = _TTM_PATHS[key]
    if period == StatementPeriod.TTM:
        return ttm, {}
    return normal, {"period": period.value}


class FMPFinancialLoader(AbstractFinancialLoader):
    """FMP 财务数据加载器。

    实现 AbstractFinancialLoader 接口，通过 FMP API 获取财务数据。
    支持年度、季度、TTM 等多种报告期。
    """

    async def get_income_statement(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> pl.DataFrame:
        """获取收入声明（损益表）。

        Args:
            symbol: 股票代码
            period: 报告期（默认年度）
            limit: 返回记录数（TTM 模式下忽略）

        Returns:
            包含收入数据的 Polars DataFrame
        """
        path, extra = _resolve_path("income", period)
        params = {**extra}
        if period != StatementPeriod.TTM:
            params["limit"] = limit
        records = await self._get_list(f"/stable/{path}/{symbol}", **params)
        return self._to_df(records, IncomeStatement)

    async def get_balance_sheet(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> pl.DataFrame:
        """获取资产负债表。

        Args:
            symbol: 股票代码
            period: 报告期（默认年度）
            limit: 返回记录数（TTM 模式下忽略）

        Returns:
            包含资产负债表数据的 Polars DataFrame
        """
        path, extra = _resolve_path("balance", period)
        params = {**extra}
        if period != StatementPeriod.TTM:
            params["limit"] = limit
        records = await self._get_list(f"/stable/{path}/{symbol}", **params)
        return self._to_df(records, BalanceSheet)

    async def get_cash_flow_statement(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> pl.DataFrame:
        """获取现金流量表。

        Args:
            symbol: 股票代码
            period: 报告期（默认年度）
            limit: 返回记录数（TTM 模式下忽略）

        Returns:
            包含现金流数据的 Polars DataFrame
        """
        path, extra = _resolve_path("cashflow", period)
        params = {**extra}
        if period != StatementPeriod.TTM:
            params["limit"] = limit
        records = await self._get_list(f"/stable/{path}/{symbol}", **params)
        return self._to_df(records, CashFlow)

    async def get_financial_ratios(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> pl.DataFrame:
        """获取财务比率。

        Args:
            symbol: 股票代码
            period: 报告期（默认年度）
            limit: 返回记录数（TTM 模式下忽略）

        Returns:
            包含财务比率数据的 Polars DataFrame
        """
        path, extra = _resolve_path("ratios", period)
        params = {**extra}
        if period != StatementPeriod.TTM:
            params["limit"] = limit
        records = await self._get_list(f"/stable/{path}/{symbol}", **params)
        return self._to_df(records, FinancialRatio)

    async def get_key_metrics(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> pl.DataFrame:
        """获取关键指标。

        Args:
            symbol: 股票代码
            period: 报告期（默认年度）
            limit: 返回记录数（TTM 模式下忽略）

        Returns:
            包含关键指标数据的 Polars DataFrame
        """
        path, extra = _resolve_path("metrics", period)
        params = {**extra}
        if period != StatementPeriod.TTM:
            params["limit"] = limit
        records = await self._get_list(f"/stable/{path}/{symbol}", **params)
        return self._to_df(records, KeyMetrics)

    async def get_valuation(self, symbol: str) -> Valuation:
        """获取公司估值。

        Args:
            symbol: 股票代码

        Returns:
            包含 DCF 估值和当前股价的 Valuation 对象
        """
        data = await self._get(f"/stable/dcf-advanced/{symbol}")
        return Valuation.model_validate(data)
