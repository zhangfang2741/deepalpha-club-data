import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.models.calendar import DividendEvent, EarningsEvent, IPOEvent, SplitEvent


class AbstractCalendarLoader(BaseLoader):
    @abstractmethod
    async def get_earnings_calendar(self, start: datetime.date, end: datetime.date) -> list[EarningsEvent]: ...
    @abstractmethod
    async def get_dividend_calendar(self, start: datetime.date, end: datetime.date) -> list[DividendEvent]: ...
    @abstractmethod
    async def get_ipo_calendar(self, start: datetime.date, end: datetime.date) -> list[IPOEvent]: ...
    @abstractmethod
    async def get_splits_calendar(self, start: datetime.date, end: datetime.date) -> list[SplitEvent]: ...
