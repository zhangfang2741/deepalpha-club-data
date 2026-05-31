import datetime

import polars as pl
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.calendar_loader import FMPCalendarLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_earnings_calendar(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-05-02", "eps": 1.53,
        "epsEstimated": 1.50, "time": "amc", "revenueEstimated": 90000000000,
    }])
    loader = FMPCalendarLoader(client)
    df = await loader.get_earnings_calendar(datetime.date(2024, 5, 1), datetime.date(2024, 5, 31))
    assert isinstance(df, pl.DataFrame)
    assert "symbol" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_dividend_calendar(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-05-10", "dividend": 0.25,
        "recordDate": "2024-05-13", "paymentDate": "2024-05-16",
    }])
    loader = FMPCalendarLoader(client)
    df = await loader.get_dividend_calendar(datetime.date(2024, 5, 1), datetime.date(2024, 5, 31))
    assert isinstance(df, pl.DataFrame)
    assert "dividend" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_ipo_calendar(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "XYZ", "company": "XYZ Corp", "date": "2024-05-15",
        "exchange": "NASDAQ", "priceRange": "$10-$12", "shares": 5000000,
    }])
    loader = FMPCalendarLoader(client)
    df = await loader.get_ipo_calendar(datetime.date(2024, 5, 1), datetime.date(2024, 5, 31))
    assert isinstance(df, pl.DataFrame)
    assert "company" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_splits_calendar(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "date": "2024-06-10", "numerator": 10.0, "denominator": 1.0,
    }])
    loader = FMPCalendarLoader(client)
    df = await loader.get_splits_calendar(datetime.date(2024, 6, 1), datetime.date(2024, 6, 30))
    assert isinstance(df, pl.DataFrame)
    assert "numerator" in df.columns
    await client.aclose()
