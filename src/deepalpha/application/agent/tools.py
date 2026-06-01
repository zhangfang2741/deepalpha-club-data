"""Agent 工具定义（LangChain @tool）"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.tools import tool as lc_tool

if TYPE_CHECKING:
    from deepalpha.application.services.analyst_service import AnalystService
    from deepalpha.application.services.calendar_service import CalendarService
    from deepalpha.application.services.company_service import CompanyService
    from deepalpha.application.services.concept_service import ConceptService
    from deepalpha.application.services.financial_service import FinancialService
    from deepalpha.application.services.insider_service import InsiderService
    from deepalpha.application.services.market_service import MarketService
    from deepalpha.application.services.news_service import NewsService
    from deepalpha.application.services.performance_service import PerformanceService


class Services:
    def __init__(
        self,
        concept: ConceptService,
        market: MarketService,
        financial: FinancialService,
        analyst: AnalystService,
        company: CompanyService,
        news: NewsService,
        performance: PerformanceService,
        insider: InsiderService,
        calendar: CalendarService,
    ) -> None:
        self.concept = concept
        self.market = market
        self.financial = financial
        self.analyst = analyst
        self.company = company
        self.news = news
        self.performance = performance
        self.insider = insider
        self.calendar = calendar


# ── 格式化辅助函数 ────────────────────────────────────────────────────────────

def _fmt_b(val: float | None) -> str:
    if val is None: return "N/A"
    return f"${val / 1e9:.2f}B" if abs(val) >= 1e9 else f"${val / 1e6:.0f}M"

def _fmt_pct(val: float | None) -> str:
    if val is None: return "N/A"
    return f"{val * 100:.1f}%"

def _fmt_price(val: float | None) -> str:
    if val is None: return "N/A"
    return f"${val:.2f}"


def build_tools(services: Services) -> list:
    """创建注入了 services 依赖的 LangChain 工具列表。"""

    # ── 概念股池 ──────────────────────────────────────────────────────────────
    @lc_tool
    async def search_concept(concept: str) -> str:
        """查询美股概念股池，返回该概念下成分股列表（含ETF覆盖数和权重）。concept: 概念名称"""
        stocks = await services.concept.get_concept(concept)
        if not stocks:
            return f"概念 '{concept}' 不存在或暂无数据"
        lines = [f"{s.symbol}: ETF覆盖={s.etf_count}, 权重={s.total_weight:.1f}%" for s in stocks[:20]]
        return f"概念 '{concept}' 共 {len(stocks)} 只成分股（显示前20）：\n" + "\n".join(lines)

    @lc_tool
    async def list_concepts() -> str:  # type: ignore[empty-body]
        """列出所有可用的美股概念板块分类及成分股数量。"""
        summaries = await services.concept.list_summaries()
        return "\n".join(f"{s.concept_name_zh or s.concept}（{s.stock_count}只）" for s in summaries)

    # ── 行情 ──────────────────────────────────────────────────────────────────
    @lc_tool
    async def get_quote(symbol: str) -> str:
        """获取美股股票实时报价、涨跌幅、市值。symbol: 股票代码，如 'AAPL'"""
        q = await services.market.get_quote(symbol)
        pct = f"{q.changes_percentage:.2f}%" if q.changes_percentage is not None else "N/A"
        cap = _fmt_b(q.market_cap)
        return f"{q.symbol} {q.name}: 现价={_fmt_price(q.price)}, 涨跌幅={pct}, 市值={cap}"

    # ── 财务报表 ──────────────────────────────────────────────────────────────
    @lc_tool
    async def get_income_statement(symbol: str) -> str:
        """获取公司最新年度利润表（营收、净利润、EPS、EBITDA）。symbol: 股票代码"""
        stmt = await services.financial.get_latest_income(symbol)
        if stmt is None:
            return f"{symbol} 暂无财务数据"
        return (
            f"{symbol} 利润表（{stmt.date} {stmt.period}）：\n"
            f"营收={_fmt_b(stmt.revenue)}, 毛利={_fmt_b(stmt.gross_profit)}, "
            f"营业利润={_fmt_b(stmt.operating_income)}, 净利润={_fmt_b(stmt.net_income)}, "
            f"EBITDA={_fmt_b(stmt.ebitda)}, EPS={stmt.eps}, 稀释EPS={stmt.eps_diluted}"
        )

    @lc_tool
    async def get_balance_sheet(symbol: str) -> str:
        """获取公司最新资产负债表（总资产、负债、净资产、现金、债务）。symbol: 股票代码"""
        bs = await services.financial.get_balance_sheet(symbol)
        if bs is None:
            return f"{symbol} 暂无资产负债表数据"
        return (
            f"{symbol} 资产负债表（{bs.date} {bs.period}）：\n"
            f"总资产={_fmt_b(bs.total_assets)}, 总负债={_fmt_b(bs.total_liabilities)}, "
            f"净资产={_fmt_b(bs.total_stockholders_equity)}, "
            f"现金={_fmt_b(bs.cash_and_cash_equivalents)}, "
            f"总债务={_fmt_b(bs.total_debt)}, 净债务={_fmt_b(bs.net_debt)}"
        )

    @lc_tool
    async def get_cash_flow(symbol: str) -> str:
        """获取公司最新现金流量表（经营/投资/自由现金流）。symbol: 股票代码"""
        cf = await services.financial.get_cash_flow(symbol)
        if cf is None:
            return f"{symbol} 暂无现金流数据"
        return (
            f"{symbol} 现金流（{cf.date} {cf.period}）：\n"
            f"经营现金流={_fmt_b(cf.operating_cash_flow)}, "
            f"资本支出={_fmt_b(cf.capital_expenditure)}, "
            f"自由现金流={_fmt_b(cf.free_cash_flow)}, "
            f"股息支出={_fmt_b(cf.dividends_paid)}"
        )

    @lc_tool
    async def get_financial_ratios(symbol: str) -> str:
        """获取公司关键财务比率（毛利率、净利率、ROE、ROA、负债率）。symbol: 股票代码"""
        r = await services.financial.get_financial_ratios(symbol)
        if r is None:
            return f"{symbol} 暂无财务比率数据"
        return (
            f"{symbol} 财务比率（{r.date} {r.period}）：\n"
            f"毛利率={_fmt_pct(r.gross_profit_margin)}, "
            f"营业利润率={_fmt_pct(r.operating_profit_margin)}, "
            f"净利润率={_fmt_pct(r.net_profit_margin)}, "
            f"ROE={_fmt_pct(r.return_on_equity)}, ROA={_fmt_pct(r.return_on_assets)}, "
            f"流动比率={r.current_ratio:.2f if r.current_ratio else 'N/A'}, "
            f"负债率={r.debt_equity_ratio:.2f if r.debt_equity_ratio else 'N/A'}"
        )

    @lc_tool
    async def get_key_metrics(symbol: str) -> str:
        """获取公司关键估值指标（市盈率、市净率、EV/EBITDA、FCF收益率）。symbol: 股票代码"""
        m = await services.financial.get_key_metrics(symbol)
        if m is None:
            return f"{symbol} 暂无关键指标数据"
        return (
            f"{symbol} 关键指标（{m.date} {m.period}）：\n"
            f"PE={m.pe_ratio:.1f if m.pe_ratio else 'N/A'}, "
            f"PB={m.price_to_book:.2f if m.price_to_book else 'N/A'}, "
            f"PS={m.price_to_sales:.2f if m.price_to_sales else 'N/A'}, "
            f"EV/EBITDA={m.ev_to_ebitda:.1f if m.ev_to_ebitda else 'N/A'}, "
            f"FCF/股={_fmt_price(m.free_cash_flow_per_share)}, "
            f"盈利收益率={_fmt_pct(m.earnings_yield)}"
        )

    @lc_tool
    async def get_valuation(symbol: str) -> str:
        """获取公司 DCF 内在价值估算与当前股价对比。symbol: 股票代码"""
        v = await services.financial.get_valuation(symbol)
        discount = ((v.stock_price - v.dcf) / v.dcf * 100) if v.dcf and v.stock_price else None
        disc_str = f"（溢价 {discount:.1f}%）" if discount and discount > 0 else f"（折价 {abs(discount):.1f}%）" if discount else ""
        return (
            f"{symbol} DCF估值：内在价值={_fmt_price(v.dcf)}, "
            f"当前股价={_fmt_price(v.stock_price)}{disc_str}"
        )

    # ── 分析师 ────────────────────────────────────────────────────────────────
    @lc_tool
    async def get_analyst_ratings(symbol: str) -> str:
        """获取分析师评级汇总（买入/持有/卖出数量及最新评级）。symbol: 股票代码"""
        ratings = await services.analyst.get_ratings(symbol)
        if not ratings:
            return f"{symbol} 暂无分析师评级"
        latest = ratings[0]
        return (
            f"{symbol} 分析师评级（最新 {latest.date if hasattr(latest, 'date') else ''}）：\n"
            f"综合建议={latest.rating_recommendation}, "
            f"评分={latest.rating_score if hasattr(latest, 'rating_score') else 'N/A'}, "
            f"共 {len(ratings)} 份评级记录"
        )

    @lc_tool
    async def get_price_targets(symbol: str) -> str:
        """获取分析师目标价汇总（最新、平均、最高、最低目标价）。symbol: 股票代码"""
        targets = await services.analyst.get_price_targets(symbol)
        if not targets:
            return f"{symbol} 暂无价格目标数据"
        prices = [t.price_target for t in targets if t.price_target is not None]
        if not prices:
            return f"{symbol} 价格目标数据不完整"
        latest = targets[0]
        return (
            f"{symbol} 分析师目标价（共 {len(targets)} 份）：\n"
            f"最新={_fmt_price(latest.price_target)}（{latest.analyst_company}，{latest.published_date}）, "
            f"均值={_fmt_price(sum(prices)/len(prices))}, "
            f"最高={_fmt_price(max(prices))}, 最低={_fmt_price(min(prices))}"
        )

    # ── 公司信息 ──────────────────────────────────────────────────────────────
    @lc_tool
    async def get_company_profile(symbol: str) -> str:
        """获取公司基本信息（行业、市值、员工数、CEO、业务描述）。symbol: 股票代码"""
        p = await services.company.get_profile(symbol)
        desc = (p.description[:200] + "…") if p.description and len(p.description) > 200 else p.description
        return (
            f"{p.symbol} {p.company_name}：\n"
            f"板块={p.sector}, 行业={p.industry}, 交易所={p.exchange}, "
            f"国家={p.country}, CEO={p.ceo}, 员工={p.full_time_employees}, "
            f"上市日={p.ipo_date}\n描述：{desc}"
        )

    @lc_tool
    async def get_peers(symbol: str) -> str:
        """获取股票的同行竞争对手列表。symbol: 股票代码"""
        peers = await services.company.get_peers(symbol)
        if not peers:
            return f"{symbol} 暂无竞争对手数据"
        return f"{symbol} 同行对标：{', '.join(peers)}"

    # ── 新闻 ──────────────────────────────────────────────────────────────────
    @lc_tool
    async def get_news(symbol: str) -> str:
        """获取股票最新新闻资讯（标题、来源、情绪倾向）。symbol: 股票代码"""
        articles = await services.news.get_news(symbol=symbol, limit=8)
        if not articles:
            return f"{symbol} 暂无新闻"
        lines = [
            f"[{a.published_date.strftime('%m-%d') if a.published_date else '?'}] "
            f"{a.title} ({a.site or '?'}, {a.sentiment or '?'})"
            for a in articles
        ]
        return f"{symbol} 最新新闻：\n" + "\n".join(lines)

    # ── 内幕/国会交易 ─────────────────────────────────────────────────────────
    @lc_tool
    async def get_insider_trades(symbol: str) -> str:
        """获取公司内部人员（高管/董事）最近买卖记录。symbol: 股票代码"""
        trades = await services.insider.get_insider_trades(symbol, limit=10)
        if not trades:
            return f"{symbol} 暂无内幕交易数据"
        lines = [
            f"{t.transaction_date} {t.reporting_name}（{t.type_of_owner}）: "
            f"{'买入' if t.acquisition_or_disposition == 'A' else '卖出'} "
            f"{t.securities_transacted:,.0f}股 @ {_fmt_price(t.price)}"
            for t in trades if t.securities_transacted
        ]
        return f"{symbol} 内幕交易（最近10笔）：\n" + "\n".join(lines)

    # ── 市场表现 ──────────────────────────────────────────────────────────────
    @lc_tool
    async def get_market_gainers() -> str:  # type: ignore[empty-body]
        """获取今日美股涨幅榜前10只股票。"""
        movers = await services.performance.get_gainers(limit=10)
        if not movers:
            return "暂无涨幅榜数据"
        lines = [
            f"{m.symbol} {m.name or ''}: {_fmt_price(m.price)} "
            f"(+{m.changes_percentage:.2f}%)" if m.changes_percentage else f"{m.symbol}"
            for m in movers
        ]
        return "今日涨幅榜：\n" + "\n".join(lines)

    @lc_tool
    async def get_market_losers() -> str:  # type: ignore[empty-body]
        """获取今日美股跌幅榜前10只股票。"""
        movers = await services.performance.get_losers(limit=10)
        if not movers:
            return "暂无跌幅榜数据"
        lines = [
            f"{m.symbol} {m.name or ''}: {_fmt_price(m.price)} "
            f"({m.changes_percentage:.2f}%)" if m.changes_percentage else f"{m.symbol}"
            for m in movers
        ]
        return "今日跌幅榜：\n" + "\n".join(lines)

    @lc_tool
    async def get_sector_performance() -> str:  # type: ignore[empty-body]
        """获取美股各板块今日涨跌幅排行。"""
        sectors = await services.performance.get_sector_performance()
        if not sectors:
            return "暂无板块表现数据"
        lines = [f"{s.sector}: {s.changes_percentage}" for s in sectors]
        return "板块表现：\n" + "\n".join(lines)

    # ── 日历事件 ──────────────────────────────────────────────────────────────
    @lc_tool
    async def get_upcoming_earnings() -> str:  # type: ignore[empty-body]
        """获取未来7天即将发布财报的美股公司列表。"""
        events = await services.calendar.get_upcoming_earnings(days=7)
        if not events:
            return "未来7天暂无财报发布"
        lines = [
            f"{e.date} {e.symbol}: EPS预期={e.eps_estimated}, 时段={e.time or '?'}"
            for e in events[:15]
        ]
        return "即将发布财报（7天内）：\n" + "\n".join(lines)

    # ── 投研报告 ──────────────────────────────────────────────────────────────
    @lc_tool
    async def generate_report(symbol: str) -> str:
        """生成指定股票的综合投研报告（行情+财务+分析师+新闻）。symbol: 股票代码"""
        import asyncio
        q, stmt, ratings, profile = await asyncio.gather(
            services.market.get_quote(symbol),
            services.financial.get_latest_income(symbol),
            services.analyst.get_ratings(symbol),
            services.company.get_profile(symbol),
        )
        rating_str = ratings[0].rating_recommendation if ratings else "N/A"
        pct = f"{q.changes_percentage:.2f}%" if q.changes_percentage is not None else "N/A"
        return (
            f"# {symbol} 投研报告\n\n"
            f"**公司**: {profile.company_name}｜{profile.sector}·{profile.industry}\n"
            f"**行情**: 现价={_fmt_price(q.price)}, 涨跌幅={pct}, 市值={_fmt_b(q.market_cap)}\n"
            f"**财务**: 营收={_fmt_b(stmt.revenue if stmt else None)}, "
            f"净利润={_fmt_b(stmt.net_income if stmt else None)}, "
            f"EPS={stmt.eps if stmt else 'N/A'}\n"
            f"**分析师**: {rating_str}"
        )

    return [
        search_concept, list_concepts,
        get_quote,
        get_income_statement, get_balance_sheet, get_cash_flow,
        get_financial_ratios, get_key_metrics, get_valuation,
        get_analyst_ratings, get_price_targets,
        get_company_profile, get_peers,
        get_news,
        get_insider_trades,
        get_market_gainers, get_market_losers, get_sector_performance,
        get_upcoming_earnings,
        generate_report,
    ]


async def dispatch_tool(name: str, inputs: dict[str, Any], services: Services) -> str:
    """向后兼容：供单元测试直接调用工具逻辑。"""
    tools = {t.name: t for t in build_tools(services)}
    if name in tools:
        return await tools[name].ainvoke(inputs)
    return f"未知工具: {name}"
