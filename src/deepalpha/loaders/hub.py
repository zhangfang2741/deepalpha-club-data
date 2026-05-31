# src/deepalpha/loaders/hub.py
from typing import Protocol, runtime_checkable
from deepalpha.loaders.market import AbstractMarketLoader
from deepalpha.loaders.financial import AbstractFinancialLoader
from deepalpha.loaders.company import AbstractCompanyLoader
from deepalpha.loaders.analyst import AbstractAnalystLoader
from deepalpha.loaders.calendar import AbstractCalendarLoader
from deepalpha.loaders.news import AbstractNewsLoader

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
