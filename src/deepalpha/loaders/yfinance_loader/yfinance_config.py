# src/deepalpha/loaders/yfinance_loader/yfinance_config.py
"""Configuration for the YFinance data loader."""
from typing import Optional


class YFinanceConfig:
    """Configuration for YFinanceLoader.

    Attributes:
        rate_limit: Seconds to sleep between per-symbol requests (default 0.5)
        retries: Auto-retry count with exponential backoff (default 3)
        proxy: HTTP proxy URL, e.g. "http://proxy:8080" (default None)
        timeout: Request timeout in seconds (default 30)
        tz_cache_path: Path for yfinance timezone cache (default /tmp/yf_tz_cache)
        repair: Enable yfinance price repair (default True)
    """

    def __init__(
        self,
        rate_limit: float = 0.5,
        retries: int = 3,
        proxy: Optional[str] = None,
        timeout: int = 30,
        tz_cache_path: str = "/tmp/yf_tz_cache",
        repair: bool = True,
    ):
        self.rate_limit = rate_limit
        self.retries = retries
        self.proxy = proxy
        self.timeout = timeout
        self.tz_cache_path = tz_cache_path
        self.repair = repair
