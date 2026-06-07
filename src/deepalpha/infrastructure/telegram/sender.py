"""
Telegram 频道发送器（infrastructure 适配器）

实现 ICreatorSender 协议，通过 Bot API 将创作者帖子推送到 Telegram 频道。
channel_id 为空时进入干运行模式（仅打印，不发送）。
"""

import logging

import httpx

from deepalpha.domain.creator.models import CreatorPost

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org/bot{token}"
_MAX_MESSAGE_LEN = 4096


class TelegramSender:
    """Telegram Bot API 发送器。

    Args:
        bot_token: Telegram Bot Token（由 @BotFather 创建）
        channel_id: 目标频道 ID（@username 或 -100xxxxxxx），
                    空字符串时进入干运行模式
    """

    def __init__(self, bot_token: str, channel_id: str) -> None:
        self._token = bot_token
        self._channel_id = channel_id
        self._api_base = _API_BASE.format(token=bot_token)
        self._dry_run = not channel_id

    async def send_post(self, post: CreatorPost) -> int | None:
        """发送创作者帖子到 Telegram 频道。

        Returns:
            成功时返回 Telegram message_id；干运行或失败时返回 None
        """
        text = _format_message(post)

        if self._dry_run:
            logger.info("[DRY-RUN] Telegram 消息预览:\n%s", text)
            return None

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{self._api_base}/sendMessage",
                    json={
                        "chat_id": self._channel_id,
                        "text": text[:_MAX_MESSAGE_LEN],
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                message_id: int = data["result"]["message_id"]
                logger.info(
                    "已推送到 Telegram [msg_id=%d]: %s", message_id, post.title
                )
                return message_id
        except Exception as exc:
            logger.error("Telegram 发送失败 [%s]: %s", post.title, exc)
            return None


def _format_message(post: CreatorPost) -> str:
    """将创作者帖子格式化为 Telegram HTML 文章消息。"""
    pub_date = post.published_at.strftime("%Y-%m-%d")
    # 文章正文超长时截断（预留 header + footer 约 150 字符）
    article = _esc(post.content_zh)
    max_article_len = _MAX_MESSAGE_LEN - 200
    if len(article) > max_article_len:
        article = article[:max_article_len] + "…"

    return (
        f"<b>{_esc(post.title)}</b>\n"
        f"<i>{_esc(post.channel_name)} · {pub_date}</i>\n\n"
        f"{article}\n\n"
        f'<a href="{post.url}">▶ 原视频</a>'
    )


def _esc(text: str) -> str:
    """HTML 转义（Telegram HTML parse mode 要求）。"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
