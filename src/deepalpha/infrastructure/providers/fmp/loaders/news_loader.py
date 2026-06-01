"""FMP 新闻数据加载器实现"""

import datetime
from typing import Any

from deepalpha.domain.market.enums import AssetClass
from deepalpha.infrastructure.providers.base import BaseLoader
from deepalpha.models.news import NewsArticle

_ASSET_CLASS_PATHS: dict[AssetClass, str] = {
    AssetClass.CRYPTO: "news/crypto",
    AssetClass.FOREX:  "news/forex",
}


class FMPNewsLoader(BaseLoader):
    """FMP 新闻数据加载器。

    实现 AbstractNewsLoader 接口，通过 FMP stable API 获取新闻数据。
    股票新闻使用 /stable/news/stock?symbol=X，参数名从 tickers 改为 symbol。
    """

    async def get_news(
        self,
        symbols: list[str] | None = None,
        asset_class: AssetClass | None = None,
        limit: int = 20,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[NewsArticle]:
        """获取新闻数据。

        根据不同的查询条件调用相应的 API 端点：
        - 如果提供 symbols，查询指定股票的新闻（/stable/news/stock）
        - 如果提供 asset_class（CRYPTO、FOREX），查询特定资产类别的新闻
        - 否则查询通用新闻（/stable/fmp-articles）

        Args:
            symbols: 股票代码列表（可选）
            asset_class: 资产类别（可选）
            limit: 返回记录数，默认 20
            start: 开始日期（可选）
            end: 结束日期（可选）

        Returns:
            NewsArticle 领域对象列表
        """
        params: dict[str, Any] = {"limit": limit}
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)

        if symbols:
            params["symbol"] = ",".join(symbols)
            path = "/stable/news/stock"
        elif asset_class and asset_class in _ASSET_CLASS_PATHS:
            path = f"/stable/{_ASSET_CLASS_PATHS[asset_class]}"
        else:
            path = "/stable/fmp-articles"

        records = await self._get_list(path, **params)
        if path == "/stable/fmp-articles":
            for r in records:
                r.setdefault("url", r.pop("link", ""))
                r.setdefault("publishedDate", r.pop("date", None))
                r.setdefault("text", r.pop("content", None))
        return self._to_models(records, NewsArticle)
