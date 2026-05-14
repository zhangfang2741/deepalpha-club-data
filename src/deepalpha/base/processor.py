"""Base processor plugin interface for L1/L2 data processing"""
from abc import ABC, abstractmethod
from typing import Any

import polars as pl


class BaseProcessor(ABC):
    """Abstract base class for all data processor plugins.

    Each processor plugin must implement process() method.
    """

    name: str
    version: str = "1.0.0"

    @abstractmethod
    def process(self, df: pl.DataFrame, **kwargs: Any) -> pl.DataFrame:
        """Process input DataFrame and return cleaned result.

        Args:
            df: Input DataFrame to process
            **kwargs: Processor-specific parameters

        Returns:
            polars.DataFrame: Processed data
        """
        ...

    def validate_output(self, df: pl.DataFrame) -> bool:
        """Validate processed output.

        Default implementation checks for empty DataFrame.
        Override for custom validation rules.

        Args:
            df: Processed DataFrame

        Returns:
            bool: True if output is valid
        """
        return not df.is_empty()