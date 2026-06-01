"""新闻 API 路由"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from deepalpha.application.services.news_service import NewsService
from deepalpha.application.agent.tools import Services
from deepalpha.domain.news.models import NewsArticle
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/news", tags=["news"])


def _svc(svc: Annotated[Services, Depends(get_services)]) -> NewsService:
    return svc.news


@router.get("/{symbol}", response_model=list[NewsArticle])
async def get_news(
    symbol: str,
    limit: int = Query(10, ge=1, le=50),
    svc: Annotated[NewsService, Depends(_svc)] = ...,
) -> list[NewsArticle]:
    return await svc.get_news(symbol=symbol.upper(), limit=limit)
