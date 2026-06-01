"""概念股池领域模型（domain 层，零外部依赖）"""
import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConceptEtfMap(BaseModel):
    """概念 → ETF 映射记录（月度更新）"""
    model_config = ConfigDict(populate_by_name=True)

    concept: str = Field(title="概念名称", description="Morningstar 板块分类名（英文）")
    etf_symbol: str = Field(title="ETF 代码", description="ETF 股票代码")
    etf_name: str | None = Field(None, title="ETF 名称", description="ETF 完整名称（英文）")
    aum_million: float | None = Field(None, title="AUM（百万美元）", description="ETF 管理资产规模")
    etfdb_slug: str | None = Field(None, title="分类标识", description="分类 slug")
    updated_at: datetime.date = Field(title="更新日期", description="数据写入日期")
    concept_name_zh: str | None = Field(None, title="概念中文名", description="Morningstar 分类中文名")
    etf_name_zh: str | None = Field(None, title="ETF 中文名", description="ETF 简称（中文）")
    description_zh: str | None = Field(None, title="ETF 中文介绍", description="ETF 一句话中文描述")


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

    concept: str = Field(title="概念名称", description="Morningstar 板块分类名（英文）")
    concept_name_zh: str | None = Field(None, title="概念中文名", description="中文板块名称")
    etf_count: int = Field(title="ETF 数量", description="该概念下通过 AUM 过滤的 ETF 数量")
    stock_count: int = Field(title="成分股数量", description="最新日期的成分股总数")
    top_symbols: list[str] = Field(title="核心成分股", description="etf_count 最高的前 5 只股票代码")
    last_updated: datetime.date = Field(title="最后更新日", description="最新持仓快照日期")
