"""
月度任务：构建概念 → ETF 映射表

调度：每月 1 日 02:00（新加坡时间）
流程：ETFdb 抓取 → Finnhub AUM 过滤 → concept_etf_map 写入
"""

import asyncio
import logging

from deepalpha.infrastructure.config import ConceptPipelineConfig
from deepalpha.infrastructure.db.concept_repo import ConceptRepo
from deepalpha.infrastructure.providers.etfdb.scraper import scrape_concept_etf_candidates
from deepalpha.infrastructure.providers.finnhub.etf_loader import filter_etfs_by_aum
from deepalpha.infrastructure.providers.finnhub.client import FinnhubClient
from deepalpha.infrastructure.providers.finnhub.config import FinnhubConfig

logger = logging.getLogger(__name__)


async def main(config: ConceptPipelineConfig | None = None) -> None:
    if config is None:
        config = ConceptPipelineConfig()

    logger.info("开始抓取 ETFdb 主题分类...")
    candidates = await scrape_concept_etf_candidates(delay=2.0)
    logger.info("抓取完成，候选 ETF 条目数: %d", len(candidates))

    finnhub_config = FinnhubConfig(finnhub_api_key=config.finnhub_api_key)
    async with FinnhubClient(finnhub_config) as client:
        logger.info("开始 AUM 过滤（阈值: %.0fM）...", config.concept_aum_threshold_million)
        etf_maps = await filter_etfs_by_aum(candidates, client, config.concept_aum_threshold_million)

    logger.info("AUM 过滤完成，通过 %d 条，写入数据库...", len(etf_maps))
    async with ConceptRepo(config.asyncpg_dsn()) as repo:
        await repo.upsert_etf_map(etf_maps)

    concepts = len({em.concept for em in etf_maps})
    etfs = len({em.etf_symbol for em in etf_maps})
    logger.info("月度任务完成：%d 个概念，%d 只 ETF", concepts, etfs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main())
