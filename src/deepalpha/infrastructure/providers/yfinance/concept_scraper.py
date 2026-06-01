"""
动态概念 ETF 发现器（零配置）

完全自动：从 Yahoo Finance 获取所有 Morningstar 主题板块分类，
再按分类批量拉取美国上市 ETF，无需手动维护任何 ETF 或概念列表。

新增概念：Morningstar 新增板块后下次运行自动纳入。
"""

import logging

import yfinance as yf
from yfinance.screener.query import ETFQuery

from deepalpha.infrastructure.providers.etfdb.scraper import ConceptEtfCandidate

logger = logging.getLogger(__name__)

# 排除非主题板块（债券、风格类、地区宽基等）——用排除规则代替正向维护列表
_EXCLUDE_PATTERNS = [
    "Bond", "Muni", "Allocation", "Trading", "Government",
    "Target-Date", "Multisector", "Nontraditional", "Ultrashort",
    "Managed Futures", "Market Neutral", "Multicurrency",
    "Long-Short", "Multialternative", "Convertibles", "Option Writing",
    "Tactical", "Leveraged", "Inverse", "Bear Market",
    " Blend", " Growth", " Value",
    "Foreign ", "World Stock", "Europe Stock", "Japan Stock",
    "Pacific", "Bank Loan", "Limited Partnership", "Miscellaneous",
    "Preferred Stock", "Other",
]


def _get_thematic_categories() -> list[str]:
    """从 Yahoo Finance 获取所有主题板块分类（自动过滤非主题类别）。"""
    q = ETFQuery("gt", ["intradayprice", 0])
    all_cats: list[str] = list(q.valid_values.get("categoryname", []))
    return [
        c for c in sorted(all_cats)
        if not any(p.lower() in c.lower() for p in _EXCLUDE_PATTERNS)
    ]


def scrape_concept_etf_candidates(
    aum_threshold_million: float = 100.0,
    max_per_category: int = 50,
) -> list[ConceptEtfCandidate]:
    """
    自动发现所有主题板块的 ETF 候选列表。

    流程：
    1. 从 Morningstar 取所有板块分类（自动排除非主题类）
    2. 每个分类用 ETFQuery 查询美国上市 ETF
    3. 按 AUM 过滤（screener 结果内自带 netAssets）
    """
    categories = _get_thematic_categories()
    logger.info("自动发现 %d 个主题板块: %s", len(categories), categories)

    candidates: list[ConceptEtfCandidate] = []
    seen: set[tuple[str, str]] = set()

    for concept in categories:
        try:
            query = ETFQuery("and", [
                ETFQuery("eq", ["categoryname", concept]),
                ETFQuery("eq", ["region", "us"]),
            ])
            result = yf.screen(query, count=max_per_category)
            quotes = result.get("quotes", [])

            count = 0
            for q in quotes:
                sym: str = q.get("symbol", "")
                if not sym or "." in sym:  # 跳过非美国上市（含交易所后缀）
                    continue
                net_assets = q.get("netAssets") or 0
                aum_m = net_assets / 1_000_000
                if aum_m < aum_threshold_million:
                    continue
                key = (concept, sym)
                if key not in seen:
                    seen.add(key)
                    candidates.append(ConceptEtfCandidate(
                        concept=concept,
                        etf_symbol=sym,
                        etfdb_slug=concept.lower().replace(" ", "-").replace("/", ""),
                    ))
                    count += 1

            logger.info("  %s: %d 只 ETF（AUM≥%.0fM）", concept, count, aum_threshold_million)

        except Exception as e:
            logger.warning("  %s: 查询失败 (%s)", concept, e)

    logger.info("动态发现完成，共 %d 条候选", len(candidates))
    return candidates
