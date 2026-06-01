"""
概念股池数据模型

包含 ETFdb 概念分类映射、概念成分股快照及概念摘要信息。
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConceptEtfMap(BaseModel):
    """概念 → ETF 映射记录（月度更新）"""
    model_config = ConfigDict(populate_by_name=True)

    concept: str = Field(title="概念名称", description="ETFdb 主题分类名")
    etf_symbol: str = Field(title="ETF 代码", description="ETF 股票代码")
    etf_name: str | None = Field(None, title="ETF 名称", description="ETF 完整名称")
    aum_million: float | None = Field(None, title="AUM（百万美元）", description="ETF 管理资产规模")
    etfdb_slug: str | None = Field(None, title="ETFdb 分类标识", description="ETFdb URL 中的分类 slug")
    updated_at: datetime.date = Field(title="更新日期", description="数据写入日期")


class ConceptStock(BaseModel):
    """概念成分股快照（日度更新）"""
    model_config = ConfigDict(populate_by_name=True)

    date: datetime.date = Field(title="日期", description="持仓快照日期")
    concept: str = Field(title="概念名称", description="ETFdb 主题分类名")
    symbol: str = Field(title="股票代码", description="成分股 ticker")
    name: str | None = Field(None, title="公司名称", description="公司完整名称")
    etf_count: int = Field(title="ETF 覆盖数", description="持有该股的独立 ETF 数量")
    total_weight: float = Field(title="合计权重", description="在所有持有 ETF 中权重之和（%）")
    etfs: list[str] = Field(title="持有 ETF 列表", description="持有该股的 ETF 代码列表")


class ConceptSummary(BaseModel):
    """概念摘要（/concept/list 接口用）"""
    model_config = ConfigDict(populate_by_name=True)

    concept: str = Field(title="概念名称", description="ETFdb 主题分类名")
    etf_count: int = Field(title="ETF 数量", description="该概念下通过 AUM 过滤的 ETF 数量")
    stock_count: int = Field(title="成分股数量", description="最新日期的成分股总数")
    top_symbols: list[str] = Field(title="核心成分股", description="etf_count 最高的前 5 只股票代码")
    last_updated: datetime.date = Field(title="最后更新日", description="最新持仓快照日期")
