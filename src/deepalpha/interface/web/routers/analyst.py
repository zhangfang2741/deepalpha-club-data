"""分析师数据 API 路由"""
from typing import Annotated

from fastapi import APIRouter, Depends

from deepalpha.application.services.analyst_service import AnalystService
from deepalpha.application.agent.tools import Services
from deepalpha.domain.analyst.models import AnalystRating, Estimate, PriceTarget
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/analyst", tags=["analyst"])


def _svc(svc: Annotated[Services, Depends(get_services)]) -> AnalystService:
    return svc.analyst


@router.get("/{symbol}/ratings", response_model=list[AnalystRating])
async def get_ratings(symbol: str, svc: Annotated[AnalystService, Depends(_svc)]) -> list[AnalystRating]:
    return await svc.get_ratings(symbol.upper())


@router.get("/{symbol}/targets", response_model=list[PriceTarget])
async def get_price_targets(symbol: str, svc: Annotated[AnalystService, Depends(_svc)]) -> list[PriceTarget]:
    return await svc.get_price_targets(symbol.upper())


@router.get("/{symbol}/estimates", response_model=list[Estimate])
async def get_estimates(symbol: str, svc: Annotated[AnalystService, Depends(_svc)]) -> list[Estimate]:
    return await svc.get_estimates(symbol.upper())
