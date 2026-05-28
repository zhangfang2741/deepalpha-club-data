# src/deepalpha/base/base_source.py
from abc import ABC, abstractmethod
from typing import Any
import polars as pl


class BaseSource(ABC):
    version: str = "1.0.0"

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def fetch(self, **kwargs: Any) -> pl.DataFrame: ...

    @abstractmethod
    def validate(self, df: pl.DataFrame) -> bool: ...

    def to_kafka(self, df: pl.DataFrame, topic: str, bootstrap_servers: str = "localhost:9092") -> None:
        from confluent_kafka import Producer
        import json

        errors: list[str] = []

        def _on_delivery(err, msg):
            if err:
                errors.append(str(err))

        producer = Producer({"bootstrap.servers": bootstrap_servers})
        try:
            for row in df.iter_rows(named=True):
                producer.produce(
                    topic,
                    key=str(row.get("symbol") or "").encode(),
                    value=json.dumps(row, default=str).encode(),
                    on_delivery=_on_delivery,
                )
        finally:
            producer.flush()

        if errors:
            raise RuntimeError(f"Kafka delivery failed for {len(errors)} row(s): {errors[:3]}")
