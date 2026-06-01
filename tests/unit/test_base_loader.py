from unittest.mock import MagicMock

import polars as pl
import pytest
from pydantic import BaseModel

from deepalpha.infrastructure.providers.base import BaseLoader
from deepalpha.domain.governance.models import InsiderTrade


class _ConcreteLoader(BaseLoader):
    pass


@pytest.fixture
def loader():
    client = MagicMock()
    return _ConcreteLoader(client)


def test_to_models_returns_list_of_domain_objects(loader):
    records = [{
        "symbol": "AAPL", "filingDate": "2024-05-01", "transactionDate": "2024-04-29",
        "reportingName": "Tim Cook", "securityName": "Common Stock",
        "transactionType": "S-Sale", "acquisitionOrDisposition": "D",
        "securitiesTransacted": 100000, "price": 185.0,
        "typeOfOwner": "officer", "formType": "4",
        "url": "https://www.sec.gov/",
    }]
    result = loader._to_models(records, InsiderTrade)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], InsiderTrade)
    assert result[0].reporting_name == "Tim Cook"


def test_to_models_empty_records_returns_empty_list(loader):
    result = loader._to_models([], InsiderTrade)
    assert result == []


def test_to_models_cleans_empty_string_dates(loader):
    records = [{
        "symbol": "AAPL", "filingDate": "", "transactionDate": "",
        "reportingName": "Tim Cook", "securityName": "Common Stock",
        "transactionType": "S-Sale", "acquisitionOrDisposition": "D",
        "securitiesTransacted": 100000, "price": 185.0,
        "typeOfOwner": "officer", "formType": "4",
        "url": "https://www.sec.gov/",
    }]
    result = loader._to_models(records, InsiderTrade)
    assert result[0].filing_date is None
    assert result[0].transaction_date is None


def test_to_dataframe_returns_polars_dataframe():
    trade = InsiderTrade(
        symbol="AAPL",
        reporting_name="Tim Cook",
        transaction_type="S-Sale",
        price=185.0,
    )
    df = BaseLoader.to_dataframe([trade])
    assert isinstance(df, pl.DataFrame)
    assert "symbol" in df.columns
    assert df["symbol"][0] == "AAPL"


def test_to_dataframe_empty_returns_empty_dataframe():
    df = BaseLoader.to_dataframe([])
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 0
