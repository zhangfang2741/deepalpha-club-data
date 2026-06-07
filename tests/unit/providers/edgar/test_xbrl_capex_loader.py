import datetime
import httpx
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver
from deepalpha.infrastructure.providers.edgar.xbrl_capex_loader import XbrlCapexLoader

_TICKERS_JSON = {"0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"}}

_FACTS = {
    "facts": {
        "us-gaap": {
            "PaymentsToAcquirePropertyPlantAndEquipment": {
                "units": {
                    "USD": [
                        {"end": "2026-04-30", "val": 3_500_000_000, "form": "10-Q", "filed": "2026-06-05", "frame": "CY2026Q1I"}
                    ]
                }
            }
        }
    }
}


async def test_fetch_capex_signal(httpx_mock):
    httpx_mock.add_response(url="https://www.sec.gov/files/company_tickers.json", json=_TICKERS_JSON)
    httpx_mock.add_response(url="https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json", json=_FACTS)
    async with httpx.AsyncClient() as client:
        loader = XbrlCapexLoader(client, CikResolver(client))
        items = await loader.fetch("NVDA", since=datetime.date(2026, 6, 1))
    assert len(items) == 1
    assert items[0].source_type == "capex"
    assert "3,500,000,000" in items[0].text_snippet


async def test_fetch_capex_skips_old_filings(httpx_mock):
    old_facts = {
        "facts": {"us-gaap": {"PaymentsToAcquirePropertyPlantAndEquipment": {
            "units": {"USD": [{"end": "2024-01-31", "val": 1_000_000_000, "form": "10-Q", "filed": "2024-03-01", "frame": "CY2023Q4I"}]}
        }}}
    }
    httpx_mock.add_response(url="https://www.sec.gov/files/company_tickers.json", json=_TICKERS_JSON)
    httpx_mock.add_response(url="https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json", json=old_facts)
    async with httpx.AsyncClient() as client:
        loader = XbrlCapexLoader(client, CikResolver(client))
        items = await loader.fetch("NVDA", since=datetime.date(2026, 6, 1))
    assert items == []
