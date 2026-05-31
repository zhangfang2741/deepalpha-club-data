import datetime

import polars as pl
from pydantic import BaseModel, Field

from deepalpha.loaders.economics_loader import AbstractEconomicsLoader
from deepalpha.loaders.enums import Interval

_FMP_SUPPORTED: list[str] = [
    "CPI", "GDP", "REAL_GDP", "UNEMPLOYMENT",
    "FEDERAL_FUNDS_RATE", "TREASURY_YIELD", "RETAIL_SALES",
]

_FMP_ECON_PATHS: dict[str, str] = {
    "CPI":                "cpi",
    "GDP":                "gdp",
    "REAL_GDP":           "real-gdp",
    "UNEMPLOYMENT":       "unemployment",
    "FEDERAL_FUNDS_RATE": "federal-funds-rate",
    "TREASURY_YIELD":     "treasury-yield",
    "RETAIL_SALES":       "retail-sales",
}

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
        path_seg = _FMP_ECON_PATHS.get(indicator_name.upper(), indicator_name.lower())
        params: dict[str, str] = {}
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)
        records = await self._get_list(f"/stable/{path_seg}", **params)
        return self._to_df(records, _EconRow)

    async def get_available_indicators(self) -> list[str]:
        return list(_FMP_SUPPORTED)
