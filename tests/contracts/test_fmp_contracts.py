# tests/contracts/test_fmp_contracts.py
"""
FMP infrastructure 层契约测试

验证 infrastructure 层的加载器可以正常实例化，并实现了预期的接口。
"""

from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.market_loader import FMPMarketLoader
from deepalpha.infrastructure.providers.fmp.loaders.financial_loader import FMPFinancialLoader
from deepalpha.infrastructure.providers.fmp.loaders.analyst_loader import FMPAnalystLoader
from deepalpha.infrastructure.providers.fmp.loaders.calendar_loader import FMPCalendarLoader
from deepalpha.infrastructure.providers.fmp.loaders.news_loader import FMPNewsLoader
from deepalpha.infrastructure.providers.fmp.loaders.indicators_loader import FMPTechnicalIndicatorLoader
from deepalpha.infrastructure.providers.fmp.loaders.economics_loader import FMPEconomicsLoader
from deepalpha.infrastructure.providers.fmp.loaders.insider_loader import FMPInsiderTradeLoader
from deepalpha.infrastructure.providers.fmp.loaders.filings_loader import FMPSecFilingLoader
from deepalpha.infrastructure.providers.fmp.loaders.performance_loader import FMPMarketPerformanceLoader
from deepalpha.infrastructure.providers.fmp.loaders.congress_loader import FMPCongressTradeLoader
from deepalpha.infrastructure.providers.fmp.loaders.directory_loader import FMPDirectoryLoader
from deepalpha.infrastructure.providers.base import BaseLoader


def make_client() -> FMPAsyncClient:
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


def test_core_loaders_instantiable():
    client = make_client()
    assert isinstance(FMPMarketLoader(client), BaseLoader)
    assert isinstance(FMPFinancialLoader(client), BaseLoader)
    assert isinstance(FMPAnalystLoader(client), BaseLoader)
    assert isinstance(FMPCalendarLoader(client), BaseLoader)
    assert isinstance(FMPNewsLoader(client), BaseLoader)


def test_extended_loaders_instantiable():
    client = make_client()
    assert isinstance(FMPTechnicalIndicatorLoader(client), BaseLoader)
    assert isinstance(FMPEconomicsLoader(client), BaseLoader)
    assert isinstance(FMPInsiderTradeLoader(client), BaseLoader)
    assert isinstance(FMPSecFilingLoader(client), BaseLoader)
    assert isinstance(FMPMarketPerformanceLoader(client), BaseLoader)
    assert isinstance(FMPCongressTradeLoader(client), BaseLoader)
    assert isinstance(FMPDirectoryLoader(client), BaseLoader)
