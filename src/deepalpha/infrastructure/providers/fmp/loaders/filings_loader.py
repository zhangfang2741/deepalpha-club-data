import datetime

from deepalpha.infrastructure.providers.base import BaseLoader
from deepalpha.domain.governance.models import SecCompanyProfile, SecFiling

_DEFAULT_LOOKBACK_YEARS = 3


class FMPSecFilingLoader(BaseLoader):
    """FMP SEC 文件加载器。"""

    async def get_filings(
        self,
        symbol: str | None = None,
        form_type: str | None = None,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        limit: int = 20,
    ) -> list[SecFiling]:
        """/stable/sec-filings-search/symbol 要求 from 和 to 两个日期参数。
        如未传入则默认最近 3 年。

        Args:
            symbol: 股票代码（可选）
            form_type: 文件类型，如 10-K / 10-Q（可选）
            start: 开始日期（可选）
            end: 结束日期（可选）
            limit: 分页大小，默认 20

        Returns:
            SecFiling 领域对象列表
        """
        today = datetime.date.today()
        from_date = start or (today - datetime.timedelta(days=365 * _DEFAULT_LOOKBACK_YEARS))
        to_date = end or today

        params: dict[str, str | int] = {
            "from": str(from_date),
            "to": str(to_date),
            "limit": limit,
        }
        if symbol:
            params["symbol"] = symbol
        if form_type:
            params["formType"] = form_type

        records = await self._get_list("/stable/sec-filings-search/symbol", **params)
        return self._to_models(records, SecFiling)

    async def get_sec_profile(self, symbol: str) -> SecCompanyProfile:
        """获取 SEC 公司信息。

        Args:
            symbol: 股票代码

        Returns:
            SecCompanyProfile 对象
        """
        data = await self._get("/stable/sec-profile", symbol=symbol)
        return SecCompanyProfile.model_validate(data)
