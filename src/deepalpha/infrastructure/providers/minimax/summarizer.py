"""
MiniMax AI 视频内容摘要服务

将 YouTube 视频字幕或标题+描述总结为中文摘要（150-200字）。
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_API_URL = "https://api.minimax.chat/v1/chat/completions"
_MODEL = "MiniMax-Text-01"
_MAX_TRANSCRIPT_CHARS = 4000
_MAX_DESC_CHARS = 800


async def summarize_video_zh(
    api_key: str,
    title: str,
    transcript: str | None,
    description: str | None = None,
) -> str:
    """将视频内容生成中文摘要。

    优先使用字幕（transcript），无字幕时退化为标题+描述。
    API 不可用时返回兜底摘要。
    """
    if not api_key:
        return _fallback_summary(title, description)

    if transcript:
        content_block = f"视频字幕（节选）：\n{transcript[:_MAX_TRANSCRIPT_CHARS]}"
    elif description:
        content_block = f"视频描述：\n{description[:_MAX_DESC_CHARS]}"
    else:
        return f"【{title}】（暂无内容摘要）"

    prompt = (
        "你是一位专业的财经内容编辑，擅长将英文视频内容提炼成简洁的中文资讯。\n\n"
        f"视频标题：{title}\n\n"
        f"{content_block}\n\n"
        "请用中文写一段 150-200 字的视频摘要，要求：\n"
        "1. 提炼核心观点和关键信息\n"
        "2. 语言简洁专业，适合金融投资者阅读\n"
        "3. 直接输出摘要正文，不要加标题或前言"
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                _API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": _MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("MiniMax 摘要生成失败 [%s]: %s", title, exc)
        return _fallback_summary(title, description)


def _fallback_summary(title: str, description: str | None) -> str:
    """MiniMax 不可用时的兜底摘要。"""
    if description:
        short_desc = description[:200].rstrip()
        return f"{short_desc}…"
    return f"【{title}】"
