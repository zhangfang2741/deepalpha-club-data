from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import CongressChamber
from deepalpha.models.congress import CongressTrade


class AbstractCongressTradeLoader(BaseLoader):
    @abstractmethod
    async def get_congress_trades(
        self,
        symbol: str | None = None,
        chamber: CongressChamber = CongressChamber.SENATE,
        limit: int = 50,
        page: int = 0,
    ) -> list[CongressTrade]: ...
