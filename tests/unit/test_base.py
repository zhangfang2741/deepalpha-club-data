"""Tests for base plugin classes"""
import pytest
from deepalpha.base import BaseSource, BaseProcessor
import polars as pl
from abc import ABC


class TestBaseSource:
    def test_base_source_is_abc(self):
        """Verify that BaseSource is an abstract base class."""
        assert issubclass(BaseSource, ABC)

    def test_cannot_instantiate_directly(self):
        """Verify that BaseSource cannot be instantiated without implementing abstract members."""
        with pytest.raises(TypeError):
            BaseSource()

    def test_concrete_subclass_works(self):
        """Verify that a concrete subclass with name property and required methods can be instantiated."""
        class MinimalSource(BaseSource):
            @property
            def name(self) -> str: return "test"
            def fetch(self, **kwargs): return pl.DataFrame()
            def validate(self, df): return True

        source = MinimalSource()
        assert source.name == "test"


class TestBaseProcessor:
    def test_base_processor_is_abc(self):
        """Verify that BaseProcessor is an abstract base class."""
        assert issubclass(BaseProcessor, ABC)

    def test_cannot_instantiate_directly(self):
        """Verify that BaseProcessor cannot be instantiated without implementing abstract members."""
        with pytest.raises(TypeError):
            BaseProcessor()

    def test_validate_output_non_empty(self):
        """Verify that validate_output returns True for a non-empty DataFrame."""
        class MinimalProcessor(BaseProcessor):
            @property
            def name(self) -> str: return "test"
            def process(self, df, **kwargs): return df

        p = MinimalProcessor()
        assert p.validate_output(pl.DataFrame({"a": [1]})) is True

    def test_validate_output_empty(self):
        """Verify that validate_output returns False for an empty DataFrame."""
        class MinimalProcessor(BaseProcessor):
            @property
            def name(self) -> str: return "test"
            def process(self, df, **kwargs): return df

        p = MinimalProcessor()
        assert p.validate_output(pl.DataFrame()) is False
