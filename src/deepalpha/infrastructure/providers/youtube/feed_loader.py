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


async def transcribe_via_groq(
    video_id: str,
    groq_api_key: str,
    cookies_file: str = "",
) -> str | None:
    """用 yt-dlp 下载 MP3 音频，再通过 Groq Whisper API 转录。

    Groq 免费额度充裕，速度极快（21 分钟视频约 30 秒）。
    依赖：系统安装 yt-dlp。
    """
    import subprocess
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        mp3_path = Path(tmpdir) / f"{video_id}.mp3"

        # yt-dlp 下载音频为 MP3（64kbps，21 分钟 ≈ 10MB，远低于 Groq 25MB 限制）
        dl_cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "5",   # ~64kbps，Whisper 识别够用
            "--output", str(mp3_path),
            "--no-playlist",
            "--quiet",
        ]
        if cookies_file and Path(cookies_file).exists():
            dl_cmd += ["--cookies", cookies_file]
        dl_cmd.append(f"https://www.youtube.com/watch?v={video_id}")

        logger.info("开始下载音频 [%s]", video_id)
        try:
            r = subprocess.run(dl_cmd, capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                logger.warning("yt-dlp 下载失败 [%s]: %s", video_id, r.stderr[:300])
                return None
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp 下载超时 [%s]", video_id)
            return None

        if not mp3_path.exists():
            logger.warning("音频文件未生成 [%s]", video_id)
            return None

        size_mb = mp3_path.stat().st_size / 1024 / 1024
        logger.info("音频就绪 [%s] %.1fMB，发送至 Groq Whisper 转录", video_id, size_mb)

        if size_mb > 24:
            logger.warning("音频超过 25MB 限制 [%s] %.1fMB，跳过转录", video_id, size_mb)
            return None

        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=groq_api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            with mp3_path.open("rb") as f:
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=f,
                    response_format="text",
                )
            text = str(transcription).strip()
            logger.info("Groq 转录完成 [%s] %d 字符", video_id, len(text))
            return text or None
        except Exception as exc:
            logger.warning("Groq 转录失败 [%s]: %s", video_id, exc)
            return None


async def get_transcript(
    video_id: str,
    cookies_file: str = "",
    groq_api_key: str = "",
) -> str | None:
    """提取视频文字内容，按以下优先级：
    1. youtube-transcript-api 字幕轨道（快，无需下载）
    2. yt-dlp + Groq Whisper API 音频转录（用于烧录字幕或无字幕轨道的视频）

    cookies_file: Netscape 格式 cookies.txt，用于访问需登录的字幕。
    groq_api_key: 有值时才启用 Groq 转录回退。
    """
    def _fetch_subtitle() -> str | None:
        try:
            from http.cookiejar import MozillaCookieJar
            from requests import Session
            from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore[import-untyped]
            from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled  # type: ignore[import-untyped]

            http_client: Session | None = None
            if cookies_file:
                from pathlib import Path
                if Path(cookies_file).exists():
                    jar = MozillaCookieJar(cookies_file)
                    jar.load(ignore_discard=True, ignore_expires=True)
                    session = Session()
                    session.cookies = jar  # type: ignore[assignment]
                    http_client = session
                else:
                    logger.warning("cookies 文件不存在: %s", cookies_file)

            api = YouTubeTranscriptApi(http_client=http_client)
            transcript_list = api.list(video_id)

            for langs in [["en", "en-US", "en-GB"], ["zh-Hans", "zh-Hant", "zh"]]:
                try:
                    fetched = transcript_list.find_transcript(langs).fetch()
                    text = " ".join(seg.text for seg in fetched if seg.text)
                    logger.info("字幕轨道获取成功 [%s] 语言=%s, 段落数=%d", video_id, langs[0], len(fetched))
                    return text
                except NoTranscriptFound:
                    continue

            try:
                fetched = transcript_list.find_generated_transcript(["en"]).fetch()
                text = " ".join(seg.text for seg in fetched if seg.text)
                logger.info("自动字幕获取成功 [%s], 段落数=%d", video_id, len(fetched))
                return text
            except NoTranscriptFound:
                return None

        except Exception:
            return None

    # 优先尝试字幕轨道（快，无需下载）
    subtitle = await asyncio.to_thread(_fetch_subtitle)
    if subtitle:
        return subtitle

    # 回退：Groq Whisper 音频转录
    if groq_api_key:
        logger.info("字幕轨道不可用 [%s]，尝试 Groq Whisper 音频转录", video_id)
        return await transcribe_via_groq(video_id, groq_api_key, cookies_file)

    logger.warning("视频 %s 无字幕轨道，且未配置 GROQ_API_KEY，跳过转录", video_id)
    return None
