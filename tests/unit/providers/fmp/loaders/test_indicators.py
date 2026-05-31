import polars as pl
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import IndicatorType, Interval
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.errors import FMPError
from deepalpha.providers.fmp.loaders.indicators_loader import FMPTechnicalIndicatorLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_sma_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-05-02", "value": 183.5, "open": 185.0, "high": 186.0, "low": 182.0, "close": 185.5, "volume": 50000000},
    ])
    loader = FMPTechnicalIndicatorLoader(client)
    df = await loader.get_indicator("AAPL", IndicatorType.SMA, period=20)
    assert isinstance(df, pl.DataFrame)
    assert "value" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_rsi_with_interval(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-05-02", "value": 62.3, "open": 185.0, "high": 186.0, "low": 182.0, "close": 185.5, "volume": 50000000},
    ])
    loader = FMPTechnicalIndicatorLoader(client)
    df = await loader.get_indicator(
        "AAPL", IndicatorType.RSI, period=14, interval=Interval.ONE_HOUR
    )
    assert isinstance(df, pl.DataFrame)
    assert "value" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_unsupported_indicator_raises_fmp_error(httpx_mock: HTTPXMock, client):
    loader = FMPTechnicalIndicatorLoader(client)
    with pytest.raises(FMPError):
        await loader.get_indicator("AAPL", IndicatorType.MACD, period=12)
    await client.aclose()
