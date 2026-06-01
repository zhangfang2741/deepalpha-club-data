"""
新闻领域模型（domain 层）

包含财经新闻文章及其相关元数据。
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class NewsArticle(BaseModel):
    """新闻文章数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    title: str = Field(title="标题", description="新闻文章标题")
    url: str = Field(title="链接", description="新闻原文 URL")
    published_date: datetime.datetime | None = Field(None, title="发布时间", description="新闻发布的 UTC 时间")
    site: str | None = Field(None, title="来源网站", description="新闻发布媒体名称")
    text: str | None = Field(None, title="摘要", description="新闻内容摘要")
    symbol: str | None = Field(None, title="相关股票", description="新闻关联的股票代码（若有）")
    sentiment: str | None = Field(None, title="情绪倾向", description="Positive / Negative / Neutral")
