import datetime
from abc import abstractmethod

import polars as pl

from deepalpha.loaders.base import BaseLoader


class AbstractCalendarLoader(BaseLoader):
    @abstractmethod
    async def get_earnings_calendar(self, start: datetime.date, end: datetime.date) -> pl.DataFrame: ...
    @abstractmethod
    async def get_dividend_calendar(self, start: datetime.date, end: datetime.date) -> pl.DataFrame: ...
    @abstractmethod
    async def get_ipo_calendar(self, start: datetime.date, end: datetime.date) -> pl.DataFrame: ...
    @abstractmethod
    async def get_splits_calendar(self, start: datetime.date, end: datetime.date) -> pl.DataFrame: ...
