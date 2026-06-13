"""
MiniMax AI 翻译服务

批量将 Morningstar 概念名、ETF 名称翻译为中文，
并为每只 ETF 生成一句话中文介绍。
"""

import json
import logging

import httpx

logger = logging.getLogger(__name__)

_API_URL = "https://api.minimax.chat/v1/chat/completions"
_MODEL = "MiniMax-Text-01"


async def _chat(api_key: str, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
        resp = await client.post(
            _API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": _MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def _extract_json(raw: str) -> dict:
    """从模型输出中提取 JSON，兼容 markdown 代码块包裹。"""
    # 去掉 ```json ... ``` 或 ``` ... ```
    text = raw.strip()
    if "```" in text:
        start = text.find("```")
        end = text.rfind("```")
        if start != end:
            text = text[start + 3:end]
            if text.startswith("json"):
                text = text[4:]
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


async def translate_concepts(api_key: str, concepts: list[str]) -> dict[str, str]:
    """
    批量翻译 Morningstar 板块名称为中文（2-6字）。
    返回 {英文名: 中文名} 字典。
    """
    if not api_key:
        logger.warning("minimax_api_key 未配置，跳过概念翻译")
        return {}
    prompt = (
        "请将以下美股 ETF 投资主题分类名翻译为中文（2-6字，简洁专业）。\n"
        "只返回 JSON，格式：{\"英文名\": \"中文名\", ...}\n\n"
        + "\n".join(f"- {c}" for c in concepts)
    )
    try:
        raw = await _chat(api_key, prompt)
        return _extract_json(raw)
    except Exception as e:
        logger.warning("概念翻译失败: %s", e)
        return {}


async def describe_etfs(api_key: str, etf_infos: list[tuple[str, str]]) -> dict[str, tuple[str, str]]:
    """
    批量为 ETF 生成中文简称和一句话介绍。

    Args:
        api_key: MiniMax API key
        etf_infos: [(symbol, english_name), ...]

    Returns:
        {symbol: (etf_name_zh, description_zh)}
    """
    if not api_key or not etf_infos:
        return {}

    lines = "\n".join(f"- {sym}: {name}" for sym, name in etf_infos)
    prompt = (
        "请为以下美股 ETF 生成中文简称（4-10字）和一句话投资策略介绍（15-25字）。\n"
        "只返回 JSON，格式：\n"
        "{\"SMH\": {\"name_zh\": \"半导体ETF\", \"desc_zh\": \"追踪美国半导体行业龙头企业的表现\"}, ...}\n\n"
        + lines
    )
    try:
        raw = await _chat(api_key, prompt)
        data = _extract_json(raw)
        return {
            sym: (v.get("name_zh", ""), v.get("desc_zh", ""))
            for sym, v in data.items()
            if isinstance(v, dict)
        }
    except Exception as e:
        logger.warning("ETF 描述生成失败: %s", e)
        return {}
