"""集成测试 — 需要真实 FMP_API_KEY 环境变量，仅在 CI 中按需运行。

运行方式：
    uv run --no-active pytest tests/integration/ -v -m integration -s
"""
import pytest

from deepalpha import FMPDataHub
from deepalpha.loaders.enums import StatementPeriod


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_quote_real_aapl():
    async with FMPDataHub() as hub:
        quote = await hub.market.get_quote("AAPL")
    assert quote.symbol == "AAPL"
    assert quote.price > 0
    print(f"\nAAPL: ${quote.price:.2f}  变化: {quote.changes_percentage:.4f}%")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_price_history():
    import datetime
    async with FMPDataHub() as hub:
        df = await hub.market.get_price_history(
            "NVDA",
            start=datetime.date(2025, 1, 1),
            end=datetime.date(2025, 3, 31),
        )
    assert len(df) > 0
    assert "close" in df.columns
    print(f"\nNVDA 历史行情: {len(df)} 行")
    print(df.head(3).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_sector_performance_real():
    async with FMPDataHub() as hub:
        df = await hub.performance.get_sector_performance()
    # 非交易时段可能返回空，只验证列结构
    print(f"\n板块表现: {len(df)} 行")
    if len(df) > 0:
        assert "sector" in df.columns


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nvda_financial_data():
    """获取 NVDA 完整财务数据"""
    async with FMPDataHub() as hub:
        # 1. 利润表（年度）
        income_df = await hub.financial.get_income_statement("NVDA", limit=4)
        assert len(income_df) > 0, "应获取到利润表数据"
        assert "revenue" in income_df.columns
        print("\n=== NVDA 利润表（年度）===")
        print(income_df.select(["date", "revenue", "gross_profit", "net_income"]).__str__())

        # 2. 资产负债表（年度）
        balance_df = await hub.financial.get_balance_sheet("NVDA", limit=4)
        assert len(balance_df) > 0, "应获取到资产负债表数据"
        assert "total_assets" in balance_df.columns
        print("\n=== NVDA 资产负债表（年度）===")
        print(balance_df.select(["date", "total_assets", "total_liabilities", "total_stockholders_equity"]).__str__())

        # 3. 现金流量表（年度）
        cashflow_df = await hub.financial.get_cash_flow_statement("NVDA", limit=4)
        assert len(cashflow_df) > 0, "应获取到现金流量表数据"
        assert "operating_cash_flow" in cashflow_df.columns
        print("\n=== NVDA 现金流量表（年度）===")
        print(cashflow_df.select(["date", "operating_cash_flow", "capital_expenditure", "free_cash_flow"]).__str__())

        # 4. 财务比率（年度）
        ratios_df = await hub.financial.get_financial_ratios("NVDA", limit=4)
        assert len(ratios_df) > 0, "应获取到财务比率数据"
        assert "gross_profit_margin" in ratios_df.columns
        print("\n=== NVDA 财务比率（年度）===")
        print(ratios_df.select(["date", "gross_profit_margin", "return_on_equity", "return_on_assets"]).__str__())

        # 5. 关键指标（年度）
        metrics_df = await hub.financial.get_key_metrics("NVDA", limit=4)
        assert len(metrics_df) > 0, "应获取到关键指标数据"
        assert "pe_ratio" in metrics_df.columns
        print("\n=== NVDA 关键指标（年度）===")
        print(metrics_df.select(["date", "pe_ratio", "price_to_book", "price_to_sales", "ev_to_ebitda"]).__str__())

        # 6. DCF 估值
        valuation = await hub.financial.get_valuation("NVDA")
        assert valuation.dcf is not None and valuation.dcf > 0, "DCF 估值应大于 0"
        print(f"\n=== NVDA DCF 估值 ===")
        print(f"DCF 内在价值: ${valuation.dcf:.2f}")

        # 7. 季度数据（最近 2 季）
        income_q = await hub.financial.get_income_statement(
            "NVDA", period=StatementPeriod.QUARTER, limit=2
        )
        assert len(income_q) > 0, "季度数据应有记录"
        print(f"\n=== NVDA 利润表（季度，最近 2 季）===")
        print(income_q.select(["date", "period", "revenue", "net_income"]).__str__())
