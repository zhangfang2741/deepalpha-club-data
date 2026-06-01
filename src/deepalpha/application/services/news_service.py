"""新闻业务逻辑服务"""
from typing import Protocol

from deepalpha.domain.news.models import NewsArticle


class INewsProvider(Protocol):
    async def get_news(
        self,
        symbols: list[str] | None = None,
        limit: int = 10,
    ) -> list[NewsArticle]: ...


class NewsService:
    def __init__(self, provider: INewsProvider) -> None:
        self._provider = provider

    async def get_news(self, symbol: str | None = None, limit: int = 10) -> list[NewsArticle]:
        symbols = [symbol.upper()] if symbol else None
        return await self._provider.get_news(symbols=symbols, limit=limit)
