"""
日度任务：更新 ETF 持仓并刷新 Valkey 缓存

调度：每个交易日 04:30（新加坡时间，对应美东收盘后 16:30）
流程：读取 concept_etf_map → yfinance 持仓拉取 → 合并聚合 → DB 写入 → 缓存刷新
"""

import asyncio
import datetime
import logging
from collections import defaultdict

from deepalpha.infrastructure.config import ConceptPipelineConfig
from deepalpha.infrastructure.cache.concept_cache import ConceptCache
from deepalpha.infrastructure.db.concept_repo import ConceptRepo
from deepalpha.infrastructure.providers.yfinance.etf_loader import (
    aggregate_holdings,
    fetch_holdings,
)

logger = logging.getLogger(__name__)


async def main(config: ConceptPipelineConfig | None = None) -> None:
    if config is None:
        config = ConceptPipelineConfig()

    today = datetime.date.today()

    async with ConceptRepo(config.asyncpg_dsn()) as repo:
        etf_maps = await repo.load_etf_map()
        if not etf_maps:
            logger.warning("concept_etf_map 为空，请先运行 build_concept_map.py")
            return

        logger.info("读取到 %d 条 ETF 映射，开始拉取持仓...", len(etf_maps))
        unique_etfs = list({em.etf_symbol for em in etf_maps})

        holdings_by_etf: dict[str, list] = {}
        for i, etf_symbol in enumerate(unique_etfs):
            holdings = await fetch_holdings(etf_symbol)
            holdings_by_etf[etf_symbol] = holdings
            logger.info("  [%d/%d] %s: %d 条持仓", i + 1, len(unique_etfs), etf_symbol, len(holdings))

        logger.info("持仓拉取完成，开始聚合...")
        stocks = await aggregate_holdings(etf_maps, holdings_by_etf, date=today)
        logger.info("聚合完成，%d 条成分股记录，写入数据库...", len(stocks))

        await repo.upsert_stocks(today, stocks)
        logger.info("数据库写入完成，刷新 Valkey 缓存...")

        summaries = await repo.get_all_summaries()

    stocks_by_concept: dict[str, list] = defaultdict(list)
    for s in stocks:
        stocks_by_concept[s.concept].append(s)

    cache = ConceptCache(
        host=config.valkey_host,
        port=config.valkey_port,
        password=config.valkey_password,
        ssl=config.valkey_ssl,
        ttl=config.concept_cache_ttl,
    )
    try:
        await cache.set_list(summaries)
        for summary in summaries:
            await cache.set_concept(summary.concept, stocks_by_concept.get(summary.concept, []))
        logger.info("缓存刷新完成，共 %d 个概念", len(summaries))
    finally:
        await cache.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main())
