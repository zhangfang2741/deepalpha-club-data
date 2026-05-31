# tests/unit/models/test_model_annotations.py
import pytest
from pydantic import BaseModel

from deepalpha.models.analyst import AnalystRating, Estimate, PriceTarget
from deepalpha.models.calendar import DividendEvent, EarningsEvent, IPOEvent, SplitEvent
from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord
from deepalpha.models.congress import CongressTrade
from deepalpha.models.directory import ExchangeInfo, SymbolInfo
from deepalpha.models.filings import SecCompanyProfile, SecFiling
from deepalpha.models.financial import (
    BalanceSheet,
    CashFlow,
    FinancialRatio,
    IncomeStatement,
    KeyMetrics,
    Valuation,
)
from deepalpha.models.indicators import IndicatorRow
from deepalpha.models.insider import InsiderStatistics, InsiderTrade
from deepalpha.models.market import PriceBar, Quote
from deepalpha.models.news import NewsArticle
from deepalpha.models.performance import MarketMover, SectorPE, SectorPerformance


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
