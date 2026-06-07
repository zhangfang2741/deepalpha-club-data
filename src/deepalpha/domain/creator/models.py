"""
YouTube 创作者新闻流领域模型（domain 层）

包含频道配置、视频元数据及已处理的创作者帖子。
"""

import datetime

from pydantic import BaseModel, Field


class ChannelConfig(BaseModel):
    """YouTube 频道配置"""
    channel_id: str = Field(title="频道 ID（UC... 格式）")
    channel_name: str = Field(title="频道显示名称")
    enabled: bool = Field(True, title="是否启用轮询")


class YouTubeVideo(BaseModel):
    """YouTube 视频基本信息（从 RSS 解析）"""
    video_id: str = Field(title="视频 ID")
    channel_id: str = Field(title="所属频道 ID")
    channel_name: str = Field(title="频道名称")
    title: str = Field(title="视频标题")
    url: str = Field(title="视频链接")
    published_at: datetime.datetime = Field(title="发布时间（UTC）")
    description: str | None = Field(None, title="视频描述")
    thumbnail_url: str | None = Field(None, title="缩略图链接")


class CreatorPost(BaseModel):
    """已处理的创作者帖子（含 AI 中文摘要，准备推送）"""
    video_id: str = Field(title="视频 ID")
    channel_id: str = Field(title="频道 ID")
    channel_name: str = Field(title="频道名称")
    title: str = Field(title="视频标题")
    url: str = Field(title="视频链接")
    published_at: datetime.datetime = Field(title="发布时间（UTC）")
    summary_zh: str = Field(title="AI 生成中文摘要")
    thumbnail_url: str | None = Field(None, title="缩略图链接")
