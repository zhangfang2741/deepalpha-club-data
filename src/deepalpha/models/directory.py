"""
证券目录数据模型

包含股票代码、交易所等基础证券信息。
"""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


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
