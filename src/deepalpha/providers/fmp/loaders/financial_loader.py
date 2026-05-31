"""FMP 财务数据加载器实现"""

from typing import Any

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
    ) -> list[IncomeStatement]:
        """获取收入声明（损益表）。

        Args:
            symbol: 股票代码
            period: 报告期（默认年度）
            limit: 返回记录数

        Returns:
            IncomeStatement 领域对象列表
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/income-statement", **params)
        return self._to_models(records, IncomeStatement)

    async def get_balance_sheet(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[BalanceSheet]:
        """获取资产负债表。

        Args:
            symbol: 股票代码
            period: 报告期（默认年度）
            limit: 返回记录数

        Returns:
            BalanceSheet 领域对象列表
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/balance-sheet-statement", **params)
        return self._to_models(records, BalanceSheet)

    async def get_cash_flow_statement(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[CashFlow]:
        """获取现金流量表。

        Args:
            symbol: 股票代码
            period: 报告期（默认年度）
            limit: 返回记录数

        Returns:
            CashFlow 领域对象列表
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/cash-flow-statement", **params)
        return self._to_models(records, CashFlow)

    async def get_financial_ratios(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[FinancialRatio]:
        """获取财务比率。

        Args:
            symbol: 股票代码
            period: 报告期（默认年度）
            limit: 返回记录数

        Returns:
            FinancialRatio 领域对象列表
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/ratios", **params)
        return self._to_models(records, FinancialRatio)

    async def get_key_metrics(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[KeyMetrics]:
        """获取关键指标。

        Args:
            symbol: 股票代码
            period: 报告期（默认年度）
            limit: 返回记录数

        Returns:
            KeyMetrics 领域对象列表
        """
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/key-metrics", **params)
        return self._to_models(records, KeyMetrics)

    async def get_valuation(self, symbol: str) -> Valuation:
        """获取公司估值。

        Args:
            symbol: 股票代码

        Returns:
            包含 DCF 估值和当前股价的 Valuation 对象
        """
        data = await self._get("/stable/discounted-cash-flow", symbol=symbol)
        return Valuation.model_validate(data)
