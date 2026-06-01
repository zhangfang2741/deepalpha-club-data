"""概念股池 API 路由（使用 ConceptService）"""
import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from deepalpha.application.services.concept_service import ConceptService
from deepalpha.application.agent.tools import Services
from deepalpha.domain.concept.models import ConceptStock, ConceptSummary
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/concept", tags=["concept"])


def _get_concept_svc(svc: Annotated[Services, Depends(get_services)]) -> ConceptService:
    return svc.concept


@router.get("/list", response_model=list[ConceptSummary])
async def list_concepts(
    svc: Annotated[ConceptService, Depends(_get_concept_svc)],
) -> list[ConceptSummary]:
    return await svc.list_summaries()


@router.get("/{name}", response_model=list[ConceptStock])
async def get_concept(
    name: str,
    svc: Annotated[ConceptService, Depends(_get_concept_svc)],
    min_etf_count: int = Query(1, ge=1),
) -> list[ConceptStock]:
    stocks = await svc.get_concept(name)
    if not stocks:
        raise HTTPException(status_code=404, detail=f"概念 '{name}' 不存在")
    return [s for s in stocks if s.etf_count >= min_etf_count]


@router.get("/{name}/history", response_model=list[ConceptStock])
async def get_concept_history(
    name: str,
    svc: Annotated[ConceptService, Depends(_get_concept_svc)],
    start: datetime.date = Query(...),
    end: datetime.date = Query(...),
) -> list[ConceptStock]:
    return await svc.get_concept_history(name, start, end)
