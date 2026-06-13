import datetime
from deepalpha.domain.signal_radar.models import ExtractedTheme, SignalCategory, ThemeSignal
from deepalpha.interface.pipeline.signal_radar.scoring import compute_daily_scores

TODAY = datetime.date(2026, 6, 7)


def _theme(name: str, cat: SignalCategory = SignalCategory.tech_concept, conf: float = 0.9) -> ExtractedTheme:
    return ExtractedTheme(name=name, category=cat, confidence=conf)


def _signal(name: str, source: str, ticker: str = "NVDA", signal_date: datetime.date = TODAY) -> ThemeSignal:
    return ThemeSignal(theme=_theme(name), source_type=source, ticker=ticker, signal_date=signal_date)


def test_base_score_uses_source_weights():
    signals = [
        _signal("HBM3e", "capex"),        # weight=4, conf=0.9 → 3.6
        _signal("HBM3e", "earnings_call"), # weight=3, conf=0.9 → 2.7
    ]
    scores = compute_daily_scores(signals, past_scores={}, prev_cumulative={}, today=TODAY)
    assert len(scores) == 1
    assert abs(scores[0].base_score - 6.3) < 0.01


def test_momentum_caps_at_configured_max():
    signals = [_signal("MCP", "capex")]
    scores = compute_daily_scores(
        signals, past_scores={"MCP": 0.01}, prev_cumulative={}, today=TODAY, momentum_cap=3.0
    )
    assert scores[0].momentum == 3.0


def test_cumulative_adds_to_previous():
    signals = [_signal("MCP", "earnings_call")]
    scores = compute_daily_scores(
        signals, past_scores={}, prev_cumulative={"MCP": 100.0}, today=TODAY
    )
    assert scores[0].cumulative_score > 100.0


def test_company_count_tracks_unique_tickers():
    signals = [
        ThemeSignal(theme=_theme("HBM3e"), source_type="capex", ticker="NVDA", signal_date=TODAY),
        ThemeSignal(theme=_theme("HBM3e"), source_type="capex", ticker="AMD", signal_date=TODAY),
        ThemeSignal(theme=_theme("HBM3e"), source_type="capex", ticker="NVDA", signal_date=TODAY),  # 重复
    ]
    scores = compute_daily_scores(signals, past_scores={}, prev_cumulative={}, today=TODAY)
    assert scores[0].company_count == 2
