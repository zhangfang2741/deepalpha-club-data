from abc import abstractmethod

import polars as pl

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import CongressChamber


class AbstractCongressTradeLoader(BaseLoader):
    @abstractmethod
    async def get_congress_trades(
        self,
        symbol: str | None = None,
        chamber: CongressChamber = CongressChamber.SENATE,
        limit: int = 50,
        page: int = 0,
    ) -> pl.DataFrame: ...
