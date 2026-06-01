"""财务数据 API 路由"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from deepalpha.application.services.financial_service import FinancialService
from deepalpha.application.agent.tools import Services
from deepalpha.domain.financial.models import (
    BalanceSheet, CashFlow, FinancialRatio,
    IncomeStatement, KeyMetrics, Valuation,
)
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/financial", tags=["financial"])


def _svc(svc: Annotated[Services, Depends(get_services)]) -> FinancialService:
    return svc.financial


@router.get("/{symbol}/income", response_model=IncomeStatement)
async def get_income(symbol: str, svc: Annotated[FinancialService, Depends(_svc)]) -> IncomeStatement:
    stmt = await svc.get_latest_income(symbol.upper())
    if stmt is None:
        raise HTTPException(404, f"财务数据不存在: {symbol}")
    return stmt


@router.get("/{symbol}/balance", response_model=BalanceSheet)
async def get_balance(symbol: str, svc: Annotated[FinancialService, Depends(_svc)]) -> BalanceSheet:
    bs = await svc.get_balance_sheet(symbol.upper())
    if bs is None:
        raise HTTPException(404, f"资产负债表不存在: {symbol}")
    return bs


@router.get("/{symbol}/cashflow", response_model=CashFlow)
async def get_cashflow(symbol: str, svc: Annotated[FinancialService, Depends(_svc)]) -> CashFlow:
    cf = await svc.get_cash_flow(symbol.upper())
    if cf is None:
        raise HTTPException(404, f"现金流数据不存在: {symbol}")
    return cf


@router.get("/{symbol}/ratios", response_model=FinancialRatio)
async def get_ratios(symbol: str, svc: Annotated[FinancialService, Depends(_svc)]) -> FinancialRatio:
    r = await svc.get_financial_ratios(symbol.upper())
    if r is None:
        raise HTTPException(404, f"财务比率不存在: {symbol}")
    return r


@router.get("/{symbol}/metrics", response_model=KeyMetrics)
async def get_metrics(symbol: str, svc: Annotated[FinancialService, Depends(_svc)]) -> KeyMetrics:
    m = await svc.get_key_metrics(symbol.upper())
    if m is None:
        raise HTTPException(404, f"关键指标不存在: {symbol}")
    return m


@router.get("/{symbol}/valuation", response_model=Valuation)
async def get_valuation(symbol: str, svc: Annotated[FinancialService, Depends(_svc)]) -> Valuation:
    return await svc.get_valuation(symbol.upper())
