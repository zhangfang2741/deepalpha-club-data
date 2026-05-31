# src/deepalpha/models/company.py
import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CompanyProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    company_name: str = Field(title="公司名称", description="上市公司完整法定名称")
    exchange: str | None = Field(None, title="交易所", description="上市交易所代码")
    industry: str | None = Field(None, title="行业", description="所属行业分类")
    sector: str | None = Field(None, title="板块", description="所属板块分类")
    description: str | None = Field(None, title="公司描述", description="公司主营业务介绍")
    website: str | None = Field(None, title="官网", description="公司官方网站 URL")
    full_time_employees: int | None = Field(None, title="全职员工数", description="当前全职雇员总数")
    ceo: str | None = Field(None, title="首席执行官", description="现任 CEO 姓名")
    country: str | None = Field(None, title="注册国家", description="公司注册所在国家代码")
    ipo_date: datetime.date | None = Field(None, title="上市日期", description="首次公开募股日期")
    is_actively_trading: bool | None = Field(None, title="是否活跃交易", description="当前是否正常交易中")


class Executive(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    name: str = Field(title="姓名", description="高管姓名")
    title: str | None = Field(None, title="职位", description="高管职位名称，如 CEO、CFO")
    pay: float | None = Field(None, title="薪酬", description="年度薪酬（美元）")
    currency_of_pay: str | None = Field(None, title="薪酬货币", description="薪酬计价货币代码")
    gender: str | None = Field(None, title="性别", description="M 或 F")
    year_born: int | None = Field(None, title="出生年份", description="高管出生年份")


class MarketCapRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="日期", description="市值对应的交易日")
    market_cap: float = Field(title="市值", description="当日收盘市值（美元）")
