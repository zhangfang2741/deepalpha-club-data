import datetime
import pytest
from pydantic import ValidationError
from deepalpha.domain.signal_radar.models import (
    SignalCategory, ExtractedTheme, DailyThemeScore, RawSignalItem,
)


def test_signal_category_values():
    assert SignalCategory.tech_concept == "tech_concept"
    assert SignalCategory.infra_component == "infra_component"
    assert SignalCategory.engineering_concept == "engineering_concept"


def test_extracted_theme_confidence_out_of_range():
    with pytest.raises(ValidationError):
        ExtractedTheme(name="HBM3e", category=SignalCategory.infra_component, confidence=1.5)


def test_extracted_theme_confidence_below_zero():
    with pytest.raises(ValidationError):
        ExtractedTheme(name="HBM3e", category=SignalCategory.infra_component, confidence=-0.1)


def test_extracted_theme_confidence_boundary_values():
    """边界值 0.0 和 1.0 应合法"""
    t0 = ExtractedTheme(name="MCP", category=SignalCategory.tech_concept, confidence=0.0)
    t1 = ExtractedTheme(name="MCP", category=SignalCategory.tech_concept, confidence=1.0)
    assert t0.confidence == 0.0
    assert t1.confidence == 1.0


def test_daily_theme_score_breakdown_defaults_empty():
    score = DailyThemeScore(
        theme_name="MCP",
        category=SignalCategory.tech_concept,
        score_date=datetime.date(2026, 6, 7),
        base_score=10.0,
        momentum=1.5,
        final_score=15.0,
        cumulative_score=15.0,
        company_count=3,
    )
    assert score.signal_breakdown == {}


def test_raw_signal_item_text_snippet_defaults_empty():
    item = RawSignalItem(
        ticker="NVDA",
        source_type="earnings_call",
        signal_date=datetime.date(2026, 6, 7),
        doc_id="0001045810-26-000001",
    )
    assert item.text_snippet == ""
