import pytest
import polars as pl
from pytest_httpx import HTTPXMock
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.economics import FMPEconomicsLoader

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_cpi_indicator(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-03-01", "value": 3.5},
        {"date": "2024-02-01", "value": 3.2},
    ])
    loader = FMPEconomicsLoader(client)
    df = await loader.get_indicator("CPI")
    assert isinstance(df, pl.DataFrame)
    assert "value" in df.columns
    assert len(df) == 2
    await client.aclose()

@pytest.mark.asyncio
async def test_get_available_indicators_returns_list(httpx_mock: HTTPXMock, client):
    loader = FMPEconomicsLoader(client)
    indicators = await loader.get_available_indicators()
    assert isinstance(indicators, list)
    assert "CPI" in indicators
    await client.aclose()
