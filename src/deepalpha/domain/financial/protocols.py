"""financial 领域端口协议"""
from typing import Protocol, runtime_checkable

from deepalpha.domain.market.enums import StatementPeriod
from .models import BalanceSheet, CashFlow, IncomeStatement


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

    async def get_cash_flow(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[CashFlow]:
        """获取现金流量表数据"""
        ...
