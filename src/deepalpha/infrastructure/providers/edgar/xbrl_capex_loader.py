"""SEC EDGAR XBRL Capex 数据采集器"""
import datetime
import logging
import httpx
from deepalpha.domain.signal_radar.models import RawSignalItem
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver

logger = logging.getLogger(__name__)
_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"
_CONCEPT = "PaymentsToAcquirePropertyPlantAndEquipment"
_HEADERS = {"User-Agent": "DeepAlpha contact@deepalpha.club"}


class XbrlCapexLoader:
    def __init__(self, client: httpx.AsyncClient, resolver: CikResolver) -> None:
        self._client = client
        self._resolver = resolver

    async def fetch(self, ticker: str, since: datetime.date) -> list[RawSignalItem]:
        cik10 = await self._resolver.resolve(ticker)
        if not cik10:
            return []
        try:
            resp = await self._client.get(_FACTS_URL.format(cik10=cik10), headers=_HEADERS)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("获取 XBRL facts 失败 %s: %s", ticker, exc)
            return []

        entries = (
            resp.json().get("facts", {}).get("us-gaap", {})
            .get(_CONCEPT, {}).get("units", {}).get("USD", [])
        )
        items: list[RawSignalItem] = []
        for e in entries:
            filed_str = e.get("filed", "")
            if not filed_str or datetime.date.fromisoformat(filed_str) < since:
                continue
            val = e.get("val", 0)
            end = e.get("end", "")
            frame = e.get("frame", end)
            text = (
                f"{ticker} capital expenditure ({_CONCEPT}): "
                f"{val:,.0f} USD for period ending {end}, "
                f"filed {filed_str} via {e.get('form', '')}."
            )
            items.append(RawSignalItem(
                ticker=ticker,
                source_type="capex",
                signal_date=datetime.date.fromisoformat(filed_str),
                doc_id=f"{ticker}-capex-{frame}",
                text_snippet=text,
            ))
        return items
