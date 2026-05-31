from abc import abstractmethod

import polars as pl

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass


class AbstractDirectoryLoader(BaseLoader):
    @abstractmethod
    async def get_symbols(self, asset_class: AssetClass = AssetClass.STOCK) -> pl.DataFrame: ...
    @abstractmethod
    async def get_exchanges(self) -> pl.DataFrame: ...
    @abstractmethod
    async def get_sectors(self) -> list[str]: ...
    @abstractmethod
    async def get_industries(self) -> list[str]: ...
