from deepalpha.infrastructure.cache.concept_cache import ConceptCache
from deepalpha.domain.concept.protocols import IConceptCache


def test_concept_cache_satisfies_protocol():
    cache = ConceptCache.__new__(ConceptCache)
    assert isinstance(cache, IConceptCache)
