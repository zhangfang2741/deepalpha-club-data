"""
市场行情数据模型

包含实时报价、K线数据等市场交易信息。
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Quote(BaseModel):
    """实时行情报价数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码，如 AAPL")
    name: str | None = Field(None, title="公司名称", description="上市公司全称")
    price: float = Field(title="最新价格", description="最近一次成交价格（美元）")
    change: float = Field(title="涨跌额", description="相对上一收盘价的价格变动")
    changes_percentage: float | None = Field(
        None, title="涨跌幅", description="涨跌额占上一收盘价的百分比",
        validation_alias="changePercentage",
    )
    day_low: float | None = Field(None, title="日内最低价", description="当日最低成交价")
    day_high: float | None = Field(None, title="日内最高价", description="当日最高成交价")
    year_high: float | None = Field(None, title="52周最高", description="过去52周最高价")
    year_low: float | None = Field(None, title="52周最低", description="过去52周最低价")
    market_cap: float | None = Field(None, title="市值", description="总市值（美元）")
    volume: int | None = Field(None, title="成交量", description="当日已成交股数")
    avg_volume: int | None = Field(None, title="平均成交量", description="近期平均成交量")
    open: float | None = Field(None, title="开盘价", description="当日开盘价")
    previous_close: float | None = Field(None, title="前收盘价", description="上一交易日收盘价")
    eps: float | None = Field(None, title="每股收益", description="Earnings Per Share（美元）")
    pe: float | None = Field(None, title="市盈率", description="Price/Earnings 比率")
    exchange: str | None = Field(None, title="交易所", description="上市交易所代码，如 NASDAQ")
    timestamp: int | None = Field(None, title="时间戳", description="报价数据生成时间（Unix 秒）")


class PriceBar(BaseModel):
    """K线（价格柱）数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    date: datetime.datetime = Field(title="日期", description="K线时间戳：日线为 00:00:00，日内为实际时间")
    open: float = Field(title="开盘价", description="该周期开始价格")
    high: float = Field(title="最高价", description="该周期最高成交价")
    low: float = Field(title="最低价", description="该周期最低成交价")
    close: float = Field(title="收盘价", description="该周期结束价格")
    volume: float | None = Field(None, title="成交量", description="该周期成交股数（日内可能为小数）")
    adj_close: float | None = Field(None, title="复权收盘价", description="经分红/拆股调整后的收盘价")
