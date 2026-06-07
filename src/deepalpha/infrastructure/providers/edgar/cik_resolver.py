"""SEC EDGAR Ticker→CIK 映射（无需 API Key）"""
import logging
import httpx

logger = logging.getLogger(__name__)
_URL = "https://www.sec.gov/files/company_tickers.json"
_HEADERS = {"User-Agent": "DeepAlpha contact@deepalpha.club"}


class CikResolver:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._cache: dict[str, str] | None = None

    async def _load(self) -> None:
        if self._cache is not None:
            return
        resp = await self._client.get(_URL, headers=_HEADERS)
        resp.raise_for_status()
        self._cache = {
            v["ticker"].upper(): str(v["cik_str"]).zfill(10)
            for v in resp.json().values()
        }

    async def resolve(self, ticker: str) -> str | None:
        """返回零填充10位 CIK 字符串，ticker 不存在则返回 None。"""
        await self._load()
        assert self._cache is not None
        return self._cache.get(ticker.upper())
