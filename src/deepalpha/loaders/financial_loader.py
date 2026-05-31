from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.financial import (
    BalanceSheet,
    CashFlow,
    FinancialRatio,
    IncomeStatement,
    KeyMetrics,
    Valuation,
)


class AbstractFinancialLoader(BaseLoader):
    @abstractmethod
    async def get_income_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> list[IncomeStatement]: ...
    @abstractmethod
    async def get_balance_sheet(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> list[BalanceSheet]: ...
    @abstractmethod
    async def get_cash_flow_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> list[CashFlow]: ...
    @abstractmethod
    async def get_financial_ratios(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> list[FinancialRatio]: ...
    @abstractmethod
    async def get_key_metrics(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> list[KeyMetrics]: ...
    @abstractmethod
    async def get_valuation(self, symbol: str) -> Valuation: ...
