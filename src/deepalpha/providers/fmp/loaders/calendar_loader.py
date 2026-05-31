import datetime
import polars as pl
from deepalpha.loaders.calendar_loader import AbstractCalendarLoader
from deepalpha.models.calendar import EarningsEvent, DividendEvent, IPOEvent, SplitEvent


class FMPCalendarLoader(AbstractCalendarLoader):
    """FMP 日历数据加载器。"""

    async def get_earnings_calendar(
        self, start: datetime.date, end: datetime.date
    ) -> pl.DataFrame:
        """获取财报日历数据。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            财报日历 DataFrame
        """
        records = await self._get_list(
            "/stable/earnings-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_df(records, EarningsEvent)

    async def get_dividend_calendar(
        self, start: datetime.date, end: datetime.date
    ) -> pl.DataFrame:
        """获取股息日历数据。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            股息日历 DataFrame
        """
        records = await self._get_list(
            "/stable/dividends-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_df(records, DividendEvent)

    async def get_ipo_calendar(
        self, start: datetime.date, end: datetime.date
    ) -> pl.DataFrame:
        """获取 IPO 日历数据。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            IPO 日历 DataFrame
        """
        records = await self._get_list(
            "/stable/ipos-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_df(records, IPOEvent)

    async def get_splits_calendar(
        self, start: datetime.date, end: datetime.date
    ) -> pl.DataFrame:
        """获取拆股日历数据。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            拆股日历 DataFrame
        """
        records = await self._get_list(
            "/stable/splits-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_df(records, SplitEvent)
