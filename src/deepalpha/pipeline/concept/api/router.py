"""
概念股池 FastAPI 查询接口

挂载方式：
    from deepalpha.pipeline.concept.api.router import router
    app.include_router(router, prefix="/api/v1")
"""

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from deepalpha.models.concept import ConceptStock, ConceptSummary
from deepalpha.pipeline.concept.cache import ConceptCache
from deepalpha.pipeline.concept.config import ConceptPipelineConfig
from deepalpha.pipeline.concept.db import ConceptDb

router = APIRouter(prefix="/concept", tags=["concept"])


def get_config() -> ConceptPipelineConfig:
    return ConceptPipelineConfig()


def get_cache(config: Annotated[ConceptPipelineConfig, Depends(get_config)]) -> ConceptCache:
    return ConceptCache(
        host=config.valkey_host,
        port=config.valkey_port,
        password=config.valkey_password,
        ssl=config.valkey_ssl,
        ttl=config.concept_cache_ttl,
    )


@router.get("/list", response_model=list[ConceptSummary])
async def list_concepts(
    config: Annotated[ConceptPipelineConfig, Depends(get_config)],
    cache: Annotated[ConceptCache, Depends(get_cache)],
) -> list[ConceptSummary]:
    """返回所有概念摘要，包含 ETF 数量、成分股数、top5 成分股和最后更新日。"""
    cached = await cache.get_list()
    if cached is not None:
        return cached
    async with ConceptDb(config.asyncpg_dsn()) as db:
        summaries = await db.get_all_concept_summaries()
    await cache.set_list(summaries)
    return summaries


@router.get("/{name}", response_model=list[ConceptStock])
async def get_concept(
    name: str,
    config: Annotated[ConceptPipelineConfig, Depends(get_config)],
    cache: Annotated[ConceptCache, Depends(get_cache)],
    min_etf_count: int = Query(1, ge=1, description="最低 ETF 覆盖数，用于控制成分股纯度"),
) -> list[ConceptStock]:
    """返回指定概念的最新成分股列表，按 etf_count 降序排列。"""
    cached = await cache.get_concept(name)
    if cached is None:
        async with ConceptDb(config.asyncpg_dsn()) as db:
            cached = await db.get_latest_stocks(name)
        if cached:
            await cache.set_concept(name, cached)

    filtered = [s for s in (cached or []) if s.etf_count >= min_etf_count]
    if not filtered and not cached:
        raise HTTPException(status_code=404, detail=f"概念 '{name}' 不存在")
    return filtered


@router.get("/{name}/history", response_model=list[ConceptStock])
async def get_concept_history(
    name: str,
    config: Annotated[ConceptPipelineConfig, Depends(get_config)],
    start: datetime.date = Query(..., description="开始日期（含），格式 YYYY-MM-DD"),
    end: datetime.date = Query(..., description="结束日期（含），格式 YYYY-MM-DD"),
) -> list[ConceptStock]:
    """返回指定概念在日期范围内的历史成分股快照。"""
    async with ConceptDb(config.asyncpg_dsn()) as db:
        return await db.get_stocks_history(name, start, end)
