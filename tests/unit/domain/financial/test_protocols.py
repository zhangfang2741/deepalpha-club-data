"""financial 领域 Protocol 满足测试"""
from deepalpha.domain.financial.protocols import IFinancialProvider
from deepalpha.domain.financial.models import (
    BalanceSheet,
    CashFlow,
    FinancialRatio,
    IncomeStatement,
    KeyMetrics,
    Valuation,
)
from deepalpha.domain.financial.enums import StatementPeriod


class _MockFinancialProvider:
    async def get_income_statement(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[IncomeStatement]: ...

    async def get_balance_sheet(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[BalanceSheet]: ...

    async def get_cash_flow_statement(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[CashFlow]: ...

    async def get_financial_ratios(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[FinancialRatio]: ...

    async def get_key_metrics(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[KeyMetrics]: ...

    async def get_valuation(self, symbol: str) -> Valuation: ...


def test_mock_financial_provider_satisfies_protocol():
    assert isinstance(_MockFinancialProvider(), IFinancialProvider)
