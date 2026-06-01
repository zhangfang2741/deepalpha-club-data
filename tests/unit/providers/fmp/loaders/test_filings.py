import pytest
from pytest_httpx import HTTPXMock

from deepalpha.domain.governance.models import SecCompanyProfile, SecFiling
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.filings_loader import FMPSecFilingLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_filings_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "filingDate": "2024-05-02", "acceptedDate": "2024-05-02",
        "formType": "10-Q", "link": "https://sec.gov/filing/aapl-10q.htm",
        "finalLink": "https://sec.gov/filing/aapl-10q-final.htm",
    }])
    loader = FMPSecFilingLoader(client)
    result = await loader.get_filings(symbol="AAPL", form_type="10-Q")
    assert isinstance(result, list)
    assert isinstance(result[0], SecFiling)
    assert result[0].form_type == "10-Q"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sec_profile_returns_profile(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "cik": "0000320193", "symbol": "AAPL",
        "registrantName": "Apple Inc.", "sicCode": "3674",
        "sicDescription": "Electronic Computers", "sicGroup": "Manufacturing",
    }])
    loader = FMPSecFilingLoader(client)
    profile = await loader.get_sec_profile("AAPL")
    assert isinstance(profile, SecCompanyProfile)
    assert profile.cik == "0000320193"
    await client.aclose()
