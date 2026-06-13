"""信号趋势雷达 API 路由"""
import datetime
from typing import Annotated, AsyncGenerator

import asyncio

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query

from deepalpha.domain.signal_radar.models import DailyThemeScore
from deepalpha.infrastructure.config import SignalRadarPipelineConfig
from deepalpha.infrastructure.db.signal_radar_repo import SignalRadarRepo


def _sec_doc_url(doc_id: str, ticker: str | None = None) -> str:
    """从 doc_id 还原 SEC EDGAR 文件 URL。

    数据库中 doc_id 格式（8-K）:     CIK0000789019/0001193125-26-258667/ef20060722_8k.htm
    数据库中 doc_id 格式（Form D）:   0001193125-26-258667/primary_doc.xml
    数据库中 doc_id 格式（XBRL Capex）: AAPL-capex-2025-03-29
    """
    # Capex 格式：ticker-capex-日期/CY2024Q4，直接返回搜索页
    if ticker and doc_id.startswith(ticker + "-capex-"):
        return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&ticker={ticker}&type=capex&dateb=&owner=include&count=40"

    # Form D： accession/primary_doc.xml（无 CIK 前缀）
    segments = doc_id.split("/")
    if len(segments) == 2 and not doc_id.startswith("CIK"):
        acc = segments[0]
        raw_cik = acc.split("-")[0]
        cik = f"{int(raw_cik):010d}"
        return f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{segments[1]}"

    # 8-K 格式：CIK0000789019/0001193125-26-258667/ef20060722_8k.htm
    if doc_id.startswith("CIK"):
        # 格式：CIK{cik}/{accession}/{filename}
        # 直接进 filing 详情页（不带文件名）
        parts = doc_id.split("/")
        return f"https://www.sec.gov/Archives/edgar/data/{parts[0]}/{parts[1]}"

    # Fallback
    return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&ticker={ticker or doc_id}&type=&dateb=&owner=include&count=40"

router = APIRouter(prefix="/signal-radar", tags=["signal-radar"])

# 模块级 pool，第一次请求时初始化，之后复用
_pool: asyncpg.Pool | None = None  # type: ignore[type-arg]


async def _get_repo() -> AsyncGenerator[SignalRadarRepo, None]:
    global _pool
    if _pool is None:
        cfg = SignalRadarPipelineConfig()
        try:
            repo_instance = await asyncio.wait_for(
                SignalRadarRepo.create(cfg.asyncpg_dsn()), timeout=30
            )
        except (asyncio.TimeoutError, OSError, Exception) as exc:
            raise HTTPException(status_code=503, detail=f"数据库连接失败: {exc}") from exc
        _pool = repo_instance._pool
    yield SignalRadarRepo(_pool)


RepoDep = Annotated[SignalRadarRepo, Depends(_get_repo)]


@router.get("/leaderboard", response_model=list[DailyThemeScore])
async def get_leaderboard(
    repo: RepoDep,
    date: datetime.date | None = Query(default=None, description="查询日期，默认取最新有数据的日期"),
    window: str = Query("30d", description="时间窗口：7d|30d|90d|1y|3y|all"),
    category: str = Query(
        "all", description="tech_concept|infra_component|engineering_concept|all"
    ),
    limit: int = Query(50, ge=1, le=200),
) -> list[DailyThemeScore]:
    if date is None:
        date = await repo.get_latest_date()
    window_days = _parse_window(window)
    return await repo.get_leaderboard(date, window_days, category, limit)


@router.get("/trend/{theme_name}", response_model=list[DailyThemeScore])
async def get_trend(
    theme_name: str,
    repo: RepoDep,
    from_date: datetime.date = Query(
        alias="from",
        default_factory=lambda: datetime.date.today() - datetime.timedelta(days=30),
    ),
    to_date: datetime.date = Query(alias="to", default_factory=datetime.date.today),
) -> list[DailyThemeScore]:
    return await repo.get_theme_trend(theme_name, from_date, to_date)


@router.get("/snapshot", response_model=list[DailyThemeScore])
async def get_snapshot(
    repo: RepoDep,
    date: datetime.date = Query(default_factory=datetime.date.today),
    limit: int = Query(20, ge=1, le=50),
) -> list[DailyThemeScore]:
    return await repo.get_snapshot(date, limit)


@router.get("/themes", response_model=list[str])
async def search_themes(
    repo: RepoDep,
    q: str = Query("", description="模糊搜索主题名"),
    limit: int = Query(20, ge=1, le=100),
) -> list[str]:
    return await repo.search_themes(q, limit)


@router.get("/theme/{theme_name}/signals")
async def get_theme_signals(
    theme_name: str,
    repo: RepoDep,
    from_date: datetime.date | None = Query(
        default=None,
        alias="from",
        description="开始日期，默认取最早有该主题的日期",
    ),
    to_date: datetime.date | None = Query(
        default=None,
        alias="to",
        description="结束日期，默认取最新日期",
    ),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    # 默认时间范围：全部历史
    if from_date is None:
        from_date = datetime.date(2020, 1, 1)
    if to_date is None:
        to_date = datetime.date.today()

    raw = await repo.get_theme_signals(theme_name, from_date, to_date, limit)
    return [
        {
            "ticker": r["ticker"],
            "source_type": r["source_type"],
            "signal_date": r["signal_date"].isoformat() if hasattr(r["signal_date"], "isoformat") else str(r["signal_date"]),
            "sec_url": _sec_doc_url(r["doc_id"], r["ticker"]),
            "text_snippet": r["text_snippet"],
            "confidence": r["confidence"],
        }
        for r in raw
    ]


@router.get("/theme/{theme_name}/analysis")
async def analyze_theme(
    theme_name: str,
    repo: RepoDep,
    from_date: datetime.date | None = Query(default=None, alias="from"),
    to_date: datetime.date | None = Query(default=None, alias="to"),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """
    对雷达主题进行多维度 AI 业务分析（核心产品、企业定位、
    竞争格局、供应链关系、生态位），返回 5 个维度的 Markdown 表格。
    """
    from deepalpha.infrastructure.providers.minimax.theme_analyzer import analyze_theme as do_analyze

    if from_date is None:
        from_date = datetime.date(2020, 1, 1)
    if to_date is None:
        to_date = datetime.date.today()

    cfg = SignalRadarPipelineConfig()
    raw = await repo.get_theme_signals(theme_name, from_date, to_date, limit)

    signals = [
        {
            "ticker": r["ticker"],
            "source_type": r["source_type"],
            "text_snippet": r["text_snippet"],
            "confidence": r["confidence"],
        }
        for r in raw
    ]

    return await do_analyze(
        api_key=cfg.minimax_api_key,
        theme_name=theme_name,
        signals=signals,
    )


def _parse_window(window: str) -> int | None:
    mapping: dict[str, int | None] = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365,
        "3y": 1095,
        "all": None,
    }
    return mapping.get(window, 30)
