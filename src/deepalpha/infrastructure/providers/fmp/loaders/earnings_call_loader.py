import datetime

from deepalpha.domain.earnings_call.models import EarningsCallEvent, EarningsCallTranscript
from deepalpha.infrastructure.providers.base import BaseLoader


def _date_to_year_quarter(d: datetime.date) -> tuple[int, int]:
    """将日期转换为（财年, 季度），以日历季度计。"""
    quarter = (d.month - 1) // 3 + 1
    return d.year, quarter


class FMPEarningsCallLoader(BaseLoader):
    """FMP 财报电话会议数据加载器。"""

    def __init__(self, client, allowed_tickers: frozenset[str]) -> None:
        super().__init__(client)
        self._allowed = allowed_tickers

    async def get_events(
        self, start: datetime.date, end: datetime.date
    ) -> list[EarningsCallEvent]:
        """获取日期范围内的财报电话会议事件，过滤到 allowed_tickers。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            EarningsCallEvent 列表，仅包含 allowed_tickers 中的公司
        """
        today = datetime.date.today()
        records = await self._get_list(
            "/stable/earnings-calendar", **{"from": str(start), "to": str(end)}
        )
        events = []
        for r in records:
            symbol = r.get("symbol", "")
            if symbol not in self._allowed:
                continue
            raw_date = r.get("date", "")
            if not raw_date:
                continue
            try:
                d = datetime.date.fromisoformat(raw_date)
            except ValueError:
                continue
            year, quarter = _date_to_year_quarter(d)
            events.append(
                EarningsCallEvent(
                    symbol=symbol,
                    date=d,
                    year=year,
                    quarter=quarter,
                    has_transcript=d <= today,
                )
            )
        return events

    async def get_transcript(
        self, symbol: str, year: int, quarter: int
    ) -> EarningsCallTranscript | None:
        """获取指定公司、财年、季度的电话会议原文。

        Args:
            symbol: 股票代码
            year: 财年
            quarter: 季度 1-4

        Returns:
            EarningsCallTranscript，若 FMP 无数据则返回 None
        """
        records = await self._get_list(
            "/stable/earning-call-transcript",
            symbol=symbol,
            year=year,
            quarter=quarter,
        )
        if not records:
            return None
        r = records[0]
        raw_date = r.get("date", "")
        try:
            d = datetime.date.fromisoformat(raw_date[:10])
        except (ValueError, TypeError):
            d = datetime.date.today()
        return EarningsCallTranscript(
            symbol=r.get("symbol", symbol),
            year=r.get("year", year),
            quarter=r.get("quarter", quarter),
            date=d,
            content=r.get("content", ""),
        )