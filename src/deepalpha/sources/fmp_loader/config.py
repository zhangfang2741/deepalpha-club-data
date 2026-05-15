"""FMP data loader configuration"""


class FMPConfig:
    """FMP API configuration

    Attributes:
        api_key: FMP API key
        rate_limit: Seconds between requests (default 0.5)
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