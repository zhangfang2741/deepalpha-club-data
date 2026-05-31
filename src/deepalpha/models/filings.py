import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SecFiling(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str | None = Field(None, title="股票代码", description="与该文件关联的股票代码（如有）")
    filing_date: datetime.date | None = Field(None, title="申报日期", description="向 SEC 提交文件的日期")
    accepted_date: datetime.date | None = Field(None, title="受理日期", description="SEC 系统接受并处理的日期")
    type: str | None = Field(None, title="文件类型", description="文件类型代码，如 10-K / 10-Q / 8-K")
    link: str | None = Field(None, title="文件链接", description="SEC EDGAR 原始文件 URL")


class SecCompanyProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    cik: str | None = Field(None, title="CIK", description="SEC 系统中唯一的公司识别码")
    symbol: str | None = Field(None, title="股票代码", description="交易所上市代码")
    company_name: str | None = Field(None, title="公司名称", description="在 SEC 注册的法定公司名称")
    sic: str | None = Field(None, title="SIC 代码", description="标准行业分类代码（Standard Industrial Classification）")
    state_of_incorporation: str | None = Field(None, title="注册州", description="公司在美国的注册州代码，如 DE/CA")
    fiscal_year_end: str | None = Field(None, title="财年结束月", description="公司财政年度的结束月份，如 12 月")
