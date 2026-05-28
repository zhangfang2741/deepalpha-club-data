# tests/unit/adapters/test_fmp_adapter.py
import pytest
import polars as pl
from deepalpha.adapters.base_adapter import BaseAdapter


class TestBaseAdapter:
    def test_unimplemented_adapt_price_raises(self):
        """adapt_price raises NotImplementedError when not overridden."""
        adapter = BaseAdapter()
        with pytest.raises(NotImplementedError):
            adapter.adapt_price(pl.DataFrame())

    def test_unimplemented_adapt_company_info_raises(self):
        """adapt_company_info raises NotImplementedError when not overridden."""
        adapter = BaseAdapter()
        with pytest.raises(NotImplementedError):
            adapter.adapt_company_info(pl.DataFrame())

    def test_can_instantiate_without_source_name(self):
        """BaseAdapter is a plain class, not ABC — can be instantiated."""
        adapter = BaseAdapter()
        assert adapter is not None
