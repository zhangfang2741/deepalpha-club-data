from typing import Any

from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders import (
    FMPAnalystLoader,
    FMPCalendarLoader,
    FMPCompanyLoader,
    FMPCongressTradeLoader,
    FMPDirectoryLoader,
    FMPEconomicsLoader,
    FMPFinancialLoader,
    FMPInsiderTradeLoader,
    FMPMarketLoader,
    FMPMarketPerformanceLoader,
    FMPNewsLoader,
    FMPSecFilingLoader,
    FMPTechnicalIndicatorLoader,
)


class FMPDataHub:
    """FMP 数据中枢，实现 AbstractDataHub Protocol（Core）并提供全部 Extended loader。

    使用 async with 上下文管理器确保 HTTP 连接正确关闭：

        async with FMPDataHub() as hub:
            quote = await hub.market.get_quote("AAPL")
    """

    def __init__(self, config: FMPConfig | None = None) -> None:
        cfg = config or FMPConfig()  # type: ignore[call-arg]
        self._client = FMPAsyncClient(cfg)
        self.market      = FMPMarketLoader(self._client)
        self.financial   = FMPFinancialLoader(self._client)
        self.company     = FMPCompanyLoader(self._client)
        self.analyst     = FMPAnalystLoader(self._client)
        self.calendar    = FMPCalendarLoader(self._client)
        self.news        = FMPNewsLoader(self._client)
        self.indicators  = FMPTechnicalIndicatorLoader(self._client)
        self.economics   = FMPEconomicsLoader(self._client)
        self.insider     = FMPInsiderTradeLoader(self._client)
        self.filings     = FMPSecFilingLoader(self._client)
        self.performance = FMPMarketPerformanceLoader(self._client)
        self.congress    = FMPCongressTradeLoader(self._client)
        self.directory   = FMPDirectoryLoader(self._client)

    async def __aenter__(self) -> "FMPDataHub":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._client.aclose()


__all__ = ["FMPDataHub"]
