"""
治理与监管领域模型（domain 层）

包含内部人交易、国会议员交易、SEC 申报文件等监管披露数据。
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class InsiderTrade(BaseModel):
    """内部人交易记录数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    filing_date: datetime.date | None = Field(None, title="申报日期", description="向 SEC 提交 Form 4 的日期")
    transaction_date: datetime.date | None = Field(None, title="交易日期", description="内部人实际执行买卖的日期")
    reporting_name: str | None = Field(None, title="申报人姓名", description="内部人（高管/董事/大股东）姓名")
    security_name: str | None = Field(None, title="证券名称", description="交易的证券名称，如 Common Stock")
    transaction_type: str | None = Field(None, title="交易类型代码", description="S-Sale / P-Purchase / A-Award 等 SEC 代码")
    acquisition_or_disposition: str | None = Field(None, title="买入或卖出", description="A=买入 D=卖出")
    securities_transacted: float | None = Field(None, title="交易股数", description="本次买入或卖出的股票数量")
    price: float | None = Field(None, title="成交价格", description="内部人交易成交价格（美元）")
    type_of_owner: str | None = Field(None, title="持有人类型", description="director / officer / 10 percent owner 等")
    form_type: str | None = Field(None, title="表格类型", description="SEC 表格类型，通常为 Form 4")
    url: str | None = Field(None, title="SEC 链接", description="SEC EDGAR 原始申报文件链接")


class InsiderStatistics(BaseModel):
    """按季度统计的内部人交易数据（每条记录代表一个季度）。"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    year: int | None = Field(None, title="年份", description="统计所在年份")
    quarter: int | None = Field(None, title="季度", description="统计所在季度（1-4）")
    acquired_transactions: int | None = Field(None, title="买入笔数", description="本季度内部人买入交易总笔数")
    disposed_transactions: int | None = Field(None, title="卖出笔数", description="本季度内部人卖出交易总笔数")
    total_acquired: float | None = Field(None, title="买入总股数", description="本季度合计买入股数")
    total_disposed: float | None = Field(None, title="卖出总股数", description="本季度合计卖出股数")
    total_purchases: int | None = Field(None, title="公开买入次数", description="公开市场买入操作次数")
    total_sales: int | None = Field(None, title="公开卖出次数", description="公开市场卖出操作次数")


class CongressTrade(BaseModel):
    """国会议员交易记录数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    disclosure_date: datetime.date | None = Field(None, title="披露日期", description="议员提交披露的日期")
    transaction_date: datetime.date | None = Field(None, title="交易日期", description="议员实际执行买卖的日期")
    first_name: str | None = Field(None, title="名", description="议员名")
    last_name: str | None = Field(None, title="姓", description="议员姓")
    office: str | None = Field(None, title="姓名/职位", description="议员全名，如 John Boozman")
    district: str | None = Field(None, title="选区/州", description="议员所在州或选区编号")
    owner: str | None = Field(None, title="持有关系", description="Self / Joint / Spouse")
    type: str | None = Field(None, title="交易类型", description="Purchase / Sale / Exchange")
    amount: str | None = Field(None, title="交易金额区间", description="STOCK Act 规定的申报金额区间")
    asset_description: str | None = Field(None, title="资产描述", description="交易标的完整名称")
    asset_type: str | None = Field(None, title="资产类型", description="Stock / Option / Other")
    link: str | None = Field(None, title="披露链接", description="SEC 披露原文链接")


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
