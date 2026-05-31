import pytest
from pydantic import BaseModel, Field

from deepalpha.loaders.base import BaseLoader


class FakeClient:
    def __init__(self, response):
        self._response = response

    async def get(self, path, **params):
        return self._response


class SimpleModel(BaseModel):
    value: int = Field(title="值", description="测试字段")


class ConcreteLoader(BaseLoader):
    pass  # BaseLoader 无抽象方法，可直接实例化用于测试辅助方法


@pytest.mark.asyncio
async def test_get_unwraps_list():
    client = FakeClient([{"value": 42}])
    loader = ConcreteLoader(client)
    result = await loader._get("/test")
    assert result == {"value": 42}


@pytest.mark.asyncio
async def test_get_raises_on_empty():
    client = FakeClient([])
    loader = ConcreteLoader(client)
    with pytest.raises(ValueError, match="Empty response"):
        await loader._get("/test")


@pytest.mark.asyncio
async def test_get_list_returns_list():
    client = FakeClient([{"value": 1}, {"value": 2}])
    loader = ConcreteLoader(client)
    result = await loader._get_list("/test")
    assert result == [{"value": 1}, {"value": 2}]


def test_to_df_validates_and_returns_dataframe():
    import polars as pl

    client = FakeClient(None)
    loader = ConcreteLoader(client)
    df = loader._to_df([{"value": 10}, {"value": 20}], SimpleModel)
    assert isinstance(df, pl.DataFrame)
    assert df["value"].to_list() == [10, 20]
