import asyncio
import time
from typing import Any

import httpx

from deepalpha.core.logging import log_call
from deepalpha.infrastructure.providers.finnhub.config import FinnhubConfig


class FinnhubClient:
    """Finnhub HTTP 客户端，内置令牌桶限速（免费版 60次/分钟）。"""

    def __init__(self, config: FinnhubConfig) -> None:
        self._config = config
        self._http = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self._last_request_at: float = 0.0

    @log_call("finnhub")
    async def _get(self, path: str, **params: Any) -> Any:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._config.rate_limit_interval:
            await asyncio.sleep(self._config.rate_limit_interval - elapsed)
        response = await self._http.get(path, params={"token": self._config.finnhub_api_key, **params})
        response.raise_for_status()
        self._last_request_at = time.monotonic()
        return response.json()

    async def get_etf_profile(self, symbol: str) -> dict[str, Any]:
        """获取 ETF 概况（含 mktCap 字段，单位美元）。"""
        return await self._get("/api/v1/stock/profile2", symbol=symbol)

    async def get_etf_holdings(self, symbol: str) -> list[dict[str, Any]]:
        """获取 ETF 全量持仓列表。"""
        data = await self._get("/api/v1/etf/holdings", symbol=symbol)
        if isinstance(data, dict):
            return data.get("holdings", [])
        return []

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "FinnhubClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
