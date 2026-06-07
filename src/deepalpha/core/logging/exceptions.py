"""Infrastructure 层统一异常，所有 provider/cache/db 异常均包装为此类型。"""


class DeepAlphaInfraError(Exception):
    """Infrastructure 层统一异常基类。

    所有原始异常（FMPError、httpx.HTTPError、asyncpg 等）均被 @log_call
    捕获后包装为此类型抛出，application 层只需捕获 DeepAlphaInfraError。

    Attributes:
        provider: 来源标识，如 "fmp"、"finnhub"、"cache"、"db"
        method: 方法名，如 "get_income_statement"
        original: 原始异常实例
    """

    def __init__(self, provider: str, method: str, original: Exception) -> None:
        self.provider = provider
        self.method = method
        self.original = original
        super().__init__(
            f"[{provider}.{method}] {type(original).__name__}: {original}"
        )
