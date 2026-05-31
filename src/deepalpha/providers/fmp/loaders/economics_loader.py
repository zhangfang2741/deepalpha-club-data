import datetime

import polars as pl
from pydantic import BaseModel, Field

from deepalpha.loaders.economics_loader import AbstractEconomicsLoader
from deepalpha.loaders.enums import Interval

_FMP_SUPPORTED: list[str] = [
    "CPI", "GDP", "REAL_GDP", "UNEMPLOYMENT",
    "FEDERAL_FUNDS_RATE", "TREASURY_YIELD", "RETAIL_SALES",
]

class _EconRow(BaseModel):
    date: datetime.date = Field(title="日期", description="经济指标数据对应的时间点")
    value: float | None = Field(None, title="指标值", description="经济指标的数值")

class FMPEconomicsLoader(AbstractEconomicsLoader):
    async def get_indicator(
        self,
        indicator_name: str,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_MONTH,
    ) -> pl.DataFrame:
        params: dict[str, str] = {"name": indicator_name.upper()}
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)
        records = await self._get_list("/stable/economics-indicators", **params)
        return self._to_df(records, _EconRow)

    async def get_available_indicators(self) -> list[str]:
        return list(_FMP_SUPPORTED)
