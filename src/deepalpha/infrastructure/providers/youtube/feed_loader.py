"""
YouTube RSS Feed 加载器

通过 YouTube 公开 RSS Feed 获取频道最新视频，
并使用 youtube-transcript-api 提取字幕文本。
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx

from deepalpha.domain.creator.models import ChannelConfig, YouTubeVideo

logger = logging.getLogger(__name__)

_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


async def fetch_channel_videos(
    channel: ChannelConfig,
    client: httpx.AsyncClient,
) -> list[YouTubeVideo]:
    """获取频道最新视频（RSS 返回最近 15 条）。"""
    url = _RSS_URL.format(channel_id=channel.channel_id)
    try:
        resp = await client.get(url, timeout=15.0)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("获取频道 %s RSS 失败: %s", channel.channel_name, exc)
        return []

    return _parse_feed(resp.text, channel)


def _parse_feed(xml_text: str, channel: ChannelConfig) -> list[YouTubeVideo]:
    """解析 YouTube RSS XML，返回视频列表。"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.warning("解析 %s RSS XML 失败: %s", channel.channel_name, exc)
        return []

    videos: list[YouTubeVideo] = []
    for entry in root.findall("atom:entry", _NS):
        video_id_el = entry.find("yt:videoId", _NS)
        title_el = entry.find("atom:title", _NS)
        link_el = entry.find("atom:link[@rel='alternate']", _NS)
        published_el = entry.find("atom:published", _NS)

        if video_id_el is None or title_el is None or published_el is None:
            continue

        video_id = (video_id_el.text or "").strip()
        title = (title_el.text or "").strip()
        published_str = (published_el.text or "").strip()
        link = link_el.get("href", f"https://www.youtube.com/watch?v={video_id}") if link_el is not None else f"https://www.youtube.com/watch?v={video_id}"

        try:
            published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        except ValueError:
            published_at = datetime.now(timezone.utc)

        # 缩略图和描述（media namespace）
        media_group = entry.find("media:group", _NS)
        thumbnail_url: str | None = None
        description: str | None = None
        if media_group is not None:
            thumb_el = media_group.find("media:thumbnail", _NS)
            if thumb_el is not None:
                thumbnail_url = thumb_el.get("url")
            desc_el = media_group.find("media:description", _NS)
            if desc_el is not None:
                description = (desc_el.text or "").strip() or None

        if not video_id or not title:
            continue

        videos.append(
            YouTubeVideo(
                video_id=video_id,
                channel_id=channel.channel_id,
                channel_name=channel.channel_name,
                title=title,
                url=link,
                published_at=published_at,
                description=description,
                thumbnail_url=thumbnail_url,
            )
        )

    return videos


async def get_transcript(video_id: str) -> str | None:
    """提取视频字幕文本（优先英文，其次任意语言）。

    youtube-transcript-api 是同步库，通过 asyncio.to_thread 调用。
    无字幕时返回 None。
    """
    def _fetch() -> str | None:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore[import-untyped]
            from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound  # type: ignore[import-untyped]

            try:
                segments = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=["en", "en-US", "en-GB", "zh-Hans", "zh-Hant", "zh"]
                )
            except (NoTranscriptFound, Exception):
                # 回退：获取任意可用语言
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript(["en"])
                segments = transcript.fetch()

            return " ".join(seg["text"] for seg in segments if seg.get("text"))
        except Exception as exc:
            logger.debug("视频 %s 无可用字幕: %s", video_id, exc)
            return None

    try:
        return await asyncio.to_thread(_fetch)
    except Exception as exc:
        logger.debug("字幕提取线程异常 %s: %s", video_id, exc)
        return None
