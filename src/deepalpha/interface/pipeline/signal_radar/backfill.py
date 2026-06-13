"""
信号趋势雷达 Backfill 脚本

按日期顺序回放原始信号，重建最近 N 天的每日得分快照。
不依赖 LLM，直接复用已提取的主题。

用法:
  uv run python -m deepalpha.interface.pipeline.signal_radar.backfill
"""
from __future__ import annotations

import asyncio
import datetime
import json
import logging
from collections import defaultdict

import asyncpg

from deepalpha.domain.signal_radar.models import (
    DailyThemeScore,
    ExtractedTheme,
    SignalCategory,
    ThemeSignal,
)
from deepalpha.infrastructure.config import SignalRadarPipelineConfig
from deepalpha.interface.pipeline.signal_radar.scoring import compute_daily_scores

logger = logging.getLogger(__name__)


async def backfill(days: int = 30, momentum_window: int = 7, momentum_cap: float = 3.0) -> None:
    cfg = SignalRadarPipelineConfig()
    pool: asyncpg.Pool[asyncpg.Record] = await asyncpg.create_pool(cfg.asyncpg_dsn())  # type: ignore[assignment]

    try:
        # ── 1. 读取所有原始信号 + 主题 ──
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    ri.ticker,
                    ri.source_type,
                    ri.signal_date,
                    et.theme_name,
                    et.category,
                    et.confidence
                FROM signal_raw_items ri
                JOIN signal_extracted_themes et ON et.raw_item_id = ri.id
                WHERE ri.signal_date >= CURRENT_DATE - make_interval(days => $1)::interval
                ORDER BY ri.signal_date
                """,
                days,
            )

        # 按日期分组
        signals_by_date: dict[datetime.date, list[ThemeSignal]] = defaultdict(list)
        for r in rows:
            date: datetime.date = r["signal_date"]
            signals_by_date[date].append(
                ThemeSignal(
                    theme=ExtractedTheme(
                        name=r["theme_name"],
                        category=SignalCategory(r["category"]),
                        confidence=float(r["confidence"]),
                    ),
                    source_type=r["source_type"],
                    ticker=r["ticker"],
                    signal_date=date,
                )
            )

        if not signals_by_date:
            logger.warning("没有任何原始信号，退出")
            return

        all_dates = sorted(signals_by_date.keys())
        logger.info("发现 %d 个有信号的唯一日期: %s ~ %s", len(all_dates), all_dates[0], all_dates[-1])

        # ── 2. 按日期顺序回放 ──
        cumulative: dict[str, float] = defaultdict(float)
        past_scores_cache: dict[datetime.date, dict[str, float]] = {}

        async with pool.acquire() as conn:
            for date in all_dates:
                day_signals = signals_by_date[date]
                if not day_signals:
                    continue

                logger.info("处理 %s，信号数: %d", date, len(day_signals))

                # 计算过去 momentum_window 天的平均 base_score
                since = date - datetime.timedelta(days=momentum_window)
                sum_base: dict[str, float] = defaultdict(float)
                count_base: dict[str, int] = defaultdict(int)
                for past_date, scores in past_scores_cache.items():
                    if since <= past_date < date:
                        for theme, base in scores.items():
                            sum_base[theme] += base
                            count_base[theme] += 1
                past_scores = {t: sum_base[t] / max(count_base[t], 1) for t in sum_base}

                daily_scores = compute_daily_scores(
                    signals=day_signals,
                    past_scores=past_scores,
                    prev_cumulative=dict(cumulative),
                    today=date,
                    momentum_cap=momentum_cap,
                )

                for s in daily_scores:
                    cumulative[s.theme_name] = s.cumulative_score
                past_scores_cache[date] = {s.theme_name: s.base_score for s in daily_scores}

                await _upsert_scores(conn, daily_scores)

            logger.info("Backfill 完成，共 %d 天，%d 个唯一主题", len(all_dates), len(cumulative))
    finally:
        await pool.close()


async def _upsert_scores(conn: asyncpg.Connection, scores: list[DailyThemeScore]) -> None:
    if not scores:
        return
    await conn.executemany(
        """
        INSERT INTO signal_theme_daily_scores
            (theme_name, category, score_date, base_score, momentum, final_score,
             cumulative_score, company_count, signal_breakdown)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
        ON CONFLICT (theme_name, score_date) DO UPDATE SET
            base_score=EXCLUDED.base_score, momentum=EXCLUDED.momentum,
            final_score=EXCLUDED.final_score, cumulative_score=EXCLUDED.cumulative_score,
            company_count=EXCLUDED.company_count, signal_breakdown=EXCLUDED.signal_breakdown,
            updated_at=NOW()
        """,
        [
            (
                s.theme_name, s.category.value, s.score_date,
                s.base_score, s.momentum, s.final_score,
                s.cumulative_score, s.company_count,
                json.dumps(s.signal_breakdown),
            )
            for s in scores
        ],
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="重建信号雷达每日评分快照")
    parser.add_argument("--days", type=int, default=30, help="回溯天数（默认 30）")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(backfill(days=args.days))