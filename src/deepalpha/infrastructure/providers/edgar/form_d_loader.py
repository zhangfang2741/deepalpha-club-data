"""
SEC EDGAR Form D 融资申报采集器

通过 EFTS 全文检索获取科技类创业融资 Form D，
提取 businessDescription 字段作为信号文本。
"""
import datetime
import logging
import xml.etree.ElementTree as ET
import httpx
from deepalpha.domain.signal_radar.models import RawSignalItem

logger = logging.getLogger(__name__)
_EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
_DOC_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/primary_doc.xml"
_HEADERS = {"User-Agent": "DeepAlpha contact@deepalpha.club"}


def _parse_business_desc(xml_text: str) -> str:
    """从 Form D XML 提取 businessDescription 字段文本。"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return ""
    for tag in ["businessDescription", ".//businessDescription"]:
        elem = root.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
    return ""


class FormDLoader:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def fetch(
        self,
        since: datetime.date,
        until: datetime.date,
        max_items: int = 50,
    ) -> list[RawSignalItem]:
        """采集 since~until 期间的 Form D 融资申报。"""
        params = {
            "forms": "D",
            "dateRange": "custom",
            "startdt": since.isoformat(),
            "enddt": until.isoformat(),
            "hits.hits.total": "true",
        }
        try:
            resp = await self._client.get(_EFTS_URL, params=params, headers=_HEADERS)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("EFTS Form D 搜索失败: %s", exc)
            return []

        hits = resp.json().get("hits", {}).get("hits", [])
        items: list[RawSignalItem] = []

        for hit in hits[:max_items]:
            src = hit.get("_source", {})
            acc = src.get("accession_no", "")
            file_date_str = src.get("file_date", "")
            entity = src.get("entity_name", "Unknown")
            if not acc or not file_date_str:
                continue

            cik_int = int(acc.split("-")[0])
            acc_nodash = acc.replace("-", "")
            doc_url = _DOC_URL.format(cik_int=cik_int, acc_nodash=acc_nodash)

            try:
                doc_resp = await self._client.get(doc_url, headers=_HEADERS)
                doc_resp.raise_for_status()
                desc = _parse_business_desc(doc_resp.text)
            except httpx.HTTPError:
                desc = ""

            if not desc:
                continue

            text = f"[Form D] {entity}: {desc}"
            items.append(RawSignalItem(
                ticker="__FORM_D__",
                source_type="form_d",
                signal_date=datetime.date.fromisoformat(file_date_str),
                doc_id=f"CIK{cik_int:010d}/{acc}/primary_doc.xml",
                text_snippet=text[:2000],
            ))

        return items
