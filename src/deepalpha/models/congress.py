import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CongressTrade(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    filing_date: datetime.date | None = Field(None, title="申报日期", description="议员提交披露的日期")
    transaction_date: datetime.date | None = Field(None, title="交易日期", description="议员实际执行买卖的日期")
    representative: str | None = Field(None, title="议员姓名", description="提交披露的国会议员姓名")
    district: str | None = Field(None, title="选区", description="众议员的选区编号（参议员为 None）")
    type: str | None = Field(None, title="交易类型", description="Purchase / Sale / Exchange")
    amount: str | None = Field(None, title="交易金额区间", description="STOCK Act 规定的申报金额区间")
    asset_description: str | None = Field(None, title="资产描述", description="交易标的完整名称")
