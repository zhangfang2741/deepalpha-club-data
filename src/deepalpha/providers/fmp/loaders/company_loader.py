import datetime

import polars as pl

from deepalpha.loaders.company_loader import AbstractCompanyLoader
from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord


class FMPCompanyLoader(AbstractCompanyLoader):
    """FMP 公司数据加载器。"""

    async def get_profile(self, symbol: str) -> CompanyProfile:
        """获取公司信息。

        Args:
            symbol: 股票代码

        Returns:
            CompanyProfile 对象
        """
        data = await self._get(f"/stable/profile-symbol/{symbol}")
        return CompanyProfile.model_validate(data)

    async def get_executives(self, symbol: str) -> pl.DataFrame:
        """获取高管名单。

        Args:
            symbol: 股票代码

        Returns:
            高管信息 DataFrame
        """
        records = await self._get_list(f"/stable/company-executives/{symbol}")
        return self._to_df(records, Executive)

    async def get_peers(self, symbol: str) -> list[str]:
        """获取竞争对手列表。

        Args:
            symbol: 股票代码

        Returns:
            竞争对手股票代码列表
        """
        data = await self._get(f"/stable/peers/{symbol}")
        peers: list[str] = data.get("peersList", [])
        return peers

    async def get_market_cap(
        self, symbol: str, start: datetime.date | None = None, end: datetime.date | None = None
    ) -> pl.DataFrame:
        """获取市值数据。

        Args:
            symbol: 股票代码
            start: 开始日期（可选）
            end: 结束日期（可选）

        Returns:
            市值数据 DataFrame
        """
        if start is None and end is None:
            records = await self._get_list(f"/stable/market-cap/{symbol}")
        else:
            params: dict[str, str] = {}
            if start:
                params["from"] = str(start)
            if end:
                params["to"] = str(end)
            records = await self._get_list(f"/stable/historical-market-cap/{symbol}", **params)
        return self._to_df(records, MarketCapRecord)
