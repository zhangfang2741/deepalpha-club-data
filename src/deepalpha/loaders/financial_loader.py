from abc import abstractmethod

import polars as pl

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.financial import Valuation


class AbstractFinancialLoader(BaseLoader):
    @abstractmethod
    async def get_income_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_balance_sheet(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_cash_flow_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_financial_ratios(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_key_metrics(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_valuation(self, symbol: str) -> Valuation: ...
