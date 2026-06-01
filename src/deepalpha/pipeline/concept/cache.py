"""
概念股池 Valkey 缓存层

KEY 规范：
  concept:__list__       → list[ConceptSummary] JSON，TTL 2 天
  concept:{name}         → list[ConceptStock] JSON，TTL 2 天
"""

import json

import valkey.asyncio as valkey_asyncio

from deepalpha.models.concept import ConceptStock, ConceptSummary


class ConceptCache:
    """Valkey（Upstash）缓存层，管理概念摘要列表和各概念成分股列表。"""

    def __init__(self, host: str, port: int, password: str, ssl: bool, ttl: int = 172800) -> None:
        self._client = valkey_asyncio.Valkey(
            host=host, port=port, password=password, ssl=ssl, decode_responses=True
        )
        self._ttl = ttl

    async def get_concept(self, name: str) -> list[ConceptStock] | None:
        data = await self._client.get(f"concept:{name}")
        if data is None:
            return None
        return [ConceptStock.model_validate(item) for item in json.loads(data)]

    async def set_concept(self, name: str, stocks: list[ConceptStock]) -> None:
        payload = json.dumps([s.model_dump(mode="json") for s in stocks])
        await self._client.set(f"concept:{name}", payload, ex=self._ttl)

    async def get_list(self) -> list[ConceptSummary] | None:
        data = await self._client.get("concept:__list__")
        if data is None:
            return None
        return [ConceptSummary.model_validate(item) for item in json.loads(data)]

    async def set_list(self, summaries: list[ConceptSummary]) -> None:
        payload = json.dumps([s.model_dump(mode="json") for s in summaries])
        await self._client.set("concept:__list__", payload, ex=self._ttl)

    async def close(self) -> None:
        await self._client.aclose()
