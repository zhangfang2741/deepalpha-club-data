"""财务数据业务逻辑服务"""
from deepalpha.domain.financial.enums import StatementPeriod
from deepalpha.domain.financial.models import IncomeStatement
from deepalpha.domain.financial.protocols import IFinancialProvider


class FinancialService:
    def __init__(self, provider: IFinancialProvider) -> None:
        self._provider = provider

    async def get_latest_income(self, symbol: str) -> IncomeStatement | None:
        stmts = await self._provider.get_income_statement(
            symbol, period=StatementPeriod.ANNUAL, limit=1
        )
        return stmts[0] if stmts else None
