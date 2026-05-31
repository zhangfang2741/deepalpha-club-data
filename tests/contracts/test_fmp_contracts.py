# tests/contracts/test_fmp_contracts.py
from deepalpha.loaders.market import AbstractMarketLoader
from deepalpha.loaders.financial import AbstractFinancialLoader
from deepalpha.loaders.company import AbstractCompanyLoader
from deepalpha.loaders.analyst import AbstractAnalystLoader
from deepalpha.loaders.calendar import AbstractCalendarLoader
from deepalpha.loaders.news import AbstractNewsLoader
from deepalpha.loaders.indicators import AbstractTechnicalIndicatorLoader
from deepalpha.loaders.economics import AbstractEconomicsLoader
from deepalpha.loaders.insider import AbstractInsiderTradeLoader
from deepalpha.loaders.filings import AbstractSecFilingLoader
from deepalpha.loaders.performance import AbstractMarketPerformanceLoader
from deepalpha.loaders.congress import AbstractCongressTradeLoader
from deepalpha.loaders.directory import AbstractDirectoryLoader
from deepalpha.loaders.hub import AbstractDataHub

def test_abstract_loaders_importable():
    assert AbstractMarketLoader is not None
    assert AbstractDataHub is not None

import pytest
from deepalpha.providers.fmp import FMPDataHub
from deepalpha.providers.fmp.config import FMPConfig

def test_fmp_data_hub_implements_abstract_data_hub():
    cfg = FMPConfig(api_key="test-key")
    hub = FMPDataHub(cfg)
    assert isinstance(hub, AbstractDataHub)

def test_fmp_data_hub_has_all_core_loaders():
    cfg = FMPConfig(api_key="test-key")
    hub = FMPDataHub(cfg)
    assert hasattr(hub, "market")
    assert hasattr(hub, "financial")
    assert hasattr(hub, "company")
    assert hasattr(hub, "analyst")
    assert hasattr(hub, "calendar")
    assert hasattr(hub, "news")

def test_fmp_data_hub_has_all_extended_loaders():
    cfg = FMPConfig(api_key="test-key")
    hub = FMPDataHub(cfg)
    assert hasattr(hub, "indicators")
    assert hasattr(hub, "economics")
    assert hasattr(hub, "insider")
    assert hasattr(hub, "filings")
    assert hasattr(hub, "performance")
    assert hasattr(hub, "congress")
    assert hasattr(hub, "directory")
