"""Tests for configuration management"""
import pytest
from pathlib import Path
import tempfile
import yaml
from deepalpha.config import load_config, AppConfig


class TestLoadConfig:
    """Test configuration loading"""

    def test_load_minimal_config(self, tmp_path):
        """Load minimal valid configuration"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
sources:
  fmp:
    api_key: "test-key"
kafka:
  bootstrap_servers: "localhost:9092"
storage:
  parquet_path: "/tmp/warehouse"
""")

        config = load_config(config_file)
        assert config.sources["fmp"].api_key == "test-key"
        assert config.kafka.bootstrap_servers == "localhost:9092"
        assert config.storage.parquet_path == "/tmp/warehouse"

    def test_load_full_config(self, tmp_path):
        """Load complete configuration with all fields"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
sources:
  fmp:
    api_key: "fmp-key"
    rate_limit: 0.5
  stocktwits:
    poll_interval: 20

kafka:
  bootstrap_servers: "kafka:9092"
  topics:
    news: "raw.news"
    stocktwits: "raw.stocktwits"
    processed_sentiment: "processed.sentiment"

storage:
  parquet_path: "warehouse/"
  es_hosts:
    - "es1:9200"
    - "es2:9200"

data_api:
  host: "0.0.0.0"
  port: 8000
  token: "secret"

alerts:
  channels:
    slack: "#alerts"
    email: "test@example.com"
  rules:
    - name: "high_null"
      condition: "null_ratio > 0.1"
      severity: "warning"
""")

        config = load_config(config_file)
        assert config.sources["fmp"].rate_limit == 0.5
        assert config.sources["stocktwits"].poll_interval == 20
        assert len(config.kafka.topics.model_dump()) == 6
        assert len(config.storage.es_hosts) == 2
        assert config.data_api.port == 8000
        assert len(config.alerts.rules) == 1

    def test_file_not_found(self):
        """Raise error when config file missing"""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")