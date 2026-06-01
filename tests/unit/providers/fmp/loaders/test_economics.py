import pytest
from pytest_httpx import HTTPXMock

from deepalpha.models.indicators import IndicatorRow
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.economics_loader import FMPEconomicsLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_cpi_indicator_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"name": "CPI", "date": "2024-03-01", "value": 313.5},
        {"name": "CPI", "date": "2024-02-01", "value": 311.2},
    ])
    loader = FMPEconomicsLoader(client)
    result = await loader.get_indicator("CPI")
    assert isinstance(result, list)
    assert isinstance(result[0], IndicatorRow)
    assert result[0].value == 313.5
    await client.aclose()

@pytest.mark.asyncio
async def test_get_indicator_not_found_returns_empty_list(httpx_mock: HTTPXMock, client):
    from deepalpha.infrastructure.providers.fmp.errors import FMPNotFoundError
    httpx_mock.add_exception(FMPNotFoundError("not found"))
    loader = FMPEconomicsLoader(client)
    result = await loader.get_indicator("UNKNOWN")
    assert result == []
    await client.aclose()

@pytest.mark.asyncio
async def test_get_available_indicators_returns_list(client):
    loader = FMPEconomicsLoader(client)
    indicators = await loader.get_available_indicators()
    assert isinstance(indicators, list)
    assert "CPI" in indicators
    await client.aclose()
