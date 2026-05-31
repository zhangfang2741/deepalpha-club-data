import polars as pl

from deepalpha.loaders.congress_loader import AbstractCongressTradeLoader
from deepalpha.loaders.enums import CongressChamber
from deepalpha.models.congress import CongressTrade


class FMPCongressTradeLoader(AbstractCongressTradeLoader):
    """FMP 国会议员交易数据加载器。"""

    async def get_congress_trades(
        self,
        symbol: str | None = None,
        chamber: CongressChamber = CongressChamber.SENATE,
        limit: int = 50,
        page: int = 0,
    ) -> pl.DataFrame:
        """获取国会议员交易数据。

        Args:
            symbol: 股票代码（可选）
            chamber: 国会议院（参议院或众议院，默认为参议院）
            limit: 返回记录数限制（默认为 50）
            page: 分页页码（默认为 0）

        Returns:
            国会议员交易数据 DataFrame
        """
        chamber_prefix = "senate" if chamber == CongressChamber.SENATE else "house-disclosure"
        if symbol:
            path = f"/stable/{chamber_prefix}-trading"
            params: dict[str, str | int] = {"symbol": symbol, "limit": limit, "page": page}
        else:
            path = f"/stable/{chamber_prefix}-latest"
            params = {"limit": limit, "page": page}
        records = await self._get_list(path, **params)
        return self._to_df(records, CongressTrade)
