"""FastAPI 依赖注入：组装 infrastructure → services → agent"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

import asyncpg
from fastapi import FastAPI

from deepalpha.application.agent.runner import AgentRunner
from deepalpha.application.agent.tools import Services
from deepalpha.application.services.analyst_service import AnalystService
from deepalpha.application.services.calendar_service import CalendarService
from deepalpha.application.services.company_service import CompanyService
from deepalpha.application.services.concept_service import ConceptService
from deepalpha.application.services.financial_service import FinancialService
from deepalpha.application.services.insider_service import InsiderService
from deepalpha.application.services.market_service import MarketService
from deepalpha.application.services.news_service import NewsService
from deepalpha.application.services.performance_service import PerformanceService
from deepalpha.infrastructure.cache.concept_cache import ConceptCache
from deepalpha.infrastructure.db.concept_repo import ConceptRepo
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.analyst_loader import FMPAnalystLoader
from deepalpha.infrastructure.providers.fmp.loaders.calendar_loader import FMPCalendarLoader
from deepalpha.infrastructure.providers.fmp.loaders.company_loader import FMPCompanyLoader
from deepalpha.infrastructure.providers.fmp.loaders.financial_loader import FMPFinancialLoader
from deepalpha.infrastructure.providers.fmp.loaders.insider_loader import FMPInsiderTradeLoader
from deepalpha.infrastructure.providers.fmp.loaders.congress_loader import FMPCongressTradeLoader
from deepalpha.infrastructure.providers.fmp.loaders.market_loader import FMPMarketLoader
from deepalpha.infrastructure.providers.fmp.loaders.news_loader import FMPNewsLoader
from deepalpha.infrastructure.providers.fmp.loaders.performance_loader import FMPMarketPerformanceLoader
from deepalpha.infrastructure.config import ConceptPipelineConfig
from deepalpha.core.logging import setup_logging


@lru_cache(maxsize=1)
def get_config() -> ConceptPipelineConfig:
    return ConceptPipelineConfig()


_services: Services | None = None
_pool: asyncpg.Pool | None = None  # type: ignore[type-arg]
_cache: ConceptCache | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _services, _pool, _cache
    setup_logging()
    cfg = get_config()

    _pool = await asyncpg.create_pool(cfg.asyncpg_dsn())
    _cache = ConceptCache(
        host=cfg.valkey_host,
        port=cfg.valkey_port,
        password=cfg.valkey_password,
        ssl=cfg.valkey_ssl,
    )

    repo = ConceptRepo(cfg.asyncpg_dsn())
    repo._pool = _pool
    await repo.initialize()

    fmp_cfg = FMPConfig()
    fmp = FMPAsyncClient(fmp_cfg)

    _services = Services(
        concept=ConceptService(repo, _cache),
        market=MarketService(FMPMarketLoader(fmp)),
        financial=FinancialService(FMPFinancialLoader(fmp)),
        analyst=AnalystService(FMPAnalystLoader(fmp)),
        company=CompanyService(FMPCompanyLoader(fmp)),
        news=NewsService(FMPNewsLoader(fmp)),
        performance=PerformanceService(FMPMarketPerformanceLoader(fmp)),
        insider=InsiderService(
            insider=FMPInsiderTradeLoader(fmp),
            congress=FMPCongressTradeLoader(fmp),
        ),
        calendar=CalendarService(FMPCalendarLoader(fmp)),
    )

    yield

    if _cache:
        await _cache.close()
    if _pool:
        await _pool.close()


def get_services() -> Services:
    assert _services is not None, "Services not initialized"
    return _services


def get_runner() -> AgentRunner:
    return AgentRunner(get_services())
