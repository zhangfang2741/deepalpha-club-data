"""
信号趋势雷达 Pipeline

调度建议：每日 UTC 06:00 运行一次（cron: 0 6 * * *）

流程：
  1. 读取 qqq_tickers.yaml 和 greenhouse_slugs.yaml
  2. 并发采集 8-K / XBRL Capex（按 ticker 并发，限制5个并发）
  3. 串行采集 Form D（跨公司，单次搜索）
  4. 并发采集 Greenhouse/Lever 招聘
  5. 批量 LLM 提取主题
  6. 计算加权动量评分
  7. 写入 PostgreSQL 每日快照
"""
import asyncio
import datetime
import logging
from pathlib import Path

import httpx
import yaml

from collections import defaultdict

from deepalpha.domain.signal_radar.models import ExtractedTheme, RawSignalItem, ThemeSignal
from deepalpha.infrastructure.config import SignalRadarPipelineConfig
from deepalpha.infrastructure.db.signal_radar_repo import SignalRadarRepo
from deepalpha.infrastructure.providers.edgar.cik_resolver import CikResolver
from deepalpha.infrastructure.providers.edgar.filing_8k_loader import Filing8KLoader
from deepalpha.infrastructure.providers.edgar.form_d_loader import FormDLoader
from deepalpha.infrastructure.providers.edgar.xbrl_capex_loader import XbrlCapexLoader
from deepalpha.infrastructure.providers.greenhouse.job_loader import CompanySlug, JobLoader
from deepalpha.infrastructure.providers.minimax.theme_extractor import ThemeExtractor
from deepalpha.interface.pipeline.signal_radar.scoring import compute_daily_scores

logger = logging.getLogger(__name__)


def load_tickers(yaml_path: str) -> list[str]:
    path = Path(yaml_path)
    if not path.exists():
        logger.warning("QQQ tickers 配置不存在: %s", yaml_path)
        return []
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [str(t) for t in data.get("tickers", [])]


def load_slugs(yaml_path: str) -> list[CompanySlug]:
    path = Path(yaml_path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [
        CompanySlug(ticker=c["ticker"], slug=c["slug"], type=c["type"])
        for c in data.get("companies", [])
    ]


async def collect_all_signals(
    tickers: list[str],
    slugs: list[CompanySlug],
    since: datetime.date,
    until: datetime.date,
    client: httpx.AsyncClient,
) -> list[RawSignalItem]:
    resolver = CikResolver(client)
    loader_8k = Filing8KLoader(client, resolver)
    loader_capex = XbrlCapexLoader(client, resolver)
    loader_form_d = FormDLoader(client)
    loader_jobs = JobLoader(client)

    sem = asyncio.Semaphore(20)

    async def fetch_ticker(ticker: str) -> list[RawSignalItem]:
        async with sem:
            items_8k = await loader_8k.fetch(ticker, since)
            await asyncio.sleep(0.1)  # EDGAR 礼貌延迟
            items_capex = await loader_capex.fetch(ticker, since)
            return items_8k + items_capex

    ticker_results = await asyncio.gather(*[fetch_ticker(t) for t in tickers])
    all_items: list[RawSignalItem] = [item for sublist in ticker_results for item in sublist]

    form_d_items = await loader_form_d.fetch(since=since, until=until)
    all_items.extend(form_d_items)

    job_results = await asyncio.gather(*[loader_jobs.fetch(slug, since) for slug in slugs])
    all_items.extend([item for sublist in job_results for item in sublist])

    logger.info("采集完成，共 %d 条原始信号", len(all_items))
    return all_items


async def main(config: SignalRadarPipelineConfig | None = None) -> None:
    if config is None:
        config = SignalRadarPipelineConfig()

    today = datetime.date.today()
    since = today - datetime.timedelta(days=config.edgar_lookback_days)

    tickers = load_tickers(config.qqq_tickers_yaml)
    slugs = load_slugs(config.greenhouse_slugs_yaml)
    if not tickers:
        logger.warning("无 QQQ tickers 配置，退出")
        return

    logger.info("开始信号雷达 pipeline，日期: %s，监控 %d 个 ticker", today, len(tickers))

    repo = await SignalRadarRepo.create(config.asyncpg_dsn())
    try:
        await repo.log_pipeline_run(today)
        items_fetched = 0
        themes_extracted = 0

        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            all_items = await collect_all_signals(tickers, slugs, since, today, client)
            extractor = ThemeExtractor(client, api_key=config.minimax_api_key)

            all_signals: list[ThemeSignal] = []
            for item in all_items:
                if await repo.is_raw_item_processed(item.ticker, item.source_type, item.doc_id):
                    continue
                raw_id = await repo.insert_raw_item(
                    item.ticker, item.source_type, item.signal_date, item.doc_id, item.text_snippet
                )
                items_fetched += 1
                themes = await extractor.extract(item.text_snippet, item.source_type)
                if themes:
                    await repo.insert_extracted_themes(raw_id, themes, item.signal_date)
                    themes_extracted += len(themes)
                    for t in themes:
                        all_signals.append(
                            ThemeSignal(theme=t, source_type=item.source_type, ticker=item.ticker, signal_date=item.signal_date)
                        )
                await asyncio.sleep(0.05)  # MiniMax 限速保护

        if all_signals:
            # 按信号实际日期分组，分别计算每一天的得分
            by_date: dict[datetime.date, list[ThemeSignal]] = defaultdict(list)
            for sig in all_signals:
                               by_date[sig.signal_date].append(sig)

            for score_date, day_signals in sorted(by_date.items()):
                theme_names = list({s.theme.name for s in day_signals})
                past_scores = await repo.get_past_base_scores(
                    theme_names, score_date, config.momentum_window_days
                )
                prev_cumulative = await repo.get_cumulative_scores(theme_names, score_date)
                daily_scores = compute_daily_scores(
                    day_signals, past_scores, prev_cumulative, score_date, config.momentum_cap
                )
                await repo.upsert_daily_scores(daily_scores)
                logger.info("写入 %s 的 %d 个主题得分快照", score_date, len(daily_scores))

        await repo.update_pipeline_run(today, "success", items_fetched, themes_extracted, None)
        logger.info("Pipeline 完成：%d 条新信号，%d 个主题", items_fetched, themes_extracted)

    except Exception as exc:
        logger.error("Pipeline 失败: %s", exc, exc_info=True)
        await repo.update_pipeline_run(today, "failed", 0, 0, str(exc))
        raise
    finally:
        await repo.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(main())
