# src/deepalpha/loaders/fmp_loader/fmp_config.py
"""FMP API configuration."""


class FMPConfig:
    """Configuration for the FMP data loader.

    Attributes:
        api_key: FMP API key
        rate_limit: Seconds to sleep between requests (default 0.5)
        base_url: FMP API base URL
    """

    def __init__(
        self,
        api_key: str = "",
        rate_limit: float = 0.5,
        base_url: str = "https://site.financialmodelingprep.com/api/v3",
    ):
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.base_url = base_url
