import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import IndicatorType, Interval
from deepalpha.models.indicators import IndicatorRow


class AbstractTechnicalIndicatorLoader(BaseLoader):
    @abstractmethod
    async def get_indicator(
        self,
        symbol: str,
        indicator: IndicatorType,
        period: int,
        interval: Interval = Interval.ONE_DAY,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[IndicatorRow]: ...
