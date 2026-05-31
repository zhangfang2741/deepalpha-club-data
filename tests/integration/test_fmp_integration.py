"""集成测试 — 需要真实 FMP_API_KEY 环境变量，仅在 CI 中按需运行。

运行方式：
    FMP_API_KEY=your_key uv run pytest tests/integration/ -v -m integration
"""
import pytest
from deepalpha import FMPDataHub


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_quote_real_aapl():
    async with FMPDataHub() as hub:
        quote = await hub.market.get_quote("AAPL")
    assert quote.symbol == "AAPL"
    assert quote.price > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_income_statement_real():
    async with FMPDataHub() as hub:
        df = await hub.financial.get_income_statement("AAPL", limit=1)
    assert len(df) == 1
    assert "revenue" in df.columns


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_sector_performance_real():
    async with FMPDataHub() as hub:
        df = await hub.performance.get_sector_performance()
    assert len(df) > 0
    assert "sector" in df.columns
