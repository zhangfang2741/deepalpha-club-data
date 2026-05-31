import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class InsiderTrade(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    filing_date: datetime.date | None = Field(None, title="申报日期", description="向 SEC 提交 Form 4 的日期")
    transaction_date: datetime.date | None = Field(None, title="交易日期", description="内部人实际执行买卖的日期")
    reporting_name: str | None = Field(None, title="申报人姓名", description="内部人（高管/董事/大股东）姓名")
    type_of_security: str | None = Field(None, title="证券类型", description="普通股 / 期权 等")
    acquition_or_disposition: str | None = Field(None, title="买入或卖出", description="A=买入 D=卖出")
    shares: float | None = Field(None, title="交易股数", description="本次买入或卖出的股票数量")
    price: float | None = Field(None, title="成交价格", description="内部人交易成交价格（美元）")


class InsiderStatistics(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    total_bought: int | None = Field(None, title="买入笔数", description="统计期内内部人买入交易总笔数")
    total_sold: int | None = Field(None, title="卖出笔数", description="统计期内内部人卖出交易总笔数")
    total_bought_amount: float | None = Field(None, title="买入金额", description="买入交易总金额（美元）")
    total_sold_amount: float | None = Field(None, title="卖出金额", description="卖出交易总金额（美元）")
