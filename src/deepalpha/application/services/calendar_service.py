"""日历事件业务逻辑服务"""
import datetime
from typing import Protocol

from deepalpha.domain.market.models import EarningsEvent, DividendEvent


class ICalendarProvider(Protocol):
    async def get_earnings_calendar(self, start: datetime.date, end: datetime.date) -> list[EarningsEvent]: ...
    async def get_dividend_calendar(self, start: datetime.date, end: datetime.date) -> list[DividendEvent]: ...


class CalendarService:
    def __init__(self, provider: ICalendarProvider) -> None:
        self._provider = provider

    async def get_upcoming_earnings(self, days: int = 7) -> list[EarningsEvent]:
        today = datetime.date.today()
        end = today + datetime.timedelta(days=days)
        events = await self._provider.get_earnings_calendar(start=today, end=end)
        return sorted(events, key=lambda e: e.date)

    async def get_upcoming_dividends(self, days: int = 14) -> list[DividendEvent]:
        today = datetime.date.today()
        end = today + datetime.timedelta(days=days)
        events = await self._provider.get_dividend_calendar(start=today, end=end)
        return sorted(events, key=lambda e: e.date)
