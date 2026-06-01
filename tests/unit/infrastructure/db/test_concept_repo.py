from deepalpha.infrastructure.db.concept_repo import ConceptRepo
from deepalpha.domain.concept.protocols import IConceptRepo


def test_concept_repo_satisfies_protocol():
    repo = ConceptRepo.__new__(ConceptRepo)
    assert isinstance(repo, IConceptRepo)
