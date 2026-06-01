"""财务数据业务逻辑服务"""
from deepalpha.domain.financial.enums import StatementPeriod
from deepalpha.domain.financial.models import (
    BalanceSheet, CashFlow, FinancialRatio,
    IncomeStatement, KeyMetrics, Valuation,
)
from deepalpha.domain.financial.protocols import IFinancialProvider


class FinancialService:
    def __init__(self, provider: IFinancialProvider) -> None:
        self._provider = provider

    async def get_latest_income(self, symbol: str) -> IncomeStatement | None:
        stmts = await self._provider.get_income_statement(
            symbol, period=StatementPeriod.ANNUAL, limit=1
        )
        return stmts[0] if stmts else None

    async def get_income_statements(self, symbol: str, limit: int = 4) -> list[IncomeStatement]:
        return await self._provider.get_income_statement(
            symbol, period=StatementPeriod.ANNUAL, limit=limit
        )

    async def get_balance_sheet(self, symbol: str) -> BalanceSheet | None:
        rows = await self._provider.get_balance_sheet(
            symbol, period=StatementPeriod.ANNUAL, limit=1
        )
        return rows[0] if rows else None

    async def get_cash_flow(self, symbol: str) -> CashFlow | None:
        rows = await self._provider.get_cash_flow_statement(
            symbol, period=StatementPeriod.ANNUAL, limit=1
        )
        return rows[0] if rows else None

    async def get_financial_ratios(self, symbol: str) -> FinancialRatio | None:
        rows = await self._provider.get_financial_ratios(
            symbol, period=StatementPeriod.ANNUAL, limit=1
        )
        return rows[0] if rows else None

    async def get_key_metrics(self, symbol: str) -> KeyMetrics | None:
        rows = await self._provider.get_key_metrics(
            symbol, period=StatementPeriod.ANNUAL, limit=1
        )
        return rows[0] if rows else None

    async def get_valuation(self, symbol: str) -> Valuation:
        return await self._provider.get_valuation(symbol)
