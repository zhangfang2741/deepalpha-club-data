from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FMPConfig(BaseSettings):
    api_key: str = Field(title="API 密钥", description="FMP API Key，从环境变量 FMP_API_KEY 读取")
    base_url: str = Field("https://financialmodelingprep.com", title="API 基础地址")
    timeout: float = Field(30.0, title="超时时间（秒）")
    max_connections: int = Field(10, title="最大并发连接数")
    max_retries: int = Field(3, title="最大重试次数", description="5xx 时的指数退避重试次数")

    model_config = SettingsConfigDict(env_prefix="FMP_", env_file=".env")
