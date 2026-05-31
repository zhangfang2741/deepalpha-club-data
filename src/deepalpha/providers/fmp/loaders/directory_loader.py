import polars as pl
from deepalpha.loaders.directory_loader import AbstractDirectoryLoader
from deepalpha.loaders.enums import AssetClass
from deepalpha.models.directory import SymbolInfo, ExchangeInfo


_SYMBOL_PATHS: dict[AssetClass, str] = {
    AssetClass.STOCK:       "actively-trading-list",
    AssetClass.ETF:         "ETFs-list",
    AssetClass.INDEX:       "company-symbols-list",
    AssetClass.CRYPTO:      "company-symbols-list",
    AssetClass.FOREX:       "company-symbols-list",
    AssetClass.COMMODITY:   "company-symbols-list",
    AssetClass.MUTUAL_FUND: "company-symbols-list",
}


class FMPDirectoryLoader(AbstractDirectoryLoader):
    """FMP 目录数据加载器。"""

    async def get_symbols(self, asset_class: AssetClass = AssetClass.STOCK) -> pl.DataFrame:
        """获取证券代码列表。

        Args:
            asset_class: 资产类别（默认为股票）

        Returns:
            证券代码信息 DataFrame
        """
        path = _SYMBOL_PATHS.get(asset_class, "company-symbols-list")
        records = await self._get_list(f"/stable/{path}")
        return self._to_df(records, SymbolInfo)

    async def get_exchanges(self) -> pl.DataFrame:
        """获取交易所列表。

        Returns:
            交易所信息 DataFrame
        """
        records = await self._get_list("/stable/available-exchanges")
        return self._to_df(records, ExchangeInfo)

    async def get_sectors(self) -> list[str]:
        """获取行业部门列表。

        Returns:
            行业部门名称列表
        """
        records = await self._get_list("/stable/available-sectors")
        return [r.get("sector", "") for r in records if r.get("sector")]

    async def get_industries(self) -> list[str]:
        """获取产业列表。

        Returns:
            产业名称列表
        """
        records = await self._get_list("/stable/available-industries")
        return [r.get("industry", "") for r in records if r.get("industry")]
