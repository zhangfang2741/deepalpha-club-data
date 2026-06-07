import datetime
import pytest
from pydantic import ValidationError
from deepalpha.domain.signal_radar.models import (
    SignalCategory, ExtractedTheme, DailyThemeScore,
)


def test_signal_category_values():
    assert SignalCategory.tech_concept == "tech_concept"
    assert SignalCategory.infra_component == "infra_component"
    assert SignalCategory.engineering_concept == "engineering_concept"


def test_extracted_theme_confidence_out_of_range():
    with pytest.raises(ValidationError):
        ExtractedTheme(name="HBM3e", category=SignalCategory.infra_component, confidence=1.5)


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
