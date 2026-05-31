"""集成测试 — 需要真实 FMP_API_KEY 环境变量，仅在 CI 中按需运行。

运行方式：
    uv run --no-active pytest tests/integration/ -v -m integration -s
"""
import datetime

import polars as pl
import pytest

from deepalpha import FMPDataHub
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import (
    AssetClass,
    CongressChamber,
    IndicatorType,
    Interval,
    MoverDirection,
    StatementPeriod,
)


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
        bars = await hub.market.get_price_history(
            "NVDA",
            start=datetime.date(2025, 1, 1),
            end=datetime.date(2025, 3, 31),
        )
    assert isinstance(bars, list)
    assert len(bars) > 0
    df = BaseLoader.to_dataframe(bars)
    assert "close" in df.columns
    print(f"\nNVDA 历史行情: {len(bars)} 行")
    print(df.head(3).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_sector_performance_real():
    async with FMPDataHub() as hub:
        sectors = await hub.performance.get_sector_performance()
    assert isinstance(sectors, list)
    # 非交易时段可能返回空，只验证列结构
    print(f"\n板块表现: {len(sectors)} 行")
    if len(sectors) > 0:
        df = BaseLoader.to_dataframe(sectors)
        assert "sector" in df.columns


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nvda_financial_data():
    """获取 NVDA 完整财务数据"""
    async with FMPDataHub() as hub:
        # 1. 利润表（年度）
        income_stmts = await hub.financial.get_income_statement("NVDA", limit=4)
        assert isinstance(income_stmts, list)
        assert len(income_stmts) > 0, "应获取到利润表数据"
        income_df = BaseLoader.to_dataframe(income_stmts)
        assert "revenue" in income_df.columns
        print("\n=== NVDA 利润表（年度）===")
        print(income_df.select(["date", "revenue", "gross_profit", "net_income"]).__str__())

        # 2. 资产负债表（年度）
        balance_sheets = await hub.financial.get_balance_sheet("NVDA", limit=4)
        assert isinstance(balance_sheets, list)
        assert len(balance_sheets) > 0, "应获取到资产负债表数据"
        balance_df = BaseLoader.to_dataframe(balance_sheets)
        assert "total_assets" in balance_df.columns
        print("\n=== NVDA 资产负债表（年度）===")
        print(balance_df.select(["date", "total_assets", "total_liabilities", "total_stockholders_equity"]).__str__())

        # 3. 现金流量表（年度）
        cashflows = await hub.financial.get_cash_flow_statement("NVDA", limit=4)
        assert isinstance(cashflows, list)
        assert len(cashflows) > 0, "应获取到现金流量表数据"
        cashflow_df = BaseLoader.to_dataframe(cashflows)
        assert "operating_cash_flow" in cashflow_df.columns
        print("\n=== NVDA 现金流量表（年度）===")
        print(cashflow_df.select(["date", "operating_cash_flow", "capital_expenditure", "free_cash_flow"]).__str__())

        # 4. 财务比率（年度）
        ratios = await hub.financial.get_financial_ratios("NVDA", limit=4)
        assert isinstance(ratios, list)
        assert len(ratios) > 0, "应获取到财务比率数据"
        ratios_df = BaseLoader.to_dataframe(ratios)
        assert "gross_profit_margin" in ratios_df.columns
        print("\n=== NVDA 财务比率（年度）===")
        print(ratios_df.select(["date", "gross_profit_margin", "return_on_equity", "return_on_assets"]).__str__())

        # 5. 关键指标（年度）
        metrics = await hub.financial.get_key_metrics("NVDA", limit=4)
        assert isinstance(metrics, list)
        assert len(metrics) > 0, "应获取到关键指标数据"
        metrics_df = BaseLoader.to_dataframe(metrics)
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
        assert isinstance(income_q, list)
        assert len(income_q) > 0, "季度数据应有记录"
        income_q_df = BaseLoader.to_dataframe(income_q)
        print(f"\n=== NVDA 利润表（季度，最近 2 季）===")
        print(income_q_df.select(["date", "period", "revenue", "net_income"]).__str__())


# ── 市场数据（补充） ──────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_quotes_batch():
    """批量获取多只股票报价"""
    async with FMPDataHub() as hub:
        quotes = await hub.market.get_quotes(["AAPL", "MSFT", "NVDA"])
    assert isinstance(quotes, list)
    assert len(quotes) == 3
    df = BaseLoader.to_dataframe(quotes)
    assert "symbol" in df.columns
    print(f"\n批量报价:")
    print(df.select(["symbol", "price"]).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_price_history_intraday():
    """获取小时级别历史价格"""
    async with FMPDataHub() as hub:
        bars = await hub.market.get_price_history(
            "AAPL",
            start=datetime.date(2026, 5, 28),
            end=datetime.date(2026, 5, 30),
            interval=Interval.ONE_HOUR,
        )
    assert isinstance(bars, list)
    print(f"\nAAPL 小时行情: {len(bars)} 行")
    if len(bars) > 0:
        df = BaseLoader.to_dataframe(bars)
        assert "close" in df.columns
        print(df.head(3).__str__())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_market_snapshot():
    """获取全市场快照（FMP Start 返回空列表）"""
    async with FMPDataHub() as hub:
        snapshots = await hub.market.get_market_snapshot(AssetClass.STOCK)
    assert isinstance(snapshots, list)
    print(f"\n全市场快照: {len(snapshots)} 行（FMP Start 不支持此端点，预期为空）")


# ── 分析师数据 ────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_aapl_analyst_data():
    """获取 AAPL 完整分析师数据"""
    async with FMPDataHub() as hub:
        # 1. 分析师评级快照
        ratings = await hub.analyst.get_ratings("AAPL")
        assert isinstance(ratings, list)
        print(f"\n=== AAPL 分析师评级 === {len(ratings)} 行")
        if len(ratings) > 0:
            ratings_df = BaseLoader.to_dataframe(ratings)
            assert "rating" in ratings_df.columns
            print(ratings_df.head(3).__str__())

        # 2. 价格目标汇总
        targets = await hub.analyst.get_price_targets("AAPL")
        assert isinstance(targets, list)
        print(f"\n=== AAPL 价格目标汇总 ===")
        if len(targets) > 0:
            targets_df = BaseLoader.to_dataframe(targets)
            assert "last_month" in targets_df.columns
            print(targets_df.__str__())

        # 3. 盈利预测（年度）
        estimates = await hub.analyst.get_estimates("AAPL")
        assert isinstance(estimates, list)
        print(f"\n=== AAPL 盈利预测（年度）=== {len(estimates)} 行")
        if len(estimates) > 0:
            estimates_df = BaseLoader.to_dataframe(estimates)
            print(estimates_df.head(3).__str__())


# ── 日历数据 ──────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_calendar_data():
    """获取各类市场事件日历"""
    start = datetime.date(2026, 5, 1)
    end = datetime.date(2026, 7, 31)

    async with FMPDataHub() as hub:
        # 1. 财报日历
        earnings = await hub.calendar.get_earnings_calendar(start, end)
        assert isinstance(earnings, list)
        print(f"\n=== 财报日历（{start} ~ {end}）=== {len(earnings)} 行")
        if len(earnings) > 0:
            earnings_df = BaseLoader.to_dataframe(earnings)
            assert "symbol" in earnings_df.columns
            print(earnings_df.head(3).__str__())

        # 2. 股息日历
        dividends = await hub.calendar.get_dividend_calendar(start, end)
        assert isinstance(dividends, list)
        print(f"\n=== 股息日历（{start} ~ {end}）=== {len(dividends)} 行")
        if len(dividends) > 0:
            dividend_df = BaseLoader.to_dataframe(dividends)
            assert "dividend" in dividend_df.columns
            print(dividend_df.head(3).__str__())

        # 3. IPO 日历
        ipos = await hub.calendar.get_ipo_calendar(start, end)
        assert isinstance(ipos, list)
        print(f"\n=== IPO 日历（{start} ~ {end}）=== {len(ipos)} 行")
        if len(ipos) > 0:
            ipo_df = BaseLoader.to_dataframe(ipos)
            assert "company" in ipo_df.columns
            print(ipo_df.head(3).__str__())

        # 4. 拆股日历
        splits = await hub.calendar.get_splits_calendar(start, end)
        assert isinstance(splits, list)
        print(f"\n=== 拆股日历（{start} ~ {end}）=== {len(splits)} 行")
        if len(splits) > 0:
            splits_df = BaseLoader.to_dataframe(splits)
            assert "numerator" in splits_df.columns
            print(splits_df.head(3).__str__())


# ── 公司数据 ──────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_aapl_company_data():
    """获取 AAPL 完整公司信息"""
    async with FMPDataHub() as hub:
        # 1. 公司概况
        profile = await hub.company.get_profile("AAPL")
        assert profile.symbol == "AAPL", "应返回 AAPL 的公司概况"
        assert profile.company_name is not None
        print(f"\n=== AAPL 公司概况 ===")
        print(f"公司名: {profile.company_name}  行业: {profile.industry}  板块: {profile.sector}")
        print(f"CEO: {profile.ceo}  员工数: {profile.full_time_employees}")

        # 2. 高管名单
        executives = await hub.company.get_executives("AAPL")
        assert isinstance(executives, list)
        print(f"\n=== AAPL 高管名单 === {len(executives)} 人")
        if len(executives) > 0:
            executives_df = BaseLoader.to_dataframe(executives)
            assert "name" in executives_df.columns
            print(executives_df.select(["name", "title"]).head(3).__str__())

        # 3. 同业竞争对手
        peers = await hub.company.get_peers("AAPL")
        assert isinstance(peers, list), "应返回列表"
        print(f"\n=== AAPL 竞争对手 === {len(peers)} 家")
        print(peers[:10])

        # 4. 当前市值
        market_caps = await hub.company.get_market_cap("AAPL")
        assert isinstance(market_caps, list)
        print(f"\n=== AAPL 当前市值 ===")
        if len(market_caps) > 0:
            market_cap_df = BaseLoader.to_dataframe(market_caps)
            assert "market_cap" in market_cap_df.columns
            print(market_cap_df.head(1).__str__())

        # 5. 历史市值
        hist_caps = await hub.company.get_market_cap(
            "AAPL",
            start=datetime.date(2026, 1, 1),
            end=datetime.date(2026, 3, 31),
        )
        assert isinstance(hist_caps, list)
        print(f"\n=== AAPL 历史市值（Q1 2026）=== {len(hist_caps)} 行")
        if len(hist_caps) > 0:
            hist_cap_df = BaseLoader.to_dataframe(hist_caps)
            print(hist_cap_df.head(3).__str__())


# ── 国会议员交易 ──────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_congress_trades():
    """获取国会议员交易数据"""
    async with FMPDataHub() as hub:
        # 1. 参议院最新交易
        senate_trades = await hub.congress.get_congress_trades(
            chamber=CongressChamber.SENATE, limit=20
        )
        assert isinstance(senate_trades, list)
        print(f"\n=== 参议院最新交易 === {len(senate_trades)} 行")
        if len(senate_trades) > 0:
            senate_df = BaseLoader.to_dataframe(senate_trades)
            assert "office" in senate_df.columns
            print(senate_df.select(["office", "symbol", "type", "amount"]).head(5).__str__())

        # 2. 众议院最新交易
        house_trades = await hub.congress.get_congress_trades(
            chamber=CongressChamber.HOUSE, limit=20
        )
        assert isinstance(house_trades, list)
        print(f"\n=== 众议院最新交易 === {len(house_trades)} 行")
        if len(house_trades) > 0:
            house_df = BaseLoader.to_dataframe(house_trades)
            print(house_df.select(["office", "symbol", "type", "amount"]).head(5).__str__())


# ── 目录数据 ──────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_directory_data():
    """获取市场目录数据"""
    async with FMPDataHub() as hub:
        # 1. 股票代码列表（限制行数只验证结构）
        symbols = await hub.directory.get_symbols(AssetClass.STOCK)
        assert isinstance(symbols, list)
        assert len(symbols) > 0, "应返回股票代码列表"
        symbols_df = BaseLoader.to_dataframe(symbols)
        assert "symbol" in symbols_df.columns
        print(f"\n=== 股票代码列表 === 共 {len(symbols)} 只")
        print(symbols_df.head(3).__str__())

        # 2. 交易所列表
        exchanges = await hub.directory.get_exchanges()
        assert isinstance(exchanges, list)
        print(f"\n=== 交易所列表 === {len(exchanges)} 个")
        if len(exchanges) > 0:
            exchanges_df = BaseLoader.to_dataframe(exchanges)
            assert "exchange" in exchanges_df.columns
            print(exchanges_df.head(5).__str__())

        # 3. 板块列表
        sectors = await hub.directory.get_sectors()
        assert isinstance(sectors, list)
        print(f"\n=== 板块列表 === {len(sectors)} 个: {sectors}")

        # 4. 行业列表
        industries = await hub.directory.get_industries()
        assert isinstance(industries, list)
        print(f"\n=== 行业列表 === {len(industries)} 个（前10）: {industries[:10]}")


# ── 宏观经济数据 ──────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_economics_data():
    """获取宏观经济指标数据"""
    async with FMPDataHub() as hub:
        # 1. 可用指标列表
        available = await hub.economics.get_available_indicators()
        assert isinstance(available, list)
        assert "CPI" in available
        assert "GDP" in available
        print(f"\n=== 可用经济指标 === {available}")

        # 2. CPI 数据
        cpi_rows = await hub.economics.get_indicator(
            "CPI",
            start=datetime.date(2024, 1, 1),
            end=datetime.date(2025, 12, 31),
        )
        assert isinstance(cpi_rows, list)
        print(f"\n=== CPI 数据（2024-2025）=== {len(cpi_rows)} 行（FMP Start 计划可能不支持，为空则正常）")
        if len(cpi_rows) > 0:
            cpi_df = BaseLoader.to_dataframe(cpi_rows)
            print(cpi_df.head(5).__str__())

        # 3. GDP 数据
        gdp_rows = await hub.economics.get_indicator(
            "GDP",
            start=datetime.date(2023, 1, 1),
            end=datetime.date(2025, 12, 31),
        )
        assert isinstance(gdp_rows, list)
        print(f"\n=== GDP 数据（2023-2025）=== {len(gdp_rows)} 行")
        if len(gdp_rows) > 0:
            gdp_df = BaseLoader.to_dataframe(gdp_rows)
            print(gdp_df.head(3).__str__())

        # 4. 联邦基准利率
        ffr_rows = await hub.economics.get_indicator(
            "FEDERAL_FUNDS_RATE",
            start=datetime.date(2024, 1, 1),
        )
        assert isinstance(ffr_rows, list)
        print(f"\n=== 联邦基准利率（2024 至今）=== {len(ffr_rows)} 行")
        if len(ffr_rows) > 0:
            ffr_df = BaseLoader.to_dataframe(ffr_rows)
            print(ffr_df.head(5).__str__())


# ── SEC 文件数据 ───────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_aapl_filings_data():
    """获取 AAPL SEC 文件数据"""
    async with FMPDataHub() as hub:
        # 1. 按股票代码查询 10-K 文件
        filings_10k = await hub.filings.get_filings(symbol="AAPL", form_type="10-K", limit=5)
        assert isinstance(filings_10k, list)
        print(f"\n=== AAPL 10-K 文件 === {len(filings_10k)} 份")
        if len(filings_10k) > 0:
            filings_10k_df = BaseLoader.to_dataframe(filings_10k)
            assert "form_type" in filings_10k_df.columns
            print(filings_10k_df.select(["filing_date", "form_type", "link"]).head(3).__str__())

        # 2. 按股票代码查询 10-Q 文件
        filings_10q = await hub.filings.get_filings(symbol="AAPL", form_type="10-Q", limit=5)
        assert isinstance(filings_10q, list)
        print(f"\n=== AAPL 10-Q 文件 === {len(filings_10q)} 份")
        if len(filings_10q) > 0:
            filings_10q_df = BaseLoader.to_dataframe(filings_10q)
            print(filings_10q_df.select(["filing_date", "form_type"]).head(3).__str__())

        # 3. SEC 公司信息
        sec_profile = await hub.filings.get_sec_profile("AAPL")
        assert sec_profile.symbol == "AAPL"
        assert sec_profile.cik is not None
        print(f"\n=== AAPL SEC 公司信息 ===")
        print(f"CIK: {sec_profile.cik}  注册名: {sec_profile.registrant_name}")
        print(f"SIC: {sec_profile.sic_code}  行业: {sec_profile.sic_description}")


# ── 技术指标数据 ──────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nvda_technical_indicators():
    """获取 NVDA 技术指标数据"""
    start = datetime.date(2025, 1, 1)
    end = datetime.date(2025, 12, 31)

    async with FMPDataHub() as hub:
        # 1. 简单移动平均线（SMA 20）
        sma_rows = await hub.indicators.get_indicator(
            "NVDA", IndicatorType.SMA, period=20, start=start, end=end
        )
        assert isinstance(sma_rows, list)
        assert len(sma_rows) > 0, "应获取到 SMA 数据"
        sma_df = BaseLoader.to_dataframe(sma_rows)
        assert "value" in sma_df.columns
        print(f"\n=== NVDA SMA(20)（2025）=== {len(sma_rows)} 行")
        print(sma_df.head(3).__str__())

        # 2. 相对强弱指数（RSI 14）
        rsi_rows = await hub.indicators.get_indicator(
            "NVDA", IndicatorType.RSI, period=14, start=start, end=end
        )
        assert isinstance(rsi_rows, list)
        if len(rsi_rows) > 0:
            rsi_df = BaseLoader.to_dataframe(rsi_rows)
            assert "value" in rsi_df.columns
            print(f"\n=== NVDA RSI(14)（2025）=== {len(rsi_rows)} 行")
            print(rsi_df.head(3).__str__())

        # 3. 指数移动平均线（EMA 50）
        ema_rows = await hub.indicators.get_indicator(
            "NVDA", IndicatorType.EMA, period=50, start=start, end=end
        )
        assert isinstance(ema_rows, list)
        if len(ema_rows) > 0:
            ema_df = BaseLoader.to_dataframe(ema_rows)
            assert "value" in ema_df.columns
        print(f"\n=== NVDA EMA(50)（2025）=== {len(ema_rows)} 行")

        # 4. 小时级别 RSI（验证 interval 参数）
        rsi_1h = await hub.indicators.get_indicator(
            "NVDA", IndicatorType.RSI, period=14,
            interval=Interval.ONE_HOUR,
            start=datetime.date(2026, 5, 1),
            end=datetime.date(2026, 5, 31),
        )
        assert isinstance(rsi_1h, list)
        print(f"\n=== NVDA RSI(14) 1h（2026-05）=== {len(rsi_1h)} 行")


# ── 内部人交易数据 ────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insider_trades():
    """获取内部人交易数据"""
    async with FMPDataHub() as hub:
        # 1. 全市场最新内部人交易
        latest_trades = await hub.insider.get_insider_trades(limit=20)
        assert isinstance(latest_trades, list)
        # FMP Start 稳定 API 暂不提供内部人交易端点，可能返回空列表
        print(f"\n=== 全市场最新内部人交易 === {len(latest_trades)} 条（FMP Start 计划可能不支持）")
        if len(latest_trades) > 0:
            latest_df = BaseLoader.to_dataframe(latest_trades)
            assert "reporting_name" in latest_df.columns
            print(latest_df.select(["symbol", "reporting_name", "transaction_type", "securities_transacted"]).head(5).__str__())

        # 2. 按股票代码查询（AAPL 内部人交易）
        aapl_trades = await hub.insider.get_insider_trades(symbol="AAPL", limit=10)
        assert isinstance(aapl_trades, list)
        print(f"\n=== AAPL 内部人交易 === {len(aapl_trades)} 条")
        if len(aapl_trades) > 0:
            aapl_df = BaseLoader.to_dataframe(aapl_trades)
            print(aapl_df.select(["reporting_name", "securities_transacted", "price"]).head(5).__str__())

        # 3. 内部人交易季度统计（NVDA）
        nvda_stats = await hub.insider.get_insider_statistics("NVDA")
        assert isinstance(nvda_stats, list)
        print(f"\n=== NVDA 内部人交易季度统计 === {len(nvda_stats)} 季")
        if len(nvda_stats) > 0:
            nvda_stats_df = BaseLoader.to_dataframe(nvda_stats)
            assert "acquired_transactions" in nvda_stats_df.columns
            print(nvda_stats_df.select(["year", "quarter", "acquired_transactions", "disposed_transactions"]).head(4).__str__())


# ── 新闻数据 ──────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_news_data():
    """获取各类财经新闻"""
    async with FMPDataHub() as hub:
        # 1. 按股票代码查询新闻（AAPL + MSFT）
        stock_news = await hub.news.get_news(symbols=["AAPL", "MSFT"], limit=10)
        assert isinstance(stock_news, list)
        print(f"\n=== AAPL/MSFT 新闻 === {len(stock_news)} 条")
        if len(stock_news) > 0:
            stock_news_df = BaseLoader.to_dataframe(stock_news)
            assert "title" in stock_news_df.columns
            print(stock_news_df.select(["published_date", "site", "title"]).head(3).__str__())

        # 2. 通用财经新闻
        general_news = await hub.news.get_news(limit=10)
        assert isinstance(general_news, list)
        print(f"\n=== 通用财经新闻 === {len(general_news)} 条")
        if len(general_news) > 0:
            general_news_df = BaseLoader.to_dataframe(general_news)
            print(general_news_df.select(["published_date", "site", "title"]).head(3).__str__())

        # 3. 加密货币新闻
        crypto_news = await hub.news.get_news(asset_class=AssetClass.CRYPTO, limit=10)
        assert isinstance(crypto_news, list)
        print(f"\n=== 加密货币新闻 === {len(crypto_news)} 条")
        if len(crypto_news) > 0:
            crypto_news_df = BaseLoader.to_dataframe(crypto_news)
            print(crypto_news_df.select(["published_date", "title"]).head(3).__str__())

        # 4. 外汇新闻
        forex_news = await hub.news.get_news(asset_class=AssetClass.FOREX, limit=5)
        assert isinstance(forex_news, list)
        print(f"\n=== 外汇新闻 === {len(forex_news)} 条")


# ── 市场表现数据 ──────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_performance_data():
    """获取市场表现数据（涨跌榜 + 板块表现）"""
    async with FMPDataHub() as hub:
        # 1. 涨幅榜（前 10）
        gainers = await hub.performance.get_movers(MoverDirection.GAINERS, limit=10)
        assert isinstance(gainers, list)
        print(f"\n=== 涨幅榜 === {len(gainers)} 只")
        if len(gainers) > 0:
            gainers_df = BaseLoader.to_dataframe(gainers)
            assert "symbol" in gainers_df.columns
            print(gainers_df.select(["symbol", "name", "price", "changes_percentage"]).head(5).__str__())

        # 2. 跌幅榜（前 10）
        losers = await hub.performance.get_movers(MoverDirection.LOSERS, limit=10)
        assert isinstance(losers, list)
        print(f"\n=== 跌幅榜 === {len(losers)} 只")
        if len(losers) > 0:
            losers_df = BaseLoader.to_dataframe(losers)
            print(losers_df.select(["symbol", "name", "changes_percentage"]).head(5).__str__())

        # 3. 成交量榜（前 10）
        actives = await hub.performance.get_movers(MoverDirection.ACTIVE, limit=10)
        assert isinstance(actives, list)
        print(f"\n=== 成交量榜 === {len(actives)} 只")
        if len(actives) > 0:
            actives_df = BaseLoader.to_dataframe(actives)
            print(actives_df.select(["symbol", "name", "volume"]).head(5).__str__())

        # 4. 板块表现（今日）
        sector_perfs = await hub.performance.get_sector_performance()
        assert isinstance(sector_perfs, list)
        print(f"\n=== 板块表现（今日）=== {len(sector_perfs)} 个板块")
        if len(sector_perfs) > 0:
            sector_perf_df = BaseLoader.to_dataframe(sector_perfs)
            assert "sector" in sector_perf_df.columns
            print(sector_perf_df.__str__())

        # 5. 板块市盈率（今日）
        sector_pes = await hub.performance.get_sector_pe()
        assert isinstance(sector_pes, list)
        print(f"\n=== 板块市盈率（今日）=== {len(sector_pes)} 个板块")
        if len(sector_pes) > 0:
            sector_pe_df = BaseLoader.to_dataframe(sector_pes)
            assert "pe" in sector_pe_df.columns
            print(sector_pe_df.__str__())
