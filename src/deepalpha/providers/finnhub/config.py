from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FinnhubConfig(BaseSettings):
    finnhub_api_key: str = Field(title="API 密钥", description="Finnhub API Key")
    base_url: str = Field("https://finnhub.io", title="API 基础地址")
    timeout: float = Field(30.0, title="超时时间（秒）")
    rate_limit_interval: float = Field(1.1, title="请求最小间隔（秒）", description="免费版 60次/分钟")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
