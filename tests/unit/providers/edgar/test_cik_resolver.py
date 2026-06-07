import httpx
import pytest
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver


async def test_resolve_known_ticker(httpx_mock):
    httpx_mock.add_response(
        url="https://www.sec.gov/files/company_tickers.json",
        json={
            "0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
            "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
        },
    )
    async with httpx.AsyncClient() as client:
        resolver = CikResolver(client)
        assert await resolver.resolve("NVDA") == "0001045810"
        assert await resolver.resolve("nvda") == "0001045810"  # 大小写不敏感


async def test_resolve_unknown_returns_none(httpx_mock):
    httpx_mock.add_response(
        url="https://www.sec.gov/files/company_tickers.json",
        json={"0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"}},
    )
    async with httpx.AsyncClient() as client:
        resolver = CikResolver(client)
        assert await resolver.resolve("UNKNOWN") is None
