"""FMP 公司数据加载器实现"""

import datetime
from typing import Any

from deepalpha.infrastructure.providers.base import BaseLoader
from deepalpha.domain.company.models import CompanyProfile, Executive, MarketCapRecord


class FMPCompanyLoader(BaseLoader):
    """FMP 公司数据加载器。

    实现 AbstractCompanyLoader 接口，通过 FMP stable API 获取公司数据。
    所有端点使用 ?symbol=X 查询参数格式。
    """

    async def get_profile(self, symbol: str) -> CompanyProfile:
        """获取公司信息。

        Args:
            symbol: 股票代码

        Returns:
            CompanyProfile 对象
        """
        data = await self._get("/stable/profile", symbol=symbol)
        return CompanyProfile.model_validate(data)

    async def get_executives(self, symbol: str) -> list[Executive]:
        """获取高管名单。

        Args:
            symbol: 股票代码

        Returns:
            Executive 领域对象列表
        """
        records = await self._get_list("/stable/key-executives", symbol=symbol)
        return self._to_models(records, Executive)

    async def get_peers(self, symbol: str) -> list[str]:
        """获取竞争对手列表。

        /stable/stock-peers?symbol=X 返回包含 symbol 字段的对象列表。

        Args:
            symbol: 股票代码

        Returns:
            竞争对手股票代码列表
        """
        records = await self._get_list("/stable/stock-peers", symbol=symbol)
        return [r.get("symbol", "") for r in records if r.get("symbol")]

    async def get_market_cap(
        self, symbol: str, start: datetime.date | None = None, end: datetime.date | None = None
    ) -> list[MarketCapRecord]:
        """获取市值数据。

        Args:
            symbol: 股票代码
            start: 开始日期（可选），指定时查询历史市值
            end: 结束日期（可选）

        Returns:
            MarketCapRecord 领域对象列表
        """
        if start is None and end is None:
            records = await self._get_list("/stable/market-capitalization", symbol=symbol)
        else:
            params: dict[str, Any] = {"symbol": symbol}
            if start:
                params["from"] = str(start)
            if end:
                params["to"] = str(end)
            records = await self._get_list("/stable/historical-market-capitalization", **params)
        return self._to_models(records, MarketCapRecord)
