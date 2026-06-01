import datetime

import pytest
from pytest_httpx import HTTPXMock

from deepalpha.domain.market.models import DividendEvent, EarningsEvent, IPOEvent, SplitEvent
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.calendar_loader import FMPCalendarLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


START = datetime.date(2024, 1, 1)
END = datetime.date(2024, 3, 31)


@pytest.mark.asyncio
async def test_get_earnings_calendar_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-02-01",
        "eps": 2.18, "epsEstimated": 2.10, "time": "amc", "revenueEstimated": 118000000000,
    }])
    loader = FMPCalendarLoader(client)
    result = await loader.get_earnings_calendar(START, END)
    assert isinstance(result, list)
    assert isinstance(result[0], EarningsEvent)
    assert result[0].symbol == "AAPL"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_dividend_calendar_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-02-09",
        "dividend": 0.24, "recordDate": "2024-02-12", "paymentDate": "2024-02-15",
    }])
    loader = FMPCalendarLoader(client)
    result = await loader.get_dividend_calendar(START, END)
    assert isinstance(result, list)
    assert isinstance(result[0], DividendEvent)
    assert result[0].dividend == 0.24
    await client.aclose()


@pytest.mark.asyncio
async def test_get_ipo_calendar_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NEWCO", "company": "New Company Inc.", "date": "2024-02-20",
        "exchange": "NASDAQ", "priceRange": "$10-$12", "shares": 10000000,
    }])
    loader = FMPCalendarLoader(client)
    result = await loader.get_ipo_calendar(START, END)
    assert isinstance(result, list)
    assert isinstance(result[0], IPOEvent)
    assert result[0].symbol == "NEWCO"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_splits_calendar_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "date": "2024-06-10", "numerator": 10.0, "denominator": 1.0,
    }])
    loader = FMPCalendarLoader(client)
    result = await loader.get_splits_calendar(START, END)
    assert isinstance(result, list)
    assert isinstance(result[0], SplitEvent)
    assert result[0].numerator == 10.0
    await client.aclose()
