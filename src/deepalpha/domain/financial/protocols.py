"""financial 领域端口协议"""
from typing import Protocol, runtime_checkable

from .enums import StatementPeriod
from .models import BalanceSheet, CashFlow, FinancialRatio, IncomeStatement, KeyMetrics, Valuation


@runtime_checkable
class IFinancialProvider(Protocol):
    """财务数据提供者协议"""

    async def get_income_statement(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[IncomeStatement]:
        """获取利润表数据"""
        ...

    async def get_balance_sheet(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[BalanceSheet]:
        """获取资产负债表数据"""
        ...

    async def get_cash_flow_statement(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[CashFlow]:
        """获取现金流量表数据"""
        ...

    async def get_financial_ratios(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[FinancialRatio]:
        """获取财务比率数据"""
        ...

    async def get_key_metrics(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[KeyMetrics]:
        """获取关键财务指标数据"""
        ...

    async def get_valuation(self, symbol: str) -> Valuation:
        """获取公司估值数据"""
        ...
