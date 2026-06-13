"""
MiniMax AI 视频内容翻译服务

将 YouTube 视频字幕翻译并整理为可直接阅读的中文文章。
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_API_URL = "https://api.minimax.chat/v1/chat/completions"
_MODEL = "MiniMax-Text-01"
_MAX_TRANSCRIPT_CHARS = 8000
_MAX_DESC_CHARS = 800


async def translate_to_article_zh(
    api_key: str,
    title: str,
    transcript: str | None,
    description: str | None = None,
) -> str:
    """将视频字幕翻译为结构完整的中文文章。

    优先使用字幕（transcript），无字幕时退化为标题+描述生成摘要。
    API 不可用时返回兜底文本。
    """
    if not api_key:
        return _fallback(title, description)

    if transcript:
        content_block = f"视频字幕原文：\n{transcript[:_MAX_TRANSCRIPT_CHARS]}"
        instruction = (
            "请将以上视频字幕翻译并整理为一篇结构清晰的中文文章（600-900字），要求：\n"
            "1. 完整保留所有重要观点、数据、案例和结论，不要省略关键信息\n"
            "2. 按逻辑顺序重新组织段落，使文章读起来流畅自然\n"
            "3. 使用书面中文，专业财经词汇准确翻译\n"
            "4. 直接输出文章正文，分段落，不要加标题"
        )
    elif description:
        content_block = f"视频描述：\n{description[:_MAX_DESC_CHARS]}"
        instruction = (
            "根据以上视频标题和描述，用中文写一段 200-300 字的内容介绍，\n"
            "说明该视频可能涵盖的核心内容，语言专业自然。\n"
            "直接输出正文，不要加标题。"
        )
    else:
        return f"【{title}】（视频暂无字幕或描述）"

    prompt = (
        f"视频标题：{title}\n\n"
        f"{content_block}\n\n"
        f"{instruction}"
    )

    try:
        async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
            resp = await client.post(
                _API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": _MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 2000,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            # 去掉 Markdown 代码块标记
            content = _strip_markdown(content)
            return content
    except Exception as exc:
        logger.warning("MiniMax 文章翻译失败 [%s]: %s", title, exc)
        return _fallback(title, description)


def _strip_markdown(text: str) -> str:
    """去掉 Markdown 代码块标记，返回纯文本。"""
    import re
    text = re.sub(r'^```[a-z]*\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    return text.strip()


def _fallback(title: str, description: str | None) -> str:
    """MiniMax 不可用时的兜底文本。"""
    if description:
        return description[:500].rstrip() + ("…" if len(description) > 500 else "")
    return f"【{title}】"
