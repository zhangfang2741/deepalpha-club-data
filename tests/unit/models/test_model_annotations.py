# tests/unit/models/test_model_annotations.py
import pytest
from pydantic import BaseModel


def assert_fields_annotated(model: type[BaseModel]) -> None:
    schema = model.model_json_schema()
    props = schema.get("properties", {})
    for field_name, field_info in props.items():
        assert "title" in field_info, f"{model.__name__}.{field_name} 缺少 title"
        assert field_info["title"], f"{model.__name__}.{field_name} title 为空"


from deepalpha.models.market import Quote, PriceBar
from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord
from deepalpha.models.financial import (
    IncomeStatement, BalanceSheet, CashFlow,
    FinancialRatio, KeyMetrics, Valuation,
)


@pytest.mark.parametrize("model", [
    Quote, PriceBar,
    CompanyProfile, Executive, MarketCapRecord,
    IncomeStatement, BalanceSheet, CashFlow,
    FinancialRatio, KeyMetrics, Valuation,
])
def test_all_fields_have_title(model):
    assert_fields_annotated(model)
