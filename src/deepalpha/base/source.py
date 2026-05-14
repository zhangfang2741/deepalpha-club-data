"""Base source plugin interface for L0 data ingestion"""
from abc import ABC, abstractmethod
from typing import Any

import polars as pl


class BaseSource(ABC):
    """Abstract base class for all data source plugins.

    Each source plugin must implement fetch() and validate() methods.
    Optionally can use to_kafka() to push data to Kafka topics.
    """

    name: str
    version: str = "1.0.0"

    @abstractmethod
    def fetch(self, **kwargs: Any) -> pl.DataFrame:
        """Fetch data from the source.

        Args:
            **kwargs: Source-specific parameters (e.g., start_date, end_date)

        Returns:
            polars.DataFrame: Raw data from source
        """
        ...

    @abstractmethod
    def validate(self, df: pl.DataFrame) -> bool:
        """Validate fetched data.

        Args:
            df: DataFrame to validate

        Returns:
            bool: True if data passes validation rules
        """
        ...

    def to_kafka(
        self,
        df: pl.DataFrame,
        topic: str,
        bootstrap_servers: str = "localhost:9092",
    ) -> None:
        """Push DataFrame to Kafka topic.

        Args:
            df: DataFrame to send
            topic: Kafka topic name
            bootstrap_servers: Kafka broker address
        """
        from confluent.kafka import Producer
        import json

        producer = Producer({"bootstrap.servers": bootstrap_servers})

        for row in df.iter_rows(named=True):
            producer.produce(
                topic,
                key=row.get("symbol", "").encode("utf-8"),
                value=json.dumps(row).encode("utf-8"),
            )

        producer.flush()
        producer.close()