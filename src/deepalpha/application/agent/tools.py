"""Agent 工具定义（LangChain @tool）"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.tools import tool as lc_tool

if TYPE_CHECKING:
    from deepalpha.application.services.analyst_service import AnalystService
    from deepalpha.application.services.concept_service import ConceptService
    from deepalpha.application.services.financial_service import FinancialService
    from deepalpha.application.services.market_service import MarketService


class Services:
    def __init__(
        self,
        concept: ConceptService,
        market: MarketService,
        financial: FinancialService,
        analyst: AnalystService,
    ) -> None:
        self.concept = concept
        self.market = market
        self.financial = financial
        self.analyst = analyst


def build_tools(services: Services) -> list:
    """创建注入了 services 依赖的 LangChain 工具列表。"""

    @lc_tool
    async def search_concept(concept: str) -> str:
        """查询美股概念股池，返回该概念下成分股列表（含ETF覆盖数和权重）。concept: 概念名称，如 'AI / Machine Learning'"""
        stocks = await services.concept.get_concept(concept)
        if not stocks:
            return f"概念 '{concept}' 不存在或暂无数据"
        lines = [
            f"{s.symbol}: ETF覆盖={s.etf_count}, 权重={s.total_weight:.1f}%"
            for s in stocks[:20]
        ]
        return f"概念 '{concept}' 共 {len(stocks)} 只成分股（显示前20）：\n" + "\n".join(lines)

    @lc_tool
    async def get_quote(symbol: str) -> str:
        """获取美股股票实时报价、涨跌幅、市值。symbol: 股票代码，如 'AAPL'"""
        q = await services.market.get_quote(symbol)
        pct = f"{q.changes_percentage:.2f}%" if q.changes_percentage is not None else "N/A"
        cap = f"{q.market_cap / 1e9:.1f}B" if q.market_cap else "N/A"
        return f"{q.symbol}: 价格={q.price}, 涨跌幅={pct}, 市值={cap}"

    @lc_tool
    async def get_financials(symbol: str) -> str:
        """获取公司最新年度财务报表（营收、净利润、EPS）。symbol: 股票代码"""
        stmt = await services.financial.get_latest_income(symbol)
        if stmt is None:
            return f"{symbol} 暂无财务数据"
        rev = f"{stmt.revenue / 1e9:.1f}B" if stmt.revenue else "N/A"
        ni = f"{stmt.net_income / 1e9:.1f}B" if stmt.net_income else "N/A"
        return (
            f"{symbol} ({stmt.date} {stmt.period}): "
            f"营收={rev}, 净利润={ni}, EPS={stmt.eps}"
        )

    @lc_tool
    async def generate_report(symbol: str) -> str:
        """生成指定股票的结构化投研报告，综合行情、财务、分析师评级。symbol: 股票代码"""
        q = await services.market.get_quote(symbol)
        stmt = await services.financial.get_latest_income(symbol)
        ratings = await services.analyst.get_ratings(symbol)
        rating_str = ratings[0].rating_recommendation if ratings else "N/A"
        pct = f"{q.changes_percentage:.2f}%" if q.changes_percentage is not None else "N/A"
        rev = f"{stmt.revenue / 1e9:.1f}B" if stmt and stmt.revenue else "N/A"
        ni = f"{stmt.net_income / 1e9:.1f}B" if stmt and stmt.net_income else "N/A"
        return (
            f"# {symbol} 投研报告\n\n"
            f"**行情**: 现价={q.price}, 涨跌幅={pct}\n"
            f"**财务**: 营收={rev}, 净利润={ni}\n"
            f"**分析师评级**: {rating_str}"
        )

    return [search_concept, get_quote, get_financials, generate_report]


async def dispatch_tool(name: str, inputs: dict[str, Any], services: Services) -> str:
    """向后兼容：供单元测试直接调用工具逻辑。"""
    if name == "search_concept":
        stocks = await services.concept.get_concept(inputs["concept"])
        if not stocks:
            return f"概念 '{inputs['concept']}' 不存在或暂无数据"
        lines = [
            f"{s.symbol}: ETF覆盖={s.etf_count}, 权重={s.total_weight:.1f}%"
            for s in stocks[:20]
        ]
        return (
            f"概念 '{inputs['concept']}' 共 {len(stocks)} 只成分股（显示前20）：\n"
            + "\n".join(lines)
        )

    if name == "get_quote":
        q = await services.market.get_quote(inputs["symbol"])
        pct = f"{q.changes_percentage:.2f}%" if q.changes_percentage is not None else "N/A"
        cap = f"{q.market_cap / 1e9:.1f}B" if q.market_cap else "N/A"
        return f"{q.symbol}: 价格={q.price}, 涨跌幅={pct}, 市值={cap}"

    if name == "get_financials":
        stmt = await services.financial.get_latest_income(inputs["symbol"])
        if stmt is None:
            return f"{inputs['symbol']} 暂无财务数据"
        rev = f"{stmt.revenue / 1e9:.1f}B" if stmt.revenue else "N/A"
        ni = f"{stmt.net_income / 1e9:.1f}B" if stmt.net_income else "N/A"
        return (
            f"{inputs['symbol']} ({stmt.date} {stmt.period}): "
            f"营收={rev}, 净利润={ni}, EPS={stmt.eps}"
        )

    if name == "generate_report":
        symbol = inputs["symbol"]
        q = await services.market.get_quote(symbol)
        stmt = await services.financial.get_latest_income(symbol)
        ratings = await services.analyst.get_ratings(symbol)
        rating_str = ratings[0].rating_recommendation if ratings else "N/A"
        pct = f"{q.changes_percentage:.2f}%" if q.changes_percentage is not None else "N/A"
        rev = f"{stmt.revenue / 1e9:.1f}B" if stmt and stmt.revenue else "N/A"
        ni = f"{stmt.net_income / 1e9:.1f}B" if stmt and stmt.net_income else "N/A"
        return (
            f"# {symbol} 投研报告\n\n"
            f"**行情**: 现价={q.price}, 涨跌幅={pct}\n"
            f"**财务**: 营收={rev}, 净利润={ni}\n"
            f"**分析师评级**: {rating_str}"
        )

    return f"未知工具: {name}"
