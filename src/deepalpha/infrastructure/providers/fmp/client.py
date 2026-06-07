import asyncio
from typing import Any

import httpx

from deepalpha.core.logging import log_call
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.errors import (
    FMPAuthError,
    FMPError,
    FMPNotFoundError,
    FMPRateLimitError,
    FMPServerError,
)


class FMPAsyncClient:
    def __init__(self, config: FMPConfig) -> None:
        self._config = config
        self._http = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            limits=httpx.Limits(max_connections=config.max_connections),
        )

    @log_call("fmp", passthrough=(FMPError,))
    async def get(self, path: str, **params: Any) -> Any:
        params["apikey"] = self._config.api_key
        delay = 1.0
        rate_limit_count = 0
        for attempt in range(self._config.max_retries + 1):
            response = await self._http.get(path, params=params)
            if response.status_code == 401:
                raise FMPAuthError("API Key 无效或过期")
            if response.status_code == 402:
                raise FMPAuthError(f"当前订阅计划不支持此端点: {path}")
            if response.status_code == 403:
                raise FMPAuthError(f"访问被拒绝，请检查 API Key 或订阅计划: {path}")
            if response.status_code == 429:
                rate_limit_count += 1
                if rate_limit_count > self._config.max_retries:
                    raise FMPRateLimitError(f"速率限制，已重试 {rate_limit_count} 次: {path}")
                wait = float(response.headers.get("Retry-After", delay))
                await asyncio.sleep(wait)
                continue
            if response.status_code == 404:
                raise FMPNotFoundError(f"资源不存在: {path}")
            if response.status_code >= 500:
                if attempt == self._config.max_retries:
                    raise FMPServerError(f"服务端错误 {response.status_code}: {path}")
                await asyncio.sleep(delay)
                delay *= 2
                continue
            response.raise_for_status()
            return response.json()
        raise FMPServerError(f"超出最大重试次数: {path}")

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "FMPAsyncClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
