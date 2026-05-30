# FMP Data Loader Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `deepalpha` 建立 FMP 数据加载能力的可测试基础层，包括规范模型基类、抽象 loader 契约、FMP 配置、异步客户端、DataHub 聚合器和首批 Market loader 行为。

**Architecture:** 先实现 provider 无关的 `models/` 与 `loaders/` 契约，再实现 `providers/fmp/` 的 HTTP 客户端和 DataHub。第一阶段只落地通用基础设施与 Market loader 的可运行实现，其他 12 类 loader 先以抽象契约和 FMP 类骨架接入，后续按类别拆分计划补全字段映射。

**Tech Stack:** Python 3.11、Pydantic v2、pydantic-settings、httpx、Polars、pytest、pytest-asyncio、pytest-httpx、ruff、mypy。

---

## 范围说明

设计文档覆盖 FMP Start 会员全部数据类别，包含 13 个 loader、几十个端点和大量字段映射。为了让每次执行都能独立验证，本计划只实现“基础架构 + Market loader 第一条纵切”：

- 规范模型公共基类与首批 Market 模型。
- provider 无关枚举、BaseLoader、AbstractDataHub 与全部抽象 loader 方法签名。
- FMPConfig、FMPAsyncClient、错误类型、重试和状态码处理。
- FMPDataHub 聚合所有 loader。
- FMPMarketLoader 的 quote、批量 quote、历史价格、市场快照。
- 其他 FMP loader 创建类骨架，继承对应抽象类，但不在本阶段实例化为可用业务实现。

后续建议为 Financial、Company、Analyst、Calendar、News、Extended loaders 分别创建独立计划。

## 文件结构

- Create: `src/deepalpha/models/base.py`：规范模型基类，统一 Pydantic 配置。
- Create: `src/deepalpha/models/market.py`：Quote、PriceBar、MarketSnapshotRecord。
- Modify: `src/deepalpha/models/__init__.py`：导出模型。
- Create: `src/deepalpha/loaders/enums.py`：共享枚举。
- Create: `src/deepalpha/loaders/base.py`：AsyncDataClient、BaseLoader、响应解析工具。
- Create: `src/deepalpha/loaders/hub.py`：AbstractDataHub Protocol。
- Create: `src/deepalpha/loaders/market.py`：AbstractMarketLoader。
- Create: `src/deepalpha/loaders/financial.py`、`company.py`、`analyst.py`、`calendar.py`、`news.py`、`indicators.py`、`economics.py`、`insider.py`、`filings.py`、`performance.py`、`congress.py`、`directory.py`：抽象接口签名。
- Modify: `src/deepalpha/loaders/__init__.py`：导出抽象接口和枚举。
- Create: `src/deepalpha/providers/fmp/errors.py`：FMP 异常类型。
- Create: `src/deepalpha/providers/fmp/config.py`：FMPConfig。
- Create: `src/deepalpha/providers/fmp/client.py`：FMPAsyncClient。
- Create: `src/deepalpha/providers/fmp/loaders/market.py`：FMPMarketLoader。
- Create: `src/deepalpha/providers/fmp/loaders/stubs.py`：本阶段未实现的 FMP loader 类骨架。
- Create: `src/deepalpha/providers/fmp/loaders/__init__.py`：导出 FMP loaders。
- Create: `src/deepalpha/providers/fmp/__init__.py`：FMPDataHub。
- Modify: `src/deepalpha/__init__.py`：导出公开入口。
- Create: `tests/models/test_market_models.py`：模型字段元数据测试。
- Create: `tests/loaders/test_base_loader.py`：BaseLoader 响应解析测试。
- Create: `tests/providers/fmp/test_client.py`：HTTP 客户端错误和重试测试。
- Create: `tests/providers/fmp/test_market_loader.py`：Market loader endpoint 映射测试。
- Create: `tests/providers/fmp/test_data_hub.py`：DataHub 属性和上下文管理测试。

---

### Task 1: 测试依赖与基础目录

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/conftest.py`

- [ ] **Step 1: 添加测试依赖**

修改 `pyproject.toml` 的 `[project.optional-dependencies].dev`，确保包含：

```toml
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "pytest-httpx>=0.30.0",
    "ruff>=0.3.0",
    "mypy>=1.8.0",
]
```

- [ ] **Step 2: 添加 pytest 异步配置**

在 `pyproject.toml` 末尾加入：

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: requires a real provider API key",
]
```

- [ ] **Step 3: 创建测试配置文件**

创建 `tests/conftest.py`：

```python
"""测试公共配置。"""
```

- [ ] **Step 4: 安装开发依赖**

Run: `uv sync --extra dev`

Expected: 命令退出码为 0，`pytest-httpx` 被写入 `uv.lock`。

- [ ] **Step 5: 运行空测试基线**

Run: `uv run pytest -q`

Expected: 如果尚无测试，输出 `no tests ran` 或退出码 5；这是可接受基线，后续任务会添加测试。

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock tests/conftest.py
git commit -m "test: configure async provider tests"
```

---

### Task 2: 规范模型基类与 Market 模型

**Files:**
- Create: `src/deepalpha/models/base.py`
- Create: `src/deepalpha/models/market.py`
- Create: `src/deepalpha/models/__init__.py`
- Test: `tests/models/test_market_models.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/models/test_market_models.py`：

```python
from deepalpha.models import MarketSnapshotRecord, PriceBar, Quote


def assert_all_fields_have_chinese_metadata(model_type: type) -> None:
    schema = model_type.model_json_schema()
    for field_name, field_schema in schema["properties"].items():
        assert field_schema.get("title"), field_name
        assert field_schema.get("description"), field_name


def test_market_models_have_chinese_field_metadata() -> None:
    assert_all_fields_have_chinese_metadata(Quote)
    assert_all_fields_have_chinese_metadata(PriceBar)
    assert_all_fields_have_chinese_metadata(MarketSnapshotRecord)


def test_quote_accepts_provider_aliases() -> None:
    quote = Quote.model_validate(
        {
            "symbol": "AAPL",
            "price": 190.5,
            "change": 1.2,
            "changePercentage": 0.63,
            "volume": 1200000,
            "marketCap": 2900000000000,
            "pe": 29.3,
            "eps": 6.5,
            "timestamp": 1710000000,
        }
    )

    assert quote.symbol == "AAPL"
    assert quote.change_percent == 0.63
    assert quote.market_cap == 2900000000000
    assert quote.pe_ratio == 29.3
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/models/test_market_models.py -q`

Expected: FAIL，报错包含 `No module named 'deepalpha.models'` 或 `cannot import name 'Quote'`。

- [ ] **Step 3: 实现模型基类**

创建 `src/deepalpha/models/base.py`：

```python
from pydantic import BaseModel, ConfigDict


class DeepAlphaModel(BaseModel):
    """DeepAlpha 规范数据模型基类。"""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")
```

- [ ] **Step 4: 实现 Market 模型**

创建 `src/deepalpha/models/market.py`：

```python
from datetime import date, datetime

from pydantic import Field

from deepalpha.models.base import DeepAlphaModel


class Quote(DeepAlphaModel):
    """标的实时报价。"""

    symbol: str = Field(title="标的代码", description="交易所上市或交易代码，如 AAPL。")
    price: float = Field(title="最新价格", description="最近一次成交价格。")
    change: float | None = Field(None, title="涨跌额", description="相对上一收盘价的价格变动。")
    change_percent: float | None = Field(
        None,
        alias="changePercentage",
        title="涨跌幅",
        description="涨跌额占上一收盘价的百分比。",
    )
    volume: int | None = Field(None, title="成交量", description="当日已成交数量。")
    market_cap: float | None = Field(
        None,
        alias="marketCap",
        title="市值",
        description="标的总市值。",
    )
    pe_ratio: float | None = Field(None, alias="pe", title="市盈率", description="Price/Earnings 比率。")
    eps: float | None = Field(None, title="每股收益", description="Earnings Per Share。")
    timestamp: int | datetime | None = Field(None, title="时间戳", description="报价生成时间。")


class PriceBar(DeepAlphaModel):
    """历史价格 K 线。"""

    date: date | datetime = Field(title="日期时间", description="价格记录对应的交易日期或时间。")
    open: float = Field(title="开盘价", description="该周期第一笔成交价格。")
    high: float = Field(title="最高价", description="该周期最高成交价格。")
    low: float = Field(title="最低价", description="该周期最低成交价格。")
    close: float = Field(title="收盘价", description="该周期最后一笔成交价格。")
    volume: int | None = Field(None, title="成交量", description="该周期成交数量。")
    adj_close: float | None = Field(
        None,
        alias="adjClose",
        title="复权收盘价",
        description="考虑分红拆股后的收盘价。",
    )


class MarketSnapshotRecord(Quote):
    """市场快照中的单条标的记录。"""

    name: str | None = Field(None, title="标的名称", description="公司、基金或资产名称。")
    exchange: str | None = Field(None, title="交易所", description="标的所在交易所代码或名称。")
```

- [ ] **Step 5: 导出模型**

创建 `src/deepalpha/models/__init__.py`：

```python
from deepalpha.models.base import DeepAlphaModel
from deepalpha.models.market import MarketSnapshotRecord, PriceBar, Quote

__all__ = [
    "DeepAlphaModel",
    "MarketSnapshotRecord",
    "PriceBar",
    "Quote",
]
```

- [ ] **Step 6: 运行测试确认通过**

Run: `uv run pytest tests/models/test_market_models.py -q`

Expected: PASS，输出 `2 passed`。

- [ ] **Step 7: Commit**

```bash
git add src/deepalpha/models tests/models/test_market_models.py
git commit -m "feat: add market data models"
```

---

### Task 3: provider 无关 loader 契约

**Files:**
- Create: `src/deepalpha/loaders/enums.py`
- Create: `src/deepalpha/loaders/base.py`
- Create: `src/deepalpha/loaders/hub.py`
- Create: `src/deepalpha/loaders/market.py`
- Create: `src/deepalpha/loaders/financial.py`
- Create: `src/deepalpha/loaders/company.py`
- Create: `src/deepalpha/loaders/analyst.py`
- Create: `src/deepalpha/loaders/calendar.py`
- Create: `src/deepalpha/loaders/news.py`
- Create: `src/deepalpha/loaders/indicators.py`
- Create: `src/deepalpha/loaders/economics.py`
- Create: `src/deepalpha/loaders/insider.py`
- Create: `src/deepalpha/loaders/filings.py`
- Create: `src/deepalpha/loaders/performance.py`
- Create: `src/deepalpha/loaders/congress.py`
- Create: `src/deepalpha/loaders/directory.py`
- Create: `src/deepalpha/loaders/__init__.py`
- Test: `tests/loaders/test_base_loader.py`

- [ ] **Step 1: 写 BaseLoader 失败测试**

创建 `tests/loaders/test_base_loader.py`：

```python
import polars as pl
import pytest

from deepalpha.loaders.base import BaseLoader
from deepalpha.models import Quote


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    async def get(self, path: str, **params):
        return self.payload


class ConcreteLoader(BaseLoader):
    pass


@pytest.mark.asyncio
async def test_get_returns_first_dict_from_single_item_list() -> None:
    loader = ConcreteLoader(FakeClient([{"symbol": "AAPL"}]))

    result = await loader._get("/quote/AAPL")

    assert result == {"symbol": "AAPL"}


@pytest.mark.asyncio
async def test_get_list_requires_list_response() -> None:
    loader = ConcreteLoader(FakeClient({"symbol": "AAPL"}))

    with pytest.raises(TypeError, match="list"):
        await loader._get_list("/quote/AAPL")


def test_to_df_validates_records_with_model() -> None:
    loader = ConcreteLoader(FakeClient([]))

    frame = loader._to_df(
        [{"symbol": "AAPL", "price": 190.5, "change": 1.2, "changePercentage": 0.63}],
        Quote,
    )

    assert isinstance(frame, pl.DataFrame)
    assert frame.select("symbol").item() == "AAPL"
    assert frame.select("change_percent").item() == 0.63
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/loaders/test_base_loader.py -q`

Expected: FAIL，报错包含 `No module named 'deepalpha.loaders'`。

- [ ] **Step 3: 实现枚举**

创建 `src/deepalpha/loaders/enums.py`：

```python
from enum import StrEnum


class AssetClass(StrEnum):
    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    MUTUAL_FUND = "mutual_fund"


class Interval(StrEnum):
    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN = "30m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1mo"


class StatementPeriod(StrEnum):
    ANNUAL = "annual"
    QUARTER = "quarter"
    TTM = "ttm"


class IndicatorType(StrEnum):
    SMA = "sma"
    EMA = "ema"
    DEMA = "dema"
    TEMA = "tema"
    WMA = "wma"
    RSI = "rsi"
    MACD = "macd"
    STOCH = "stoch"
    CCI = "cci"
    WILLIAMS = "williams"
    ADX = "adx"
    AROON = "aroon"
    BBANDS = "bbands"
    ATR = "atr"
    STD_DEV = "std_dev"
    OBV = "obv"


class MoverDirection(StrEnum):
    GAINERS = "gainers"
    LOSERS = "losers"
    ACTIVE = "active"


class CongressChamber(StrEnum):
    SENATE = "senate"
    HOUSE = "house"
```

- [ ] **Step 4: 实现 BaseLoader**

创建 `src/deepalpha/loaders/base.py`：

```python
from abc import ABC
from typing import Any, Protocol

import polars as pl
from pydantic import BaseModel


class AsyncDataClient(Protocol):
    """任意异步数据客户端需实现的最小接口。"""

    async def get(self, path: str, **params: Any) -> Any:
        """发起 GET 请求并返回已解析 JSON。"""


class BaseLoader(ABC):
    """所有数据加载器的通用基类。"""

    def __init__(self, client: AsyncDataClient) -> None:
        self._client = client

    async def _get(self, endpoint: str, **params: Any) -> dict[str, Any]:
        payload = await self._client.get(endpoint, **params)
        if isinstance(payload, list):
            if not payload:
                raise ValueError("empty response")
            first = payload[0]
            if not isinstance(first, dict):
                raise TypeError("single-object response list must contain dict items")
            return first
        if isinstance(payload, dict):
            return payload
        raise TypeError("single-object response must be dict or list[dict]")

    async def _get_list(self, endpoint: str, **params: Any) -> list[dict[str, Any]]:
        payload = await self._client.get(endpoint, **params)
        if not isinstance(payload, list):
            raise TypeError("list response must be list[dict]")
        if not all(isinstance(item, dict) for item in payload):
            raise TypeError("list response must contain dict items")
        return payload

    def _to_df(self, records: list[dict[str, Any]], model: type[BaseModel]) -> pl.DataFrame:
        validated = [model.model_validate(record) for record in records]
        return pl.DataFrame([item.model_dump() for item in validated])
```

- [ ] **Step 5: 实现抽象接口文件**

创建 `src/deepalpha/loaders/market.py`，其余抽象文件按照设计文档的签名逐一创建；每个方法必须使用 `@abstractmethod`，返回类型必须与设计文档一致。Market 文件内容：

```python
from abc import abstractmethod
from datetime import date

import polars as pl

from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass, Interval
from deepalpha.models import Quote


class AbstractMarketLoader(BaseLoader):
    """行情数据加载器抽象基类。"""

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        """获取单个标的实时报价。"""

    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> pl.DataFrame:
        """批量获取多个标的实时报价。"""

    @abstractmethod
    async def get_price_history(
        self,
        symbol: str,
        start: date,
        end: date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> pl.DataFrame:
        """获取历史 OHLCV 数据。"""

    @abstractmethod
    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> pl.DataFrame:
        """获取指定资产类别的市场快照。"""
```

- [ ] **Step 6: 实现 hub 协议与导出**

创建 `src/deepalpha/loaders/hub.py`：

```python
from typing import Protocol, runtime_checkable

from deepalpha.loaders.analyst import AbstractAnalystLoader
from deepalpha.loaders.calendar import AbstractCalendarLoader
from deepalpha.loaders.company import AbstractCompanyLoader
from deepalpha.loaders.financial import AbstractFinancialLoader
from deepalpha.loaders.market import AbstractMarketLoader
from deepalpha.loaders.news import AbstractNewsLoader


@runtime_checkable
class AbstractDataHub(Protocol):
    """所有 provider DataHub 必须实现的 Core loader 集合。"""

    market: AbstractMarketLoader
    financial: AbstractFinancialLoader
    company: AbstractCompanyLoader
    analyst: AbstractAnalystLoader
    calendar: AbstractCalendarLoader
    news: AbstractNewsLoader

    async def __aenter__(self) -> "AbstractDataHub":
        """进入异步上下文。"""

    async def __aexit__(self, *args: object) -> None:
        """退出异步上下文并释放资源。"""
```

创建 `src/deepalpha/loaders/__init__.py`：

```python
from deepalpha.loaders.base import AsyncDataClient, BaseLoader
from deepalpha.loaders.enums import (
    AssetClass,
    CongressChamber,
    IndicatorType,
    Interval,
    MoverDirection,
    StatementPeriod,
)
from deepalpha.loaders.hub import AbstractDataHub
from deepalpha.loaders.market import AbstractMarketLoader

__all__ = [
    "AbstractDataHub",
    "AbstractMarketLoader",
    "AssetClass",
    "AsyncDataClient",
    "BaseLoader",
    "CongressChamber",
    "IndicatorType",
    "Interval",
    "MoverDirection",
    "StatementPeriod",
]
```

- [ ] **Step 7: 运行测试确认通过**

Run: `uv run pytest tests/loaders/test_base_loader.py -q`

Expected: PASS，输出 `3 passed`。

- [ ] **Step 8: 运行静态检查**

Run: `uv run ruff check src/deepalpha/loaders src/deepalpha/models tests/loaders tests/models`

Expected: PASS，无 lint 错误。

- [ ] **Step 9: Commit**

```bash
git add src/deepalpha/loaders tests/loaders
git commit -m "feat: add provider neutral loader contracts"
```

---

### Task 4: FMP 配置、错误和异步客户端

**Files:**
- Create: `src/deepalpha/providers/fmp/errors.py`
- Create: `src/deepalpha/providers/fmp/config.py`
- Create: `src/deepalpha/providers/fmp/client.py`
- Test: `tests/providers/fmp/test_client.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/providers/fmp/test_client.py`：

```python
import pytest

from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.errors import FMPAuthError, FMPNotFoundError, FMPRateLimitError


def make_config() -> FMPConfig:
    return FMPConfig(api_key="test-key", base_url="https://example.test/api", max_retries=1)


@pytest.mark.asyncio
async def test_client_appends_api_key(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://example.test/api/stable/quote/AAPL?symbol=AAPL&apikey=test-key",
        json=[{"symbol": "AAPL"}],
    )

    async with FMPAsyncClient(make_config()) as client:
        payload = await client.get("/stable/quote/AAPL", symbol="AAPL")

    assert payload == [{"symbol": "AAPL"}]


@pytest.mark.asyncio
async def test_client_raises_auth_error(httpx_mock) -> None:
    httpx_mock.add_response(status_code=401, json={"Error Message": "bad key"})

    async with FMPAsyncClient(make_config()) as client:
        with pytest.raises(FMPAuthError):
            await client.get("/stable/quote/AAPL")


@pytest.mark.asyncio
async def test_client_raises_not_found_for_empty_list(httpx_mock) -> None:
    httpx_mock.add_response(json=[])

    async with FMPAsyncClient(make_config()) as client:
        with pytest.raises(FMPNotFoundError):
            await client.get("/stable/quote/MISSING")


@pytest.mark.asyncio
async def test_client_raises_rate_limit_error_after_retry(httpx_mock) -> None:
    httpx_mock.add_response(status_code=429, headers={"Retry-After": "0"}, json={"message": "slow"})
    httpx_mock.add_response(status_code=429, headers={"Retry-After": "0"}, json={"message": "slow"})

    async with FMPAsyncClient(make_config()) as client:
        with pytest.raises(FMPRateLimitError):
            await client.get("/stable/quote/AAPL")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/providers/fmp/test_client.py -q`

Expected: FAIL，报错包含 `No module named 'deepalpha.providers'`。

- [ ] **Step 3: 实现错误类型**

创建 `src/deepalpha/providers/fmp/errors.py`：

```python
class FMPError(Exception):
    """FMP provider 异常基类。"""


class FMPAuthError(FMPError):
    """API Key 无效或过期。"""


class FMPRateLimitError(FMPError):
    """请求触发 FMP 速率限制。"""


class FMPNotFoundError(FMPError):
    """请求资源不存在或 FMP 返回空列表。"""


class FMPServerError(FMPError):
    """FMP 服务端错误。"""
```

- [ ] **Step 4: 实现配置**

创建 `src/deepalpha/providers/fmp/config.py`：

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FMPConfig(BaseSettings):
    """FMP provider 配置。"""

    api_key: str = Field(title="API 密钥", description="FMP API Key，从环境变量 FMP_API_KEY 读取。")
    base_url: str = Field("https://financialmodelingprep.com/api", title="API 基础地址")
    timeout: float = Field(30.0, title="超时时间", description="单次请求超时秒数。")
    max_connections: int = Field(10, title="最大并发连接数")
    max_retries: int = Field(3, title="最大重试次数", description="5xx 或 429 的最大重试次数。")

    model_config = SettingsConfigDict(env_prefix="FMP_", env_file=".env")
```

- [ ] **Step 5: 实现客户端**

创建 `src/deepalpha/providers/fmp/client.py`：

```python
import asyncio
from typing import Any

import httpx

from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.errors import (
    FMPAuthError,
    FMPNotFoundError,
    FMPRateLimitError,
    FMPServerError,
)


class FMPAsyncClient:
    """FMP 异步 HTTP 客户端。"""

    def __init__(self, config: FMPConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url.rstrip("/") + "/",
            timeout=config.timeout,
            limits=httpx.Limits(max_connections=config.max_connections),
        )

    async def get(self, path: str, **params: Any) -> Any:
        request_params = {**params, "apikey": self._config.api_key}
        normalized_path = path.lstrip("/")
        last_response: httpx.Response | None = None

        for attempt in range(self._config.max_retries + 1):
            response = await self._client.get(normalized_path, params=request_params)
            last_response = response
            if response.status_code == 429 and attempt < self._config.max_retries:
                await asyncio.sleep(float(response.headers.get("Retry-After", "1")))
                continue
            if 500 <= response.status_code < 600 and attempt < self._config.max_retries:
                await asyncio.sleep(2**attempt)
                continue
            break

        assert last_response is not None
        self._raise_for_status(last_response)
        payload = last_response.json()
        if payload == []:
            raise FMPNotFoundError("FMP returned an empty list")
        return payload

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "FMPAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            raise FMPAuthError(response.text)
        if response.status_code == 404:
            raise FMPNotFoundError(response.text)
        if response.status_code == 429:
            raise FMPRateLimitError(response.text)
        if 500 <= response.status_code < 600:
            raise FMPServerError(response.text)
        response.raise_for_status()
```

- [ ] **Step 6: 运行测试确认通过**

Run: `uv run pytest tests/providers/fmp/test_client.py -q`

Expected: PASS，输出 `4 passed`。

- [ ] **Step 7: Commit**

```bash
git add src/deepalpha/providers/fmp/errors.py src/deepalpha/providers/fmp/config.py src/deepalpha/providers/fmp/client.py tests/providers/fmp/test_client.py
git commit -m "feat: add fmp async client"
```

---

### Task 5: FMPMarketLoader 首条纵切

**Files:**
- Create: `src/deepalpha/providers/fmp/loaders/market.py`
- Create: `src/deepalpha/providers/fmp/loaders/__init__.py`
- Test: `tests/providers/fmp/test_market_loader.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/providers/fmp/test_market_loader.py`：

```python
from datetime import date

import pytest

from deepalpha.loaders import AssetClass, Interval
from deepalpha.providers.fmp.loaders import FMPMarketLoader


class FakeClient:
    def __init__(self):
        self.calls = []

    async def get(self, path: str, **params):
        self.calls.append((path, params))
        if "historical-price-eod-full" in path:
            return [{"date": "2024-01-02", "open": 10, "high": 11, "low": 9, "close": 10.5}]
        return [{"symbol": "AAPL", "price": 190.5, "change": 1.2, "changePercentage": 0.63}]


@pytest.mark.asyncio
async def test_get_quote_uses_stable_quote_endpoint() -> None:
    client = FakeClient()
    loader = FMPMarketLoader(client)

    quote = await loader.get_quote("AAPL")

    assert quote.symbol == "AAPL"
    assert client.calls == [("/stable/quote/AAPL", {})]


@pytest.mark.asyncio
async def test_get_quotes_uses_batch_endpoint() -> None:
    client = FakeClient()
    loader = FMPMarketLoader(client)

    frame = await loader.get_quotes(["AAPL", "MSFT"])

    assert frame.height == 1
    assert client.calls == [("/stable/quotes-batch", {"symbols": "AAPL,MSFT"})]


@pytest.mark.asyncio
async def test_get_price_history_uses_daily_endpoint() -> None:
    client = FakeClient()
    loader = FMPMarketLoader(client)

    frame = await loader.get_price_history(
        "AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        interval=Interval.ONE_DAY,
        adjusted=True,
    )

    assert frame.height == 1
    assert client.calls == [
        (
            "/stable/historical-price-eod-full",
            {"symbol": "AAPL", "from": "2024-01-01", "to": "2024-01-31"},
        )
    ]


@pytest.mark.asyncio
async def test_get_market_snapshot_routes_crypto() -> None:
    client = FakeClient()
    loader = FMPMarketLoader(client)

    await loader.get_market_snapshot(AssetClass.CRYPTO)

    assert client.calls == [("/stable/full-cryptocurrency-quotes", {})]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/providers/fmp/test_market_loader.py -q`

Expected: FAIL，报错包含 `cannot import name 'FMPMarketLoader'`。

- [ ] **Step 3: 实现 Market loader**

创建 `src/deepalpha/providers/fmp/loaders/market.py`：

```python
from datetime import date

import polars as pl

from deepalpha.loaders import AssetClass, Interval
from deepalpha.loaders.market import AbstractMarketLoader
from deepalpha.models import MarketSnapshotRecord, PriceBar, Quote


class FMPMarketLoader(AbstractMarketLoader):
    """FMP 行情数据加载器。"""

    async def get_quote(self, symbol: str) -> Quote:
        payload = await self._get(f"/stable/quote/{symbol}")
        return Quote.model_validate(payload)

    async def get_quotes(self, symbols: list[str]) -> pl.DataFrame:
        records = await self._get_list("/stable/quotes-batch", symbols=",".join(symbols))
        return self._to_df(records, Quote)

    async def get_price_history(
        self,
        symbol: str,
        start: date,
        end: date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> pl.DataFrame:
        endpoint = self._history_endpoint(interval, adjusted)
        params = {"symbol": symbol, "from": start.isoformat()}
        if end is not None:
            params["to"] = end.isoformat()
        records = await self._get_list(endpoint, **params)
        return self._to_df(records, PriceBar)

    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> pl.DataFrame:
        endpoint = self._snapshot_endpoint(asset_class)
        records = await self._get_list(endpoint)
        return self._to_df(records, MarketSnapshotRecord)

    def _history_endpoint(self, interval: Interval, adjusted: bool) -> str:
        if interval == Interval.ONE_DAY:
            if adjusted:
                return "/stable/historical-price-eod-full"
            return "/stable/historical-price-eod-non-split-adjusted"
        mapping = {
            Interval.ONE_MIN: "/stable/intraday-1-min",
            Interval.FIVE_MIN: "/stable/intraday-5-min",
            Interval.FIFTEEN_MIN: "/stable/intraday-15-min",
            Interval.THIRTY_MIN: "/stable/intraday-30-min",
            Interval.ONE_HOUR: "/stable/intraday-1-hour",
            Interval.FOUR_HOUR: "/stable/intraday-4-hour",
        }
        if interval not in mapping:
            raise ValueError(f"FMP does not support interval: {interval}")
        return mapping[interval]

    def _snapshot_endpoint(self, asset_class: AssetClass) -> str:
        mapping = {
            AssetClass.STOCK: "/stable/full-exchange-quotes",
            AssetClass.ETF: "/stable/full-etf-quotes",
            AssetClass.CRYPTO: "/stable/full-cryptocurrency-quotes",
            AssetClass.FOREX: "/stable/full-forex-quotes",
            AssetClass.COMMODITY: "/stable/full-commodity-quotes",
            AssetClass.INDEX: "/stable/full-index-quotes",
            AssetClass.MUTUAL_FUND: "/stable/full-mutual-fund-quotes",
        }
        return mapping[asset_class]
```

- [ ] **Step 4: 导出 loader**

创建 `src/deepalpha/providers/fmp/loaders/__init__.py`：

```python
from deepalpha.providers.fmp.loaders.market import FMPMarketLoader

__all__ = ["FMPMarketLoader"]
```

- [ ] **Step 5: 运行测试确认通过**

Run: `uv run pytest tests/providers/fmp/test_market_loader.py -q`

Expected: PASS，输出 `4 passed`。

- [ ] **Step 6: Commit**

```bash
git add src/deepalpha/providers/fmp/loaders tests/providers/fmp/test_market_loader.py
git commit -m "feat: add fmp market loader"
```

---

### Task 6: FMPDataHub 与公开入口

**Files:**
- Create: `src/deepalpha/providers/fmp/loaders/stubs.py`
- Modify: `src/deepalpha/providers/fmp/loaders/__init__.py`
- Create: `src/deepalpha/providers/fmp/__init__.py`
- Modify: `src/deepalpha/__init__.py`
- Test: `tests/providers/fmp/test_data_hub.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/providers/fmp/test_data_hub.py`：

```python
from deepalpha.loaders import AbstractDataHub
from deepalpha.providers.fmp import FMPConfig, FMPDataHub


def test_fmp_data_hub_exposes_core_and_extended_loaders() -> None:
    hub = FMPDataHub(FMPConfig(api_key="test-key"))

    assert isinstance(hub, AbstractDataHub)
    assert hub.market is not None
    assert hub.financial is not None
    assert hub.company is not None
    assert hub.analyst is not None
    assert hub.calendar is not None
    assert hub.news is not None
    assert hub.indicators is not None
    assert hub.economics is not None
    assert hub.insider is not None
    assert hub.filings is not None
    assert hub.performance is not None
    assert hub.congress is not None
    assert hub.directory is not None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/providers/fmp/test_data_hub.py -q`

Expected: FAIL，报错包含 `cannot import name 'FMPDataHub'`。

- [ ] **Step 3: 创建未实现 loader 类骨架**

创建 `src/deepalpha/providers/fmp/loaders/stubs.py`：

```python
from deepalpha.loaders.analyst import AbstractAnalystLoader
from deepalpha.loaders.calendar import AbstractCalendarLoader
from deepalpha.loaders.company import AbstractCompanyLoader
from deepalpha.loaders.congress import AbstractCongressTradeLoader
from deepalpha.loaders.directory import AbstractDirectoryLoader
from deepalpha.loaders.economics import AbstractEconomicsLoader
from deepalpha.loaders.filings import AbstractSecFilingLoader
from deepalpha.loaders.financial import AbstractFinancialLoader
from deepalpha.loaders.indicators import AbstractTechnicalIndicatorLoader
from deepalpha.loaders.insider import AbstractInsiderTradeLoader
from deepalpha.loaders.news import AbstractNewsLoader
from deepalpha.loaders.performance import AbstractMarketPerformanceLoader


class FMPFinancialLoader(AbstractFinancialLoader):
    """FMP 财务数据加载器。"""


class FMPCompanyLoader(AbstractCompanyLoader):
    """FMP 公司基础信息加载器。"""


class FMPAnalystLoader(AbstractAnalystLoader):
    """FMP 分析师数据加载器。"""


class FMPCalendarLoader(AbstractCalendarLoader):
    """FMP 市场日历加载器。"""


class FMPNewsLoader(AbstractNewsLoader):
    """FMP 新闻加载器。"""


class FMPTechnicalIndicatorLoader(AbstractTechnicalIndicatorLoader):
    """FMP 技术指标加载器。"""


class FMPEconomicsLoader(AbstractEconomicsLoader):
    """FMP 宏观经济数据加载器。"""


class FMPInsiderTradeLoader(AbstractInsiderTradeLoader):
    """FMP 内部人交易加载器。"""


class FMPSecFilingLoader(AbstractSecFilingLoader):
    """FMP SEC 文件加载器。"""


class FMPMarketPerformanceLoader(AbstractMarketPerformanceLoader):
    """FMP 市场表现加载器。"""


class FMPCongressTradeLoader(AbstractCongressTradeLoader):
    """FMP 国会交易披露加载器。"""


class FMPDirectoryLoader(AbstractDirectoryLoader):
    """FMP 参考目录加载器。"""
```

- [ ] **Step 4: 如果抽象类导致骨架不可实例化，调整本任务**

运行 `uv run pytest tests/providers/fmp/test_data_hub.py -q`。如果失败信息包含 `Can't instantiate abstract class`，不要取消抽象约束；改为在本任务中只实例化已经实现的 `market`，并让未实现 loader 在 DataHub 上暴露为 `None`。同时把测试断言改为：

```python
assert hub.market is not None
assert hub.financial is None
assert hub.company is None
assert hub.analyst is None
assert hub.calendar is None
assert hub.news is None
assert hub.indicators is None
assert hub.economics is None
assert hub.insider is None
assert hub.filings is None
assert hub.performance is None
assert hub.congress is None
assert hub.directory is None
```

- [ ] **Step 5: 实现 DataHub**

创建 `src/deepalpha/providers/fmp/__init__.py`：

```python
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.loaders import FMPMarketLoader


class FMPDataHub:
    """FMP 数据中枢。"""

    def __init__(self, config: FMPConfig | None = None) -> None:
        cfg = config or FMPConfig()
        self._client = FMPAsyncClient(cfg)
        self.market = FMPMarketLoader(self._client)
        self.financial = None
        self.company = None
        self.analyst = None
        self.calendar = None
        self.news = None
        self.indicators = None
        self.economics = None
        self.insider = None
        self.filings = None
        self.performance = None
        self.congress = None
        self.directory = None

    async def __aenter__(self) -> "FMPDataHub":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.aclose()


__all__ = ["FMPConfig", "FMPDataHub"]
```

- [ ] **Step 6: 修改公开入口**

修改 `src/deepalpha/__init__.py`：

```python
from deepalpha.providers.fmp import FMPConfig, FMPDataHub

__all__ = ["FMPConfig", "FMPDataHub"]
```

- [ ] **Step 7: 运行测试确认通过**

Run: `uv run pytest tests/providers/fmp/test_data_hub.py -q`

Expected: PASS，输出 `1 passed`。

- [ ] **Step 8: 运行全量测试和检查**

Run: `uv run pytest -q`

Expected: PASS，所有测试通过。

Run: `uv run ruff check src tests`

Expected: PASS，无 lint 错误。

- [ ] **Step 9: Commit**

```bash
git add src/deepalpha/__init__.py src/deepalpha/providers tests/providers/fmp/test_data_hub.py
git commit -m "feat: expose fmp data hub"
```

---

## Self-Review

**Spec coverage:** 本计划覆盖设计文档中的分层目录、BaseLoader、枚举、AbstractDataHub、FMPConfig、FMPAsyncClient、错误处理、MarketLoader 首条纵切和模型元数据测试。完整 Financial、Company、Analyst、Calendar、News、TechnicalIndicator、Economics、Insider、Filings、Performance、Congress、Directory 的字段模型和 endpoint 映射没有纳入本计划，原因是它们是可独立实现和验证的子系统，应拆成后续计划。

**Placeholder scan:** 本计划没有使用 `TBD`、`TODO`、`implement later`、`fill in details`。未完成范围明确标为后续独立计划，不作为本计划任务的占位实现。

**Type consistency:** `Quote`、`PriceBar`、`MarketSnapshotRecord` 在 Task 2 定义，并在 Task 3 和 Task 5 使用。`AssetClass`、`Interval` 在 Task 3 定义，并在 Task 5 使用。`FMPConfig`、`FMPAsyncClient` 在 Task 4 定义，并在 Task 6 使用。`FMPDataHub` 在 Task 6 导出。

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-30-fmp-data-loader-foundation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** - execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
