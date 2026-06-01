import pytest
from unittest.mock import AsyncMock

from deepalpha.application.services.market_service import MarketService
from deepalpha.domain.market.models import Quote


@pytest.fixture
def mock_provider():
    p = AsyncMock()
    p.get_quote = AsyncMock(return_value=Quote(symbol="AAPL", price=190.5, change=1.2))
    return p


@pytest.mark.asyncio
async def test_get_quote_delegates_to_provider(mock_provider):
    svc = MarketService(mock_provider)
    q = await svc.get_quote("AAPL")
    mock_provider.get_quote.assert_called_once_with("AAPL")
    assert q.symbol == "AAPL"
    assert q.price == 190.5
