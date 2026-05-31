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
