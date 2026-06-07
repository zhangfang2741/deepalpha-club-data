"""
YouTube 创作者新闻流协议接口（domain 层）

定义 infrastructure 层需要实现的抽象接口，application 层依赖此协议。
"""

from typing import Protocol

from deepalpha.domain.creator.models import CreatorPost


class ICreatorRepo(Protocol):
    """创作者视频处理记录仓储协议"""

    async def is_processed(self, video_id: str) -> bool:
        """检查视频是否已处理过"""
        ...

    async def mark_processed(
        self, video_id: str, channel_id: str, message_id: int | None
    ) -> None:
        """将视频标记为已处理，记录 Telegram message_id（可为空）"""
        ...


class ICreatorSender(Protocol):
    """创作者帖子发送协议"""

    async def send_post(self, post: CreatorPost) -> int | None:
        """发送帖子，返回 Telegram message_id；干运行模式返回 None"""
        ...
