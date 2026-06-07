import pytest
from deepalpha.domain.concept.protocols import IConceptRepo, IConceptCache
from deepalpha.domain.concept.models import ConceptEtfMap, ConceptStock, ConceptSummary
import datetime


class _MockRepo:
    async def load_etf_map(self) -> list[ConceptEtfMap]: return []
    async def upsert_etf_map(self, records: list[ConceptEtfMap]) -> None: pass
    async def get_latest_stocks(self, concept: str) -> list[ConceptStock]: return []
    async def upsert_stocks(self, date: datetime.date, records: list[ConceptStock]) -> None: pass
    async def get_all_summaries(self) -> list[ConceptSummary]: return []
    async def get_etfs_by_concept(self, concept: str) -> list[ConceptEtfMap]: return []


class _MockCache:
    async def get_concept(self, name: str) -> list[ConceptStock] | None: return None
    async def set_concept(self, name: str, stocks: list[ConceptStock]) -> None: pass
    async def get_list(self) -> list[ConceptSummary] | None: return None
    async def set_list(self, summaries: list[ConceptSummary]) -> None: pass


def test_mock_repo_satisfies_protocol():
    assert isinstance(_MockRepo(), IConceptRepo)


def test_mock_cache_satisfies_protocol():
    assert isinstance(_MockCache(), IConceptCache)
