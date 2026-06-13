"""earnings_call 领域 Protocol 满足测试"""
import datetime
from deepalpha.domain.earnings_call.protocols import (
    IEarningsCallLoader,
    IEarningsCallRepo,
)
from deepalpha.domain.earnings_call.models import (
    EarningsCallDetail,
    EarningsCallEvent,
    EarningsCallTranscript,
)


class _MockEarningsCallLoader:
    async def get_events(
        self, start: datetime.date, end: datetime.date
    ) -> list[EarningsCallEvent]:
        ...

    async def get_transcript(
        self, symbol: str, year: int, quarter: int
    ) -> EarningsCallTranscript | None:
        ...


class _MockEarningsCallRepo:
    async def get_detail(
        self, symbol: str, year: int, quarter: int
    ) -> EarningsCallDetail | None:
        ...

    async def save_detail(self, detail: EarningsCallDetail) -> None:
        ...


def test_mock_satisfies_loader_protocol():
    assert isinstance(_MockEarningsCallLoader(), IEarningsCallLoader)


def test_mock_satisfies_repo_protocol():
    assert isinstance(_MockEarningsCallRepo(), IEarningsCallRepo)
