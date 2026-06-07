"""
信号趋势雷达评分引擎（纯函数，无 I/O）

最终分 = 加权基础分 × min(动量系数, cap)
动量系数 = 今日基础分 / max(过去N天均值, 1)
"""
import datetime
from deepalpha.domain.signal_radar.models import DailyThemeScore, SignalCategory, ThemeSignal

_SOURCE_WEIGHTS: dict[str, int] = {
    "earnings_call": 3,
    "capex":         4,
    "form_d":        2,
    "job_posting":   1,
}


def compute_daily_scores(
    signals: list[ThemeSignal],
    past_scores: dict[str, float],
    prev_cumulative: dict[str, float],
    today: datetime.date,
    momentum_cap: float = 3.0,
) -> list[DailyThemeScore]:
    """计算今日所有主题的得分快照列表，按 final_score 倒序排列。"""
    base: dict[str, float] = {}
    breakdown: dict[str, dict[str, float]] = {}
    companies: dict[str, set[str]] = {}
    categories: dict[str, SignalCategory] = {}

    for sig in signals:
        name = sig.theme.name
        weight = _SOURCE_WEIGHTS.get(sig.source_type, 1)
        contribution = weight * sig.theme.confidence

        if name not in base:
            base[name] = 0.0
            breakdown[name] = {}
            companies[name] = set()
            categories[name] = sig.theme.category

        base[name] += contribution
        breakdown[name][sig.source_type] = (
            breakdown[name].get(sig.source_type, 0.0) + contribution
        )
        companies[name].add(sig.ticker)

    results: list[DailyThemeScore] = []
    for name, base_score in base.items():
        avg_past = past_scores.get(name, 0.0)
        momentum = base_score / max(avg_past, 1.0)
        momentum = min(momentum, momentum_cap)
        final = base_score * momentum
        cumulative = prev_cumulative.get(name, 0.0) + final
        results.append(DailyThemeScore(
            theme_name=name,
            category=categories[name],
            score_date=today,
            base_score=round(base_score, 4),
            momentum=round(momentum, 4),
            final_score=round(final, 4),
            cumulative_score=round(cumulative, 4),
            company_count=len(companies[name]),
            signal_breakdown={k: round(v, 4) for k, v in breakdown[name].items()},
        ))
    return sorted(results, key=lambda s: s.final_score, reverse=True)
