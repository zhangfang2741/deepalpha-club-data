import datetime
import pytest
from unittest.mock import AsyncMock

from deepalpha.application.agent.tools import dispatch_tool, build_tools, Services
from deepalpha.domain.concept.models import ConceptStock
from deepalpha.domain.market.models import Quote


class FakeServices:
    def __init__(self):
        self.concept = AsyncMock()
        self.market = AsyncMock()
        self.financial = AsyncMock()
        self.analyst = AsyncMock()


@pytest.mark.asyncio
async def test_search_concept_returns_formatted_list():
    svc = FakeServices()
    svc.concept.get_concept = AsyncMock(return_value=[
        ConceptStock(
            date=datetime.date(2026, 6, 1), concept="AI", symbol="NVDA",
            etf_count=5, total_weight=10.0, etfs=["BOTZ"],
        )
    ])
    result = await dispatch_tool("search_concept", {"concept": "AI"}, svc)
    assert "NVDA" in result
    assert "5" in result


@pytest.mark.asyncio
async def test_search_concept_empty_returns_message():
    svc = FakeServices()
    svc.concept.get_concept = AsyncMock(return_value=[])
    result = await dispatch_tool("search_concept", {"concept": "Unknown"}, svc)
    assert "不存在" in result


@pytest.mark.asyncio
async def test_get_quote_returns_price_info():
    svc = FakeServices()
    svc.market.get_quote = AsyncMock(return_value=Quote(
        symbol="AAPL", price=190.5, change=1.2, changes_percentage=0.63,
    ))
    result = await dispatch_tool("get_quote", {"symbol": "AAPL"}, svc)
    assert "190.5" in result
    assert "AAPL" in result


def test_tools_list_has_four_entries():
    from unittest.mock import MagicMock
    svc = MagicMock(spec=Services)
    tools = build_tools(svc)
    assert len(tools) == 4
    names = {t.name for t in tools}
    assert names == {"search_concept", "get_quote", "get_financials", "generate_report"}
