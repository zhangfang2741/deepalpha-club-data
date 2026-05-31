# src/deepalpha/loaders/hub.py
from typing import Protocol, runtime_checkable
from deepalpha.loaders.market_loader import AbstractMarketLoader
from deepalpha.loaders.financial_loader import AbstractFinancialLoader
from deepalpha.loaders.company_loader import AbstractCompanyLoader
from deepalpha.loaders.analyst_loader import AbstractAnalystLoader
from deepalpha.loaders.calendar_loader import AbstractCalendarLoader
from deepalpha.loaders.news_loader import AbstractNewsLoader

@runtime_checkable
class AbstractDataHub(Protocol):
    market:    AbstractMarketLoader
    financial: AbstractFinancialLoader
    company:   AbstractCompanyLoader
    analyst:   AbstractAnalystLoader
    calendar:  AbstractCalendarLoader
    news:      AbstractNewsLoader

    async def __aenter__(self) -> "AbstractDataHub": ...
    async def __aexit__(self, *_: object) -> None: ...
