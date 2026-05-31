from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.analyst import AnalystRating, Estimate, PriceTarget


class AbstractAnalystLoader(BaseLoader):
    @abstractmethod
    async def get_ratings(self, symbol: str) -> list[AnalystRating]: ...
    @abstractmethod
    async def get_price_targets(self, symbol: str) -> list[PriceTarget]: ...
    @abstractmethod
    async def get_estimates(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL
    ) -> list[Estimate]: ...
