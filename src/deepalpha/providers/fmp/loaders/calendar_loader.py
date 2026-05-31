import datetime

from deepalpha.loaders.calendar_loader import AbstractCalendarLoader
from deepalpha.models.calendar import DividendEvent, EarningsEvent, IPOEvent, SplitEvent


class FMPCalendarLoader(AbstractCalendarLoader):
    """FMP 日历数据加载器。"""

    async def get_earnings_calendar(
        self, start: datetime.date, end: datetime.date
    ) -> list[EarningsEvent]:
        """获取财报日历数据。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            EarningsEvent 领域对象列表
        """
        records = await self._get_list(
            "/stable/earnings-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_models(records, EarningsEvent)

    async def get_dividend_calendar(
        self, start: datetime.date, end: datetime.date
    ) -> list[DividendEvent]:
        """获取股息日历数据。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            DividendEvent 领域对象列表
        """
        records = await self._get_list(
            "/stable/dividends-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_models(records, DividendEvent)

    async def get_ipo_calendar(
        self, start: datetime.date, end: datetime.date
    ) -> list[IPOEvent]:
        """获取 IPO 日历数据。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            IPOEvent 领域对象列表
        """
        records = await self._get_list(
            "/stable/ipos-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_models(records, IPOEvent)

    async def get_splits_calendar(
        self, start: datetime.date, end: datetime.date
    ) -> list[SplitEvent]:
        """获取拆股日历数据。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            SplitEvent 领域对象列表
        """
        records = await self._get_list(
            "/stable/splits-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_models(records, SplitEvent)
