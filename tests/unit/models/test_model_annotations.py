# tests/unit/models/test_model_annotations.py
import pytest
from pydantic import BaseModel

from deepalpha.domain.analyst.models import AnalystRating, Estimate, PriceTarget
from deepalpha.domain.market.models import (
    DividendEvent,
    EarningsEvent,
    ExchangeInfo,
    IPOEvent,
    IndicatorRow,
    MarketMover,
    PriceBar,
    Quote,
    SectorPE,
    SectorPerformance,
    SplitEvent,
    SymbolInfo,
)
from deepalpha.domain.company.models import CompanyProfile, Executive, MarketCapRecord
from deepalpha.domain.governance.models import CongressTrade, InsiderStatistics, InsiderTrade, SecCompanyProfile, SecFiling
from deepalpha.domain.financial.models import (
    BalanceSheet,
    CashFlow,
    FinancialRatio,
    IncomeStatement,
    KeyMetrics,
    Valuation,
)
from deepalpha.domain.news.models import NewsArticle


def assert_fields_annotated(model: type[BaseModel]) -> None:
    schema = model.model_json_schema()
    props = schema.get("properties", {})
    for field_name, field_info in props.items():
        assert "title" in field_info, f"{model.__name__}.{field_name} 缺少 title"
        assert field_info["title"], f"{model.__name__}.{field_name} title 为空"


@pytest.mark.parametrize("model", [
    Quote, PriceBar,
    CompanyProfile, Executive, MarketCapRecord,
    IncomeStatement, BalanceSheet, CashFlow,
    FinancialRatio, KeyMetrics, Valuation,
    AnalystRating, PriceTarget, Estimate,
    EarningsEvent, DividendEvent, IPOEvent, SplitEvent,
    NewsArticle,
    InsiderTrade, InsiderStatistics,
    SecFiling, SecCompanyProfile,
    MarketMover, SectorPerformance, SectorPE,
    CongressTrade,
    SymbolInfo, ExchangeInfo,
    IndicatorRow,
])
def test_all_fields_have_title(model):
    assert_fields_annotated(model)
