"""
MiniMax LLM 主题深度分析器

基于信号雷达提取的主题，对该主题的技术/业务含义进行多维度分析，
输出 5 个维度的结构化 Markdown 表格：
  1. 核心产品
  2. 企业定位
  3. 竞争格局
  4. 供应链关系
  5. 生态位
"""

import logging
import re

import httpx

logger = logging.getLogger(__name__)


_XBRL_PATTERN = re.compile(
    r'^(?:'
    r'\w+-\d{8}\s'           # nvda-20260520 ...
    r'|\d{10}\s'             # 0001045810 ...
    r'|8-K\s'                # 8-K false ...
    r'|(?:false|true)\s\d'   # false 0000097476 ... (XBRL boolean)
    r'|<\?xml'               # <?xml ...
    r'|<[A-Za-z]+[\s>]'      # <root> 或 <tag attr=...
    r')',
    re.IGNORECASE,
)


def _is_readable_text(text: str) -> bool:
    """判断 text 是否为可读自然语言（过滤 XBRL/XML/SEC 原始乱码）。"""
    if not text or len(text) < 30:
        return False
    # 命中 XBRL/XML 模式的直接排除
    if _XBRL_PATTERN.match(text.strip()):
        return False
    # 字母字符占比低于 35% 的认为是结构化数据乱码
    alpha = sum(1 for c in text if c.isalpha())
    return alpha / len(text) >= 0.35


def _clean_snippet(text: str) -> str:
    """清理 snippet：去掉多余空白，截断到合理长度。"""
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:300]

_API_URL = "https://api.minimax.chat/v1/chat/completions"
_MODEL = "MiniMax-Text-01"


async def analyze_theme(
    api_key: str,
    theme_name: str,
    signals: list[dict],
) -> dict:
    """
    对雷达主题进行多维度 AI 业务分析。

    Args:
        api_key: MiniMax API key
        theme_name: 主题名称（如 "HBM3e"、"NVLink"）
        signals: 该主题的原始信号列表，每条含 ticker / source_type / text_snippet / confidence

    Returns:
        {
            "products":  str (Markdown table),
            "position":  str (Markdown table),
            "competition": str (Markdown table),
            "supply_chain": str (Markdown table),
            "ecosystem": str (Markdown table),
        }
    """
    if not api_key:
        return {dim: "【请配置 MINIMAX_API_KEY】" for dim in ("products", "position", "competition", "supply_chain", "ecosystem")}

    if not signals:
        return {dim: "暂无信号数据" for dim in ("products", "position", "competition", "supply_chain", "ecosystem")}

    # 汇总参与公司，过滤掉 XBRL 乱码 snippet
    ticker_set = set()
    signal_lines = []
    for s in signals:
        ticker_set.add(s["ticker"])
        raw_snippet = s.get("text_snippet") or ""
        if not _is_readable_text(raw_snippet):
            continue  # 跳过 XBRL/XML 乱码
        snippet = _clean_snippet(raw_snippet)
        source = s.get("source_type", "unknown")
        conf = s.get("confidence", 0)
        signal_lines.append(
            f"- [{source}] {s['ticker']}（置信{conf:.2f}）: {snippet}"
        )

    tickers = sorted(ticker_set)
    signal_context = "\n".join(signal_lines[:20]) if signal_lines else "（无可读信号原文，请基于训练知识分析）"
    ticker_list = ", ".join(tickers[:20])

    prompt = _build_prompt(theme_name, ticker_list, signal_context)

    try:
        async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
            resp = await client.post(
                _API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": _MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning("主题分析 LLM 调用失败 [%s]: %s", theme_name, exc)
        return {dim: f"【分析失败: {exc}】" for dim in ("products", "position", "competition", "supply_chain", "ecosystem")}

    return _parse_analysis(content)


def _build_prompt(theme_name: str, ticker_list: str, signal_context: str) -> str:
    return f"""你是一位专业的美股科技行业研究分析师。请对「{theme_name}」技术主题进行深度业务分析。

## 主题概述
「{theme_name}」是当前资本市场关注的技术趋势，以下是相关信号数据（来自 SEC 8-K 财报电话会、XBRL 资本支出、Form D 融资申报等）：

## 参与公司
{ticker_list}

## 信号原文片段（按置信度排序）
{signal_context}

## 分析要求
请基于信号数据和你的训练知识（世界知识）对上述主题进行分析：
- 对于知名技术主题，使用你知道的真实技术背景
- 结合信号原文中的业务描述做具体分析
- 所有内容用**简体中文**输出

请依次输出以下5个表格，每个表格前标注维度标题：

## 维度一：核心产品
分析该主题涉及的核心产品/技术/服务，一句话描述。
| 公司 | 核心产品/服务 | 备注 |
| AAPL | iPhone、Mac芯片中的{theme_name}应用 |  |

## 维度二：企业定位
分析各公司在该主题中的市场定位、规模、核心优势与差异化。
| 公司 | 定位 | 规模/营收级别 | 备注 |

## 维度三：竞争格局
分析主题内公司之间的竞争关系（直接竞争/互补/无关）。
| 公司 A | 公司 B | 竞争关系 | 备注 |

## 维度四：供应链关系
分析主题内公司之间的上下游供应商/客户关系。
| 上游 | 关系描述 | 下游 | 备注 |

## 维度五：生态位
分析各公司在整体生态系统中的角色定位（平台层/基础设施层/应用层/服务层）。
| 公司 | 生态位 | 角色描述 |
"""


def _parse_analysis(content: str) -> dict:
    """从 LLM 输出中解析出 5 个维度的表格文本。"""
    result: dict = {dim: "" for dim in ("products", "position", "competition", "supply_chain", "ecosystem")}
    dimension_map = {
        "维度一": "products",
        "维度二": "position",
        "维度三": "competition",
        "维度四": "supply_chain",
        "维度五": "ecosystem",
    }

    current: str | None = None
    lines = content.split("\n")
    for line in lines:
        stripped = line.strip()
        for prefix, key in dimension_map.items():
            if prefix in stripped:
                current = key
                break
        else:
            if current and stripped:
                result[current] += line + "\n"

    # 如果完全没解析出任何维度，把全文放入所有维度（至少显示原始内容）
    if not any(result.values()):
        for key in result:
            result[key] = content
    return result
