import datetime
import pytest
from deepalpha.domain.concept.models import ConceptEtfMap, ConceptStock, ConceptSummary


def test_concept_stock_instantiation():
    stock = ConceptStock(
        date=datetime.date(2026, 6, 1),
        concept="AI",
        symbol="NVDA",
        etf_count=5,
        total_weight=10.0,
        etfs=["BOTZ", "AIQ"],
    )
    assert stock.symbol == "NVDA"
    assert stock.etfs == ["BOTZ", "AIQ"]


def test_concept_etf_map_optional_fields():
    m = ConceptEtfMap(
        concept="AI",
        etf_symbol="BOTZ",
        updated_at=datetime.date(2026, 6, 1),
    )
    assert m.etf_name is None
    assert m.aum_million is None


def test_concept_summary_top_symbols():
    s = ConceptSummary(
        concept="AI",
        etf_count=4,
        stock_count=120,
        top_symbols=["NVDA", "MSFT"],
        last_updated=datetime.date(2026, 6, 1),
    )
    assert s.top_symbols == ["NVDA", "MSFT"]
