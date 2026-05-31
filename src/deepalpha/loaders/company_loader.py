import datetime
from abc import abstractmethod

import polars as pl

from deepalpha.loaders.base import BaseLoader
from deepalpha.models.company import CompanyProfile


class AbstractCompanyLoader(BaseLoader):
    @abstractmethod
    async def get_profile(self, symbol: str) -> CompanyProfile: ...
    @abstractmethod
    async def get_executives(self, symbol: str) -> pl.DataFrame: ...
    @abstractmethod
    async def get_peers(self, symbol: str) -> list[str]: ...
    @abstractmethod
    async def get_market_cap(
        self, symbol: str, start: datetime.date | None = None, end: datetime.date | None = None
    ) -> pl.DataFrame: ...
