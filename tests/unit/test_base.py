"""Tests for base plugin classes"""
import pytest
from deepalpha.base import BaseSource, BaseProcessor
import polars as pl
from abc import ABC


class TestBaseSource:
    """Test BaseSource abstract interface"""

    def test_base_source_is_abc(self):
        """BaseSource should be abstract base class"""
        assert issubclass(BaseSource, ABC)

    def test_fetch_is_abstract(self):
        """fetch() must be implemented by subclass"""
        with pytest.raises(TypeError):
            BaseSource()

    def test_validate_is_abstract(self):
        """validate() must be implemented by subclass"""

        class MinimalSource(BaseSource):
            def fetch(self, **kwargs):
                return pl.DataFrame()

            def validate(self, df: pl.DataFrame) -> bool:
                return True

        source = MinimalSource()
        assert hasattr(source, "validate")


class TestBaseProcessor:
    """Test BaseProcessor abstract interface"""

    def test_base_processor_is_abc(self):
        """BaseProcessor should be abstract base class"""
        assert issubclass(BaseProcessor, ABC)

    def test_process_is_abstract(self):
        """process() must be implemented by subclass"""
        with pytest.raises(TypeError):
            BaseProcessor()

    def test_validate_output_default(self):
        """Default validate_output returns True for non-empty DataFrame"""

        class MinimalProcessor(BaseProcessor):
            def process(self, df: pl.DataFrame, **kwargs) -> pl.DataFrame:
                return df

        processor = MinimalProcessor()
        df = pl.DataFrame({"a": [1, 2, 3]})
        assert processor.validate_output(df) is True

    def test_validate_output_empty(self):
        """Default validate_output returns False for empty DataFrame"""

        class MinimalProcessor(BaseProcessor):
            def process(self, df: pl.DataFrame, **kwargs) -> pl.DataFrame:
                return df

        processor = MinimalProcessor()
        df = pl.DataFrame()
        assert processor.validate_output(df) is False