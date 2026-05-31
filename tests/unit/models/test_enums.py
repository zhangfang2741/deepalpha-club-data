# tests/unit/models/test_enums.py
from deepalpha.loaders.enums import (
    AssetClass, Interval, StatementPeriod,
    IndicatorType, MoverDirection, CongressChamber,
)
from deepalpha.providers.fmp.errors import (
    FMPError, FMPAuthError, FMPRateLimitError,
    FMPNotFoundError, FMPServerError,
)

def test_asset_class_values():
    assert AssetClass.STOCK == "stock"
    assert AssetClass.CRYPTO == "crypto"

def test_interval_values():
    assert Interval.ONE_DAY == "1d"
    assert Interval.ONE_HOUR == "1h"

def test_statement_period_ttm():
    assert StatementPeriod.TTM == "ttm"

def test_indicator_type_coverage():
    assert IndicatorType.SMA == "sma"
    assert IndicatorType.MACD == "macd"

def test_fmp_error_hierarchy():
    assert issubclass(FMPAuthError, FMPError)
    assert issubclass(FMPRateLimitError, FMPError)
    assert issubclass(FMPNotFoundError, FMPError)
    assert issubclass(FMPServerError, FMPError)
