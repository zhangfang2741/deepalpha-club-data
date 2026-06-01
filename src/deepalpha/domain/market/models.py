"""市场领域模型（domain 层）

包含行情报价、K线、日历事件、技术指标、市场表现、证券目录等市场相关模型。
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


# ── 日历事件 ──────────────────────────────────────────────────────────────────


class EarningsEvent(BaseModel):
    """财报发布事件数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="财报发布日", description="预计或实际财报发布日期")
    eps: float | None = Field(None, title="实际EPS", description="实际公布的每股收益（美元）")
    eps_estimated: float | None = Field(None, title="EPS预期", description="市场共识 EPS 预测（美元）")
    time: str | None = Field(None, title="发布时段", description="bmo=开盘前 / amc=收盘后")
    revenue_estimated: float | None = Field(None, title="营收预期", description="市场共识营收预测（美元）")


class DividendEvent(BaseModel):
    """股息分红事件数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="除息日", description="股息除权基准日")
    dividend: float | None = Field(None, title="股息金额", description="每股现金股息（美元）")
    record_date: datetime.date | None = Field(None, title="股权登记日", description="确认分红资格的截止日期")
    payment_date: datetime.date | None = Field(None, title="派息日", description="实际向股东支付股息的日期")


class IPOEvent(BaseModel):
    """IPO 上市事件数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="拟上市股票代码")
    company: str | None = Field(None, title="公司名称", description="拟上市公司名称")
    date: datetime.date = Field(title="上市日期", description="预计首次公开交易日期")
    exchange: str | None = Field(None, title="上市交易所", description="拟上市交易所代码")
    price_range: str | None = Field(None, title="发行价区间", description="承销商拟定发行价格范围（美元）")
    shares: int | None = Field(None, title="发行股数", description="本次 IPO 发行总股数")


class SplitEvent(BaseModel):
    """股票拆分事件数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="拆股生效日", description="拆/合股正式生效的交易日")
    numerator: float | None = Field(None, title="拆股分子", description="拆股比例分子，如 4:1 中的 4")
    denominator: float | None = Field(None, title="拆股分母", description="拆股比例分母，如 4:1 中的 1")


# ── 技术指标 ──────────────────────────────────────────────────────────────────


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


# ── 市场表现 ──────────────────────────────────────────────────────────────────


class MarketMover(BaseModel):
    """市场涨跌股票数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    name: str | None = Field(None, title="公司名称", description="上市公司名称")
    change: float | None = Field(None, title="涨跌额", description="相对上一收盘价的变动额（美元）")
    price: float | None = Field(None, title="当前价格", description="最新成交价格（美元）")
    changes_percentage: float | None = Field(
        None, title="涨跌幅", description="相对上一收盘价的百分比变化",
        validation_alias="changesPercentage",
    )
    volume: int | None = Field(None, title="成交量", description="当日成交总股数")


class SectorPerformance(BaseModel):
    """板块表现数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    sector: str = Field(title="板块名称", description="GICS 或 FMP 定义的板块分类名称")
    changes_percentage: str | None = Field(
        None, title="涨跌幅", description="当日或历史日期的板块整体涨跌幅（百分比字符串）",
        validation_alias="changesPercentage",
    )


class SectorPE(BaseModel):
    """板块市盈率数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    date: datetime.date | None = Field(None, title="日期", description="PE 数据对应的交易日")
    sector: str = Field(title="板块名称", description="GICS 或 FMP 定义的板块分类名称")
    pe: float | None = Field(None, title="市盈率", description="该板块所有成分股的综合市盈率")


# ── 证券目录 ──────────────────────────────────────────────────────────────────


class SymbolInfo(BaseModel):
    """股票代码信息数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    name: str | None = Field(None, title="公司名称", description="证券发行人完整名称")
    exchange: str | None = Field(None, title="交易所", description="上市交易所代码")
    exchange_short_name: str | None = Field(None, title="交易所简称", description="交易所简短标识")
    type: str | None = Field(None, title="证券类型", description="stock / etf / trust 等")


class ExchangeInfo(BaseModel):
    """交易所信息数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    exchange: str = Field(title="交易所代码", description="FMP 系统内部使用的交易所标识")
    name: str | None = Field(None, title="交易所名称", description="交易所完整名称")
    country: str | None = Field(None, title="所在国家", description="交易所所在国家代码（ISO 3166-1）")
    currency: str | None = Field(None, title="交易货币", description="该交易所的主要计价货币代码")
