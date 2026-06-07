"""
基础设施层全局配置

从环境变量（或 .env 文件）中读取所有外部服务的连接参数。
"""

from urllib.parse import quote

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConceptPipelineConfig(BaseSettings):
    """概念股池 pipeline 全局配置，从环境变量读取。"""

    postgres_host: str = Field(title="PostgreSQL 主机")
    postgres_port: int = Field(5432, title="PostgreSQL 端口")
    postgres_db: str = Field(title="数据库名")
    postgres_user: str = Field(title="数据库用户名")
    postgres_password: str = Field(title="数据库密码")
    postgres_ssl: bool = Field(False, title="是否启用 SSL")

    valkey_host: str = Field(title="Valkey 主机")
    valkey_port: int = Field(6379, title="Valkey 端口")
    valkey_password: str = Field("", title="Valkey 密码")
    valkey_ssl: bool = Field(False, title="是否启用 Valkey SSL")

    finnhub_api_key: str = Field(title="Finnhub API Key")
    minimax_api_key: str = Field("", title="MiniMax API Key")

    concept_cache_ttl: int = Field(172800, title="缓存 TTL（秒）", description="默认 2 天")
    concept_aum_threshold_million: float = Field(100.0, title="AUM 过滤阈值（百万美元）")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def asyncpg_dsn(self) -> str:
        ssl_param = "?sslmode=require" if self.postgres_ssl else ""
        user = quote(self.postgres_user, safe="")
        password = quote(self.postgres_password, safe="")
        return (
            f"postgresql://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}{ssl_param}"
        )


class CreatorNewsPipelineConfig(BaseSettings):
    """YouTube 创作者新闻流 pipeline 全局配置，从环境变量读取。"""

    postgres_host: str = Field(title="PostgreSQL 主机")
    postgres_port: int = Field(5432, title="PostgreSQL 端口")
    postgres_db: str = Field(title="数据库名")
    postgres_user: str = Field(title="数据库用户名")
    postgres_password: str = Field(title="数据库密码")
    postgres_ssl: bool = Field(False, title="是否启用 SSL")

    telegram_bot_token: str = Field(title="Telegram Bot Token")
    telegram_channel_id: str = Field("", title="Telegram 频道 ID（空=干运行）")

    minimax_api_key: str = Field("", title="MiniMax API Key（用于中文摘要）")

    youtube_channels_yaml: str = Field(
        "config/youtube_channels.yaml", title="YouTube 频道配置文件路径"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def asyncpg_dsn(self) -> str:
        ssl_param = "?sslmode=require" if self.postgres_ssl else ""
        user = quote(self.postgres_user, safe="")
        password = quote(self.postgres_password, safe="")
        return (
            f"postgresql://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}{ssl_param}"
        )
