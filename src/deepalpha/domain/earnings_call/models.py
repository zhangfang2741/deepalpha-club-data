"""财报电话会议领域模型（domain 层）

包含财报电话会议日历事件、英文原文以及完整处理结果等数据模型。
"""

import datetime

from pydantic import BaseModel, Field


class EarningsCallEvent(BaseModel):
    """日历上某场财报电话会议（可能尚未召开）"""

    symbol: str = Field(title="股票代码")
    date: datetime.date = Field(title="会议日期")
    year: int = Field(title="财年")
    quarter: int = Field(title="季度", ge=1, le=4)
    has_transcript: bool = Field(title="是否已有原文")


class EarningsCallTranscript(BaseModel):
    """FMP API 返回的英文原文"""

    symbol: str = Field(title="股票代码")
    year: int = Field(title="财年")
    quarter: int = Field(title="季度")
    date: datetime.date = Field(title="会议日期")
    content: str = Field(title="英文全文")


class EarningsCallDetail(BaseModel):
    """完整处理结果，翻译后缓存到 PostgreSQL"""

    symbol: str = Field(title="股票代码")
    year: int = Field(title="财年")
    quarter: int = Field(title="季度")
    date: datetime.date = Field(title="会议日期")
    company_name: str = Field(title="公司名称")
    description_zh: str = Field(title="公司简介（中文）")
    products_zh: str = Field(title="主要产品（中文）")
    summary_zh: str = Field(title="AI 摘要（中文，约400字）")
    transcript_zh: str = Field(title="完整原文中文翻译")
    translated_at: datetime.datetime = Field(title="翻译时间")
