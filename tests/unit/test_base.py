"""Tests for base plugin classes"""
import pytest
from deepalpha.base import BaseSource, BaseProcessor
import polars as pl
from abc import ABC


class TestBaseSource:
    def test_base_source_is_abc(self):
        assert issubclass(BaseSource, ABC)

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseSource()

    def test_concrete_subclass_works(self):
        class MinimalSource(BaseSource):
            name = "test"
            def fetch(self, **kwargs): return pl.DataFrame()
            def validate(self, df): return True

        source = MinimalSource()
        assert source.name == "test"


class TestBaseProcessor:
    def test_base_processor_is_abc(self):
        assert issubclass(BaseProcessor, ABC)

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseProcessor()

    def test_validate_output_non_empty(self):
        class MinimalProcessor(BaseProcessor):
            def process(self, df, **kwargs): return df

        p = MinimalProcessor()
        assert p.validate_output(pl.DataFrame({"a": [1]})) is True

    def test_validate_output_empty(self):
        class MinimalProcessor(BaseProcessor):
            def process(self, df, **kwargs): return df

        p = MinimalProcessor()
        assert p.validate_output(pl.DataFrame()) is False
