"""日历事件 API 路由"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from deepalpha.application.services.calendar_service import CalendarService
from deepalpha.application.agent.tools import Services
from deepalpha.domain.market.models import DividendEvent, EarningsEvent
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _svc(svc: Annotated[Services, Depends(get_services)]) -> CalendarService:
    return svc.calendar


@router.get("/earnings", response_model=list[EarningsEvent])
async def get_upcoming_earnings(
    days: int = Query(7, ge=1, le=30),
    svc: Annotated[CalendarService, Depends(_svc)] = ...,
) -> list[EarningsEvent]:
    return await svc.get_upcoming_earnings(days=days)


@router.get("/dividends", response_model=list[DividendEvent])
async def get_upcoming_dividends(
    days: int = Query(14, ge=1, le=60),
    svc: Annotated[CalendarService, Depends(_svc)] = ...,
) -> list[DividendEvent]:
    return await svc.get_upcoming_dividends(days=days)
