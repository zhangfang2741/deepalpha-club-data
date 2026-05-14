"""Configuration management for DeepAlpha"""
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    """Source plugin configuration"""

    api_key: str = ""
    rate_limit: float = 0.5
    poll_interval: int = 60


class KafkaTopics(BaseModel):
    """Kafka topic names"""

    news: str = "raw.news"
    stocktwits: str = "raw.stocktwits"
    sec_filings: str = "raw.sec_filings"
    macro_events: str = "raw.macro_events"
    processed_sentiment: str = "processed.sentiment"
    dlq_failed: str = "dlq.failed"


class KafkaConfig(BaseModel):
    """Kafka configuration"""

    bootstrap_servers: str = "localhost:9092"
    topics: KafkaTopics = Field(default_factory=KafkaTopics)


class StorageConfig(BaseModel):
    """Storage configuration"""

    parquet_path: str = "warehouse/"
    es_hosts: list[str] = Field(default_factory=lambda: ["localhost:9200"])


class DataAPIConfig(BaseModel):
    """Data API configuration"""

    host: str = "0.0.0.0"
    port: int = 8000
    token: str = ""


class AlertRule(BaseModel):
    """Alert rule configuration"""

    name: str
    condition: str
    severity: str = "warning"
    channel: str = "slack"


class AlertsConfig(BaseModel):
    """Alerts configuration"""

    channels: dict[str, str] = Field(default_factory=dict)
    rules: list[AlertRule] = Field(default_factory=list)


class AppConfig(BaseModel):
    """Main application configuration"""

    sources: dict[str, SourceConfig] = Field(default_factory=dict)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    data_api: DataAPIConfig = Field(default_factory=DataAPIConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)


def load_config(config_path: str | Path = "config.yaml") -> AppConfig:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml

    Returns:
        AppConfig: Parsed configuration

    Raises:
        FileNotFoundError: If config file not found
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    return AppConfig.model_validate(raw)