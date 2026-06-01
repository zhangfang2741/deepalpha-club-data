"""
日度任务：更新 ETF 持仓并刷新 Valkey 缓存

调度：每个交易日 04:30（新加坡时间，对应美东收盘后 16:30）
流程：读取 concept_etf_map → Finnhub 持仓拉取 → 合并聚合 → DB 写入 → 缓存刷新
"""

import asyncio
import datetime
import logging

from deepalpha.pipeline.concept.cache import ConceptCache
from deepalpha.pipeline.concept.config import ConceptPipelineConfig
from deepalpha.pipeline.concept.db import ConceptDb
from deepalpha.pipeline.concept.finnhub_loader import (
    aggregate_holdings,
    fetch_holdings_with_fallback,
)
from deepalpha.providers.finnhub.client import FinnhubClient
from deepalpha.providers.finnhub.config import FinnhubConfig

logger = logging.getLogger(__name__)


async def run(config: ConceptPipelineConfig | None = None) -> None:
    if config is None:
        config = ConceptPipelineConfig()

    today = datetime.date.today()
    finnhub_config = FinnhubConfig(finnhub_api_key=config.finnhub_api_key)

    async with ConceptDb(config.asyncpg_dsn()) as db:
        etf_maps = await db.load_etf_map()
        if not etf_maps:
            logger.warning("concept_etf_map 为空，请先运行 build_concept_map.py")
            return

        logger.info("读取到 %d 条 ETF 映射，开始拉取持仓...", len(etf_maps))
        unique_etfs = list({em.etf_symbol for em in etf_maps})

        holdings_by_etf: dict[str, list] = {}
        async with FinnhubClient(finnhub_config) as client:
            for etf_symbol in unique_etfs:
                holdings = await fetch_holdings_with_fallback(etf_symbol, client)
                holdings_by_etf[etf_symbol] = holdings
                logger.debug("  %s: %d 条持仓", etf_symbol, len(holdings))

        logger.info("持仓拉取完成，开始聚合...")
        stocks = await aggregate_holdings(etf_maps, holdings_by_etf, date=today)
        logger.info("聚合完成，%d 条成分股记录，写入数据库...", len(stocks))

        await db.upsert_stocks(stocks)
        logger.info("数据库写入完成，刷新 Valkey 缓存...")

        summaries = await db.get_all_concept_summaries()

    cache = ConceptCache(
        host=config.valkey_host,
        port=config.valkey_port,
        password=config.valkey_password,
        ssl=config.valkey_ssl,
        ttl=config.concept_cache_ttl,
    )
    try:
        await cache.set_list(summaries)
        async with ConceptDb(config.asyncpg_dsn()) as db:
            for summary in summaries:
                concept_stocks = await db.get_latest_stocks(summary.concept)
                await cache.set_concept(summary.concept, concept_stocks)
        logger.info("缓存刷新完成，共 %d 个概念", len(summaries))
    finally:
        await cache.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run())
