"""earnings_call 领域端口协议"""

import datetime
from typing import Protocol

from deepalpha.domain.earnings_call.models import (
    EarningsCallDetail,
    EarningsCallEvent,
    EarningsCallTranscript,
)


class AbstractEarningsCallLoader(Protocol):
    """财报电话会议加载器抽象协议"""

    async def get_events(
        self, start: datetime.date, end: datetime.date
    ) -> list[EarningsCallEvent]:
        """获取日期范围内的财报电话会议事件列表"""
        ...

    async def get_transcript(
        self, symbol: str, year: int, quarter: int
    ) -> EarningsCallTranscript | None:
        """获取特定公司和季度的财报电话会议原文"""
        ...


class AbstractEarningsCallRepo(Protocol):
    """财报电话会议数据仓储抽象协议"""

    async def get_detail(
        self, symbol: str, year: int, quarter: int
    ) -> EarningsCallDetail | None:
        """获取处理后的财报电话会议详情"""
        ...

    async def save_detail(self, detail: EarningsCallDetail) -> None:
        """保存处理后的财报电话会议详情"""
        ...
