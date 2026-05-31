# Domain Model Loader Refactor 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将所有 loader 批量方法从返回 `pl.DataFrame` 改为返回 `list[DomainModel]`，在 `BaseLoader` 上添加 `to_dataframe()` 静态工具方法。

**Architecture:** 先在 `BaseLoader` 中新增 `_to_models()` 和 `to_dataframe()`（保留 `_to_df()` 过渡），逐个 loader 域迁移（abstract + FMP 实现 + 单元测试）后，最后删除 `_to_df()`。

**Tech Stack:** Python 3.10+, Pydantic v2, Polars, pytest-asyncio, pytest-httpx

---

## 文件变更范围

| 文件 | 操作 |
| --- | --- |
| `src/deepalpha/loaders/base.py` | 修改：加 TypeVar/Sequence import，加 `_to_models()`，加 `to_dataframe()` 静态方法，最后删 `_to_df()` |
| `src/deepalpha/loaders/market_loader.py` | 修改：3 个批量方法签名改为 `list[Quote]`/`list[PriceBar]` |
| `src/deepalpha/loaders/financial_loader.py` | 修改：5 个批量方法签名 |
| `src/deepalpha/loaders/company_loader.py` | 修改：2 个批量方法签名 |
| `src/deepalpha/loaders/analyst_loader.py` | 修改：3 个批量方法签名 |
| `src/deepalpha/loaders/calendar_loader.py` | 修改：4 个批量方法签名 |
| `src/deepalpha/loaders/news_loader.py` | 修改：1 个批量方法签名 |
| `src/deepalpha/loaders/insider_loader.py` | 修改：2 个批量方法签名 |
| `src/deepalpha/loaders/congress_loader.py` | 修改：1 个批量方法签名 |
| `src/deepalpha/loaders/filings_loader.py` | 修改：1 个批量方法签名 |
| `src/deepalpha/loaders/indicators_loader.py` | 修改：1 个批量方法签名 |
| `src/deepalpha/loaders/economics_loader.py` | 修改：1 个批量方法签名 |
| `src/deepalpha/loaders/performance_loader.py` | 修改：3 个批量方法签名 |
| `src/deepalpha/loaders/directory_loader.py` | 修改：2 个批量方法签名 |
| `src/deepalpha/providers/fmp/loaders/market_loader.py` | 修改：`_to_df` → `_to_models`，返回类型 |
| `src/deepalpha/providers/fmp/loaders/financial_loader.py` | 修改 |
| `src/deepalpha/providers/fmp/loaders/company_loader.py` | 修改 |
| `src/deepalpha/providers/fmp/loaders/analyst_loader.py` | 修改 |
| `src/deepalpha/providers/fmp/loaders/calendar_loader.py` | 修改 |
| `src/deepalpha/providers/fmp/loaders/news_loader.py` | 修改 |
| `src/deepalpha/providers/fmp/loaders/insider_loader.py` | 修改 |
| `src/deepalpha/providers/fmp/loaders/congress_loader.py` | 修改 |
| `src/deepalpha/providers/fmp/loaders/filings_loader.py` | 修改 |
| `src/deepalpha/providers/fmp/loaders/indicators_loader.py` | 修改 |
| `src/deepalpha/providers/fmp/loaders/economics_loader.py` | 修改（含特殊日期过滤迁移，删除 `_EconRow`） |
| `src/deepalpha/providers/fmp/loaders/performance_loader.py` | 修改 |
| `src/deepalpha/providers/fmp/loaders/directory_loader.py` | 修改 |
| `tests/unit/test_base_loader.py` | 新建：测试 `_to_models` 和 `to_dataframe` |
| `tests/unit/providers/fmp/loaders/test_market.py` | 修改：断言改为 list |
| `tests/unit/providers/fmp/loaders/test_financial.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_company.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_analyst.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_calendar.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_news.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_insider.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_congress.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_filings.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_indicators.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_economics.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_performance.py` | 修改 |
| `tests/unit/providers/fmp/loaders/test_directory.py` | 修改 |
| `tests/integration/test_fmp_integration.py` | 修改：DataFrame 断言改为 list 断言 |

---

## Task 1: BaseLoader — 新增 `_to_models` 和 `to_dataframe`

**Files:**
- Modify: `src/deepalpha/loaders/base.py`
- Create: `tests/unit/test_base_loader.py`

> 注意：这一步保留 `_to_df()` 不删，让其他 FMP loader 暂时不报错。`_to_df()` 在所有 loader 迁移完成后（Task 15）才删除。

- [ ] **Step 1: 写失败测试**

新建 `tests/unit/test_base_loader.py`：

```python
from unittest.mock import MagicMock

import polars as pl
import pytest
from pydantic import BaseModel

from deepalpha.loaders.base import BaseLoader
from deepalpha.models.insider import InsiderTrade


class _ConcreteLoader(BaseLoader):
    pass


@pytest.fixture
def loader():
    client = MagicMock()
    return _ConcreteLoader(client)


def test_to_models_returns_list_of_domain_objects(loader):
    records = [{
        "symbol": "AAPL", "filingDate": "2024-05-01", "transactionDate": "2024-04-29",
        "reportingName": "Tim Cook", "securityName": "Common Stock",
        "transactionType": "S-Sale", "acquisitionOrDisposition": "D",
        "securitiesTransacted": 100000, "price": 185.0,
        "typeOfOwner": "officer", "formType": "4",
        "url": "https://www.sec.gov/",
    }]
    result = loader._to_models(records, InsiderTrade)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], InsiderTrade)
    assert result[0].reporting_name == "Tim Cook"


def test_to_models_empty_records_returns_empty_list(loader):
    result = loader._to_models([], InsiderTrade)
    assert result == []


def test_to_models_cleans_empty_string_dates(loader):
    records = [{
        "symbol": "AAPL", "filingDate": "", "transactionDate": "",
        "reportingName": "Tim Cook", "securityName": "Common Stock",
        "transactionType": "S-Sale", "acquisitionOrDisposition": "D",
        "securitiesTransacted": 100000, "price": 185.0,
        "typeOfOwner": "officer", "formType": "4",
        "url": "https://www.sec.gov/",
    }]
    result = loader._to_models(records, InsiderTrade)
    assert result[0].filing_date is None
    assert result[0].transaction_date is None


def test_to_dataframe_returns_polars_dataframe():
    from deepalpha.models.insider import InsiderTrade
    trade = InsiderTrade(
        symbol="AAPL",
        reporting_name="Tim Cook",
        transaction_type="S-Sale",
        price=185.0,
    )
    df = BaseLoader.to_dataframe([trade])
    assert isinstance(df, pl.DataFrame)
    assert "symbol" in df.columns
    assert df["symbol"][0] == "AAPL"


def test_to_dataframe_empty_returns_empty_dataframe():
    df = BaseLoader.to_dataframe([])
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Users/zhangfang/deepalpha-club-data
uv run pytest tests/unit/test_base_loader.py -v
```

预期: FAILED — `_to_models` 和 `to_dataframe` 不存在

- [ ] **Step 3: 更新 `base.py`**

完整替换 `src/deepalpha/loaders/base.py` 为：

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/unit/test_base_loader.py -v
```

预期: 5 passed

- [ ] **Step 5: 提交**

```bash
git add src/deepalpha/loaders/base.py tests/unit/test_base_loader.py
git commit -m "feat: add BaseLoader._to_models() and to_dataframe() static method"
```

---

## Task 2: Market Loader

**Files:**
- Modify: `src/deepalpha/loaders/market_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/market_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_market.py`

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_market.py` 中的断言：

```python
import datetime

import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import AssetClass
from deepalpha.models.market import PriceBar, Quote
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.market_loader import FMPMarketLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_quote_returns_quote(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "price": 189.84, "change": 2.31,
        "changePercentage": 1.23, "volume": 45000000,
    }])
    loader = FMPMarketLoader(client)
    quote = await loader.get_quote("AAPL")
    assert isinstance(quote, Quote)
    assert quote.symbol == "AAPL"
    assert quote.price == 189.84
    assert quote.changes_percentage == 1.23
    await client.aclose()

@pytest.mark.asyncio
async def test_get_quotes_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"symbol": "AAPL", "price": 189.84, "change": 2.31, "changePercentage": 1.23, "volume": 1000},
    ])
    httpx_mock.add_response(json=[
        {"symbol": "MSFT", "price": 420.10, "change": 1.05, "changePercentage": 0.25, "volume": 2000},
    ])
    loader = FMPMarketLoader(client)
    result = await loader.get_quotes(["AAPL", "MSFT"])
    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], Quote)
    assert result[0].symbol == "AAPL"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_price_history_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-01-05", "open": 185.0, "high": 190.0, "low": 184.0, "close": 189.0, "volume": 50000000},
        {"date": "2024-01-04", "open": 182.0, "high": 186.0, "low": 181.0, "close": 185.0, "volume": 48000000},
    ])
    loader = FMPMarketLoader(client)
    result = await loader.get_price_history("AAPL", start=datetime.date(2024, 1, 1))
    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], PriceBar)
    assert result[0].close == 189.0
    await client.aclose()

@pytest.mark.asyncio
async def test_get_market_snapshot_returns_empty_list(client):
    loader = FMPMarketLoader(client)
    result = await loader.get_market_snapshot(AssetClass.STOCK)
    assert isinstance(result, list)
    assert result == []
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_market.py -v
```

预期: FAILED — 返回 `pl.DataFrame` 不是 `list`

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/market_loader.py`：

```python
import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass, Interval
from deepalpha.models.market import PriceBar, Quote


class AbstractMarketLoader(BaseLoader):
    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote: ...
    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> list[Quote]: ...
    @abstractmethod
    async def get_price_history(
        self, symbol: str, start: datetime.date, end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY, adjusted: bool = True,
    ) -> list[PriceBar]: ...
    @abstractmethod
    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> list[Quote]: ...
```

- [ ] **Step 4: 更新 FMP 实现**

在 `src/deepalpha/providers/fmp/loaders/market_loader.py` 中：
- 删除 `import polars as pl`
- 修改 `get_quotes`、`get_price_history`、`get_market_snapshot` 的返回类型和实现

完整文件如下：

```python
"""FMP 市场数据加载器实现"""

import datetime
from typing import Any

from deepalpha.loaders.enums import AssetClass, Interval
from deepalpha.loaders.market_loader import AbstractMarketLoader
from deepalpha.models.market import PriceBar, Quote

_INTRADAY_PATHS: dict[Interval, str] = {
    Interval.ONE_MIN:     "historical-chart/1min",
    Interval.FIVE_MIN:    "historical-chart/5min",
    Interval.FIFTEEN_MIN: "historical-chart/15min",
    Interval.THIRTY_MIN:  "historical-chart/30min",
    Interval.ONE_HOUR:    "historical-chart/1hour",
    Interval.FOUR_HOUR:   "historical-chart/4hour",
}


class FMPMarketLoader(AbstractMarketLoader):
    """FMP 市场数据加载器。

    实现 AbstractMarketLoader 接口，通过 FMP stable API 获取市场数据。
    所有端点使用 ?symbol=X 查询参数格式。
    """

    async def get_quote(self, symbol: str) -> Quote:
        data = await self._get("/stable/quote", symbol=symbol)
        return Quote.model_validate(data)

    async def get_quotes(self, symbols: list[str]) -> list[Quote]:
        result: list[Quote] = []
        for sym in symbols:
            records = await self._get_list("/stable/quote", symbol=sym)
            result.extend(self._to_models(records, Quote))
        return result

    async def get_price_history(
        self,
        symbol: str,
        start: datetime.date,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> list[PriceBar]:
        params: dict[str, Any] = {"symbol": symbol, "from": str(start)}
        if end:
            params["to"] = str(end)
        if interval in _INTRADAY_PATHS:
            path = f"/stable/{_INTRADAY_PATHS[interval]}"
        else:
            path = "/stable/historical-price-eod/full"
        records = await self._get_list(path, **params)
        return self._to_models(records, PriceBar)

    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> list[Quote]:
        return []
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_market.py -v
```

预期: 4 passed

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/market_loader.py \
        src/deepalpha/providers/fmp/loaders/market_loader.py \
        tests/unit/providers/fmp/loaders/test_market.py
git commit -m "refactor: market loader returns list[Quote]/list[PriceBar]"
```

---

## Task 3: Financial Loader

**Files:**
- Modify: `src/deepalpha/loaders/financial_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/financial_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_financial.py`

- [ ] **Step 1: 更新测试（令其失败）**

打开 `tests/unit/providers/fmp/loaders/test_financial.py`，将每个 `assert isinstance(df, pl.DataFrame)` + `assert "xxx" in df.columns` 改为 `assert isinstance(result, list)` + `assert isinstance(result[0], XxxModel)`。

完整替换文件为：

```python
"""FMP 财务数据加载器测试"""

import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.financial import (
    BalanceSheet,
    CashFlow,
    FinancialRatio,
    IncomeStatement,
    KeyMetrics,
    Valuation,
)
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.financial_loader import FMPFinancialLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


_INCOME_ROW = {
    "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
    "revenue": 383285000000, "grossProfit": 169148000000,
    "operatingIncome": 114301000000, "netIncome": 96995000000,
    "eps": 6.13, "epsDiluted": 6.12, "ebitda": 130000000000,
}


@pytest.mark.asyncio
async def test_get_income_statement_annual(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_INCOME_ROW])
    loader = FMPFinancialLoader(client)
    result = await loader.get_income_statement("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], IncomeStatement)
    assert result[0].symbol == "AAPL"
    assert result[0].revenue == 383285000000
    await client.aclose()


@pytest.mark.asyncio
async def test_get_income_statement_ttm(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_INCOME_ROW])
    loader = FMPFinancialLoader(client)
    result = await loader.get_income_statement("AAPL", period=StatementPeriod.TTM)
    assert isinstance(result, list)
    assert len(result) == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_get_balance_sheet_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
        "totalAssets": 352755000000, "totalLiabilities": 290437000000,
        "totalStockholdersEquity": 62146000000,
    }])
    loader = FMPFinancialLoader(client)
    result = await loader.get_balance_sheet("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], BalanceSheet)
    assert result[0].total_assets == 352755000000
    await client.aclose()


@pytest.mark.asyncio
async def test_get_cash_flow_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
        "netIncome": 96995000000, "operatingCashFlow": 113000000000,
        "capitalExpenditure": -10959000000, "freeCashFlow": 99584000000,
    }])
    loader = FMPFinancialLoader(client)
    result = await loader.get_cash_flow_statement("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], CashFlow)
    await client.aclose()


@pytest.mark.asyncio
async def test_get_financial_ratios_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
        "peRatio": 29.5, "priceToBookRatio": 47.2, "currentRatio": 1.07,
    }])
    loader = FMPFinancialLoader(client)
    result = await loader.get_financial_ratios("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], FinancialRatio)
    await client.aclose()


@pytest.mark.asyncio
async def test_get_key_metrics_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
        "revenuePerShare": 24.32, "netIncomePerShare": 6.13, "marketCap": 2800000000000,
    }])
    loader = FMPFinancialLoader(client)
    result = await loader.get_key_metrics("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], KeyMetrics)
    await client.aclose()


@pytest.mark.asyncio
async def test_get_valuation_returns_valuation_object(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "dcf": 182.5, "stockPrice": 189.84,
    }])
    loader = FMPFinancialLoader(client)
    result = await loader.get_valuation("AAPL")
    assert isinstance(result, Valuation)
    assert result.symbol == "AAPL"
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_financial.py -v
```

预期: FAILED

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/financial_loader.py`：

```python
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.financial import (
    BalanceSheet,
    CashFlow,
    FinancialRatio,
    IncomeStatement,
    KeyMetrics,
    Valuation,
)


class AbstractFinancialLoader(BaseLoader):
    @abstractmethod
    async def get_income_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> list[IncomeStatement]: ...
    @abstractmethod
    async def get_balance_sheet(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> list[BalanceSheet]: ...
    @abstractmethod
    async def get_cash_flow_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> list[CashFlow]: ...
    @abstractmethod
    async def get_financial_ratios(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> list[FinancialRatio]: ...
    @abstractmethod
    async def get_key_metrics(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> list[KeyMetrics]: ...
    @abstractmethod
    async def get_valuation(self, symbol: str) -> Valuation: ...
```

- [ ] **Step 4: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/financial_loader.py`：

```python
"""FMP 财务数据加载器实现"""

from typing import Any

from deepalpha.loaders.enums import StatementPeriod
from deepalpha.loaders.financial_loader import AbstractFinancialLoader
from deepalpha.models.financial import (
    BalanceSheet,
    CashFlow,
    FinancialRatio,
    IncomeStatement,
    KeyMetrics,
    Valuation,
)


class FMPFinancialLoader(AbstractFinancialLoader):
    """FMP 财务数据加载器。"""

    async def get_income_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5,
    ) -> list[IncomeStatement]:
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/income-statement", **params)
        return self._to_models(records, IncomeStatement)

    async def get_balance_sheet(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5,
    ) -> list[BalanceSheet]:
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/balance-sheet-statement", **params)
        return self._to_models(records, BalanceSheet)

    async def get_cash_flow_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5,
    ) -> list[CashFlow]:
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/cash-flow-statement", **params)
        return self._to_models(records, CashFlow)

    async def get_financial_ratios(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5,
    ) -> list[FinancialRatio]:
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/ratios", **params)
        return self._to_models(records, FinancialRatio)

    async def get_key_metrics(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5,
    ) -> list[KeyMetrics]:
        params: dict[str, Any] = {"symbol": symbol, "period": period.value, "limit": limit}
        records = await self._get_list("/stable/key-metrics", **params)
        return self._to_models(records, KeyMetrics)

    async def get_valuation(self, symbol: str) -> Valuation:
        data = await self._get("/stable/discounted-cash-flow", symbol=symbol)
        return Valuation.model_validate(data)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_financial.py -v
```

预期: 7 passed

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/financial_loader.py \
        src/deepalpha/providers/fmp/loaders/financial_loader.py \
        tests/unit/providers/fmp/loaders/test_financial.py
git commit -m "refactor: financial loader returns list[IncomeStatement/BalanceSheet/...]"
```

---

## Task 4: Company Loader

**Files:**
- Modify: `src/deepalpha/loaders/company_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/company_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_company.py`

- [ ] **Step 1: 读取现有测试，确认需要修改的断言**

```bash
cat tests/unit/providers/fmp/loaders/test_company.py
```

- [ ] **Step 2: 更新测试（令其失败）**

将 `test_company.py` 中 `get_executives` 和 `get_market_cap` 的断言改为 list：

```python
import datetime

import pytest
from pytest_httpx import HTTPXMock

from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.company_loader import FMPCompanyLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_profile_returns_company_profile(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "companyName": "Apple Inc.", "sector": "Technology",
        "industry": "Consumer Electronics", "exchange": "NASDAQ",
        "marketCap": 2800000000000, "description": "Apple Inc. designs...",
    }])
    loader = FMPCompanyLoader(client)
    profile = await loader.get_profile("AAPL")
    assert isinstance(profile, CompanyProfile)
    assert profile.symbol == "AAPL"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_executives_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "title": "CEO", "name": "Tim Cook", "pay": 99420000,
        "currencyPay": "USD", "gender": "male", "yearBorn": 1960,
    }])
    loader = FMPCompanyLoader(client)
    result = await loader.get_executives("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], Executive)
    assert result[0].name == "Tim Cook"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_peers_returns_list_of_strings(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"symbol": "MSFT"}, {"symbol": "GOOGL"}, {"symbol": "AMZN"},
    ])
    loader = FMPCompanyLoader(client)
    peers = await loader.get_peers("AAPL")
    assert isinstance(peers, list)
    assert "MSFT" in peers
    await client.aclose()


@pytest.mark.asyncio
async def test_get_market_cap_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-05-01", "marketCap": 2800000000000,
    }])
    loader = FMPCompanyLoader(client)
    result = await loader.get_market_cap("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], MarketCapRecord)
    assert result[0].market_cap == 2800000000000
    await client.aclose()
```

- [ ] **Step 3: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_company.py -v
```

- [ ] **Step 4: 更新 abstract loader**

替换 `src/deepalpha/loaders/company_loader.py`：

```python
import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord


class AbstractCompanyLoader(BaseLoader):
    @abstractmethod
    async def get_profile(self, symbol: str) -> CompanyProfile: ...
    @abstractmethod
    async def get_executives(self, symbol: str) -> list[Executive]: ...
    @abstractmethod
    async def get_peers(self, symbol: str) -> list[str]: ...
    @abstractmethod
    async def get_market_cap(
        self, symbol: str, start: datetime.date | None = None, end: datetime.date | None = None
    ) -> list[MarketCapRecord]: ...
```

- [ ] **Step 5: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/company_loader.py`：

```python
"""FMP 公司数据加载器实现"""

import datetime
from typing import Any

from deepalpha.loaders.company_loader import AbstractCompanyLoader
from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord


class FMPCompanyLoader(AbstractCompanyLoader):
    """FMP 公司数据加载器。"""

    async def get_profile(self, symbol: str) -> CompanyProfile:
        data = await self._get("/stable/profile", symbol=symbol)
        return CompanyProfile.model_validate(data)

    async def get_executives(self, symbol: str) -> list[Executive]:
        records = await self._get_list("/stable/key-executives", symbol=symbol)
        return self._to_models(records, Executive)

    async def get_peers(self, symbol: str) -> list[str]:
        records = await self._get_list("/stable/stock-peers", symbol=symbol)
        return [r.get("symbol", "") for r in records if r.get("symbol")]

    async def get_market_cap(
        self, symbol: str, start: datetime.date | None = None, end: datetime.date | None = None
    ) -> list[MarketCapRecord]:
        if start is None and end is None:
            records = await self._get_list("/stable/market-capitalization", symbol=symbol)
        else:
            params: dict[str, Any] = {"symbol": symbol}
            if start:
                params["from"] = str(start)
            if end:
                params["to"] = str(end)
            records = await self._get_list("/stable/historical-market-capitalization", **params)
        return self._to_models(records, MarketCapRecord)
```

- [ ] **Step 6: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_company.py -v
```

- [ ] **Step 7: 提交**

```bash
git add src/deepalpha/loaders/company_loader.py \
        src/deepalpha/providers/fmp/loaders/company_loader.py \
        tests/unit/providers/fmp/loaders/test_company.py
git commit -m "refactor: company loader returns list[Executive]/list[MarketCapRecord]"
```

---

## Task 5: Analyst Loader

**Files:**
- Modify: `src/deepalpha/loaders/analyst_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/analyst_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_analyst.py`

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_analyst.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.models.analyst import AnalystRating, Estimate, PriceTarget
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.analyst_loader import FMPAnalystLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_ratings_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-01-01",
        "rating": "S+", "ratingRecommendation": "Strong Buy", "ratingScore": 1,
    }])
    loader = FMPAnalystLoader(client)
    result = await loader.get_ratings("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], AnalystRating)
    assert result[0].rating == "S+"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_price_targets_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json={
        "symbol": "AAPL", "lastMonth": 198.0, "lastQuarter": 195.0,
        "lastYear": 185.0, "allTime": 175.0,
    })
    loader = FMPAnalystLoader(client)
    result = await loader.get_price_targets("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], PriceTarget)
    assert result[0].last_month == 198.0
    await client.aclose()


@pytest.mark.asyncio
async def test_get_estimates_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-09-30",
        "estimatedRevenueAvg": 390000000000, "estimatedEpsAvg": 6.50,
        "numberAnalystEstimatedRevenue": 28,
    }])
    loader = FMPAnalystLoader(client)
    result = await loader.get_estimates("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], Estimate)
    assert result[0].estimated_eps_avg == 6.50
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_analyst.py -v
```

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/analyst_loader.py`：

```python
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.analyst import AnalystRating, Estimate, PriceTarget


class AbstractAnalystLoader(BaseLoader):
    @abstractmethod
    async def get_ratings(self, symbol: str) -> list[AnalystRating]: ...
    @abstractmethod
    async def get_price_targets(self, symbol: str) -> list[PriceTarget]: ...
    @abstractmethod
    async def get_estimates(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL
    ) -> list[Estimate]: ...
```

- [ ] **Step 4: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/analyst_loader.py`：

```python
"""FMP 分析师数据加载器实现"""

from typing import Any

from deepalpha.loaders.analyst_loader import AbstractAnalystLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.analyst import AnalystRating, Estimate, PriceTarget


class FMPAnalystLoader(AbstractAnalystLoader):
    """FMP 分析师数据加载器。"""

    async def get_ratings(self, symbol: str) -> list[AnalystRating]:
        records = await self._get_list("/stable/ratings-snapshot", symbol=symbol)
        return self._to_models(records, AnalystRating)

    async def get_price_targets(self, symbol: str) -> list[PriceTarget]:
        data = await self._get("/stable/price-target-summary", symbol=symbol)
        return self._to_models([data], PriceTarget)

    async def get_estimates(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL
    ) -> list[Estimate]:
        params: dict[str, Any] = {"symbol": symbol, "period": period.value}
        records = await self._get_list("/stable/analyst-estimates", **params)
        return self._to_models(records, Estimate)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_analyst.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/analyst_loader.py \
        src/deepalpha/providers/fmp/loaders/analyst_loader.py \
        tests/unit/providers/fmp/loaders/test_analyst.py
git commit -m "refactor: analyst loader returns list[AnalystRating/PriceTarget/Estimate]"
```

---

## Task 6: Calendar Loader

**Files:**
- Modify: `src/deepalpha/loaders/calendar_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/calendar_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_calendar.py`

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_calendar.py`：

```python
import datetime

import pytest
from pytest_httpx import HTTPXMock

from deepalpha.models.calendar import DividendEvent, EarningsEvent, IPOEvent, SplitEvent
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.calendar_loader import FMPCalendarLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


START = datetime.date(2024, 1, 1)
END = datetime.date(2024, 3, 31)


@pytest.mark.asyncio
async def test_get_earnings_calendar_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-02-01",
        "eps": 2.18, "epsEstimated": 2.10, "time": "amc", "revenueEstimated": 118000000000,
    }])
    loader = FMPCalendarLoader(client)
    result = await loader.get_earnings_calendar(START, END)
    assert isinstance(result, list)
    assert isinstance(result[0], EarningsEvent)
    assert result[0].symbol == "AAPL"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_dividend_calendar_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-02-09",
        "dividend": 0.24, "recordDate": "2024-02-12", "paymentDate": "2024-02-15",
    }])
    loader = FMPCalendarLoader(client)
    result = await loader.get_dividend_calendar(START, END)
    assert isinstance(result, list)
    assert isinstance(result[0], DividendEvent)
    assert result[0].dividend == 0.24
    await client.aclose()


@pytest.mark.asyncio
async def test_get_ipo_calendar_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NEWCO", "company": "New Company Inc.", "date": "2024-02-20",
        "exchange": "NASDAQ", "priceRange": "$10-$12", "shares": 10000000,
    }])
    loader = FMPCalendarLoader(client)
    result = await loader.get_ipo_calendar(START, END)
    assert isinstance(result, list)
    assert isinstance(result[0], IPOEvent)
    assert result[0].symbol == "NEWCO"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_splits_calendar_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "date": "2024-06-10", "numerator": 10.0, "denominator": 1.0,
    }])
    loader = FMPCalendarLoader(client)
    result = await loader.get_splits_calendar(START, END)
    assert isinstance(result, list)
    assert isinstance(result[0], SplitEvent)
    assert result[0].numerator == 10.0
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_calendar.py -v
```

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/calendar_loader.py`：

```python
import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.models.calendar import DividendEvent, EarningsEvent, IPOEvent, SplitEvent


class AbstractCalendarLoader(BaseLoader):
    @abstractmethod
    async def get_earnings_calendar(self, start: datetime.date, end: datetime.date) -> list[EarningsEvent]: ...
    @abstractmethod
    async def get_dividend_calendar(self, start: datetime.date, end: datetime.date) -> list[DividendEvent]: ...
    @abstractmethod
    async def get_ipo_calendar(self, start: datetime.date, end: datetime.date) -> list[IPOEvent]: ...
    @abstractmethod
    async def get_splits_calendar(self, start: datetime.date, end: datetime.date) -> list[SplitEvent]: ...
```

- [ ] **Step 4: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/calendar_loader.py`：

```python
import datetime

from deepalpha.loaders.calendar_loader import AbstractCalendarLoader
from deepalpha.models.calendar import DividendEvent, EarningsEvent, IPOEvent, SplitEvent


class FMPCalendarLoader(AbstractCalendarLoader):
    """FMP 日历数据加载器。"""

    async def get_earnings_calendar(self, start: datetime.date, end: datetime.date) -> list[EarningsEvent]:
        records = await self._get_list(
            "/stable/earnings-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_models(records, EarningsEvent)

    async def get_dividend_calendar(self, start: datetime.date, end: datetime.date) -> list[DividendEvent]:
        records = await self._get_list(
            "/stable/dividends-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_models(records, DividendEvent)

    async def get_ipo_calendar(self, start: datetime.date, end: datetime.date) -> list[IPOEvent]:
        records = await self._get_list(
            "/stable/ipos-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_models(records, IPOEvent)

    async def get_splits_calendar(self, start: datetime.date, end: datetime.date) -> list[SplitEvent]:
        records = await self._get_list(
            "/stable/splits-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_models(records, SplitEvent)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_calendar.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/calendar_loader.py \
        src/deepalpha/providers/fmp/loaders/calendar_loader.py \
        tests/unit/providers/fmp/loaders/test_calendar.py
git commit -m "refactor: calendar loader returns list[EarningsEvent/DividendEvent/...]"
```

---

## Task 7: News Loader

**Files:**
- Modify: `src/deepalpha/loaders/news_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/news_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_news.py`

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_news.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.models.news import NewsArticle
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.news_loader import FMPNewsLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_stock_news_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "title": "Apple Reports Record Revenue", "url": "https://example.com/aapl",
        "publishedDate": "2024-05-02T18:00:00.000Z", "site": "Reuters",
        "text": "Apple Inc. reported...", "symbol": "AAPL", "sentiment": "Positive",
    }])
    loader = FMPNewsLoader(client)
    result = await loader.get_news(symbols=["AAPL"])
    assert isinstance(result, list)
    assert isinstance(result[0], NewsArticle)
    assert result[0].symbol == "AAPL"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_general_news_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "title": "Market Update", "link": "https://fmp.com/article/1",
        "date": "2024-05-02T12:00:00.000Z", "content": "Markets were mixed today...",
    }])
    loader = FMPNewsLoader(client)
    result = await loader.get_news()
    assert isinstance(result, list)
    assert isinstance(result[0], NewsArticle)
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_news.py -v
```

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/news_loader.py`：

```python
import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass
from deepalpha.models.news import NewsArticle


class AbstractNewsLoader(BaseLoader):
    @abstractmethod
    async def get_news(
        self,
        symbols: list[str] | None = None,
        asset_class: AssetClass | None = None,
        limit: int = 20,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[NewsArticle]: ...
```

- [ ] **Step 4: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/news_loader.py`：

```python
"""FMP 新闻数据加载器实现"""

import datetime
from typing import Any

from deepalpha.loaders.enums import AssetClass
from deepalpha.loaders.news_loader import AbstractNewsLoader
from deepalpha.models.news import NewsArticle

_ASSET_CLASS_PATHS: dict[AssetClass, str] = {
    AssetClass.CRYPTO: "news/crypto",
    AssetClass.FOREX:  "news/forex",
}


class FMPNewsLoader(AbstractNewsLoader):
    """FMP 新闻数据加载器。"""

    async def get_news(
        self,
        symbols: list[str] | None = None,
        asset_class: AssetClass | None = None,
        limit: int = 20,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[NewsArticle]:
        params: dict[str, Any] = {"limit": limit}
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)

        if symbols:
            params["symbol"] = ",".join(symbols)
            path = "/stable/news/stock"
        elif asset_class and asset_class in _ASSET_CLASS_PATHS:
            path = f"/stable/{_ASSET_CLASS_PATHS[asset_class]}"
        else:
            path = "/stable/fmp-articles"

        records = await self._get_list(path, **params)
        if path == "/stable/fmp-articles":
            for r in records:
                r.setdefault("url", r.pop("link", ""))
                r.setdefault("publishedDate", r.pop("date", None))
                r.setdefault("text", r.pop("content", None))
        return self._to_models(records, NewsArticle)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_news.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/news_loader.py \
        src/deepalpha/providers/fmp/loaders/news_loader.py \
        tests/unit/providers/fmp/loaders/test_news.py
git commit -m "refactor: news loader returns list[NewsArticle]"
```

---

## Task 8: Insider Loader

**Files:**
- Modify: `src/deepalpha/loaders/insider_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/insider_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_insider.py`

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_insider.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.models.insider import InsiderStatistics, InsiderTrade
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.insider_loader import FMPInsiderTradeLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

_TRADE_ROW = {
    "symbol": "AAPL", "filingDate": "2024-05-01", "transactionDate": "2024-04-29",
    "reportingName": "Tim Cook", "securityName": "Common Stock",
    "transactionType": "S-Sale", "acquisitionOrDisposition": "D",
    "securitiesTransacted": 100000, "price": 185.0,
    "typeOfOwner": "officer", "formType": "4",
    "url": "https://www.sec.gov/",
}

@pytest.mark.asyncio
async def test_get_insider_trades_all_market(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_TRADE_ROW])
    loader = FMPInsiderTradeLoader(client)
    result = await loader.get_insider_trades()
    assert isinstance(result, list)
    assert isinstance(result[0], InsiderTrade)
    assert result[0].reporting_name == "Tim Cook"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_insider_trades_by_symbol(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_TRADE_ROW])
    loader = FMPInsiderTradeLoader(client)
    result = await loader.get_insider_trades(symbol="AAPL", limit=10)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].symbol == "AAPL"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_insider_trades_not_found_returns_empty_list(httpx_mock: HTTPXMock, client):
    from deepalpha.providers.fmp.errors import FMPNotFoundError
    httpx_mock.add_exception(FMPNotFoundError("not found"))
    loader = FMPInsiderTradeLoader(client)
    result = await loader.get_insider_trades(symbol="UNKN")
    assert result == []
    await client.aclose()

@pytest.mark.asyncio
async def test_get_insider_statistics(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {
            "symbol": "AAPL", "year": 2026, "quarter": 1,
            "acquiredTransactions": 5, "disposedTransactions": 20,
            "totalAcquired": 50000.0, "totalDisposed": 200000.0,
            "totalPurchases": 1, "totalSales": 15,
        },
    ])
    loader = FMPInsiderTradeLoader(client)
    result = await loader.get_insider_statistics("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], InsiderStatistics)
    assert result[0].acquired_transactions == 5
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_insider.py -v
```

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/insider_loader.py`：

```python
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.models.insider import InsiderStatistics, InsiderTrade


class AbstractInsiderTradeLoader(BaseLoader):
    @abstractmethod
    async def get_insider_trades(
        self, symbol: str | None = None, limit: int = 50, page: int = 0
    ) -> list[InsiderTrade]: ...
    @abstractmethod
    async def get_insider_statistics(self, symbol: str) -> list[InsiderStatistics]: ...
```

- [ ] **Step 4: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/insider_loader.py`：

```python
from deepalpha.loaders.insider_loader import AbstractInsiderTradeLoader
from deepalpha.models.insider import InsiderStatistics, InsiderTrade


class FMPInsiderTradeLoader(AbstractInsiderTradeLoader):
    """FMP 内部人交易数据加载器。"""

    async def get_insider_trades(
        self, symbol: str | None = None, limit: int = 50, page: int = 0
    ) -> list[InsiderTrade]:
        from deepalpha.providers.fmp.errors import FMPNotFoundError
        try:
            if symbol:
                records = await self._get_list(
                    "/stable/insider-trades-search",
                    symbol=symbol, limit=limit, page=page,
                )
            else:
                records = await self._get_list(
                    "/stable/insider-trades-latest", limit=limit, page=page
                )
        except FMPNotFoundError:
            return []
        return self._to_models(records, InsiderTrade)

    async def get_insider_statistics(self, symbol: str) -> list[InsiderStatistics]:
        from deepalpha.providers.fmp.errors import FMPNotFoundError
        try:
            records = await self._get_list(f"/stable/insider-trade-statistics/{symbol}")
        except FMPNotFoundError:
            return []
        return self._to_models(records, InsiderStatistics)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_insider.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/insider_loader.py \
        src/deepalpha/providers/fmp/loaders/insider_loader.py \
        tests/unit/providers/fmp/loaders/test_insider.py
git commit -m "refactor: insider loader returns list[InsiderTrade]/list[InsiderStatistics]"
```

---

## Task 9: Congress Loader

**Files:**
- Modify: `src/deepalpha/loaders/congress_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/congress_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_congress.py`

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_congress.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import CongressChamber
from deepalpha.models.congress import CongressTrade
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.congress_loader import FMPCongressTradeLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

_TRADE_ROW = {
    "symbol": "NVDA", "disclosureDate": "2024-04-15", "transactionDate": "2024-04-10",
    "firstName": "John", "lastName": "Smith", "office": "John Smith",
    "district": "AR", "owner": "Self",
    "type": "Purchase", "amount": "$1,001 - $15,000",
    "assetDescription": "NVIDIA Corp", "assetType": "Stock",
    "link": "https://efdsearch.senate.gov/",
}

@pytest.mark.asyncio
async def test_get_senate_trades_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_TRADE_ROW])
    loader = FMPCongressTradeLoader(client)
    result = await loader.get_congress_trades(chamber=CongressChamber.SENATE)
    assert isinstance(result, list)
    assert isinstance(result[0], CongressTrade)
    assert result[0].office == "John Smith"
    assert result[0].first_name == "John"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_house_trades_by_symbol_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{**_TRADE_ROW, "firstName": "Jane", "lastName": "Doe", "office": "Jane Doe"}])
    loader = FMPCongressTradeLoader(client)
    result = await loader.get_congress_trades(symbol="NVDA", chamber=CongressChamber.HOUSE)
    assert isinstance(result, list)
    assert result[0].symbol == "NVDA"
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_congress.py -v
```

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/congress_loader.py`：

```python
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import CongressChamber
from deepalpha.models.congress import CongressTrade


class AbstractCongressTradeLoader(BaseLoader):
    @abstractmethod
    async def get_congress_trades(
        self,
        symbol: str | None = None,
        chamber: CongressChamber = CongressChamber.SENATE,
        limit: int = 50,
        page: int = 0,
    ) -> list[CongressTrade]: ...
```

- [ ] **Step 4: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/congress_loader.py`：

```python
from deepalpha.loaders.congress_loader import AbstractCongressTradeLoader
from deepalpha.loaders.enums import CongressChamber
from deepalpha.models.congress import CongressTrade


class FMPCongressTradeLoader(AbstractCongressTradeLoader):
    """FMP 国会议员交易数据加载器。"""

    async def get_congress_trades(
        self,
        symbol: str | None = None,
        chamber: CongressChamber = CongressChamber.SENATE,
        limit: int = 50,
        page: int = 0,
    ) -> list[CongressTrade]:
        chamber_prefix = "senate" if chamber == CongressChamber.SENATE else "house"
        if symbol:
            path = f"/stable/{chamber_prefix}-trading"
            params: dict[str, str | int] = {"symbol": symbol, "limit": limit, "page": page}
        else:
            path = f"/stable/{chamber_prefix}-latest"
            params = {"limit": limit, "page": page}
        records = await self._get_list(path, **params)
        return self._to_models(records, CongressTrade)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_congress.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/congress_loader.py \
        src/deepalpha/providers/fmp/loaders/congress_loader.py \
        tests/unit/providers/fmp/loaders/test_congress.py
git commit -m "refactor: congress loader returns list[CongressTrade]"
```

---

## Task 10: Filings Loader

**Files:**
- Modify: `src/deepalpha/loaders/filings_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/filings_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_filings.py`

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_filings.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.models.filings import SecCompanyProfile, SecFiling
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.filings_loader import FMPSecFilingLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_filings_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "filingDate": "2024-05-02", "acceptedDate": "2024-05-02",
        "formType": "10-Q", "link": "https://sec.gov/filing/aapl-10q.htm",
        "finalLink": "https://sec.gov/filing/aapl-10q-final.htm",
    }])
    loader = FMPSecFilingLoader(client)
    result = await loader.get_filings(symbol="AAPL", form_type="10-Q")
    assert isinstance(result, list)
    assert isinstance(result[0], SecFiling)
    assert result[0].form_type == "10-Q"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sec_profile_returns_profile(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "cik": "0000320193", "symbol": "AAPL",
        "registrantName": "Apple Inc.", "sicCode": "3674",
        "sicDescription": "Electronic Computers", "sicGroup": "Manufacturing",
    }])
    loader = FMPSecFilingLoader(client)
    profile = await loader.get_sec_profile("AAPL")
    assert isinstance(profile, SecCompanyProfile)
    assert profile.cik == "0000320193"
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_filings.py -v
```

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/filings_loader.py`：

```python
import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.models.filings import SecCompanyProfile, SecFiling


class AbstractSecFilingLoader(BaseLoader):
    @abstractmethod
    async def get_filings(
        self,
        symbol: str | None = None,
        form_type: str | None = None,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        limit: int = 20,
    ) -> list[SecFiling]: ...
    @abstractmethod
    async def get_sec_profile(self, symbol: str) -> SecCompanyProfile: ...
```

- [ ] **Step 4: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/filings_loader.py`：

```python
import datetime

from deepalpha.loaders.filings_loader import AbstractSecFilingLoader
from deepalpha.models.filings import SecCompanyProfile, SecFiling

_DEFAULT_LOOKBACK_YEARS = 3


class FMPSecFilingLoader(AbstractSecFilingLoader):
    """FMP SEC 文件加载器。"""

    async def get_filings(
        self,
        symbol: str | None = None,
        form_type: str | None = None,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        limit: int = 20,
    ) -> list[SecFiling]:
        today = datetime.date.today()
        from_date = start or (today - datetime.timedelta(days=365 * _DEFAULT_LOOKBACK_YEARS))
        to_date = end or today

        params: dict[str, str | int] = {
            "from": str(from_date),
            "to": str(to_date),
            "limit": limit,
        }
        if symbol:
            params["symbol"] = symbol
        if form_type:
            params["formType"] = form_type

        records = await self._get_list("/stable/sec-filings-search/symbol", **params)
        return self._to_models(records, SecFiling)

    async def get_sec_profile(self, symbol: str) -> SecCompanyProfile:
        data = await self._get("/stable/sec-profile", symbol=symbol)
        return SecCompanyProfile.model_validate(data)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_filings.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/filings_loader.py \
        src/deepalpha/providers/fmp/loaders/filings_loader.py \
        tests/unit/providers/fmp/loaders/test_filings.py
git commit -m "refactor: filings loader returns list[SecFiling]"
```

---

## Task 11: Technical Indicators Loader

**Files:**
- Modify: `src/deepalpha/loaders/indicators_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/indicators_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_indicators.py`

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_indicators.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import IndicatorType, Interval
from deepalpha.models.indicators import IndicatorRow
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.errors import FMPError
from deepalpha.providers.fmp.loaders.indicators_loader import FMPTechnicalIndicatorLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_sma_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-05-02T00:00:00", "sma": 183.5, "open": 185.0, "high": 186.0, "low": 182.0, "close": 185.5, "volume": 50000000},
    ])
    loader = FMPTechnicalIndicatorLoader(client)
    result = await loader.get_indicator("AAPL", IndicatorType.SMA, period=20)
    assert isinstance(result, list)
    assert isinstance(result[0], IndicatorRow)
    assert result[0].value == 183.5
    await client.aclose()

@pytest.mark.asyncio
async def test_get_rsi_with_interval_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-05-02T00:00:00", "rsi": 62.3, "open": 185.0, "high": 186.0, "low": 182.0, "close": 185.5, "volume": 50000000},
    ])
    loader = FMPTechnicalIndicatorLoader(client)
    result = await loader.get_indicator(
        "AAPL", IndicatorType.RSI, period=14, interval=Interval.ONE_HOUR
    )
    assert isinstance(result, list)
    assert isinstance(result[0], IndicatorRow)
    assert result[0].value == 62.3
    await client.aclose()

@pytest.mark.asyncio
async def test_unsupported_indicator_raises_fmp_error(httpx_mock: HTTPXMock, client):
    loader = FMPTechnicalIndicatorLoader(client)
    with pytest.raises(FMPError):
        await loader.get_indicator("AAPL", IndicatorType.MACD, period=12)
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_indicators.py -v
```

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/indicators_loader.py`：

```python
import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import IndicatorType, Interval
from deepalpha.models.indicators import IndicatorRow


class AbstractTechnicalIndicatorLoader(BaseLoader):
    @abstractmethod
    async def get_indicator(
        self,
        symbol: str,
        indicator: IndicatorType,
        period: int,
        interval: Interval = Interval.ONE_DAY,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[IndicatorRow]: ...
```

- [ ] **Step 4: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/indicators_loader.py`：

```python
import datetime
from typing import Any

from deepalpha.loaders.enums import IndicatorType, Interval
from deepalpha.loaders.indicators_loader import AbstractTechnicalIndicatorLoader
from deepalpha.models.indicators import IndicatorRow
from deepalpha.providers.fmp.errors import FMPError

_FMP_INDICATOR_PATHS: dict[IndicatorType, str] = {
    IndicatorType.SMA:      "sma",
    IndicatorType.EMA:      "ema",
    IndicatorType.DEMA:     "dema",
    IndicatorType.TEMA:     "tema",
    IndicatorType.WMA:      "wma",
    IndicatorType.RSI:      "rsi",
    IndicatorType.ADX:      "adx",
    IndicatorType.WILLIAMS: "williams",
    IndicatorType.STD_DEV:  "standardDeviation",
}

_FMP_INDICATOR_FIELD: dict[IndicatorType, str] = {
    IndicatorType.SMA:      "sma",
    IndicatorType.EMA:      "ema",
    IndicatorType.DEMA:     "dema",
    IndicatorType.TEMA:     "tema",
    IndicatorType.WMA:      "wma",
    IndicatorType.RSI:      "rsi",
    IndicatorType.ADX:      "adx",
    IndicatorType.WILLIAMS: "williams",
    IndicatorType.STD_DEV:  "standardDeviation",
}

_FMP_TIMEFRAME: dict[Interval, str] = {
    Interval.ONE_MIN:     "1min",
    Interval.FIVE_MIN:    "5min",
    Interval.FIFTEEN_MIN: "15min",
    Interval.THIRTY_MIN:  "30min",
    Interval.ONE_HOUR:    "1hour",
    Interval.FOUR_HOUR:   "4hour",
    Interval.ONE_DAY:     "1day",
}


class FMPTechnicalIndicatorLoader(AbstractTechnicalIndicatorLoader):
    """FMP Start 会员技术指标加载器。"""

    async def get_indicator(
        self,
        symbol: str,
        indicator: IndicatorType,
        period: int,
        interval: Interval = Interval.ONE_DAY,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[IndicatorRow]:
        path_segment = _FMP_INDICATOR_PATHS.get(indicator)
        if path_segment is None:
            raise FMPError(
                f"FMP Start 不支持指标 {indicator}，支持的指标: "
                + ", ".join(str(k) for k in _FMP_INDICATOR_PATHS.keys())
            )
        timeframe = _FMP_TIMEFRAME.get(interval, "1day")
        params: dict[str, Any] = {
            "symbol": symbol,
            "periodLength": period,
            "timeframe": timeframe,
        }
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)
        records = await self._get_list(f"/stable/technical-indicators/{path_segment}", **params)
        field_name = _FMP_INDICATOR_FIELD.get(indicator, indicator.value)
        for r in records:
            if field_name in r and "value" not in r:
                r["value"] = r[field_name]
        return self._to_models(records, IndicatorRow)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_indicators.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/indicators_loader.py \
        src/deepalpha/providers/fmp/loaders/indicators_loader.py \
        tests/unit/providers/fmp/loaders/test_indicators.py
git commit -m "refactor: indicators loader returns list[IndicatorRow]"
```

---

## Task 12: Economics Loader（特殊处理）

**Files:**
- Modify: `src/deepalpha/loaders/economics_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/economics_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_economics.py`

> 特殊点：
> 1. 删除 FMP 实现中的私有 `_EconRow` 模型，改用 `IndicatorRow`
> 2. `IndicatorRow.date` 是 `datetime.datetime`，而过滤参数 `start/end` 是 `datetime.date`，需转换后比较
> 3. `AbstractEconomicsLoader` 中原有 `get_available_indicators() -> list[str]` 不变

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_economics.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.models.indicators import IndicatorRow
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.economics_loader import FMPEconomicsLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_cpi_indicator_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"name": "CPI", "date": "2024-03-01", "value": 313.5},
        {"name": "CPI", "date": "2024-02-01", "value": 311.2},
    ])
    loader = FMPEconomicsLoader(client)
    result = await loader.get_indicator("CPI")
    assert isinstance(result, list)
    assert isinstance(result[0], IndicatorRow)
    assert result[0].value == 313.5
    await client.aclose()

@pytest.mark.asyncio
async def test_get_indicator_not_found_returns_empty_list(httpx_mock: HTTPXMock, client):
    from deepalpha.providers.fmp.errors import FMPNotFoundError
    httpx_mock.add_exception(FMPNotFoundError("not found"))
    loader = FMPEconomicsLoader(client)
    result = await loader.get_indicator("UNKNOWN")
    assert result == []
    await client.aclose()

@pytest.mark.asyncio
async def test_get_available_indicators_returns_list(client):
    loader = FMPEconomicsLoader(client)
    indicators = await loader.get_available_indicators()
    assert isinstance(indicators, list)
    assert "CPI" in indicators
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_economics.py -v
```

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/economics_loader.py`：

```python
import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import Interval
from deepalpha.models.indicators import IndicatorRow


class AbstractEconomicsLoader(BaseLoader):
    @abstractmethod
    async def get_indicator(
        self,
        indicator_name: str,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_MONTH,
    ) -> list[IndicatorRow]: ...
    @abstractmethod
    async def get_available_indicators(self) -> list[str]: ...
```

- [ ] **Step 4: 更新 FMP 实现（含日期过滤迁移）**

替换 `src/deepalpha/providers/fmp/loaders/economics_loader.py`：

```python
import datetime

from deepalpha.loaders.economics_loader import AbstractEconomicsLoader
from deepalpha.loaders.enums import Interval
from deepalpha.models.indicators import IndicatorRow

_FMP_SUPPORTED: list[str] = [
    "CPI", "GDP", "REAL_GDP", "UNEMPLOYMENT",
    "FEDERAL_FUNDS_RATE", "TREASURY_YIELD", "RETAIL_SALES",
]


class FMPEconomicsLoader(AbstractEconomicsLoader):
    async def get_indicator(
        self,
        indicator_name: str,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_MONTH,
    ) -> list[IndicatorRow]:
        from deepalpha.providers.fmp.errors import FMPNotFoundError
        try:
            records = await self._get_list(
                "/stable/economics-indicators", name=indicator_name.upper()
            )
        except FMPNotFoundError:
            return []
        models = self._to_models(records, IndicatorRow)
        # IndicatorRow.date 是 datetime.datetime，需转换 date 参数后比较
        if start:
            start_dt = datetime.datetime(start.year, start.month, start.day)
            models = [m for m in models if m.date >= start_dt]
        if end:
            end_dt = datetime.datetime(end.year, end.month, end.day, 23, 59, 59)
            models = [m for m in models if m.date <= end_dt]
        return models

    async def get_available_indicators(self) -> list[str]:
        return list(_FMP_SUPPORTED)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_economics.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/economics_loader.py \
        src/deepalpha/providers/fmp/loaders/economics_loader.py \
        tests/unit/providers/fmp/loaders/test_economics.py
git commit -m "refactor: economics loader returns list[IndicatorRow], remove _EconRow"
```

---

## Task 13: Performance Loader

**Files:**
- Modify: `src/deepalpha/loaders/performance_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/performance_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_performance.py`

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_performance.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import MoverDirection
from deepalpha.models.performance import MarketMover, SectorPE, SectorPerformance
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.performance_loader import FMPMarketPerformanceLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_movers_gainers_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "name": "NVIDIA", "change": 45.0,
        "price": 900.0, "changesPercentage": 5.26, "volume": 30000000,
    }])
    loader = FMPMarketPerformanceLoader(client)
    result = await loader.get_movers(MoverDirection.GAINERS, limit=10)
    assert isinstance(result, list)
    assert isinstance(result[0], MarketMover)
    assert result[0].symbol == "NVDA"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sector_performance_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"sector": "Technology", "changesPercentage": "1.23%"},
        {"sector": "Energy", "changesPercentage": "-0.45%"},
    ])
    loader = FMPMarketPerformanceLoader(client)
    result = await loader.get_sector_performance()
    assert isinstance(result, list)
    assert isinstance(result[0], SectorPerformance)
    assert result[0].sector == "Technology"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sector_pe_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-05-02", "sector": "Technology", "pe": 32.5},
    ])
    loader = FMPMarketPerformanceLoader(client)
    result = await loader.get_sector_pe()
    assert isinstance(result, list)
    assert isinstance(result[0], SectorPE)
    assert result[0].pe == 32.5
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_performance.py -v
```

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/performance_loader.py`：

```python
import datetime
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import MoverDirection
from deepalpha.models.performance import MarketMover, SectorPE, SectorPerformance


class AbstractMarketPerformanceLoader(BaseLoader):
    @abstractmethod
    async def get_movers(
        self, direction: MoverDirection, limit: int = 20
    ) -> list[MarketMover]: ...
    @abstractmethod
    async def get_sector_performance(self, date: datetime.date | None = None) -> list[SectorPerformance]: ...
    @abstractmethod
    async def get_sector_pe(self, date: datetime.date | None = None) -> list[SectorPE]: ...
```

- [ ] **Step 4: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/performance_loader.py`：

```python
"""FMP 市场表现数据加载器实现"""

import datetime

from deepalpha.loaders.enums import MoverDirection
from deepalpha.loaders.performance_loader import AbstractMarketPerformanceLoader
from deepalpha.models.performance import MarketMover, SectorPE, SectorPerformance

_MOVER_PATHS: dict[MoverDirection, str] = {
    MoverDirection.GAINERS: "biggest-gainers",
    MoverDirection.LOSERS:  "biggest-losers",
    MoverDirection.ACTIVE:  "most-actives",
}


class FMPMarketPerformanceLoader(AbstractMarketPerformanceLoader):
    """FMP 市场表现加载器。"""

    async def get_movers(
        self, direction: MoverDirection, limit: int = 20
    ) -> list[MarketMover]:
        path = _MOVER_PATHS[direction]
        records = await self._get_list(f"/stable/{path}", limit=limit)
        return self._to_models(records, MarketMover)

    async def get_sector_performance(self, date: datetime.date | None = None) -> list[SectorPerformance]:
        query_date = date or datetime.date.today()
        records = await self._get_list(
            "/stable/sector-performance-snapshot", date=str(query_date)
        )
        return self._to_models(records, SectorPerformance)

    async def get_sector_pe(self, date: datetime.date | None = None) -> list[SectorPE]:
        query_date = date or datetime.date.today()
        records = await self._get_list(
            "/stable/sector-pe-snapshot", date=str(query_date)
        )
        return self._to_models(records, SectorPE)
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_performance.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/performance_loader.py \
        src/deepalpha/providers/fmp/loaders/performance_loader.py \
        tests/unit/providers/fmp/loaders/test_performance.py
git commit -m "refactor: performance loader returns list[MarketMover/SectorPerformance/SectorPE]"
```

---

## Task 14: Directory Loader

**Files:**
- Modify: `src/deepalpha/loaders/directory_loader.py`
- Modify: `src/deepalpha/providers/fmp/loaders/directory_loader.py`
- Modify: `tests/unit/providers/fmp/loaders/test_directory.py`

- [ ] **Step 1: 更新测试（令其失败）**

替换 `tests/unit/providers/fmp/loaders/test_directory.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.loaders.enums import AssetClass
from deepalpha.models.directory import ExchangeInfo, SymbolInfo
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders.directory_loader import FMPDirectoryLoader


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_symbols_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ",
        "exchangeShortName": "NASDAQ", "type": "stock",
    }])
    loader = FMPDirectoryLoader(client)
    result = await loader.get_symbols(AssetClass.STOCK)
    assert isinstance(result, list)
    assert isinstance(result[0], SymbolInfo)
    assert result[0].symbol == "AAPL"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_exchanges_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "exchange": "NASDAQ", "name": "National Association of Securities Dealers Automated Quotations",
    }])
    loader = FMPDirectoryLoader(client)
    result = await loader.get_exchanges()
    assert isinstance(result, list)
    assert isinstance(result[0], ExchangeInfo)
    assert result[0].exchange == "NASDAQ"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sectors_returns_list_of_strings(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{"sector": "Technology"}, {"sector": "Healthcare"}])
    loader = FMPDirectoryLoader(client)
    sectors = await loader.get_sectors()
    assert isinstance(sectors, list)
    assert "Technology" in sectors
    await client.aclose()

@pytest.mark.asyncio
async def test_get_industries_returns_list_of_strings(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{"industry": "Semiconductors"}])
    loader = FMPDirectoryLoader(client)
    industries = await loader.get_industries()
    assert "Semiconductors" in industries
    await client.aclose()
```

- [ ] **Step 2: 运行确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_directory.py -v
```

- [ ] **Step 3: 更新 abstract loader**

替换 `src/deepalpha/loaders/directory_loader.py`：

```python
from abc import abstractmethod

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass
from deepalpha.models.directory import ExchangeInfo, SymbolInfo


class AbstractDirectoryLoader(BaseLoader):
    @abstractmethod
    async def get_symbols(self, asset_class: AssetClass = AssetClass.STOCK) -> list[SymbolInfo]: ...
    @abstractmethod
    async def get_exchanges(self) -> list[ExchangeInfo]: ...
    @abstractmethod
    async def get_sectors(self) -> list[str]: ...
    @abstractmethod
    async def get_industries(self) -> list[str]: ...
```

- [ ] **Step 4: 更新 FMP 实现**

替换 `src/deepalpha/providers/fmp/loaders/directory_loader.py`：

```python
from deepalpha.loaders.directory_loader import AbstractDirectoryLoader
from deepalpha.loaders.enums import AssetClass
from deepalpha.models.directory import ExchangeInfo, SymbolInfo

_SYMBOL_PATHS: dict[AssetClass, str] = {
    AssetClass.STOCK:       "actively-trading-list",
    AssetClass.ETF:         "ETFs-list",
    AssetClass.INDEX:       "company-symbols-list",
    AssetClass.CRYPTO:      "company-symbols-list",
    AssetClass.FOREX:       "company-symbols-list",
    AssetClass.COMMODITY:   "company-symbols-list",
    AssetClass.MUTUAL_FUND: "company-symbols-list",
}


class FMPDirectoryLoader(AbstractDirectoryLoader):
    """FMP 目录数据加载器。"""

    async def get_symbols(self, asset_class: AssetClass = AssetClass.STOCK) -> list[SymbolInfo]:
        path = _SYMBOL_PATHS.get(asset_class, "company-symbols-list")
        records = await self._get_list(f"/stable/{path}")
        return self._to_models(records, SymbolInfo)

    async def get_exchanges(self) -> list[ExchangeInfo]:
        records = await self._get_list("/stable/available-exchanges")
        return self._to_models(records, ExchangeInfo)

    async def get_sectors(self) -> list[str]:
        records = await self._get_list("/stable/available-sectors")
        return [r.get("sector", "") for r in records if r.get("sector")]

    async def get_industries(self) -> list[str]:
        records = await self._get_list("/stable/available-industries")
        return [r.get("industry", "") for r in records if r.get("industry")]
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_directory.py -v
```

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/directory_loader.py \
        src/deepalpha/providers/fmp/loaders/directory_loader.py \
        tests/unit/providers/fmp/loaders/test_directory.py
git commit -m "refactor: directory loader returns list[SymbolInfo]/list[ExchangeInfo]"
```

---

## Task 15: 删除 `_to_df()` + 更新集成测试

**Files:**
- Modify: `src/deepalpha/loaders/base.py`
- Modify: `tests/integration/test_fmp_integration.py`

- [ ] **Step 1: 确认所有单元测试绿灯**

```bash
uv run pytest tests/unit/ -v
```

预期: 全部 PASSED。如有失败，先修复再继续。

- [ ] **Step 2: 删除 `base.py` 中的 `_to_df()` 方法**

从 `src/deepalpha/loaders/base.py` 中删除整个 `_to_df` 方法（包括 docstring）：

```python
# 删除以下代码块：
def _to_df(
    self, records: list[dict[str, Any]], model: type[BaseModel]
) -> pl.DataFrame:
    """已废弃：请使用 _to_models() + to_dataframe()。保留以兼容迁移期间的旧调用。"""
    if not records:
        return pl.DataFrame()
    clean = [{k: (None if v == "" else v) for k, v in r.items()} for r in records]
    validated = [model.model_validate(r) for r in clean]
    return pl.DataFrame([v.model_dump() for v in validated])
```

删除后，`base.py` 中也不再需要 `import polars as pl`。从 import 区域移除 `import polars as pl`（保留 `from pydantic import BaseModel`，`to_dataframe` 仍然需要它作为 return type hint；`pl.DataFrame` 仍在返回类型中用到，所以保留 `import polars as pl`）。

> 注意：`to_dataframe()` 返回 `pl.DataFrame`，所以 `import polars as pl` 仍然需要保留。只删 `_to_df` 方法本身。

- [ ] **Step 3: 确认单元测试仍然绿灯**

```bash
uv run pytest tests/unit/ -v
```

预期: 全部 PASSED

- [ ] **Step 4: 更新集成测试**

在 `tests/integration/test_fmp_integration.py` 中，将所有对批量方法的 `pl.DataFrame` 断言改为 list 断言。需要修改的典型模式：

```python
# 改前（集成测试示例）
df = await hub.market.get_price_history("NVDA", start=datetime.date(2025, 1, 1), ...)
assert len(df) > 0
assert "close" in df.columns

# 改后
from deepalpha.loaders.base import BaseLoader
from deepalpha.models.market import PriceBar

bars = await hub.market.get_price_history("NVDA", start=datetime.date(2025, 1, 1), ...)
assert len(bars) > 0
assert isinstance(bars[0], PriceBar)
# 如需检查列名，先转换：
df = BaseLoader.to_dataframe(bars)
assert "close" in df.columns
```

具体步骤：
1. 打开 `tests/integration/test_fmp_integration.py`
2. 在文件顶部添加 `from deepalpha.loaders.base import BaseLoader`
3. 逐个 test 函数，将批量方法返回值的变量名从 `df` 改为有意义的名称（`bars`、`trades`、`ratings` 等），并更新断言
4. 凡是需要检查 `.columns` 或做 DataFrame 操作的地方，在断言前加一行 `df = BaseLoader.to_dataframe(result)` 再操作

- [ ] **Step 5: 提交**

```bash
git add src/deepalpha/loaders/base.py \
        tests/integration/test_fmp_integration.py
git commit -m "refactor: remove deprecated _to_df(), update integration tests"
```

- [ ] **Step 6: 运行全量单元测试确认**

```bash
uv run pytest tests/unit/ -v --tb=short
```

预期: 全部 PASSED
