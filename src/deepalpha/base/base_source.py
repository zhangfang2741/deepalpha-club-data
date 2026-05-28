# src/deepalpha/base/base_source.py
from abc import ABC, abstractmethod
from typing import Any
import polars as pl


class BaseSource(ABC):
    name: str
    version: str = "1.0.0"

    @abstractmethod
    def fetch(self, **kwargs: Any) -> pl.DataFrame: ...

    @abstractmethod
    def validate(self, df: pl.DataFrame) -> bool: ...

    def to_kafka(self, df: pl.DataFrame, topic: str, bootstrap_servers: str = "localhost:9092") -> None:
        from confluent_kafka import Producer
        import json
        producer = Producer({"bootstrap.servers": bootstrap_servers})
        for row in df.iter_rows(named=True):
            producer.produce(topic, key=row.get("symbol", "").encode(), value=json.dumps(row).encode())
        producer.flush()
