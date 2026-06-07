"""信号雷达数据层 Protocol"""
import datetime
from typing import Protocol
from deepalpha.domain.signal_radar.models import DailyThemeScore, ExtractedTheme


class ISignalRadarRepo(Protocol):
    async def is_raw_item_processed(self, ticker: str, source_type: str, doc_id: str) -> bool: ...
    async def insert_raw_item(
        self,
        ticker: str,
        source_type: str,
        signal_date: datetime.date,
        doc_id: str,
        text_snippet: str,
    ) -> int: ...
    async def insert_extracted_themes(
        self,
        raw_item_id: int,
        themes: list[ExtractedTheme],
        extract_date: datetime.date,
    ) -> None: ...
    async def get_past_base_scores(
        self, theme_names: list[str], as_of: datetime.date, window_days: int
    ) -> dict[str, float]: ...
    async def get_cumulative_scores(
        self, theme_names: list[str], as_of: datetime.date
    ) -> dict[str, float]: ...
    async def upsert_daily_scores(self, scores: list[DailyThemeScore]) -> None: ...
    async def log_pipeline_run(self, run_date: datetime.date) -> None: ...
    async def update_pipeline_run(
        self,
        run_date: datetime.date,
        status: str,
        items_fetched: int,
        themes_extracted: int,
        error_detail: str | None,
    ) -> None: ...
    async def get_leaderboard(
        self,
        date: datetime.date,
        window_days: int | None,
        category: str | None,
        limit: int,
    ) -> list[DailyThemeScore]: ...
    async def get_theme_trend(
        self, theme_name: str, from_date: datetime.date, to_date: datetime.date
    ) -> list[DailyThemeScore]: ...
    async def get_snapshot(self, date: datetime.date, limit: int) -> list[DailyThemeScore]: ...
    async def search_themes(self, q: str, limit: int) -> list[str]: ...
