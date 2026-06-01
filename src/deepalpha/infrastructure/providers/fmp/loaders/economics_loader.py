import datetime

from deepalpha.domain.market.enums import Interval
from deepalpha.infrastructure.providers.base import BaseLoader
from deepalpha.models.indicators import IndicatorRow

_FMP_SUPPORTED: list[str] = [
    "CPI", "GDP", "REAL_GDP", "UNEMPLOYMENT",
    "FEDERAL_FUNDS_RATE", "TREASURY_YIELD", "RETAIL_SALES",
]


class FMPEconomicsLoader(BaseLoader):
    async def get_indicator(
        self,
        indicator_name: str,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_MONTH,
    ) -> list[IndicatorRow]:
        from deepalpha.infrastructure.providers.fmp.errors import FMPNotFoundError
        try:
            records = await self._get_list(
                "/stable/economics-indicators", name=indicator_name.upper()
            )
        except FMPNotFoundError:
            return []
        models = self._to_models(records, IndicatorRow)
        # IndicatorRow.date 是 datetime.datetime，需转换 date 参数后比较
        if start:
            start_dt = datetime.datetime(start.year, start.month, start.day)
            models = [m for m in models if m.date >= start_dt]
        if end:
            end_dt = datetime.datetime(end.year, end.month, end.day, 23, 59, 59)
            models = [m for m in models if m.date <= end_dt]
        return models

    async def get_available_indicators(self) -> list[str]:
        return list(_FMP_SUPPORTED)
