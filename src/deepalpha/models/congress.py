import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CongressTrade(BaseModel):
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
