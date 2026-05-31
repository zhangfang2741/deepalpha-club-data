from typing import Protocol, runtime_checkable

from deepalpha.loaders.analyst_loader import AbstractAnalystLoader
from deepalpha.loaders.calendar_loader import AbstractCalendarLoader
from deepalpha.loaders.company_loader import AbstractCompanyLoader
from deepalpha.loaders.financial_loader import AbstractFinancialLoader
from deepalpha.loaders.market_loader import AbstractMarketLoader
from deepalpha.loaders.news_loader import AbstractNewsLoader


@runtime_checkable
class AbstractDataHub(Protocol):
    """所有 provider DataHub 必须满足的 Core loader 协议（6 个必需属性）。

    Core loader 是跨 provider 通用能力，任何主流金融数据源均可覆盖。
    Extended loader（indicators/economics/insider/filings/performance/congress/directory）
    按 provider 实际支持情况选择性实现，通过 hasattr(hub, "indicators") 判断是否可用。

    用法::

        async with FMPDataHub() as hub:
            assert isinstance(hub, AbstractDataHub)   # Protocol 运行时检查
            quote = await hub.market.get_quote("AAPL")
    """

    # ── Core loaders（所有 provider 必须实现）──────────────────────
    market: AbstractMarketLoader       # 行情数据（报价/历史价格/全市场快照）
    financial: AbstractFinancialLoader # 财务报表（利润表/资产负债表/现金流/估值）
    company: AbstractCompanyLoader     # 公司信息（概况/高管/同业/市值）
    analyst: AbstractAnalystLoader     # 分析师研究（评级/目标价/盈利预测）
    calendar: AbstractCalendarLoader   # 市场事件日历（财报/分红/IPO/拆股）
    news: AbstractNewsLoader           # 财经新闻（按标的/资产类别/全市场）

    async def __aenter__(self) -> "AbstractDataHub":
        """进入异步上下文，返回自身以支持 async with 用法。"""
        ...

    async def __aexit__(self, *_: object) -> None:
        """退出异步上下文，释放 HTTP 连接等资源。"""
        ...
