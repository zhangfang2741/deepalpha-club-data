"""
MiniMax LLM 概念深度分析器

基于 LLM 训练知识 + ETF 元数据，对概念内公司进行多维度业务分析，
输出 5 个维度的结构化 Markdown 表格：
  1. 核心产品
  2. 企业定位
  3. 竞争格局
  4. 供应链关系
  5. 生态位
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_API_URL = "https://api.minimax.chat/v1/chat/completions"
_MODEL = "MiniMax-Text-01"

_TABLE_HEADERS = {
    "products": "| 公司 | 核心产品/服务 | 备注 |",
    "position": "| 公司 | 定位 | 规模/营收级别 | 备注 |",
    "competition": "| 公司 A | 公司 B | 竞争关系 | 备注 |",
    "supply_chain": "| 上游 | 关系 | 下游 | 备注 |",
    "ecosystem": "| 公司 | 生态位 | 角色描述 |",
}


async def analyze_concept(
    api_key: str,
    concept_name: str,
    concept_name_zh: str | None,
    stocks: list[dict],
    etfs: list[dict],
) -> dict:
    """
    对概念进行多维度 AI 分析。

    Args:
        api_key: MiniMax API key
        concept_name: 英文概念名（如 "Technology"）
        concept_name_zh: 中文概念名
        stocks: [{symbol, name, etf_count, total_weight, etfs}, ...]
        etfs: [{etf_symbol, etf_name, description_zh}, ...]

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

    if not stocks:
        return {dim: "暂无成分股数据" for dim in ("products", "position", "competition", "supply_chain", "ecosystem")}

    # ── 构建上下文 ──────────────────────────────────────────────────────────
    stock_lines = []
    for s in stocks[:30]:
        etf_list = ", ".join(s.get("etfs", [])[:5])
        weight = s.get("total_weight", 0)
        name = s.get("name") or s["symbol"]
        stock_lines.append(
            f"- {s['symbol']}（{name}）| ETF覆盖={s.get('etf_count', 0)} | "
            f"合计权重={weight:.2f}% | 持有ETF: {etf_list or '无'}"
        )

    etf_lines = []
    for e in etfs[:10]:
        desc = e.get("description_zh") or e.get("etf_name") or e.get("etf_name_zh") or e.get("etf_symbol")
        etf_lines.append(f"- {e['etf_symbol']}: {desc}")

    stock_context = "\n".join(stock_lines)
    etf_context = "\n".join(etf_lines) or "（无 ETF 描述数据）"
    cn = concept_name_zh or concept_name

    prompt = _build_prompt(concept_name, cn, stock_context, etf_context)

    try:
        async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
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
        logger.warning("概念分析 LLM 调用失败 [%s]: %s", concept_name, exc)
        return {dim: f"【分析失败: {exc}】" for dim in ("products", "position", "competition", "supply_chain", "ecosystem")}

    return _parse_analysis(content)


def _build_prompt(concept_name: str, concept_name_zh: str, stock_context: str, etf_context: str) -> str:
    return f"""你是一位专业的美股科技行业研究分析师。请对「{concept_name_zh}（{concept_name}）」概念板块进行深度业务分析。

## 概念板块成分股（按权重排序）:
{stock_context}

## 相关 ETF 信息:
{etf_context}

## 分析要求
请基于你的训练知识（世界知识）对上述公司进行分析，输出**5个维度**的结构化表格。
- 对于知名大公司（NVDA、AAPL、MSFT、AMZN、META、GOOG、TSLA、AVGO 等），使用你知道的真实业务信息
- 对于中小型公司，基于 ETF 持仓信息和行业分类合理推断
- 所有内容用**简体中文**输出

请依次输出以下5个表格，每个表格前标注维度名称（如「## 维度一：核心产品」）：

---

## 维度一：核心产品
分析每家公司 的主力产品/服务线，一句话描述。
| 公司 | 核心产品/服务 | 备注 |
| 上表格的格式，每个公司一行 |

## 维度二：企业定位
分析每家公司的市场定位、营收规模级别、核心优势与差异化。
| 公司 | 定位 | 规模/营收级别 | 备注 |
| 如：大型科技公司/成长型中盘股/小型创新公司 |

## 维度三：竞争格局
分析概念内公司之间的竞争关系（直接竞争/互补/无关）。
| 公司 A | 公司 B | 竞争关系 | 备注 |
| 至少覆盖5对重要的竞争关系，如无则填"无直接竞争" |

## 维度四：供应链关系
分析概念内公司之间的上下游供应商/客户关系。
| 上游 | 关系描述 | 下游 | 备注 |
| 如：供应商-客户提供商-技术授权 |
| 至少覆盖3条供应链关系，如无则填"无明显供应链关系" |

## 维度五：生态位
分析每家公司在整体生态系统中的角色定位。
| 公司 | 生态位 | 角色描述 |
| 平台层/基础设施层/应用层/服务层 |
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
        # 检测维度标题
        for prefix, key in dimension_map.items():
            if prefix in stripped:
                current = key
                break
        else:
            if current and stripped:
                result[current] += line + "\n"

    # 如果 LLM 没有按维度输出，把整个内容放进 products 作为兜底
    for key in result:
        if not result[key]:
            result[key] = content if not current else ""
    return result
