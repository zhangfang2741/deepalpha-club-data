import datetime
import polars as pl
from deepalpha.loaders.filings import AbstractSecFilingLoader
from deepalpha.models.filings import SecFiling, SecCompanyProfile


class FMPSecFilingLoader(AbstractSecFilingLoader):
    """FMP SEC 文件加载器。"""

    async def get_filings(
        self,
        symbol: str | None = None,
        form_type: str | None = None,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        limit: int = 20,
    ) -> pl.DataFrame:
        """获取 SEC 文件记录。

        Args:
            symbol: 股票代码（可选）
            form_type: 文件类型，如 10-K / 10-Q（可选）
            start: 开始日期（可选）
            end: 结束日期（可选）
            limit: 分页大小，默认 20

        Returns:
            SEC 文件记录 DataFrame
        """
        params: dict[str, str | int] = {"limit": limit}
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)
        if symbol:
            params["symbol"] = symbol
            if form_type:
                params["type"] = form_type
            records = await self._get_list("/stable/search-by-symbol", **params)
        elif form_type:
            records = await self._get_list(
                "/stable/search-by-form-type", type=form_type, **params
            )
        else:
            records = await self._get_list("/stable/search-by-symbol", **params)
        return self._to_df(records, SecFiling)

    async def get_sec_profile(self, symbol: str) -> SecCompanyProfile:
        """获取 SEC 公司信息。

        Args:
            symbol: 股票代码

        Returns:
            SecCompanyProfile 对象
        """
        data = await self._get(f"/stable/sec-company-full-profile/{symbol}")
        return SecCompanyProfile.model_validate(data)
