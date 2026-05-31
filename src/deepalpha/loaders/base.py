from abc import ABC
from collections.abc import Sequence
from typing import Any, Protocol, TypeVar, cast, runtime_checkable

import polars as pl
from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


@runtime_checkable
class AsyncDataClient(Protocol):
    """异步数据客户端协议（鸭子类型接口）。

    使用 Protocol 定义，任何实现了 ``get`` 方法的类均自动满足此协议，
    无需显式继承 AsyncDataClient。配合 @runtime_checkable 可在运行时
    通过 isinstance(obj, AsyncDataClient) 检查兼容性。
    """

    async def get(self, path: str, **params: Any) -> Any:
        """获取数据。

        Args:
            path: 端点路径
            **params: 查询参数

        Returns:
            响应数据
        """
        ...


class BaseLoader(ABC):  # noqa: B024
    """基础加载器，提供数据获取、解析和转换的辅助方法。

    这是一个辅助基类，不直接实例化。
    设计为继承 ABC 以传递 ABCMeta，确保子类（AbstractMarketLoader 等）
    能够正常使用 @abstractmethod 装饰器约束实现。
    抽象方法均定义在各 AbstractXxxLoader 子类中，而非本类。
    """

    def __init__(self, client: AsyncDataClient) -> None:
        """初始化加载器。

        Args:
            client: 实现 AsyncDataClient 协议的客户端
        """
        self._client = client

    async def _get(self, endpoint: str, **params: Any) -> dict[str, Any]:
        """获取单个记录。

        如果响应是列表，返回第一个元素；否则返回响应本身。
        如果响应为空或列表为空，抛出 ValueError。

        Args:
            endpoint: 端点路径
            **params: 查询参数

        Returns:
            单个记录字典

        Raises:
            ValueError: 响应为空时
        """
        result = await self._client.get(endpoint, **params)
        if isinstance(result, list):
            if not result:
                raise ValueError(f"Empty response for: {endpoint}")
            return cast(dict[str, Any], result[0])
        if not result:
            raise ValueError(f"Empty response for: {endpoint}")
        return cast(dict[str, Any], result)

    async def _get_list(self, endpoint: str, **params: Any) -> list[dict[str, Any]]:
        """获取记录列表。

        如果响应是列表，返回该列表；如果是单个对象，包装为列表；
        如果为 None，返回空列表。

        Args:
            endpoint: 端点路径
            **params: 查询参数

        Returns:
            记录字典列表
        """
        result = await self._client.get(endpoint, **params)
        if result is None:
            return []
        if isinstance(result, list):
            return result
        return [result]

    def _to_models(
        self, records: list[dict[str, Any]], model: type[M]
    ) -> list[M]:
        """将记录字典列表验证为领域对象列表。

        Args:
            records: 记录字典列表
            model: 用于验证的 Pydantic 模型

        Returns:
            验证后的领域对象列表；如果记录为空，返回空列表
        """
        if not records:
            return []
        # FMP 对未填写的日期字段返回空字符串，统一转为 None 再校验
        clean = [{k: (None if v == "" else v) for k, v in r.items()} for r in records]
        return [model.model_validate(r) for r in clean]

    @staticmethod
    def to_dataframe(records: Sequence[BaseModel]) -> pl.DataFrame:
        """将领域对象序列转换为 Polars DataFrame。

        Args:
            records: 领域对象序列（list 或 tuple）

        Returns:
            Polars DataFrame；如果序列为空，返回空 DataFrame
        """
        if not records:
            return pl.DataFrame()
        return pl.DataFrame([r.model_dump() for r in records])

    def _to_df(
        self, records: list[dict[str, Any]], model: type[BaseModel]
    ) -> pl.DataFrame:
        """已废弃：请使用 _to_models() + to_dataframe()。保留以兼容迁移期间的旧调用。"""
        if not records:
            return pl.DataFrame()
        clean = [{k: (None if v == "" else v) for k, v in r.items()} for r in records]
        validated = [model.model_validate(r) for r in clean]
        return pl.DataFrame([v.model_dump() for v in validated])
