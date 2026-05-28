# src/deepalpha/base/base_processor.py
from abc import ABC, abstractmethod
from typing import Any
import polars as pl


class BaseProcessor(ABC):
    version: str = "1.0.0"

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def process(self, df: pl.DataFrame, **kwargs: Any) -> pl.DataFrame: ...

    def validate_output(self, df: pl.DataFrame) -> bool:
        return not df.is_empty()
