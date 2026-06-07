"""
MiniMax LLM 主题提取器

从信号文本中提取细粒度技术/基础设施/工程概念关键词。
复用 translator.py 中相同的 API 调用模式和 _extract_json 逻辑。
"""
import json
import logging
import httpx
from deepalpha.domain.signal_radar.models import ExtractedTheme, SignalCategory

logger = logging.getLogger(__name__)
_API_URL = "https://api.minimax.chat/v1/chat/completions"
_MODEL = "MiniMax-Text-01"
_MIN_CONFIDENCE = 0.6

_SYSTEM_PROMPT = """你是一个专业的技术信号分析师，从公司文件中提取细粒度的技术/基础设施/工程关键词。

提取规则：
✅ 合格（提取这些）：
- 技术关键词：MCP、Agent Memory、Mixture of Experts、RAG Pipeline、RLHF Pipeline
- 基础设施组件：HBM3e、NVLink、InfiniBand、液冷机柜、定制ASIC、CoWoS封装、光互连
- 新兴工程概念：AI Compiler、Inference Optimization、Post-Training、Speculative Decoding

❌ 不合格（不要提取这些）：
- 行业大词：AI、云计算、数字化转型、机器学习
- 公司名/品牌名：NVIDIA、OpenAI（但产品型号如"H100"可以）
- 财务指标：营收增长、毛利率、EPS

判断标准：
1. 可以出现在工程师招聘 JD 的技能要求中
2. 可以对应到具体 Capex 支出或融资金额
3. 多家公司同期提到（跨公司共现）

输出格式（严格 JSON，不要 markdown 代码块）：
{"themes":[{"name":"标准化名称","category":"tech_concept|infra_component|engineering_concept","confidence":0.0-1.0}]}

每条信号最多提取5个主题，名称使用英文缩写或规范术语。"""


def _extract_json(raw: str) -> dict:
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


class ThemeExtractor:
    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._api_key = api_key

    async def extract(self, text: str, source_type: str) -> list[ExtractedTheme]:
        """从文本中提取主题，返回置信度 >= 0.6 的结果。"""
        if not text.strip():
            return []
        try:
            resp = await self._client.post(
                _API_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": _MODEL,
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": f"[{source_type}] {text[:2000]}"},
                    ],
                    "temperature": 0.1,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("主题提取 API 失败: %s", exc)
            return []

        try:
            content = resp.json()["choices"][0]["message"]["content"]
            data = _extract_json(content)
            themes = []
            for t in data.get("themes", []):
                try:
                    theme = ExtractedTheme(
                        name=t["name"],
                        category=SignalCategory(t["category"]),
                        confidence=float(t["confidence"]),
                    )
                    if theme.confidence >= _MIN_CONFIDENCE:
                        themes.append(theme)
                except Exception:
                    continue
            return themes
        except Exception as exc:
            logger.error("主题解析失败: %s", exc)
            return []
