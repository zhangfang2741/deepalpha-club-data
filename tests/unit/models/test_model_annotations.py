# tests/unit/models/test_model_annotations.py
import pytest
from pydantic import BaseModel
from deepalpha.models.market import Quote, PriceBar
from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord
from deepalpha.models.financial import (
    IncomeStatement, BalanceSheet, CashFlow,
    FinancialRatio, KeyMetrics, Valuation,
)
from deepalpha.models.analyst import AnalystRating, PriceTarget, Estimate
from deepalpha.models.calendar import EarningsEvent, DividendEvent, IPOEvent, SplitEvent
from deepalpha.models.news import NewsArticle
from deepalpha.models.insider import InsiderTrade, InsiderStatistics
from deepalpha.models.filings import SecFiling, SecCompanyProfile
from deepalpha.models.performance import MarketMover, SectorPerformance, SectorPE
from deepalpha.models.congress import CongressTrade
from deepalpha.models.directory import SymbolInfo, ExchangeInfo
from deepalpha.models.indicators import IndicatorRow


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
