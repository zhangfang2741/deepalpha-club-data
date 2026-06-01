"""company 领域 Protocol 满足测试"""
import datetime

from deepalpha.domain.company.protocols import ICompanyProvider
from deepalpha.domain.company.models import CompanyProfile, Executive, MarketCapRecord


class _MockCompanyProvider:
    async def get_profile(self, symbol: str) -> CompanyProfile: ...

    async def get_executives(self, symbol: str) -> list[Executive]: ...

    async def get_peers(self, symbol: str) -> list[str]: ...

    async def get_market_cap(
        self,
        symbol: str,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[MarketCapRecord]: ...


def test_mock_company_provider_satisfies_protocol():
    assert isinstance(_MockCompanyProvider(), ICompanyProvider)
