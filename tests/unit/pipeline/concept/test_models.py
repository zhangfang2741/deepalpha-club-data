import datetime
from deepalpha.models.concept import ConceptEtfMap, ConceptStock, ConceptSummary


def test_concept_etf_map_required_fields():
    m = ConceptEtfMap(
        concept="Artificial Intelligence",
        etf_symbol="BOTZ",
        updated_at=datetime.date(2026, 5, 31),
    )
    assert m.concept == "Artificial Intelligence"
    assert m.etf_symbol == "BOTZ"
    assert m.etf_name is None
    assert m.aum_million is None


def test_concept_stock_etfs_as_list():
    s = ConceptStock(
        date=datetime.date(2026, 5, 31),
        concept="Artificial Intelligence",
        symbol="NVDA",
        etf_count=3,
        total_weight=15.5,
        etfs=["BOTZ", "AIQ", "IRBO"],
    )
    assert s.etfs == ["BOTZ", "AIQ", "IRBO"]
    assert s.etf_count == 3
    assert s.name is None


def test_concept_summary_top_symbols():
    summary = ConceptSummary(
        concept="Artificial Intelligence",
        etf_count=4,
        stock_count=120,
        top_symbols=["NVDA", "AMD", "MSFT", "GOOGL", "META"],
        last_updated=datetime.date(2026, 5, 31),
    )
    assert len(summary.top_symbols) == 5
    assert summary.stock_count == 120
