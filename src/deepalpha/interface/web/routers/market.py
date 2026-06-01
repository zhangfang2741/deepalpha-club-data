"""行情数据 API 路由"""
from typing import Annotated

from fastapi import APIRouter, Depends

from deepalpha.application.services.market_service import MarketService
from deepalpha.application.agent.tools import Services
from deepalpha.domain.market.models import Quote
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/market", tags=["market"])


def _get_market_svc(svc: Annotated[Services, Depends(get_services)]) -> MarketService:
    return svc.market


@router.get("/quote/{symbol}", response_model=Quote)
async def get_quote(
    symbol: str,
    svc: Annotated[MarketService, Depends(_get_market_svc)],
) -> Quote:
    return await svc.get_quote(symbol)
