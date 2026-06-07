import datetime
import httpx
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver
from deepalpha.infrastructure.providers.edgar.filing_8k_loader import Filing8KLoader

_TICKERS_JSON = {"0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"}}

_SUBMISSIONS = {
    "filings": {
        "recent": {
            "form":            ["8-K",                   "10-Q"],
            "accessionNumber": ["0001045810-26-000001",  "0001045810-26-000002"],
            "filingDate":      ["2026-06-06",            "2026-06-05"],
            "primaryDocument": ["nvda-20260606.htm",     "nvda-20260605.htm"],
        }
    }
}


async def test_fetch_returns_8k_only(httpx_mock):
    httpx_mock.add_response(url="https://www.sec.gov/files/company_tickers.json", json=_TICKERS_JSON)
    httpx_mock.add_response(url="https://data.sec.gov/submissions/CIK0001045810.json", json=_SUBMISSIONS)
    httpx_mock.add_response(
        url="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000001/nvda-20260606.htm",
        text="We are investing in HBM3e memory and liquid cooling infrastructure.",
    )
    async with httpx.AsyncClient() as client:
        loader = Filing8KLoader(client, CikResolver(client))
        items = await loader.fetch("NVDA", since=datetime.date(2026, 6, 5))
    assert len(items) == 1
    assert items[0].source_type == "earnings_call"
    assert "HBM3e" in items[0].text_snippet


async def test_fetch_unknown_ticker_returns_empty(httpx_mock):
    httpx_mock.add_response(url="https://www.sec.gov/files/company_tickers.json", json=_TICKERS_JSON)
    async with httpx.AsyncClient() as client:
        loader = Filing8KLoader(client, CikResolver(client))
        items = await loader.fetch("UNKNOWN", since=datetime.date(2026, 6, 5))
    assert items == []
