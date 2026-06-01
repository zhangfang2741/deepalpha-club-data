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
from deepalpha.application.services.concept_service import ConceptService
from deepalpha.application.services.financial_service import FinancialService
from deepalpha.application.services.market_service import MarketService
from deepalpha.infrastructure.cache.concept_cache import ConceptCache
from deepalpha.infrastructure.db.concept_repo import ConceptRepo
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.analyst_loader import FMPAnalystLoader
from deepalpha.infrastructure.providers.fmp.loaders.financial_loader import FMPFinancialLoader
from deepalpha.infrastructure.providers.fmp.loaders.market_loader import FMPMarketLoader
from deepalpha.infrastructure.config import ConceptPipelineConfig


@lru_cache(maxsize=1)
def get_config() -> ConceptPipelineConfig:
    return ConceptPipelineConfig()


_services: Services | None = None
_pool: asyncpg.Pool | None = None  # type: ignore[type-arg]
_cache: ConceptCache | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _services, _pool, _cache
    cfg = get_config()

    _pool = await asyncpg.create_pool(cfg.asyncpg_dsn())
    _cache = ConceptCache(
        host=cfg.valkey_host,
        port=cfg.valkey_port,
        password=cfg.valkey_password,
        ssl=cfg.valkey_ssl,
    )

    repo = ConceptRepo(cfg.asyncpg_dsn())
    repo._pool = _pool  # 复用已创建的连接池

    fmp_cfg = FMPConfig()
    fmp_client = FMPAsyncClient(fmp_cfg)

    _services = Services(
        concept=ConceptService(repo, _cache),
        market=MarketService(FMPMarketLoader(fmp_client)),
        financial=FinancialService(FMPFinancialLoader(fmp_client)),
        analyst=AnalystService(FMPAnalystLoader(fmp_client)),
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
