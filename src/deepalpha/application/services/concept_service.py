"""概念股池业务逻辑服务"""
import datetime

from deepalpha.domain.concept.models import ConceptEtfMap, ConceptStock, ConceptSummary
from deepalpha.domain.concept.protocols import IConceptCache, IConceptRepo


class ConceptService:
    def __init__(self, repo: IConceptRepo, cache: IConceptCache) -> None:
        self._repo = repo
        self._cache = cache

    async def get_concept(self, name: str) -> list[ConceptStock]:
        hit = await self._cache.get_concept(name)
        if hit is not None:
            return hit
        rows = await self._repo.get_latest_stocks(name)
        if rows:
            await self._cache.set_concept(name, rows)
        return rows

    async def list_summaries(self) -> list[ConceptSummary]:
        hit = await self._cache.get_list()
        if hit is not None:
            return hit
        summaries = await self._repo.get_all_summaries()
        if summaries:
            await self._cache.set_list(summaries)
        return summaries

    async def get_concept_etfs(self, name: str) -> list[ConceptEtfMap]:
        return await self._repo.get_etfs_by_concept(name)

    async def get_concept_history(
        self, name: str, start: datetime.date, end: datetime.date
    ) -> list[ConceptStock]:
        return await self._repo.get_stocks_history(name, start, end)
