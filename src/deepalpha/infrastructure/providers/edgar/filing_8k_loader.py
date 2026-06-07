"""SEC EDGAR 8-K 电话会议文本采集器"""
import datetime
import logging
import re
import httpx
from deepalpha.domain.signal_radar.models import RawSignalItem
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver

logger = logging.getLogger(__name__)
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"
_DOC_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{doc}"
_HEADERS = {"User-Agent": "DeepAlpha contact@deepalpha.club"}


class Filing8KLoader:
    def __init__(self, client: httpx.AsyncClient, resolver: CikResolver) -> None:
        self._client = client
        self._resolver = resolver

    async def fetch(self, ticker: str, since: datetime.date) -> list[RawSignalItem]:
        cik10 = await self._resolver.resolve(ticker)
        if not cik10:
            logger.warning("无法解析 CIK: %s", ticker)
            return []
        try:
            resp = await self._client.get(_SUBMISSIONS_URL.format(cik10=cik10), headers=_HEADERS)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("获取 submissions 失败 %s: %s", ticker, exc)
            return []

        recent = resp.json().get("filings", {}).get("recent", {})
        items: list[RawSignalItem] = []
        cik_int = int(cik10)

        for form, acc, date_str, doc in zip(
            recent.get("form", []),
            recent.get("accessionNumber", []),
            recent.get("filingDate", []),
            recent.get("primaryDocument", []),
        ):
            if form != "8-K":
                continue
            filing_date = datetime.date.fromisoformat(date_str)
            if filing_date < since:
                break
            text = await self._fetch_text(cik_int, acc, doc)
            items.append(RawSignalItem(
                ticker=ticker,
                source_type="earnings_call",
                signal_date=filing_date,
                doc_id=acc,
                text_snippet=text[:2000],
            ))
        return items

    async def _fetch_text(self, cik_int: int, acc: str, doc: str) -> str:
        url = _DOC_URL.format(cik_int=cik_int, acc_nodash=acc.replace("-", ""), doc=doc)
        try:
            resp = await self._client.get(url, headers=_HEADERS)
            resp.raise_for_status()
            text = re.sub(r"<[^>]+>", " ", resp.text)
            return re.sub(r"\s+", " ", text).strip()
        except httpx.HTTPError as exc:
            logger.error("获取 8-K 文件失败: %s", exc)
            return ""
