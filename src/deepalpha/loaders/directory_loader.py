from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass
from deepalpha.models.directory import ExchangeInfo, SymbolInfo


class AbstractDirectoryLoader(BaseLoader):
    @abstractmethod
    async def get_symbols(self, asset_class: AssetClass = AssetClass.STOCK) -> list[SymbolInfo]: ...
    @abstractmethod
    async def get_exchanges(self) -> list[ExchangeInfo]: ...
    @abstractmethod
    async def get_sectors(self) -> list[str]: ...
    @abstractmethod
    async def get_industries(self) -> list[str]: ...
