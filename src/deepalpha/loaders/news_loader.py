import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass
from deepalpha.models.news import NewsArticle


class AbstractNewsLoader(BaseLoader):
    @abstractmethod
    async def get_news(
        self,
        symbols: list[str] | None = None,
        asset_class: AssetClass | None = None,
        limit: int = 20,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[NewsArticle]: ...
