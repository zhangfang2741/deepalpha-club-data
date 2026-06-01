"""Pipeline concept tasks build_concept_map - re-exported from interface.pipeline.concept.build_concept_map."""
from deepalpha.interface.pipeline.concept.build_concept_map import main
from deepalpha.pipeline.concept.etfdb_scraper import scrape_concept_etf_candidates

# Backward compatibility alias
run = main

__all__ = ["run", "scrape_concept_etf_candidates"]
