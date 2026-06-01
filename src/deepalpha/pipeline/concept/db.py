"""Pipeline concept db - re-exported from infrastructure.db.concept_repo."""
from deepalpha.infrastructure.db.concept_repo import ConceptRepo, _CREATE_TABLES_SQL

# Backward compatibility alias
ConceptDb = ConceptRepo

__all__ = ["ConceptRepo", "ConceptDb", "_CREATE_TABLES_SQL"]
