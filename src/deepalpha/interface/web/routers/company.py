"""公司信息 API 路由"""
from typing import Annotated

from fastapi import APIRouter, Depends

from deepalpha.application.services.company_service import CompanyService
from deepalpha.application.agent.tools import Services
from deepalpha.domain.company.models import CompanyProfile, Executive
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/company", tags=["company"])


def _svc(svc: Annotated[Services, Depends(get_services)]) -> CompanyService:
    return svc.company


@router.get("/{symbol}/profile", response_model=CompanyProfile)
async def get_profile(symbol: str, svc: Annotated[CompanyService, Depends(_svc)]) -> CompanyProfile:
    return await svc.get_profile(symbol.upper())


@router.get("/{symbol}/executives", response_model=list[Executive])
async def get_executives(symbol: str, svc: Annotated[CompanyService, Depends(_svc)]) -> list[Executive]:
    return await svc.get_executives(symbol.upper())


@router.get("/{symbol}/peers", response_model=list[str])
async def get_peers(symbol: str, svc: Annotated[CompanyService, Depends(_svc)]) -> list[str]:
    return await svc.get_peers(symbol.upper())
