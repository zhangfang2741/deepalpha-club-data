"""内幕/国会交易 API 路由"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from deepalpha.application.services.insider_service import InsiderService
from deepalpha.application.agent.tools import Services
from deepalpha.domain.governance.models import CongressTrade, InsiderTrade
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/insider", tags=["insider"])


def _svc(svc: Annotated[Services, Depends(get_services)]) -> InsiderService:
    return svc.insider


@router.get("/{symbol}", response_model=list[InsiderTrade])
async def get_insider_trades(
    symbol: str,
    limit: int = Query(20, ge=1, le=100),
    svc: Annotated[InsiderService, Depends(_svc)] = ...,
) -> list[InsiderTrade]:
    return await svc.get_insider_trades(symbol.upper(), limit=limit)


@router.get("/{symbol}/congress", response_model=list[CongressTrade])
async def get_congress_trades(
    symbol: str,
    limit: int = Query(20, ge=1, le=100),
    svc: Annotated[InsiderService, Depends(_svc)] = ...,
) -> list[CongressTrade]:
    return await svc.get_congress_trades(symbol.upper(), limit=limit)
