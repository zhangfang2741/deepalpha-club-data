"""FMP 财务数据加载器实现"""

from typing import Any

import polars as pl

from deepalpha.loaders.enums import StatementPeriod
from deepalpha.loaders.financial_loader import AbstractFinancialLoader
from deepalpha.models.financial import (
    BalanceSheet,
    CashFlow,
    FinancialRatio,
    IncomeStatement,
    KeyMetrics,
    Valuation,
)


class FMPFinancialLoader(AbstractFinancialLoader):
    """FMP 财务数据加载器。

    实现 AbstractFinancialLoader 接口，通过 FMP stable API 获取财务数据。
    所有端点使用 ?symbol=X 查询参数格式。
    TTM 模式统一使用 period=ttm 参数，FMP 会返回最近数据。
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
            limit: 返回记录数

        Returns:
            包含收入数据的 Polars DataFrame
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/income-statement", **params)
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
            limit: 返回记录数

        Returns:
            包含资产负债表数据的 Polars DataFrame
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/balance-sheet-statement", **params)
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
            limit: 返回记录数

        Returns:
            包含现金流数据的 Polars DataFrame
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/cash-flow-statement", **params)
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
            limit: 返回记录数

        Returns:
            包含财务比率数据的 Polars DataFrame
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/ratios", **params)
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
            limit: 返回记录数

        Returns:
            包含关键指标数据的 Polars DataFrame
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/key-metrics", **params)
        return self._to_df(records, KeyMetrics)

    async def get_valuation(self, symbol: str) -> Valuation:
        """获取公司估值。

        Args:
            symbol: 股票代码

        Returns:
            包含 DCF 估值和当前股价的 Valuation 对象
        """
        data = await self._get("/stable/discounted-cash-flow", symbol=symbol)
        return Valuation.model_validate(data)
