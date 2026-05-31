"""
技术指标数据模型

包含各类技术分析指标的计算结果。
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class IndicatorRow(BaseModel):
    """技术指标数据行"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    date: datetime.datetime = Field(title="日期", description="指标计算对应的 K 线时间戳")
    value: float | None = Field(None, title="指标值", description="该日期的技术指标计算结果")
    open: float | None = Field(None, title="开盘价", description="对应K线的开盘价（部分指标附带OHLC）")
    high: float | None = Field(None, title="最高价", description="对应K线的最高价")
    low: float | None = Field(None, title="最低价", description="对应K线的最低价")
    close: float | None = Field(None, title="收盘价", description="对应K线的收盘价")
    volume: float | None = Field(None, title="成交量", description="对应K线的成交量")
