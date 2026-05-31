"""
市场表现数据模型

包含市场涨跌榜、板块表现等市场整体走势数据。
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


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
