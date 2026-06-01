"""
yfinance ETF 数据加载器

替代 Finnhub ETF 接口（免费版无权限），用于：
- 获取 ETF AUM（totalAssets）
- 获取 ETF 前十大持仓（top_holdings）
"""

import asyncio
import datetime
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import yfinance as yf

from deepalpha.domain.concept.models import ConceptEtfMap, ConceptStock
from deepalpha.infrastructure.providers.etfdb.scraper import ConceptEtfCandidate

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


def _fetch_etf_info_sync(symbol: str) -> dict[str, Any]:
    ticker = yf.Ticker(symbol)
    info = ticker.info
    try:
        holdings_df = ticker.funds_data.top_holdings
        holdings = [
            {
                "symbol": sym,
                "name": row.get("Name") or row.get("name", ""),
                "percent": float(row.get("Holding Percent", 0)),
            }
            for sym, row in holdings_df.iterrows()
            if sym and str(sym).strip()
        ]
    except Exception:
        holdings = []
    return {
        "name": info.get("longName") or info.get("shortName", symbol),
        "aum_million": (info.get("totalAssets") or 0) / 1_000_000,
        "holdings": holdings,
    }


async def _fetch_etf_info(symbol: str) -> dict[str, Any]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _fetch_etf_info_sync, symbol)


async def filter_etfs_by_aum(
    candidates: list[ConceptEtfCandidate],
    aum_threshold_million: float = 100.0,
) -> list[ConceptEtfMap]:
    """用 yfinance 做 AUM 过滤，返回规模 >= 阈值的 ConceptEtfMap 列表。"""
    today = datetime.date.today()
    result: list[ConceptEtfMap] = []
    seen: set[tuple[str, str]] = set()

    unique_symbols = list({c.etf_symbol for c in candidates})
    logger.info("拉取 %d 只 ETF 的 AUM 数据...", len(unique_symbols))

    etf_info: dict[str, dict[str, Any]] = {}
    for i, sym in enumerate(unique_symbols):
        try:
            info = await _fetch_etf_info(sym)
            etf_info[sym] = info
            logger.debug("  [%d/%d] %s: AUM=%.0fM", i + 1, len(unique_symbols), sym, info["aum_million"])
        except Exception as e:
            logger.warning("  %s: 获取失败 (%s)", sym, e)
            etf_info[sym] = {"name": sym, "aum_million": None, "holdings": []}

    for candidate in candidates:
        key = (candidate.concept, candidate.etf_symbol)
        if key in seen:
            continue
        seen.add(key)
        info = etf_info.get(candidate.etf_symbol, {})
        aum = info.get("aum_million")
        if aum is None or aum >= aum_threshold_million:
            result.append(ConceptEtfMap(
                concept=candidate.concept,
                etf_symbol=candidate.etf_symbol,
                etf_name=info.get("name"),
                aum_million=aum,
                etfdb_slug=candidate.etfdb_slug,
                updated_at=today,
            ))

    return result


async def fetch_holdings(etf_symbol: str) -> list[dict[str, Any]]:
    """用 yfinance 拉取 ETF 前十大持仓。"""
    try:
        info = await _fetch_etf_info(etf_symbol)
        return info.get("holdings", [])
    except Exception as e:
        logger.warning("%s: 持仓拉取失败 (%s)", etf_symbol, e)
        return []


async def aggregate_holdings(
    etf_maps: list[ConceptEtfMap],
    holdings_by_etf: dict[str, list[dict[str, Any]]],
    date: datetime.date,
) -> list[ConceptStock]:
    """将各 ETF 持仓合并，计算每只股票的 etf_count 和 total_weight。"""
    data: dict[str, dict[str, list[tuple[str, float, str | None]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    etf_to_concepts: dict[str, list[str]] = defaultdict(list)
    for em in etf_maps:
        etf_to_concepts[em.etf_symbol].append(em.concept)

    for etf_symbol, concepts in etf_to_concepts.items():
        for holding in holdings_by_etf.get(etf_symbol, []):
            symbol: str = str(holding.get("symbol", "")).upper()
            if not symbol:
                continue
            name: str | None = holding.get("name")
            weight: float = float(holding.get("percent", 0)) * 100  # 转为百分比
            for concept in concepts:
                data[concept][symbol].append((etf_symbol, weight, name))

    results: list[ConceptStock] = []
    for concept, symbol_data in data.items():
        for symbol, entries in symbol_data.items():
            name = next((e[2] for e in entries if e[2]), None)
            results.append(ConceptStock(
                date=date,
                concept=concept,
                symbol=symbol,
                name=name,
                etf_count=len(entries),
                total_weight=round(sum(e[1] for e in entries), 4),
                etfs=[e[0] for e in entries],
            ))

    return results
