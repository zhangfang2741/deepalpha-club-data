"""
ETFdb 主题分类抓取器

月度运行，抓取 ETFdb 全部主题分类及各分类下的 ETF 列表。
请求间隔 2 秒，每月只运行一次，对 ETFdb 无明显压力。
"""

import asyncio
import random
from dataclasses import dataclass

import httpx
from lxml import html

ETFDB_BASE = "https://etfdb.com"

_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

_BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


@dataclass
class ConceptEtfCandidate:
    """ETFdb 抓取到的原始 concept→etf 候选（AUM 过滤前）。"""
    concept: str
    etf_symbol: str
    etfdb_slug: str


def _parse_theme_slugs(page_html: str) -> dict[str, str]:
    """从主题列表页 HTML 中解析 {concept_name: slug}。"""
    tree = html.fromstring(page_html)
    result: dict[str, str] = {}
    for link in tree.xpath("//a[contains(@href, '/type/')]"):
        href: str = link.get("href", "")
        text: str = link.text_content().strip()
        if not href or not text:
            continue
        # href 格式: /type/artificial-intelligence-etfs/
        parts = [p for p in href.strip("/").split("/") if p]
        if len(parts) >= 2 and parts[0] == "type":
            slug = parts[1]
            result[text] = slug
    return result


def _parse_etf_symbols(page_html: str) -> list[str]:
    """从主题详情页 HTML 中解析 ETF symbol 列表。"""
    tree = html.fromstring(page_html)
    symbols: list[str] = []
    # ETFdb 在 ETF 列表表格中，ticker 在链接文本里，href 格式: /etf/BOTZ/
    for link in tree.xpath("//a[contains(@href, '/etf/')]"):
        href: str = link.get("href", "")
        parts = [p for p in href.strip("/").split("/") if p]
        if len(parts) >= 2 and parts[0] == "etf":
            symbol = parts[1].upper()
            if symbol and symbol not in symbols:
                symbols.append(symbol)
    return symbols


def _make_headers() -> dict[str, str]:
    return {"User-Agent": random.choice(_USER_AGENTS), **_BROWSER_HEADERS}


async def scrape_concept_etf_candidates(delay: float = 2.0) -> list[ConceptEtfCandidate]:
    """抓取 ETFdb 所有主题分类的 ETF 候选列表（AUM 过滤前）。"""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        resp = await client.get(f"{ETFDB_BASE}/etfs/themes/", headers=_make_headers())
        resp.raise_for_status()
        slugs = _parse_theme_slugs(resp.text)

        candidates: list[ConceptEtfCandidate] = []
        for concept, slug in slugs.items():
            await asyncio.sleep(delay)
            try:
                resp = await client.get(f"{ETFDB_BASE}/type/{slug}/", headers=_make_headers())
                resp.raise_for_status()
                symbols = _parse_etf_symbols(resp.text)
                for sym in symbols:
                    candidates.append(ConceptEtfCandidate(concept=concept, etf_symbol=sym, etfdb_slug=slug))
            except httpx.HTTPError:
                continue

    return candidates
