"""
Finnhub ETF 持仓加载器

负责 AUM 过滤和持仓数据聚合（etf_count / total_weight）。
"""

import csv
import datetime
import io
from collections import defaultdict
from typing import Any, Protocol

import httpx

from deepalpha.models.concept import ConceptEtfMap, ConceptStock
from deepalpha.pipeline.concept.etfdb_scraper import ConceptEtfCandidate


class _EtfClient(Protocol):
    async def get_etf_profile(self, symbol: str) -> dict[str, Any]: ...
    async def get_etf_holdings(self, symbol: str) -> list[dict[str, Any]]: ...


async def filter_etfs_by_aum(
    candidates: list[ConceptEtfCandidate],
    client: _EtfClient,
    aum_threshold_million: float = 100.0,
) -> list[ConceptEtfMap]:
    """对候选 ETF 列表做 AUM 过滤，返回规模 >= 阈值的 ConceptEtfMap 列表。"""
    today = datetime.date.today()
    result: list[ConceptEtfMap] = []
    seen: set[tuple[str, str]] = set()

    for candidate in candidates:
        key = (candidate.concept, candidate.etf_symbol)
        if key in seen:
            continue
        seen.add(key)
        try:
            profile = await client.get_etf_profile(candidate.etf_symbol)
            mkt_cap = profile.get("mktCap")
            aum_million = mkt_cap / 1_000_000 if mkt_cap else None
            if aum_million is None or aum_million >= aum_threshold_million:
                result.append(ConceptEtfMap(
                    concept=candidate.concept,
                    etf_symbol=candidate.etf_symbol,
                    etf_name=profile.get("name"),
                    aum_million=aum_million,
                    etfdb_slug=candidate.etfdb_slug,
                    updated_at=today,
                ))
        except Exception:
            continue

    return result


async def aggregate_holdings(
    etf_maps: list[ConceptEtfMap],
    holdings_by_etf: dict[str, list[dict[str, Any]]],
    date: datetime.date,
) -> list[ConceptStock]:
    """将各 ETF 持仓合并，计算每只股票的 etf_count 和 total_weight。"""
    # concept -> symbol -> [(etf_symbol, weight, name)]
    data: dict[str, dict[str, list[tuple[str, float, str | None]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    etf_to_concepts: dict[str, list[str]] = defaultdict(list)
    for em in etf_maps:
        etf_to_concepts[em.etf_symbol].append(em.concept)

    for etf_symbol, concepts in etf_to_concepts.items():
        for holding in holdings_by_etf.get(etf_symbol, []):
            symbol: str = holding.get("symbol", "").upper()
            if not symbol:
                continue
            name: str | None = holding.get("name")
            weight: float = float(holding.get("percent", 0))
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


async def fetch_holdings_with_fallback(etf_symbol: str, client: _EtfClient) -> list[dict[str, Any]]:
    """拉取 ETF 持仓，Finnhub 失败时回落 ETF 官网 CSV。"""
    try:
        holdings = await client.get_etf_holdings(etf_symbol)
        if holdings:
            return holdings
    except Exception:
        pass
    return await _fetch_csv_fallback(etf_symbol)


# ETF 官网 CSV 兜底映射（Global X 等），可按需扩展
_CSV_URLS: dict[str, str] = {
    "BOTZ": "https://www.globalxetfs.com/funds/botz/holdings.csv",
    "AIQ": "https://www.globalxetfs.com/funds/aiq/holdings.csv",
}


async def _fetch_csv_fallback(etf_symbol: str) -> list[dict[str, Any]]:
    url = _CSV_URLS.get(etf_symbol.upper())
    if not url:
        return []
    try:
        async with httpx.AsyncClient(timeout=30.0) as http:
            resp = await http.get(url)
            resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))
        return [
            {"symbol": row.get("Ticker", "").upper(), "name": row.get("Name"), "percent": float(row.get("Weight (%)", 0) or 0)}
            for row in reader
            if row.get("Ticker")
        ]
    except Exception:
        return []
