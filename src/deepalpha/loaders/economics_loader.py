import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import Interval
from deepalpha.models.indicators import IndicatorRow


class AbstractEconomicsLoader(BaseLoader):
    @abstractmethod
    async def get_indicator(
        self,
        indicator_name: str,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_MONTH,
    ) -> list[IndicatorRow]: ...
    @abstractmethod
    async def get_available_indicators(self) -> list[str]: ...
