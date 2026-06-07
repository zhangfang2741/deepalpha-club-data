"""
YouTube 创作者新闻流 Pipeline

调度建议：每 30 分钟运行一次（cron: */30 * * * *）

流程：
  1. 读取 youtube_channels.yaml 获取启用的频道列表
  2. 每个频道拉取 RSS Feed（最近 15 个视频）
  3. 过滤已处理的视频（PostgreSQL 去重）
  4. 对新视频：提取字幕 → MiniMax 中文摘要 → 推送 Telegram → 记录 DB
"""

import asyncio
import logging
from pathlib import Path

import httpx
import yaml

from deepalpha.domain.creator.models import ChannelConfig, YouTubeVideo
from deepalpha.infrastructure.config import CreatorNewsPipelineConfig
from deepalpha.infrastructure.db.creator_repo import CreatorRepo
from deepalpha.infrastructure.providers.minimax.summarizer import summarize_video_zh
from deepalpha.infrastructure.providers.youtube.feed_loader import (
    fetch_channel_videos,
    get_transcript,
)
from deepalpha.infrastructure.telegram.sender import TelegramSender
from deepalpha.domain.creator.models import CreatorPost

logger = logging.getLogger(__name__)


def load_channels(yaml_path: str) -> list[ChannelConfig]:
    """从 YAML 配置文件加载频道列表。"""
    path = Path(yaml_path)
    if not path.exists():
        logger.warning("频道配置文件不存在: %s", yaml_path)
        return []
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    channels = []
    for item in data.get("channels", []):
        try:
            ch = ChannelConfig.model_validate(item)
            if ch.enabled:
                channels.append(ch)
        except Exception as exc:
            logger.warning("频道配置解析失败 %s: %s", item, exc)
    return channels


async def process_video(
    video: YouTubeVideo,
    repo: CreatorRepo,
    sender: TelegramSender,
    minimax_api_key: str,
) -> None:
    """处理单个新视频：摘要 → 发送 → 记录。"""
    logger.info("处理新视频: [%s] %s", video.channel_name, video.title)

    transcript = await get_transcript(video.video_id)
    if transcript:
        logger.debug("获取到字幕，长度: %d 字符", len(transcript))
    else:
        logger.debug("无字幕，使用标题+描述生成摘要")

    summary_zh = await summarize_video_zh(
        api_key=minimax_api_key,
        title=video.title,
        transcript=transcript,
        description=video.description,
    )

    post = CreatorPost(
        video_id=video.video_id,
        channel_id=video.channel_id,
        channel_name=video.channel_name,
        title=video.title,
        url=video.url,
        published_at=video.published_at,
        summary_zh=summary_zh,
        thumbnail_url=video.thumbnail_url,
    )

    message_id = await sender.send_post(post)

    # 无论发送成功与否，只要消息内容已生成就记录（避免 Telegram 限速时无限重试）
    # 若 message_id 为 None 且是干运行模式，正常记录；若是真实发送失败，也记录防止刷屏
    await repo.mark_processed(video.video_id, video.channel_id, message_id)


async def main(config: CreatorNewsPipelineConfig | None = None) -> None:
    if config is None:
        config = CreatorNewsPipelineConfig()

    channels = load_channels(config.youtube_channels_yaml)
    if not channels:
        logger.warning("无可用频道配置，退出")
        return

    logger.info("开始处理 %d 个频道...", len(channels))

    sender = TelegramSender(
        bot_token=config.telegram_bot_token,
        channel_id=config.telegram_channel_id,
    )

    async with CreatorRepo(config.asyncpg_dsn()) as repo:
        async with httpx.AsyncClient() as http_client:
            for channel in channels:
                logger.info("轮询频道: %s (%s)", channel.channel_name, channel.channel_id)
                videos = await fetch_channel_videos(channel, http_client)
                logger.info("获取到 %d 个视频", len(videos))

                # 按发布时间正序处理（先旧后新，保持频道时序）
                sorted_videos = sorted(videos, key=lambda v: v.published_at)

                new_count = 0
                for video in sorted_videos:
                    if await repo.is_processed(video.video_id):
                        continue
                    try:
                        await process_video(video, repo, sender, config.minimax_api_key)
                        new_count += 1
                        # 避免 Telegram 限速（每秒最多 1 条推送）
                        await asyncio.sleep(1.5)
                    except Exception as exc:
                        logger.error(
                            "处理视频失败 [%s] %s: %s",
                            channel.channel_name,
                            video.video_id,
                            exc,
                        )

                logger.info("频道 %s 新增推送: %d 条", channel.channel_name, new_count)

    logger.info("Pipeline 运行完毕")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(main())
