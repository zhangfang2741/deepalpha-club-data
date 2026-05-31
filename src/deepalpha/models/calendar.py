
"""
日历事件数据模型

包含财报发布、除息分红、IPO、拆股等重要日期事件。
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


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
