import polars as pl
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.models.filings import SecCompanyProfile
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.filings_loader import FMPSecFilingLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_filings_by_symbol(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "filingDate": "2024-05-02", "acceptedDate": "2024-05-02",
        "type": "10-Q", "link": "https://sec.gov/filing/aapl-10q.htm",
    }])
    loader = FMPSecFilingLoader(client)
    df = await loader.get_filings(symbol="AAPL", form_type="10-Q")
    assert isinstance(df, pl.DataFrame)
    assert "type" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sec_profile(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json={
        "cik": "0000320193", "symbol": "AAPL", "companyName": "Apple Inc.",
        "sic": "3674", "stateOfIncorporation": "CA", "fiscalYearEnd": "09",
    })
    loader = FMPSecFilingLoader(client)
    profile = await loader.get_sec_profile("AAPL")
    assert isinstance(profile, SecCompanyProfile)
    assert profile.cik == "0000320193"
    await client.aclose()
