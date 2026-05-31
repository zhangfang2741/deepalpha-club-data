"""
SEC 申报文件数据模型

包含向 SEC 提交的各类申报文件信息。
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SecFiling(BaseModel):
    """SEC 申报文件数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str | None = Field(None, title="股票代码", description="与该文件关联的股票代码（如有）")
    filing_date: datetime.datetime | None = Field(None, title="申报日期", description="向 SEC 提交文件的日期")
    accepted_date: datetime.datetime | None = Field(None, title="受理日期", description="SEC 系统接受并处理的日期")
    form_type: str | None = Field(None, title="文件类型", description="文件类型代码，如 10-K / 10-Q / 8-K")
    link: str | None = Field(None, title="文件链接", description="SEC EDGAR 原始文件 URL")
    final_link: str | None = Field(None, title="最终文件链接", description="SEC EDGAR 最终版本文件 URL")


class SecCompanyProfile(BaseModel):
    """SEC 公司资料数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    cik: str | None = Field(None, title="CIK", description="SEC 系统中唯一的公司识别码")
    symbol: str | None = Field(None, title="股票代码", description="交易所上市代码")
    registrant_name: str | None = Field(None, title="注册名称", description="在 SEC 注册的法定公司名称")
    sic_code: str | None = Field(None, title="SIC 代码", description="标准行业分类代码（Standard Industrial Classification）")
    sic_description: str | None = Field(None, title="行业描述", description="SIC 代码对应的行业描述")
    sic_group: str | None = Field(None, title="行业分组", description="SIC 分组名称")
