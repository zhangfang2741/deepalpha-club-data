"""analyst 领域 Protocol 满足测试"""
from deepalpha.domain.analyst.protocols import IAnalystProvider
from deepalpha.domain.analyst.models import AnalystRating, Estimate, PriceTarget
from deepalpha.domain.financial.enums import StatementPeriod


class _MockAnalystProvider:
    async def get_ratings(self, symbol: str) -> list[AnalystRating]: ...

    async def get_price_targets(self, symbol: str) -> list[PriceTarget]: ...

    async def get_estimates(
        self,
        symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
    ) -> list[Estimate]: ...


def test_mock_analyst_provider_satisfies_protocol():
    assert isinstance(_MockAnalystProvider(), IAnalystProvider)
