"""
Greenhouse / Lever 招聘 JD 采集器

通过公开 JSON API 获取职位列表（无需 API Key），
将同一公司所有职位标题聚合为一条信号文本。
"""
import datetime
import logging
from dataclasses import dataclass
import httpx
from deepalpha.domain.signal_radar.models import RawSignalItem

logger = logging.getLogger(__name__)
_GH_URL = "https://boards.greenhouse.io/embed/job_board/jobs.json?for={slug}"
_LEVER_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


@dataclass
class CompanySlug:
    ticker: str
    slug: str
    type: str  # "greenhouse" | "lever"


class JobLoader:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def fetch(self, company: CompanySlug, since: datetime.date) -> list[RawSignalItem]:
        if company.type == "greenhouse":
            return await self._fetch_greenhouse(company, since)
        elif company.type == "lever":
            return await self._fetch_lever(company, since)
        return []

    async def _fetch_greenhouse(self, company: CompanySlug, since: datetime.date) -> list[RawSignalItem]:
        url = _GH_URL.format(slug=company.slug)
        try:
            resp = await self._client.get(url, timeout=10.0)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Greenhouse 请求失败 %s: %s", company.slug, exc)
            return []

        jobs = resp.json().get("jobs", [])
        titles = []
        for job in jobs:
            updated = job.get("updated_at", "")
            if updated and datetime.date.fromisoformat(updated[:10]) < since:
                continue
            dept = ""
            if job.get("departments"):
                dept = job["departments"][0].get("name", "")
            titles.append(f"{job.get('title', '')} [{dept}]")

        if not titles:
            return []
        text = f"[{company.ticker}] Recent job postings: " + "; ".join(titles)
        return [RawSignalItem(
            ticker=company.ticker,
            source_type="job_posting",
            signal_date=since,
            doc_id=f"{company.ticker}-jobs-{since.isoformat()}",
            text_snippet=text[:2000],
        )]

    async def _fetch_lever(self, company: CompanySlug, since: datetime.date) -> list[RawSignalItem]:
        url = _LEVER_URL.format(slug=company.slug)
        try:
            resp = await self._client.get(url, timeout=10.0)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Lever 请求失败 %s: %s", company.slug, exc)
            return []

        postings = resp.json() if isinstance(resp.json(), list) else []
        titles = []
        for p in postings:
            created_ms = p.get("createdAt", 0)
            created = datetime.date.fromtimestamp(created_ms / 1000)
            if created < since:
                continue
            dept = p.get("categories", {}).get("department", "")
            titles.append(f"{p.get('text', '')} [{dept}]")

        if not titles:
            return []
        text = f"[{company.ticker}] Recent job postings: " + "; ".join(titles)
        return [RawSignalItem(
            ticker=company.ticker,
            source_type="job_posting",
            signal_date=since,
            doc_id=f"{company.ticker}-jobs-{since.isoformat()}",
            text_snippet=text[:2000],
        )]
