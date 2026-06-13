"""概念股池业务逻辑服务"""
import datetime

from deepalpha.domain.concept.models import ConceptEtfMap, ConceptStock, ConceptSummary
from deepalpha.domain.concept.protocols import IConceptCache, IConceptRepo


class ConceptService:
    def __init__(self, repo: IConceptRepo, cache: IConceptCache, minimax_api_key: str = "") -> None:
        self._repo = repo
        self._cache = cache
        self._minimax_api_key = minimax_api_key

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

    async def analyze_concept(self, name: str) -> dict:
        """对概念进行多维度 AI 业务分析。"""
        from deepalpha.infrastructure.providers.minimax.concept_analyzer import analyze_concept

        stocks = await self.get_concept(name)
        etfs = await self.get_concept_etfs(name)

        summaries = await self.list_summaries()
        summary = next((s for s in summaries if s.concept == name), None)
        concept_zh = summary.concept_name_zh if summary else None

        stock_dicts = [
            {
                "symbol": s.symbol,
                "name": s.name,
                "etf_count": s.etf_count,
                "total_weight": s.total_weight,
                "etfs": s.etfs,
            }
            for s in stocks
        ]
        etf_dicts = [
            {
                "etf_symbol": e.etf_symbol,
                "etf_name": e.etf_name,
                "description_zh": e.description_zh,
            }
            for e in etfs
        ]

        return await analyze_concept(
            api_key=self._minimax_api_key,
            concept_name=name,
            concept_name_zh=concept_zh,
            stocks=stock_dicts,
            etfs=etf_dicts,
        )
