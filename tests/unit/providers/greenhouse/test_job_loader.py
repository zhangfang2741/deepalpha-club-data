"""Greenhouse/Lever 招聘 JD 采集器测试"""
import datetime
import httpx
from deepalpha.infrastructure.providers.greenhouse.job_loader import JobLoader, CompanySlug


async def test_fetch_greenhouse_jobs(httpx_mock):
    """测试 Greenhouse API 职位拉取"""
    httpx_mock.add_response(
        url="https://boards.greenhouse.io/embed/job_board/jobs.json?for=nvidia",
        json={
            "jobs": [
                {"title": "Senior HBM Memory Architect", "departments": [{"name": "Hardware Engineering"}], "updated_at": "2026-06-06T00:00:00Z"},
                {"title": "AI Inference Optimization Engineer", "departments": [{"name": "Software"}], "updated_at": "2026-06-06T00:00:00Z"},
            ]
        },
    )
    slug = CompanySlug(ticker="NVDA", slug="nvidia", type="greenhouse")
    async with httpx.AsyncClient() as client:
        loader = JobLoader(client)
        items = await loader.fetch(slug, since=datetime.date(2026, 6, 5))
    assert len(items) == 1
    assert items[0].source_type == "job_posting"
    assert "HBM Memory Architect" in items[0].text_snippet


async def test_fetch_lever_jobs(httpx_mock):
    """测试 Lever API 职位拉取"""
    httpx_mock.add_response(
        url="https://api.lever.co/v0/postings/crowdstrike?mode=json",
        json=[
            {"text": "AI Security Engineer", "categories": {"department": "Engineering"}, "createdAt": 1780958400000},
        ],
    )
    slug = CompanySlug(ticker="CRWD", slug="crowdstrike", type="lever")
    async with httpx.AsyncClient() as client:
        loader = JobLoader(client)
        items = await loader.fetch(slug, since=datetime.date(2026, 6, 5))
    assert len(items) == 1
    assert "AI Security Engineer" in items[0].text_snippet
