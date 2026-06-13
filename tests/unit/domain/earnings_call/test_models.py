"""财报电话会议 domain 模型测试"""

import datetime

from deepalpha.domain.earnings_call.models import (
    EarningsCallDetail,
    EarningsCallEvent,
    EarningsCallTranscript,
)


def test_earnings_call_event_fields():
    """测试 EarningsCallEvent 字段"""
    event = EarningsCallEvent(
        symbol="AAPL",
        date=datetime.date(2026, 6, 14),
        year=2026,
        quarter=2,
        has_transcript=True,
    )
    assert event.symbol == "AAPL"
    assert event.quarter == 2
    assert event.has_transcript is True


def test_earnings_call_transcript_fields():
    """测试 EarningsCallTranscript 字段"""
    t = EarningsCallTranscript(
        symbol="AAPL",
        year=2026,
        quarter=2,
        date=datetime.date(2026, 6, 14),
        content="Good morning everyone...",
    )
    assert t.content == "Good morning everyone..."


def test_earnings_call_detail_fields():
    """测试 EarningsCallDetail 字段"""
    d = EarningsCallDetail(
        symbol="AAPL",
        year=2026,
        quarter=2,
        date=datetime.date(2026, 6, 14),
        company_name="苹果公司",
        description_zh="苹果是全球最大科技公司之一",
        products_zh="iPhone, Mac, iPad, Apple Watch",
        summary_zh="本季度营收创历史新高...",
        transcript_zh="大家好，欢迎参加苹果公司...",
        translated_at=datetime.datetime(2026, 6, 14, 10, 0, 0),
    )
    assert d.company_name == "苹果公司"
