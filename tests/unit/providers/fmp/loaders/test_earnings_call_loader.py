import datetime

import pytest
from pytest_httpx import HTTPXMock

from deepalpha.domain.earnings_call.models import EarningsCallEvent, EarningsCallTranscript
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.earnings_call_loader import (
    FMPEarningsCallLoader,
)

START = datetime.date(2026, 6, 1)
END = datetime.date(2026, 6, 30)


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_events_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"symbol": "AAPL", "date": "2026-06-14", "epsEstimated": None, "eps": None},
        {"symbol": "FAKECO", "date": "2026-06-14"},  # 不在 nasdaq100，会被过滤
    ])
    loader = FMPEarningsCallLoader(client, allowed_tickers=frozenset(["AAPL", "MSFT"]))
    events = await loader.get_events(START, END)
    assert len(events) == 1
    assert isinstance(events[0], EarningsCallEvent)
    assert events[0].symbol == "AAPL"
    # has_transcript：2026-06-14 (未来) > today 2026-06-13，故为 False
    assert events[0].has_transcript is False
    await client.aclose()


@pytest.mark.asyncio
async def test_get_transcript_returns_model(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL",
        "date": "2026-05-01",
        "year": 2026,
        "quarter": 2,
        "content": "Good morning everyone, welcome to Apple's Q2 2026 earnings call.",
    }])
    loader = FMPEarningsCallLoader(client, allowed_tickers=frozenset(["AAPL"]))
    result = await loader.get_transcript("AAPL", 2026, 2)
    assert isinstance(result, EarningsCallTranscript)
    assert result.symbol == "AAPL"
    assert result.quarter == 2
    assert "Apple" in result.content
    await client.aclose()


@pytest.mark.asyncio
async def test_get_transcript_returns_none_on_empty(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[])
    loader = FMPEarningsCallLoader(client, allowed_tickers=frozenset(["AAPL"]))
    result = await loader.get_transcript("AAPL", 2026, 3)
    assert result is None
    await client.aclose()