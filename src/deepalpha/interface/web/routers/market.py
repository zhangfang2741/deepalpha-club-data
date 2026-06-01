"""行情数据 API 路由"""
import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from deepalpha.application.services.market_service import MarketService
from deepalpha.application.services.performance_service import PerformanceService
from deepalpha.application.agent.tools import Services
from deepalpha.domain.market.enums import Interval
from deepalpha.domain.market.models import MarketMover, Quote, SectorPerformance
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/market", tags=["market"])


def _get_market_svc(svc: Annotated[Services, Depends(get_services)]) -> MarketService:
    return svc.market


def _get_perf_svc(svc: Annotated[Services, Depends(get_services)]) -> PerformanceService:
    return svc.performance


class OHLCVBar(BaseModel):
    t: str     # ISO date string  YYYY-MM-DD
    o: float
    h: float
    l: float
    c: float
    v: float


@router.get("/quote/{symbol}", response_model=Quote)
async def get_quote(
    symbol: str,
    svc: Annotated[MarketService, Depends(_get_market_svc)],
) -> Quote:
    return await svc.get_quote(symbol)


@router.get("/history/{symbol}", response_model=list[OHLCVBar])
async def get_history(
    symbol: str,
    svc: Annotated[MarketService, Depends(_get_market_svc)],
    months: int = Query(3, ge=1, le=24, description="拉取最近 N 个月的日线数据"),
) -> list[OHLCVBar]:
    """返回 OHLCV 日线数据（FMP stable/historical-price-eod/full）。"""
    end = datetime.date.today()
    start = end - datetime.timedelta(days=months * 31)
    bars = await svc.get_price_history(symbol.upper(), start=start, end=end, interval=Interval.ONE_DAY)
    return [
        OHLCVBar(
            t=b.date.strftime("%Y-%m-%d"),
            o=round(b.open, 4),
            h=round(b.high, 4),
            l=round(b.low, 4),
            c=round(b.close, 4),
            v=round(b.volume or 0, 0),
        )
        for b in sorted(bars, key=lambda x: x.date)
    ]


@router.get("/movers/{direction}", response_model=list[MarketMover])
async def get_movers(
    direction: str,
    svc: Annotated[PerformanceService, Depends(_get_perf_svc)],
    limit: int = Query(10, ge=1, le=50),
) -> list[MarketMover]:
    if direction == "gainers":
        return await svc.get_gainers(limit=limit)
    return await svc.get_losers(limit=limit)


@router.get("/sectors", response_model=list[SectorPerformance])
async def get_sectors(
    svc: Annotated[PerformanceService, Depends(_get_perf_svc)],
) -> list[SectorPerformance]:
    return await svc.get_sector_performance()
