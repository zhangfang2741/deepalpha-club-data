"""
月度任务：构建概念 → ETF 映射表

调度：每月 1 日 02:00（新加坡时间）
流程：Morningstar 分类自动发现 → AUM 过滤 → AI 翻译 → concept_etf_map 写入
"""

import asyncio
import logging
from itertools import islice

from deepalpha.infrastructure.config import ConceptPipelineConfig
from deepalpha.infrastructure.db.concept_repo import ConceptRepo
from deepalpha.infrastructure.providers.yfinance.concept_scraper import scrape_concept_etf_candidates
from deepalpha.infrastructure.providers.yfinance.etf_loader import filter_etfs_by_aum
from deepalpha.infrastructure.providers.minimax.translator import describe_etfs, translate_concepts

logger = logging.getLogger(__name__)

_BATCH = 30  # 每次翻译最多提交的 ETF 数


def _batched(iterable, n):
    it = iter(iterable)
    while chunk := list(islice(it, n)):
        yield chunk


async def main(config: ConceptPipelineConfig | None = None) -> None:
    if config is None:
        config = ConceptPipelineConfig()

    logger.info("开始自动发现主题 ETF...")
    candidates = scrape_concept_etf_candidates(
        aum_threshold_million=config.concept_aum_threshold_million,
    )
    logger.info("发现完成，候选 ETF 条目数: %d", len(candidates))

    etf_maps = await filter_etfs_by_aum(candidates, aum_threshold_million=0)
    logger.info("ETF 详情拉取完成，共 %d 条", len(etf_maps))

    # ── AI 翻译概念名 ──────────────────────────────────────────────
    concept_names = sorted({em.concept for em in etf_maps})
    api_key = config.minimax_api_key
    logger.info("翻译 %d 个概念名称...", len(concept_names))
    concept_zh = await translate_concepts(api_key, concept_names)
    logger.info("概念翻译结果: %s", concept_zh)

    # ── AI 生成 ETF 中文名+介绍（分批，避免 prompt 过长）─────────────
    unique_etfs: dict[str, str] = {
        em.etf_symbol: em.etf_name or em.etf_symbol for em in etf_maps
    }
    etf_zh: dict[str, tuple[str, str]] = {}
    batches = list(_batched(unique_etfs.items(), _BATCH))
    for i, batch in enumerate(batches):
        logger.info("翻译 ETF 批次 %d/%d（%d 只）...", i + 1, len(batches), len(batch))
        result = await describe_etfs(api_key, list(batch))
        etf_zh.update(result)

    # ── 填充翻译字段 ───────────────────────────────────────────────
    for em in etf_maps:
        em.concept_name_zh = concept_zh.get(em.concept)
        zh = etf_zh.get(em.etf_symbol)
        if zh:
            em.etf_name_zh, em.description_zh = zh

    # ── 写入数据库 ─────────────────────────────────────────────────
    logger.info("全量替换数据库（%d 条）...", len(etf_maps))
    async with ConceptRepo(config.asyncpg_dsn()) as repo:
        await repo.replace_etf_map(etf_maps)

    concepts = len({em.concept for em in etf_maps})
    etfs = len({em.etf_symbol for em in etf_maps})
    logger.info("月度任务完成：%d 个概念，%d 只 ETF", concepts, etfs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main())
