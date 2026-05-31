import datetime
from abc import abstractmethod

import polars as pl

from deepalpha.loaders.base import BaseLoader
from deepalpha.models.filings import SecCompanyProfile


class AbstractSecFilingLoader(BaseLoader):
    @abstractmethod
    async def get_filings(
        self,
        symbol: str | None = None,
        form_type: str | None = None,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        limit: int = 20,
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_sec_profile(self, symbol: str) -> SecCompanyProfile: ...
