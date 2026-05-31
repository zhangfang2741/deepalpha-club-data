# FMP 数据加载器基础层实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `deepalpha` 包中构建 FMP Start 会员完整数据加载能力，覆盖 13 个数据类别、分层解耦的 abstract loader 接口与 FMP 具体实现。

**Architecture:** models/ 层定义 provider 无关的 Pydantic 数据模型；loaders/ 层定义各类别 Abstract Loader ABC 和 AbstractDataHub Protocol；providers/fmp/ 层实现 FMPAsyncClient（httpx + 重试）和各 FMP Loader，通过 FMPDataHub 聚合。单条查询返回 Pydantic 对象，批量查询返回 Polars DataFrame。

**Tech Stack:** Python 3.11+, pydantic v2, pydantic-settings, httpx (async), polars, pytest, pytest-asyncio, pytest-httpx

---

## 文件结构

```
src/deepalpha/
├── models/
│   ├── __init__.py
│   ├── market.py         # Quote, PriceBar
│   ├── financial.py      # IncomeStatement, BalanceSheet, CashFlow,
│   │                     #   FinancialRatio, KeyMetrics, Valuation
│   ├── company.py        # CompanyProfile, Executive, MarketCapRecord
│   ├── analyst.py        # AnalystRating, PriceTarget, Estimate
│   ├── calendar.py       # EarningsEvent, DividendEvent, IPOEvent, SplitEvent
│   ├── news.py           # NewsArticle
│   ├── indicators.py     # IndicatorRow
│   ├── insider.py        # InsiderTrade, InsiderStatistics
│   ├── filings.py        # SecFiling, SecCompanyProfile
│   ├── performance.py    # MarketMover, SectorPerformance, SectorPE
│   ├── congress.py       # CongressTrade
│   └── directory.py      # SymbolInfo, ExchangeInfo
├── loaders/
│   ├── __init__.py
│   ├── enums.py          # AssetClass, Interval, StatementPeriod,
│   │                     #   IndicatorType, MoverDirection, CongressChamber
│   ├── base.py           # AsyncDataClient Protocol, BaseLoader ABC
│   ├── hub.py            # AbstractDataHub Protocol
│   ├── market.py         # AbstractMarketLoader
│   ├── financial.py      # AbstractFinancialLoader
│   ├── company.py        # AbstractCompanyLoader
│   ├── analyst.py        # AbstractAnalystLoader
│   ├── calendar.py       # AbstractCalendarLoader
│   ├── news.py           # AbstractNewsLoader
│   ├── indicators.py     # AbstractTechnicalIndicatorLoader
│   ├── economics.py      # AbstractEconomicsLoader
│   ├── insider.py        # AbstractInsiderTradeLoader
│   ├── filings.py        # AbstractSecFilingLoader
│   ├── performance.py    # AbstractMarketPerformanceLoader
│   ├── congress.py       # AbstractCongressTradeLoader
│   └── directory.py      # AbstractDirectoryLoader
└── providers/
    ├── __init__.py
    └── fmp/
        ├── __init__.py       # FMPDataHub
        ├── config.py         # FMPConfig
        ├── client.py         # FMPAsyncClient
        ├── errors.py         # FMPError 异常层次
        └── loaders/
            ├── __init__.py
            ├── market.py
            ├── financial.py
            ├── company.py
            ├── analyst.py
            ├── calendar.py
            ├── news.py
            ├── indicators.py
            ├── economics.py
            ├── insider.py
            ├── filings.py
            ├── performance.py
            ├── congress.py
            └── directory.py

tests/
├── conftest.py
├── unit/
│   ├── models/
│   │   └── test_model_annotations.py
│   └── providers/fmp/
│       ├── test_client.py
│       └── loaders/
│           ├── test_market.py
│           ├── test_financial.py
│           ├── test_company.py
│           ├── test_analyst.py
│           ├── test_calendar.py
│           ├── test_news.py
│           ├── test_indicators.py
│           ├── test_economics.py
│           ├── test_insider.py
│           ├── test_filings.py
│           ├── test_performance.py
│           ├── test_congress.py
│           └── test_directory.py
├── contracts/
│   └── test_fmp_contracts.py
└── integration/
    └── test_fmp_integration.py
```

---

### Task 1: 项目依赖与目录骨架

**Files:**

- Modify: `pyproject.toml`

- Create: `src/deepalpha/models/__init__.py`

- Create: `src/deepalpha/loaders/__init__.py`

- Create: `src/deepalpha/providers/__init__.py`

- Create: `src/deepalpha/providers/fmp/__init__.py`

- Create: `src/deepalpha/providers/fmp/loaders/__init__.py`

- Create: `tests/conftest.py`

- [ ] **Step 1: 写失败测试 — 验证 pytest-httpx 可导入**

```python
# tests/conftest.py
import pytest

def test_pytest_httpx_available():
    import pytest_httpx  # noqa: F401
```

- [ ] **Step 2: 运行验证失败**

```bash
cd /Users/zhangfang/deepalpha-club-data
uv run pytest tests/conftest.py::test_pytest_httpx_available -v
```

Expected: `ModuleNotFoundError: No module named 'pytest_httpx'`

- [ ] **Step 3: 添加 pytest-httpx 到 dev 依赖**

在 `pyproject.toml` 的 `[project.optional-dependencies]` dev 列表中追加：

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "pytest-httpx>=0.30.0",
    "ruff>=0.3.0",
    "mypy>=1.8.0",
]
```

安装依赖：

```bash
uv sync --extra dev
```

- [ ] **Step 4: 替换 conftest.py 为正式内容**

```python
# tests/conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: 需要真实 FMP API Key 才能运行")
```

- [ ] **Step 5: 创建所有包的 `__init__.py`（全部为空文件）**

```bash
mkdir -p src/deepalpha/models \
         src/deepalpha/loaders \
         src/deepalpha/providers/fmp/loaders \
         tests/unit/models \
         tests/unit/providers/fmp/loaders \
         tests/contracts \
         tests/integration

touch src/deepalpha/models/__init__.py \
      src/deepalpha/loaders/__init__.py \
      src/deepalpha/providers/__init__.py \
      src/deepalpha/providers/fmp/__init__.py \
      src/deepalpha/providers/fmp/loaders/__init__.py \
      tests/__init__.py \
      tests/unit/__init__.py \
      tests/unit/models/__init__.py \
      tests/unit/providers/__init__.py \
      tests/unit/providers/fmp/__init__.py \
      tests/unit/providers/fmp/loaders/__init__.py \
      tests/contracts/__init__.py \
      tests/integration/__init__.py
```

- [ ] **Step 6: 运行验证通过**

```bash
uv run pytest tests/ -v --collect-only
```

Expected: 收集到 0 个测试，无报错。

- [ ] **Step 7: 提交**

```bash
git add pyproject.toml src/deepalpha/ tests/
git commit -m "chore: add pytest-httpx dev dep and create package directory skeleton"
```

---

### Task 2: 枚举类型 (`loaders/enums.py`) 与 FMP 异常 (`providers/fmp/errors.py`)

**Files:**

- Create: `src/deepalpha/loaders/enums.py`

- Create: `src/deepalpha/providers/fmp/errors.py`

- Create: `tests/unit/models/test_enums.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/unit/models/test_enums.py
from deepalpha.loaders.enums import (
    AssetClass, Interval, StatementPeriod,
    IndicatorType, MoverDirection, CongressChamber,
)
from deepalpha.providers.fmp.errors import (
    FMPError, FMPAuthError, FMPRateLimitError,
    FMPNotFoundError, FMPServerError,
)

def test_asset_class_values():
    assert AssetClass.STOCK == "stock"
    assert AssetClass.CRYPTO == "crypto"

def test_interval_values():
    assert Interval.ONE_DAY == "1d"
    assert Interval.ONE_HOUR == "1h"

def test_statement_period_ttm():
    assert StatementPeriod.TTM == "ttm"

def test_indicator_type_coverage():
    assert IndicatorType.SMA == "sma"
    assert IndicatorType.MACD == "macd"

def test_fmp_error_hierarchy():
    assert issubclass(FMPAuthError, FMPError)
    assert issubclass(FMPRateLimitError, FMPError)
    assert issubclass(FMPNotFoundError, FMPError)
    assert issubclass(FMPServerError, FMPError)
```

- [ ] **Step 2: 运行验证失败**

```bash
uv run pytest tests/unit/models/test_enums.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现枚举**

```python
# src/deepalpha/loaders/enums.py
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
    ONE_MIN     = "1m"
    FIVE_MIN    = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN  = "30m"
    ONE_HOUR    = "1h"
    FOUR_HOUR   = "4h"
    ONE_DAY     = "1d"
    ONE_WEEK    = "1w"
    ONE_MONTH   = "1mo"

class StatementPeriod(StrEnum):
    ANNUAL  = "annual"
    QUARTER = "quarter"
    TTM     = "ttm"

class IndicatorType(StrEnum):
    SMA      = "sma"
    EMA      = "ema"
    DEMA     = "dema"
    TEMA     = "tema"
    WMA      = "wma"
    RSI      = "rsi"
    MACD     = "macd"
    STOCH    = "stoch"
    CCI      = "cci"
    WILLIAMS = "williams"
    ADX      = "adx"
    AROON    = "aroon"
    BBANDS   = "bbands"
    ATR      = "atr"
    STD_DEV  = "std_dev"
    OBV      = "obv"

class MoverDirection(StrEnum):
    GAINERS = "gainers"
    LOSERS  = "losers"
    ACTIVE  = "active"

class CongressChamber(StrEnum):
    SENATE = "senate"
    HOUSE  = "house"
```

- [ ] **Step 4: 实现 FMP 异常**

```python
# src/deepalpha/providers/fmp/errors.py

class FMPError(Exception):
    """FMP 客户端异常基类"""

class FMPAuthError(FMPError):
    """401 — API Key 无效或过期"""

class FMPRateLimitError(FMPError):
    """429 — 超出速率限制"""

class FMPNotFoundError(FMPError):
    """404 或空响应 — 标的不存在"""

class FMPServerError(FMPError):
    """5xx — FMP 服务端错误"""
```

- [ ] **Step 5: 运行验证通过**

```bash
uv run pytest tests/unit/models/test_enums.py -v
```

Expected: 5 passed

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/loaders/enums.py src/deepalpha/providers/fmp/errors.py tests/unit/models/test_enums.py
git commit -m "feat: add shared enums and FMP exception hierarchy"
```

---

### Task 3: `BaseLoader` ABC (`loaders/base.py`)

**Files:**

- Create: `src/deepalpha/loaders/base.py`

- Create: `tests/unit/models/test_base_loader.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/unit/models/test_base_loader.py
import pytest
from pydantic import BaseModel, Field
from deepalpha.loaders.base import BaseLoader, AsyncDataClient

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
```

- [ ] **Step 2: 运行验证失败**

```bash
uv run pytest tests/unit/models/test_base_loader.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现 BaseLoader**

```python
# src/deepalpha/loaders/base.py
from abc import ABC
from typing import Any, Protocol, runtime_checkable
import polars as pl
from pydantic import BaseModel

@runtime_checkable
class AsyncDataClient(Protocol):
    async def get(self, path: str, **params: Any) -> Any: ...

class BaseLoader(ABC):
    def __init__(self, client: AsyncDataClient) -> None:
        self._client = client

    async def _get(self, endpoint: str, **params: Any) -> dict[str, Any]:
        result = await self._client.get(endpoint, **params)
        if isinstance(result, list):
            if not result:
                raise ValueError(f"Empty response for: {endpoint}")
            return result[0]
        if not result:
            raise ValueError(f"Empty response for: {endpoint}")
        return result

    async def _get_list(self, endpoint: str, **params: Any) -> list[dict[str, Any]]:
        result = await self._client.get(endpoint, **params)
        if result is None:
            return []
        if isinstance(result, list):
            return result
        return [result]

    def _to_df(self, records: list[dict[str, Any]], model: type[BaseModel]) -> pl.DataFrame:
        if not records:
            return pl.DataFrame()
        validated = [model.model_validate(r) for r in records]
        return pl.DataFrame([v.model_dump() for v in validated])
```

- [ ] **Step 4: 运行验证通过**

```bash
uv run pytest tests/unit/models/test_base_loader.py -v
```

Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add src/deepalpha/loaders/base.py tests/unit/models/test_base_loader.py
git commit -m "feat: add BaseLoader ABC with _get/_get_list/_to_df helpers"
```

---

### Task 4: FMPConfig + FMPAsyncClient

**Files:**

- Create: `src/deepalpha/providers/fmp/config.py`

- Create: `src/deepalpha/providers/fmp/client.py`

- Create: `tests/unit/providers/fmp/test_client.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/unit/providers/fmp/test_client.py
import pytest
import httpx
from pytest_httpx import HTTPXMock
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.errors import (
    FMPAuthError, FMPNotFoundError, FMPServerError, FMPRateLimitError,
)

@pytest.fixture
def config():
    return FMPConfig(api_key="test-key")

@pytest.mark.asyncio
async def test_get_attaches_api_key(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(json={"symbol": "AAPL"})
    async with FMPAsyncClient(config) as client:
        result = await client.get("/stable/quote/AAPL")
    request = httpx_mock.get_request()
    assert "apikey=test-key" in str(request.url)
    assert result == {"symbol": "AAPL"}

@pytest.mark.asyncio
async def test_get_raises_auth_error_on_401(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(status_code=401)
    async with FMPAsyncClient(config) as client:
        with pytest.raises(FMPAuthError):
            await client.get("/stable/quote/AAPL")

@pytest.mark.asyncio
async def test_get_raises_not_found_on_404(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(status_code=404)
    async with FMPAsyncClient(config) as client:
        with pytest.raises(FMPNotFoundError):
            await client.get("/stable/quote/AAPL")

@pytest.mark.asyncio
async def test_get_retries_on_500_then_raises(httpx_mock: HTTPXMock, config):
    cfg = FMPConfig(api_key="test-key", max_retries=1)
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=500)
    async with FMPAsyncClient(cfg) as client:
        with pytest.raises(FMPServerError):
            await client.get("/stable/quote/AAPL")

@pytest.mark.asyncio
async def test_get_returns_list_unchanged(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(json=[{"symbol": "AAPL"}, {"symbol": "MSFT"}])
    async with FMPAsyncClient(config) as client:
        result = await client.get("/stable/quotes-batch")
    assert result == [{"symbol": "AAPL"}, {"symbol": "MSFT"}]
```

- [ ] **Step 2: 运行验证失败**

```bash
uv run pytest tests/unit/providers/fmp/test_client.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现 FMPConfig**

```python
# src/deepalpha/providers/fmp/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class FMPConfig(BaseSettings):
    api_key: str = Field(title="API 密钥", description="FMP API Key，从环境变量 FMP_API_KEY 读取")
    base_url: str = Field("https://financialmodelingprep.com/api", title="API 基础地址")
    timeout: float = Field(30.0, title="超时时间（秒）")
    max_connections: int = Field(10, title="最大并发连接数")
    max_retries: int = Field(3, title="最大重试次数", description="5xx 时的指数退避重试次数")

    model_config = SettingsConfigDict(env_prefix="FMP_", env_file=".env")
```

- [ ] **Step 4: 实现 FMPAsyncClient**

```python
# src/deepalpha/providers/fmp/client.py
import asyncio
from typing import Any
import httpx
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.errors import (
    FMPAuthError, FMPRateLimitError, FMPNotFoundError, FMPServerError,
)

class FMPAsyncClient:
    def __init__(self, config: FMPConfig) -> None:
        self._config = config
        self._http = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            limits=httpx.Limits(max_connections=config.max_connections),
        )

    async def get(self, path: str, **params: Any) -> Any:
        params["apikey"] = self._config.api_key
        delay = 1.0
        for attempt in range(self._config.max_retries + 1):
            response = await self._http.get(path, params=params)
            if response.status_code == 401:
                raise FMPAuthError("API Key 无效或过期")
            if response.status_code == 429:
                wait = float(response.headers.get("Retry-After", delay))
                await asyncio.sleep(wait)
                continue
            if response.status_code == 404:
                raise FMPNotFoundError(f"资源不存在: {path}")
            if response.status_code >= 500:
                if attempt == self._config.max_retries:
                    raise FMPServerError(f"服务端错误 {response.status_code}: {path}")
                await asyncio.sleep(delay)
                delay *= 2
                continue
            response.raise_for_status()
            return response.json()
        raise FMPServerError(f"超出最大重试次数: {path}")

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "FMPAsyncClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
```

- [ ] **Step 5: 运行验证通过**

```bash
uv run pytest tests/unit/providers/fmp/test_client.py -v
```

Expected: 5 passed

- [ ] **Step 6: 提交**

```bash
git add src/deepalpha/providers/fmp/config.py src/deepalpha/providers/fmp/client.py tests/unit/providers/fmp/test_client.py
git commit -m "feat: add FMPConfig and FMPAsyncClient with retry/error handling"
```

---

### Task 5: Pydantic 数据模型（核心：market / company / financial）

**Files:**

- Create: `src/deepalpha/models/market.py`

- Create: `src/deepalpha/models/company.py`

- Create: `src/deepalpha/models/financial.py`

- Create: `tests/unit/models/test_model_annotations.py`

- [ ] **Step 1: 写失败测试 — 验证所有模型字段均有中文 title/description**

```python
# tests/unit/models/test_model_annotations.py
import pytest
from pydantic import BaseModel

def assert_fields_annotated(model: type[BaseModel]) -> None:
    schema = model.model_json_schema()
    props = schema.get("properties", {})
    for field_name, field_info in props.items():
        assert "title" in field_info, f"{model.__name__}.{field_name} 缺少 title"
        assert field_info["title"], f"{model.__name__}.{field_name} title 为空"

from deepalpha.models.market import Quote, PriceBar
from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord
from deepalpha.models.financial import (
    IncomeStatement, BalanceSheet, CashFlow,
    FinancialRatio, KeyMetrics, Valuation,
)

@pytest.mark.parametrize("model", [
    Quote, PriceBar,
    CompanyProfile, Executive, MarketCapRecord,
    IncomeStatement, BalanceSheet, CashFlow,
    FinancialRatio, KeyMetrics, Valuation,
])
def test_all_fields_have_title(model):
    assert_fields_annotated(model)
```

- [ ] **Step 2: 运行验证失败**

```bash
uv run pytest tests/unit/models/test_model_annotations.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现 `models/market.py`**

```python
# src/deepalpha/models/market.py
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class Quote(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码，如 AAPL")
    name: str | None = Field(None, title="公司名称", description="上市公司全称")
    price: float = Field(title="最新价格", description="最近一次成交价格（美元）")
    change: float = Field(title="涨跌额", description="相对上一收盘价的价格变动")
    changes_percentage: float = Field(
        title="涨跌幅", description="涨跌额占上一收盘价的百分比",
        validation_alias="changesPercentage",
    )
    day_low: float | None = Field(None, title="日内最低价", description="当日最低成交价")
    day_high: float | None = Field(None, title="日内最高价", description="当日最高成交价")
    year_high: float | None = Field(None, title="52周最高", description="过去52周最高价")
    year_low: float | None = Field(None, title="52周最低", description="过去52周最低价")
    market_cap: float | None = Field(None, title="市值", description="总市值（美元）")
    volume: int | None = Field(None, title="成交量", description="当日已成交股数")
    avg_volume: int | None = Field(None, title="平均成交量", description="近期平均成交量")
    open: float | None = Field(None, title="开盘价", description="当日开盘价")
    previous_close: float | None = Field(None, title="前收盘价", description="上一交易日收盘价")
    eps: float | None = Field(None, title="每股收益", description="Earnings Per Share（美元）")
    pe: float | None = Field(None, title="市盈率", description="Price/Earnings 比率")
    exchange: str | None = Field(None, title="交易所", description="上市交易所代码，如 NASDAQ")
    timestamp: int | None = Field(None, title="时间戳", description="报价数据生成时间（Unix 秒）")

class PriceBar(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    date: date = Field(title="日期", description="K线对应的交易日或时间点")
    open: float = Field(title="开盘价", description="该周期开始价格")
    high: float = Field(title="最高价", description="该周期最高成交价")
    low: float = Field(title="最低价", description="该周期最低成交价")
    close: float = Field(title="收盘价", description="该周期结束价格")
    volume: int | None = Field(None, title="成交量", description="该周期成交股数")
    adj_close: float | None = Field(None, title="复权收盘价", description="经分红/拆股调整后的收盘价")
```

- [ ] **Step 4: 实现 `models/company.py`**

```python
# src/deepalpha/models/company.py
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class CompanyProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    company_name: str = Field(title="公司名称", description="上市公司完整法定名称")
    exchange: str | None = Field(None, title="交易所", description="上市交易所代码")
    industry: str | None = Field(None, title="行业", description="所属行业分类")
    sector: str | None = Field(None, title="板块", description="所属板块分类")
    description: str | None = Field(None, title="公司描述", description="公司主营业务介绍")
    website: str | None = Field(None, title="官网", description="公司官方网站 URL")
    full_time_employees: int | None = Field(None, title="全职员工数", description="当前全职雇员总数")
    ceo: str | None = Field(None, title="首席执行官", description="现任 CEO 姓名")
    country: str | None = Field(None, title="注册国家", description="公司注册所在国家代码")
    ipo_date: date | None = Field(None, title="上市日期", description="首次公开募股日期")
    is_actively_trading: bool | None = Field(None, title="是否活跃交易", description="当前是否正常交易中")

class Executive(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    name: str = Field(title="姓名", description="高管姓名")
    title: str | None = Field(None, title="职位", description="高管职位名称，如 CEO、CFO")
    pay: float | None = Field(None, title="薪酬", description="年度薪酬（美元）")
    currency_of_pay: str | None = Field(None, title="薪酬货币", description="薪酬计价货币代码")
    gender: str | None = Field(None, title="性别", description="M 或 F")
    year_born: int | None = Field(None, title="出生年份", description="高管出生年份")

class MarketCapRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="日期", description="市值对应的交易日")
    market_cap: float = Field(title="市值", description="当日收盘市值（美元）")
```

- [ ] **Step 5: 实现 `models/financial.py`**

```python
# src/deepalpha/models/financial.py
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class IncomeStatement(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="报告日期", description="财务报告截止日期")
    period: str = Field(title="报告期", description="annual / Q1 / Q2 / Q3 / Q4")
    revenue: float | None = Field(None, title="营业收入", description="总营收（美元）")
    gross_profit: float | None = Field(None, title="毛利润", description="营收减去销售成本")
    operating_income: float | None = Field(None, title="营业利润", description="扣除经营费用后的利润")
    net_income: float | None = Field(None, title="净利润", description="最终归属股东利润（美元）")
    eps: float | None = Field(None, title="每股收益", description="基本 EPS（美元）")
    eps_diluted: float | None = Field(None, title="稀释每股收益", description="稀释后 EPS（美元）")
    ebitda: float | None = Field(None, title="EBITDA", description="息税折旧摊销前利润（美元）")

class BalanceSheet(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="报告日期", description="资产负债表截止日期")
    period: str = Field(title="报告期", description="annual / Q1 / Q2 / Q3 / Q4")
    total_assets: float | None = Field(None, title="总资产", description="资产总计（美元）")
    total_liabilities: float | None = Field(None, title="总负债", description="负债合计（美元）")
    total_stockholders_equity: float | None = Field(None, title="股东权益", description="净资产（美元）")
    cash_and_cash_equivalents: float | None = Field(None, title="现金及等价物", description="货币资金（美元）")
    total_debt: float | None = Field(None, title="总债务", description="长短期债务合计（美元）")
    net_debt: float | None = Field(None, title="净债务", description="总债务减现金（美元）")

class CashFlow(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="报告日期", description="现金流量表截止日期")
    period: str = Field(title="报告期", description="annual / Q1 / Q2 / Q3 / Q4")
    operating_cash_flow: float | None = Field(None, title="经营活动现金流", description="核心运营产生的现金（美元）")
    capital_expenditure: float | None = Field(None, title="资本支出", description="购置固定资产等投资支出（美元）")
    free_cash_flow: float | None = Field(None, title="自由现金流", description="经营现金流减资本支出（美元）")
    dividends_paid: float | None = Field(None, title="已支付股息", description="向股东支付的现金股息（美元）")

class FinancialRatio(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="报告日期", description="财务比率计算基准日期")
    period: str = Field(title="报告期", description="annual / Q1 / Q2 / Q3 / Q4")
    current_ratio: float | None = Field(None, title="流动比率", description="流动资产/流动负债")
    gross_profit_margin: float | None = Field(None, title="毛利率", description="毛利润/营收")
    operating_profit_margin: float | None = Field(None, title="营业利润率", description="营业利润/营收")
    net_profit_margin: float | None = Field(None, title="净利润率", description="净利润/营收")
    return_on_equity: float | None = Field(None, title="净资产收益率", description="ROE = 净利润/股东权益")
    return_on_assets: float | None = Field(None, title="总资产收益率", description="ROA = 净利润/总资产")
    debt_equity_ratio: float | None = Field(None, title="资产负债率", description="总债务/股东权益")

class KeyMetrics(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="报告日期", description="关键指标计算基准日期")
    period: str = Field(title="报告期", description="annual / Q1 / Q2 / Q3 / Q4")
    pe_ratio: float | None = Field(None, title="市盈率", description="Price/Earnings")
    price_to_book: float | None = Field(None, title="市净率", description="Price/Book Value")
    price_to_sales: float | None = Field(None, title="市销率", description="Price/Sales")
    ev_to_ebitda: float | None = Field(None, title="EV/EBITDA", description="企业价值/EBITDA")
    free_cash_flow_per_share: float | None = Field(None, title="每股自由现金流", description="FCF/总股数（美元）")
    earnings_yield: float | None = Field(None, title="盈利收益率", description="EPS/Price，市盈率的倒数")

class Valuation(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    dcf: float | None = Field(None, title="DCF 内在价值", description="现金流折现法估算的每股内在价值（美元）")
    stock_price: float | None = Field(None, title="当前股价", description="估值时的市场价格（美元）")
```

- [ ] **Step 6: 运行验证通过**

```bash
uv run pytest tests/unit/models/test_model_annotations.py -v
```

Expected: 11 passed（每个模型一条 parametrize）

- [ ] **Step 7: 提交**

```bash
git add src/deepalpha/models/market.py src/deepalpha/models/company.py src/deepalpha/models/financial.py tests/unit/models/test_model_annotations.py
git commit -m "feat: add Pydantic models for market, company, and financial data"
```

---

### Task 6: Pydantic 数据模型（扩展：analyst / calendar / news / insider / filings / performance / congress / directory / indicators）

**Files:**

- Create: `src/deepalpha/models/analyst.py`

- Create: `src/deepalpha/models/calendar.py`

- Create: `src/deepalpha/models/news.py`

- Create: `src/deepalpha/models/insider.py`

- Create: `src/deepalpha/models/filings.py`

- Create: `src/deepalpha/models/performance.py`

- Create: `src/deepalpha/models/congress.py`

- Create: `src/deepalpha/models/directory.py`

- Create: `src/deepalpha/models/indicators.py`

- [ ] **Step 1: 将新模型类名加入测试 parametrize 列表**

在 `tests/unit/models/test_model_annotations.py` 末尾追加 import 和 parametrize 条目：

```python
# 追加到 test_model_annotations.py 现有 parametrize 列表中
from deepalpha.models.analyst import AnalystRating, PriceTarget, Estimate
from deepalpha.models.calendar import EarningsEvent, DividendEvent, IPOEvent, SplitEvent
from deepalpha.models.news import NewsArticle
from deepalpha.models.insider import InsiderTrade, InsiderStatistics
from deepalpha.models.filings import SecFiling, SecCompanyProfile
from deepalpha.models.performance import MarketMover, SectorPerformance, SectorPE
from deepalpha.models.congress import CongressTrade
from deepalpha.models.directory import SymbolInfo, ExchangeInfo
from deepalpha.models.indicators import IndicatorRow
```

在 `@pytest.mark.parametrize` 的列表中补充上述所有 model 类。

- [ ] **Step 2: 运行验证失败**

```bash
uv run pytest tests/unit/models/test_model_annotations.py -v
```

Expected: `ModuleNotFoundError` 或多条 FAILED

- [ ] **Step 3: 实现 `models/analyst.py`**

```python
# src/deepalpha/models/analyst.py
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class AnalystRating(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="评级日期", description="分析师发布评级的日期")
    rating: str | None = Field(None, title="综合评级", description="综合买卖评级，如 S+、A、B")
    rating_recommendation: str | None = Field(None, title="评级建议", description="Strong Buy / Buy / Hold / Sell")
    rating_score: int | None = Field(None, title="评级分数", description="数值化评级，1=强买 5=强卖")

class PriceTarget(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    last_month: float | None = Field(None, title="近月均价目标", description="近一个月分析师目标价均值（美元）")
    last_quarter: float | None = Field(None, title="近季均价目标", description="近一季度分析师目标价均值（美元）")
    last_year: float | None = Field(None, title="近年均价目标", description="近一年分析师目标价均值（美元）")
    all_time: float | None = Field(None, title="全期均价目标", description="全部历史分析师目标价均值（美元）")

class Estimate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="预测日期", description="预期数据对应的财报期末日期")
    estimated_revenue_avg: float | None = Field(None, title="营收共识预测", description="分析师营收预测均值（美元）")
    estimated_eps_avg: float | None = Field(None, title="EPS 共识预测", description="分析师 EPS 预测均值（美元）")
    number_analyst_estimated_revenue: int | None = Field(None, title="营收预测人数", description="参与营收预测的分析师数量")
```

- [ ] **Step 4: 实现 `models/calendar.py`**

```python
# src/deepalpha/models/calendar.py
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class EarningsEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="财报发布日", description="预计或实际财报发布日期")
    eps: float | None = Field(None, title="实际EPS", description="实际公布的每股收益（美元）")
    eps_estimated: float | None = Field(None, title="EPS预期", description="市场共识 EPS 预测（美元）")
    time: str | None = Field(None, title="发布时段", description="bmo=开盘前 / amc=收盘后")
    revenue_estimated: float | None = Field(None, title="营收预期", description="市场共识营收预测（美元）")

class DividendEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="除息日", description="股息除权基准日")
    dividend: float | None = Field(None, title="股息金额", description="每股现金股息（美元）")
    record_date: date | None = Field(None, title="股权登记日", description="确认分红资格的截止日期")
    payment_date: date | None = Field(None, title="派息日", description="实际向股东支付股息的日期")

class IPOEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="拟上市股票代码")
    company: str | None = Field(None, title="公司名称", description="拟上市公司名称")
    date: date = Field(title="上市日期", description="预计首次公开交易日期")
    exchange: str | None = Field(None, title="上市交易所", description="拟上市交易所代码")
    price_range: str | None = Field(None, title="发行价区间", description="承销商拟定发行价格范围（美元）")
    shares: int | None = Field(None, title="发行股数", description="本次 IPO 发行总股数")

class SplitEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: date = Field(title="拆股生效日", description="拆/合股正式生效的交易日")
    numerator: float | None = Field(None, title="拆股分子", description="拆股比例分子，如 4:1 中的 4")
    denominator: float | None = Field(None, title="拆股分母", description="拆股比例分母，如 4:1 中的 1")
```

- [ ] **Step 5: 实现 `models/news.py` / `models/indicators.py`**

```python
# src/deepalpha/models/news.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class NewsArticle(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    title: str = Field(title="标题", description="新闻文章标题")
    url: str = Field(title="链接", description="新闻原文 URL")
    published_date: datetime | None = Field(None, title="发布时间", description="新闻发布的 UTC 时间")
    site: str | None = Field(None, title="来源网站", description="新闻发布媒体名称")
    text: str | None = Field(None, title="摘要", description="新闻内容摘要")
    symbol: str | None = Field(None, title="相关股票", description="新闻关联的股票代码（若有）")
    sentiment: str | None = Field(None, title="情绪倾向", description="Positive / Negative / Neutral")
```

```python
# src/deepalpha/models/indicators.py
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class IndicatorRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    date: date = Field(title="日期", description="指标计算对应的 K 线日期")
    value: float | None = Field(None, title="指标值", description="该日期的技术指标计算结果")
    open: float | None = Field(None, title="开盘价", description="对应K线的开盘价（部分指标附带OHLC）")
    high: float | None = Field(None, title="最高价", description="对应K线的最高价")
    low: float | None = Field(None, title="最低价", description="对应K线的最低价")
    close: float | None = Field(None, title="收盘价", description="对应K线的收盘价")
    volume: int | None = Field(None, title="成交量", description="对应K线的成交量")
```

- [ ] **Step 6: 实现 `models/insider.py`**

```python
# src/deepalpha/models/insider.py
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class InsiderTrade(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    filing_date: date | None = Field(None, title="申报日期", description="向 SEC 提交 Form 4 的日期")
    transaction_date: date | None = Field(None, title="交易日期", description="内部人实际执行买卖的日期")
    reporting_name: str | None = Field(None, title="申报人姓名", description="内部人（高管/董事/大股东）姓名")
    type_of_security: str | None = Field(None, title="证券类型", description="普通股 / 期权 等")
    acquition_or_disposition: str | None = Field(None, title="买入或卖出", description="A=买入 D=卖出")
    shares: float | None = Field(None, title="交易股数", description="本次买入或卖出的股票数量")
    price: float | None = Field(None, title="成交价格", description="内部人交易成交价格（美元）")

class InsiderStatistics(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    total_bought: int | None = Field(None, title="买入笔数", description="统计期内内部人买入交易总笔数")
    total_sold: int | None = Field(None, title="卖出笔数", description="统计期内内部人卖出交易总笔数")
    total_bought_amount: float | None = Field(None, title="买入金额", description="买入交易总金额（美元）")
    total_sold_amount: float | None = Field(None, title="卖出金额", description="卖出交易总金额（美元）")
```

- [ ] **Step 7: 实现 `models/filings.py`**

```python
# src/deepalpha/models/filings.py
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class SecFiling(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str | None = Field(None, title="股票代码", description="与该文件关联的股票代码（如有）")
    filing_date: date | None = Field(None, title="申报日期", description="向 SEC 提交文件的日期")
    accepted_date: date | None = Field(None, title="受理日期", description="SEC 系统接受并处理的日期")
    type: str | None = Field(None, title="文件类型", description="文件类型代码，如 10-K / 10-Q / 8-K")
    link: str | None = Field(None, title="文件链接", description="SEC EDGAR 原始文件 URL")

class SecCompanyProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    cik: str | None = Field(None, title="CIK", description="SEC 系统中唯一的公司识别码")
    symbol: str | None = Field(None, title="股票代码", description="交易所上市代码")
    company_name: str | None = Field(None, title="公司名称", description="在 SEC 注册的法定公司名称")
    sic: str | None = Field(None, title="SIC 代码", description="标准行业分类代码（Standard Industrial Classification）")
    state_of_incorporation: str | None = Field(None, title="注册州", description="公司在美国的注册州代码，如 DE/CA")
    fiscal_year_end: str | None = Field(None, title="财年结束月", description="公司财政年度的结束月份，如 12 月")
```

- [ ] **Step 8: 实现 `models/performance.py` / `models/congress.py` / `models/directory.py`**

```python
# src/deepalpha/models/performance.py
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class MarketMover(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    name: str | None = Field(None, title="公司名称", description="上市公司名称")
    change: float | None = Field(None, title="涨跌额", description="相对上一收盘价的变动额（美元）")
    price: float | None = Field(None, title="当前价格", description="最新成交价格（美元）")
    changes_percentage: float | None = Field(
        None, title="涨跌幅", description="相对上一收盘价的百分比变化",
        validation_alias="changesPercentage",
    )
    volume: int | None = Field(None, title="成交量", description="当日成交总股数")

class SectorPerformance(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    sector: str = Field(title="板块名称", description="GICS 或 FMP 定义的板块分类名称")
    changes_percentage: str | None = Field(
        None, title="涨跌幅", description="当日或历史日期的板块整体涨跌幅（百分比字符串）",
        validation_alias="changesPercentage",
    )

class SectorPE(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    date: date | None = Field(None, title="日期", description="PE 数据对应的交易日")
    sector: str = Field(title="板块名称", description="GICS 或 FMP 定义的板块分类名称")
    pe: float | None = Field(None, title="市盈率", description="该板块所有成分股的综合市盈率")
```

```python
# src/deepalpha/models/congress.py
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class CongressTrade(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    filing_date: date | None = Field(None, title="申报日期", description="议员提交披露的日期")
    transaction_date: date | None = Field(None, title="交易日期", description="议员实际执行买卖的日期")
    representative: str | None = Field(None, title="议员姓名", description="提交披露的国会议员姓名")
    district: str | None = Field(None, title="选区", description="众议员的选区编号（参议员为 None）")
    type: str | None = Field(None, title="交易类型", description="Purchase / Sale / Exchange")
    amount: str | None = Field(None, title="交易金额区间", description="STOCK Act 规定的申报金额区间，如 $1,001 - $15,000")
    asset_description: str | None = Field(None, title="资产描述", description="交易标的完整名称（可能为公司名而非代码）")
```

```python
# src/deepalpha/models/directory.py
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class SymbolInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    name: str | None = Field(None, title="公司名称", description="证券发行人完整名称")
    exchange: str | None = Field(None, title="交易所", description="上市交易所代码")
    exchange_short_name: str | None = Field(None, title="交易所简称", description="交易所简短标识")
    type: str | None = Field(None, title="证券类型", description="stock / etf / trust 等")

class ExchangeInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    exchange: str = Field(title="交易所代码", description="FMP 系统内部使用的交易所标识")
    name: str | None = Field(None, title="交易所名称", description="交易所完整名称")
    country: str | None = Field(None, title="所在国家", description="交易所所在国家代码（ISO 3166-1）")
    currency: str | None = Field(None, title="交易货币", description="该交易所的主要计价货币代码")
```

- [ ] **Step 9: 运行验证全部通过**

```bash
uv run pytest tests/unit/models/test_model_annotations.py -v
```

Expected: 全部 passed（包含所有新增模型）

- [ ] **Step 10: 提交**

```bash
git add src/deepalpha/models/ tests/unit/models/test_model_annotations.py
git commit -m "feat: add all Pydantic models with Chinese field annotations"
```

---

### Task 7: 所有 Abstract Loader + AbstractDataHub Protocol

**Files:**

- Modify: `src/deepalpha/loaders/__init__.py`

- Create: `src/deepalpha/loaders/hub.py`

- Create: `src/deepalpha/loaders/market.py` … `directory.py`（13 个文件）

- Create: `tests/contracts/test_fmp_contracts.py`（契约测试框架，此时为空壳）

- [ ] **Step 1: 写失败测试 — 验证可导入所有 Abstract Loader**

```python
# tests/contracts/test_fmp_contracts.py
from deepalpha.loaders.market import AbstractMarketLoader
from deepalpha.loaders.financial import AbstractFinancialLoader
from deepalpha.loaders.company import AbstractCompanyLoader
from deepalpha.loaders.analyst import AbstractAnalystLoader
from deepalpha.loaders.calendar import AbstractCalendarLoader
from deepalpha.loaders.news import AbstractNewsLoader
from deepalpha.loaders.indicators import AbstractTechnicalIndicatorLoader
from deepalpha.loaders.economics import AbstractEconomicsLoader
from deepalpha.loaders.insider import AbstractInsiderTradeLoader
from deepalpha.loaders.filings import AbstractSecFilingLoader
from deepalpha.loaders.performance import AbstractMarketPerformanceLoader
from deepalpha.loaders.congress import AbstractCongressTradeLoader
from deepalpha.loaders.directory import AbstractDirectoryLoader
from deepalpha.loaders.hub import AbstractDataHub

def test_abstract_loaders_importable():
    assert AbstractMarketLoader is not None
    assert AbstractDataHub is not None
```

- [ ] **Step 2: 运行验证失败**

```bash
uv run pytest tests/contracts/test_fmp_contracts.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现所有 Abstract Loader 文件**

```python
# src/deepalpha/loaders/market.py
from abc import abstractmethod
from datetime import date
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass, Interval
from deepalpha.models.market import Quote

class AbstractMarketLoader(BaseLoader):
    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote: ...
    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> pl.DataFrame: ...
    @abstractmethod
    async def get_price_history(
        self, symbol: str, start: date, end: date | None = None,
        interval: Interval = Interval.ONE_DAY, adjusted: bool = True,
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> pl.DataFrame: ...
```

```python
# src/deepalpha/loaders/financial.py
from abc import abstractmethod
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.financial import Valuation

class AbstractFinancialLoader(BaseLoader):
    @abstractmethod
    async def get_income_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_balance_sheet(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_cash_flow_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_financial_ratios(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_key_metrics(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_valuation(self, symbol: str) -> Valuation: ...
```

```python
# src/deepalpha/loaders/company.py
from abc import abstractmethod
from datetime import date
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.models.company import CompanyProfile

class AbstractCompanyLoader(BaseLoader):
    @abstractmethod
    async def get_profile(self, symbol: str) -> CompanyProfile: ...
    @abstractmethod
    async def get_executives(self, symbol: str) -> pl.DataFrame: ...
    @abstractmethod
    async def get_peers(self, symbol: str) -> list[str]: ...
    @abstractmethod
    async def get_market_cap(
        self, symbol: str, start: date | None = None, end: date | None = None
    ) -> pl.DataFrame: ...
```

```python
# src/deepalpha/loaders/analyst.py
from abc import abstractmethod
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import StatementPeriod

class AbstractAnalystLoader(BaseLoader):
    @abstractmethod
    async def get_ratings(self, symbol: str) -> pl.DataFrame: ...
    @abstractmethod
    async def get_price_targets(self, symbol: str) -> pl.DataFrame: ...
    @abstractmethod
    async def get_estimates(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL
    ) -> pl.DataFrame: ...
```

```python
# src/deepalpha/loaders/calendar.py
from abc import abstractmethod
from datetime import date
import polars as pl
from deepalpha.loaders.base import BaseLoader

class AbstractCalendarLoader(BaseLoader):
    @abstractmethod
    async def get_earnings_calendar(self, start: date, end: date) -> pl.DataFrame: ...
    @abstractmethod
    async def get_dividend_calendar(self, start: date, end: date) -> pl.DataFrame: ...
    @abstractmethod
    async def get_ipo_calendar(self, start: date, end: date) -> pl.DataFrame: ...
    @abstractmethod
    async def get_splits_calendar(self, start: date, end: date) -> pl.DataFrame: ...
```

```python
# src/deepalpha/loaders/news.py
from abc import abstractmethod
from datetime import date
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass

class AbstractNewsLoader(BaseLoader):
    @abstractmethod
    async def get_news(
        self,
        symbols: list[str] | None = None,
        asset_class: AssetClass | None = None,
        limit: int = 20,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame: ...
```

```python
# src/deepalpha/loaders/indicators.py
from abc import abstractmethod
from datetime import date
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import Interval, IndicatorType

class AbstractTechnicalIndicatorLoader(BaseLoader):
    @abstractmethod
    async def get_indicator(
        self,
        symbol: str,
        indicator: IndicatorType,
        period: int,
        interval: Interval = Interval.ONE_DAY,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame: ...
```

```python
# src/deepalpha/loaders/economics.py
from abc import abstractmethod
from datetime import date
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import Interval

class AbstractEconomicsLoader(BaseLoader):
    @abstractmethod
    async def get_indicator(
        self,
        indicator_name: str,
        start: date | None = None,
        end: date | None = None,
        interval: Interval = Interval.ONE_MONTH,
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_available_indicators(self) -> list[str]: ...
```

```python
# src/deepalpha/loaders/insider.py
from abc import abstractmethod
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.models.insider import InsiderStatistics

class AbstractInsiderTradeLoader(BaseLoader):
    @abstractmethod
    async def get_insider_trades(
        self, symbol: str | None = None, limit: int = 50, page: int = 0
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_insider_statistics(self, symbol: str) -> InsiderStatistics: ...
```

```python
# src/deepalpha/loaders/filings.py
from abc import abstractmethod
from datetime import date
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.models.filings import SecCompanyProfile

class AbstractSecFilingLoader(BaseLoader):
    @abstractmethod
    async def get_filings(
        self,
        symbol: str | None = None,
        form_type: str | None = None,
        start: date | None = None,
        end: date | None = None,
        limit: int = 20,
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_sec_profile(self, symbol: str) -> SecCompanyProfile: ...
```

```python
# src/deepalpha/loaders/performance.py
from abc import abstractmethod
from datetime import date
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import MoverDirection

class AbstractMarketPerformanceLoader(BaseLoader):
    @abstractmethod
    async def get_movers(
        self, direction: MoverDirection, limit: int = 20
    ) -> pl.DataFrame: ...
    @abstractmethod
    async def get_sector_performance(self, date: date | None = None) -> pl.DataFrame: ...
    @abstractmethod
    async def get_sector_pe(self, date: date | None = None) -> pl.DataFrame: ...
```

```python
# src/deepalpha/loaders/congress.py
from abc import abstractmethod
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import CongressChamber

class AbstractCongressTradeLoader(BaseLoader):
    @abstractmethod
    async def get_congress_trades(
        self,
        symbol: str | None = None,
        chamber: CongressChamber = CongressChamber.SENATE,
        limit: int = 50,
        page: int = 0,
    ) -> pl.DataFrame: ...
```

```python
# src/deepalpha/loaders/directory.py
from abc import abstractmethod
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.loaders.enums import AssetClass

class AbstractDirectoryLoader(BaseLoader):
    @abstractmethod
    async def get_symbols(self, asset_class: AssetClass = AssetClass.STOCK) -> pl.DataFrame: ...
    @abstractmethod
    async def get_exchanges(self) -> pl.DataFrame: ...
    @abstractmethod
    async def get_sectors(self) -> list[str]: ...
    @abstractmethod
    async def get_industries(self) -> list[str]: ...
```

- [ ] **Step 4: 实现 `loaders/hub.py`**

```python
# src/deepalpha/loaders/hub.py
from typing import Protocol, runtime_checkable
from deepalpha.loaders.market import AbstractMarketLoader
from deepalpha.loaders.financial import AbstractFinancialLoader
from deepalpha.loaders.company import AbstractCompanyLoader
from deepalpha.loaders.analyst import AbstractAnalystLoader
from deepalpha.loaders.calendar import AbstractCalendarLoader
from deepalpha.loaders.news import AbstractNewsLoader

@runtime_checkable
class AbstractDataHub(Protocol):
    market:    AbstractMarketLoader
    financial: AbstractFinancialLoader
    company:   AbstractCompanyLoader
    analyst:   AbstractAnalystLoader
    calendar:  AbstractCalendarLoader
    news:      AbstractNewsLoader

    async def __aenter__(self) -> "AbstractDataHub": ...
    async def __aexit__(self, *_: object) -> None: ...
```

- [ ] **Step 5: 更新 `loaders/__init__.py`**

```python
# src/deepalpha/loaders/__init__.py
from deepalpha.loaders.enums import (
    AssetClass, Interval, StatementPeriod,
    IndicatorType, MoverDirection, CongressChamber,
)
from deepalpha.loaders.base import AsyncDataClient, BaseLoader
from deepalpha.loaders.hub import AbstractDataHub
from deepalpha.loaders.market import AbstractMarketLoader
from deepalpha.loaders.financial import AbstractFinancialLoader
from deepalpha.loaders.company import AbstractCompanyLoader
from deepalpha.loaders.analyst import AbstractAnalystLoader
from deepalpha.loaders.calendar import AbstractCalendarLoader
from deepalpha.loaders.news import AbstractNewsLoader
from deepalpha.loaders.indicators import AbstractTechnicalIndicatorLoader
from deepalpha.loaders.economics import AbstractEconomicsLoader
from deepalpha.loaders.insider import AbstractInsiderTradeLoader
from deepalpha.loaders.filings import AbstractSecFilingLoader
from deepalpha.loaders.performance import AbstractMarketPerformanceLoader
from deepalpha.loaders.congress import AbstractCongressTradeLoader
from deepalpha.loaders.directory import AbstractDirectoryLoader

__all__ = [
    "AssetClass", "Interval", "StatementPeriod",
    "IndicatorType", "MoverDirection", "CongressChamber",
    "AsyncDataClient", "BaseLoader", "AbstractDataHub",
    "AbstractMarketLoader", "AbstractFinancialLoader", "AbstractCompanyLoader",
    "AbstractAnalystLoader", "AbstractCalendarLoader", "AbstractNewsLoader",
    "AbstractTechnicalIndicatorLoader", "AbstractEconomicsLoader",
    "AbstractInsiderTradeLoader", "AbstractSecFilingLoader",
    "AbstractMarketPerformanceLoader", "AbstractCongressTradeLoader",
    "AbstractDirectoryLoader",
]
```

- [ ] **Step 6: 运行验证通过**

```bash
uv run pytest tests/contracts/test_fmp_contracts.py -v
```

Expected: 1 passed

- [ ] **Step 7: 提交**

```bash
git add src/deepalpha/loaders/ tests/contracts/test_fmp_contracts.py
git commit -m "feat: add all abstract loader interfaces and AbstractDataHub Protocol"
```

---

### Task 8: FMPMarketLoader

**Files:**

- Create: `src/deepalpha/providers/fmp/loaders/market.py`

- Create: `tests/unit/providers/fmp/loaders/test_market.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/unit/providers/fmp/loaders/test_market.py
import pytest
from pytest_httpx import HTTPXMock
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.market import FMPMarketLoader
from deepalpha.models.market import Quote
from deepalpha.loaders.enums import AssetClass, Interval
import polars as pl
from datetime import date

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_quote_returns_quote(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "price": 189.84, "change": 2.31,
        "changesPercentage": 1.23, "volume": 45000000,
    }])
    loader = FMPMarketLoader(client)
    quote = await loader.get_quote("AAPL")
    assert isinstance(quote, Quote)
    assert quote.symbol == "AAPL"
    assert quote.price == 189.84
    assert quote.changes_percentage == 1.23
    await client.aclose()

@pytest.mark.asyncio
async def test_get_quotes_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"symbol": "AAPL", "price": 189.84, "change": 2.31, "changesPercentage": 1.23, "volume": 1000},
        {"symbol": "MSFT", "price": 420.10, "change": 1.05, "changesPercentage": 0.25, "volume": 2000},
    ])
    loader = FMPMarketLoader(client)
    df = await loader.get_quotes(["AAPL", "MSFT"])
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 2
    assert "symbol" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_price_history_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-01-05", "open": 185.0, "high": 190.0, "low": 184.0, "close": 189.0, "volume": 50000000},
        {"date": "2024-01-04", "open": 182.0, "high": 186.0, "low": 181.0, "close": 185.0, "volume": 48000000},
    ])
    loader = FMPMarketLoader(client)
    df = await loader.get_price_history("AAPL", start=date(2024, 1, 1))
    assert isinstance(df, pl.DataFrame)
    assert "close" in df.columns
    assert len(df) == 2
    await client.aclose()

@pytest.mark.asyncio
async def test_get_market_snapshot_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"symbol": "AAPL", "price": 189.84, "change": 2.31, "changesPercentage": 1.23, "volume": 1000},
    ])
    loader = FMPMarketLoader(client)
    df = await loader.get_market_snapshot(AssetClass.STOCK)
    assert isinstance(df, pl.DataFrame)
    assert "symbol" in df.columns
    await client.aclose()
```

- [ ] **Step 2: 运行验证失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_market.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现 FMPMarketLoader**

```python
# src/deepalpha/providers/fmp/loaders/market.py
from datetime import date
import polars as pl
from deepalpha.loaders.market import AbstractMarketLoader
from deepalpha.loaders.enums import AssetClass, Interval
from deepalpha.models.market import Quote, PriceBar

_INTRADAY_PATHS: dict[Interval, str] = {
    Interval.ONE_MIN:     "intraday-1-min",
    Interval.FIVE_MIN:    "intraday-5-min",
    Interval.FIFTEEN_MIN: "intraday-15-min",
    Interval.THIRTY_MIN:  "intraday-30-min",
    Interval.ONE_HOUR:    "intraday-1-hour",
    Interval.FOUR_HOUR:   "intraday-4-hour",
}

_SNAPSHOT_PATHS: dict[AssetClass, str] = {
    AssetClass.STOCK:       "full-exchange-quotes",
    AssetClass.ETF:         "full-etf-quotes",
    AssetClass.INDEX:       "full-index-quotes",
    AssetClass.CRYPTO:      "full-cryptocurrency-quotes",
    AssetClass.FOREX:       "full-forex-quotes",
    AssetClass.COMMODITY:   "full-commodity-quotes",
    AssetClass.MUTUAL_FUND: "full-mutual-fund-quotes",
}

class FMPMarketLoader(AbstractMarketLoader):
    async def get_quote(self, symbol: str) -> Quote:
        data = await self._get(f"/stable/quote/{symbol}")
        return Quote.model_validate(data)

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
        params: dict[str, str] = {"from": str(start)}
        if end:
            params["to"] = str(end)
        if interval in _INTRADAY_PATHS:
            path = f"/stable/{_INTRADAY_PATHS[interval]}/{symbol}"
        elif adjusted:
            path = f"/stable/historical-price-eod-full/{symbol}"
        else:
            path = f"/stable/historical-price-eod-non-split-adjusted/{symbol}"
        records = await self._get_list(path, **params)
        return self._to_df(records, PriceBar)

    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> pl.DataFrame:
        suffix = _SNAPSHOT_PATHS.get(asset_class, "full-exchange-quotes")
        records = await self._get_list(f"/stable/{suffix}")
        return self._to_df(records, Quote)
```

- [ ] **Step 4: 运行验证通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_market.py -v
```

Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add src/deepalpha/providers/fmp/loaders/market.py tests/unit/providers/fmp/loaders/test_market.py
git commit -m "feat: implement FMPMarketLoader with quote/history/snapshot methods"
```

---

### Task 9: FMPFinancialLoader

**Files:**

- Create: `src/deepalpha/providers/fmp/loaders/financial.py`

- Create: `tests/unit/providers/fmp/loaders/test_financial.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/unit/providers/fmp/loaders/test_financial.py
import pytest
from pytest_httpx import HTTPXMock
from datetime import date
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.financial import FMPFinancialLoader
from deepalpha.models.financial import Valuation
from deepalpha.loaders.enums import StatementPeriod

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
async def test_get_income_statement_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_INCOME_ROW])
    loader = FMPFinancialLoader(client)
    df = await loader.get_income_statement("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "revenue" in df.columns
    assert df["symbol"][0] == "AAPL"
    await client.aclose()

@pytest.mark.asyncio
async def test_get_income_statement_ttm(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_INCOME_ROW])
    loader = FMPFinancialLoader(client)
    df = await loader.get_income_statement("AAPL", period=StatementPeriod.TTM)
    assert isinstance(df, pl.DataFrame)
    await client.aclose()

@pytest.mark.asyncio
async def test_get_valuation_returns_object(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json={"symbol": "AAPL", "dcf": 195.23, "stockPrice": 189.84})
    loader = FMPFinancialLoader(client)
    val = await loader.get_valuation("AAPL")
    assert isinstance(val, Valuation)
    assert val.symbol == "AAPL"
    assert val.dcf == 195.23
    await client.aclose()

@pytest.mark.asyncio
async def test_get_balance_sheet_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2023-09-30", "period": "annual",
        "totalAssets": 352583000000, "totalLiabilities": 290437000000,
        "totalStockholdersEquity": 62146000000, "cashAndCashEquivalents": 29965000000,
        "totalDebt": 110000000000, "netDebt": 80000000000,
    }])
    loader = FMPFinancialLoader(client)
    df = await loader.get_balance_sheet("AAPL")
    assert "total_assets" in df.columns
    await client.aclose()
```

- [ ] **Step 2: 运行验证失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_financial.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现 FMPFinancialLoader**

```python
# src/deepalpha/providers/fmp/loaders/financial.py
import polars as pl
from deepalpha.loaders.financial import AbstractFinancialLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.financial import (
    IncomeStatement, BalanceSheet, CashFlow,
    FinancialRatio, KeyMetrics, Valuation,
)

_TTM_PATHS = {
    "income":   ("income-statement", "income-statements-ttm"),
    "balance":  ("balance-sheet-statement", "balance-sheet-statements-ttm"),
    "cashflow": ("cashflow-statement", "cashflow-statements-ttm"),
    "ratios":   ("metrics-ratios", "metrics-ratios-ttm"),
    "metrics":  ("key-metrics", "key-metrics-ttm"),
}

def _period_path(key: str, period: StatementPeriod) -> str:
    normal, ttm = _TTM_PATHS[key]
    return ttm if period == StatementPeriod.TTM else normal

class FMPFinancialLoader(AbstractFinancialLoader):
    async def get_income_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame:
        path = _period_path("income", period)
        params = {} if period == StatementPeriod.TTM else {"period": period.value, "limit": limit}
        records = await self._get_list(f"/stable/{path}/{symbol}", **params)
        return self._to_df(records, IncomeStatement)

    async def get_balance_sheet(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame:
        path = _period_path("balance", period)
        params = {} if period == StatementPeriod.TTM else {"period": period.value, "limit": limit}
        records = await self._get_list(f"/stable/{path}/{symbol}", **params)
        return self._to_df(records, BalanceSheet)

    async def get_cash_flow_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame:
        path = _period_path("cashflow", period)
        params = {} if period == StatementPeriod.TTM else {"period": period.value, "limit": limit}
        records = await self._get_list(f"/stable/{path}/{symbol}", **params)
        return self._to_df(records, CashFlow)

    async def get_financial_ratios(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame:
        path = _period_path("ratios", period)
        params = {} if period == StatementPeriod.TTM else {"period": period.value, "limit": limit}
        records = await self._get_list(f"/stable/{path}/{symbol}", **params)
        return self._to_df(records, FinancialRatio)

    async def get_key_metrics(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame:
        path = _period_path("metrics", period)
        params = {} if period == StatementPeriod.TTM else {"period": period.value, "limit": limit}
        records = await self._get_list(f"/stable/{path}/{symbol}", **params)
        return self._to_df(records, KeyMetrics)

    async def get_valuation(self, symbol: str) -> Valuation:
        data = await self._get(f"/stable/dcf-advanced/{symbol}")
        return Valuation.model_validate(data)
```

- [ ] **Step 4: 运行验证通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_financial.py -v
```

Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add src/deepalpha/providers/fmp/loaders/financial.py tests/unit/providers/fmp/loaders/test_financial.py
git commit -m "feat: implement FMPFinancialLoader with statements, ratios, and valuation"
```

---

### Task 10: FMPCompanyLoader + FMPAnalystLoader

**Files:**

- Create: `src/deepalpha/providers/fmp/loaders/company.py`

- Create: `src/deepalpha/providers/fmp/loaders/analyst.py`

- Create: `tests/unit/providers/fmp/loaders/test_company.py`

- Create: `tests/unit/providers/fmp/loaders/test_analyst.py`

- [ ] **Step 1: 写失败测试 — company**

```python
# tests/unit/providers/fmp/loaders/test_company.py
import pytest
from pytest_httpx import HTTPXMock
from datetime import date
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.company import FMPCompanyLoader
from deepalpha.models.company import CompanyProfile

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_profile_returns_object(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "companyName": "Apple Inc.", "exchange": "NASDAQ",
        "industry": "Consumer Electronics", "sector": "Technology",
        "description": "Apple Inc. designs...", "website": "https://apple.com",
        "fullTimeEmployees": 164000, "ceo": "Tim Cook", "country": "US",
        "ipoDate": "1980-12-12", "isActivelyTrading": True,
    }])
    loader = FMPCompanyLoader(client)
    profile = await loader.get_profile("AAPL")
    assert isinstance(profile, CompanyProfile)
    assert profile.symbol == "AAPL"
    assert profile.company_name == "Apple Inc."
    await client.aclose()

@pytest.mark.asyncio
async def test_get_executives_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"name": "Tim Cook", "title": "CEO", "pay": 99420000, "currencyOfPay": "USD"},
    ])
    loader = FMPCompanyLoader(client)
    df = await loader.get_executives("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "name" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_peers_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{"peersList": ["MSFT", "GOOGL", "AMZN"]}])
    loader = FMPCompanyLoader(client)
    peers = await loader.get_peers("AAPL")
    assert isinstance(peers, list)
    assert "MSFT" in peers
    await client.aclose()

@pytest.mark.asyncio
async def test_get_market_cap_current(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-05-02", "marketCap": 2950000000000,
    }])
    loader = FMPCompanyLoader(client)
    df = await loader.get_market_cap("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "market_cap" in df.columns
    await client.aclose()
```

- [ ] **Step 2: 写失败测试 — analyst**

```python
# tests/unit/providers/fmp/loaders/test_analyst.py
import pytest
from pytest_httpx import HTTPXMock
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.analyst import FMPAnalystLoader

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_ratings_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-01-01",
        "rating": "S+", "ratingRecommendation": "Strong Buy", "ratingScore": 1,
    }])
    loader = FMPAnalystLoader(client)
    df = await loader.get_ratings("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "rating" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_price_targets_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json={
        "symbol": "AAPL", "lastMonth": 198.0, "lastQuarter": 195.0,
        "lastYear": 185.0, "allTime": 175.0,
    })
    loader = FMPAnalystLoader(client)
    df = await loader.get_price_targets("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "last_month" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_estimates_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-09-30",
        "estimatedRevenueAvg": 390000000000, "estimatedEpsAvg": 6.50,
        "numberAnalystEstimatedRevenue": 28,
    }])
    loader = FMPAnalystLoader(client)
    df = await loader.get_estimates("AAPL")
    assert isinstance(df, pl.DataFrame)
    assert "estimated_revenue_avg" in df.columns
    await client.aclose()
```

- [ ] **Step 3: 运行验证失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_company.py tests/unit/providers/fmp/loaders/test_analyst.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 4: 实现 FMPCompanyLoader**

```python
# src/deepalpha/providers/fmp/loaders/company.py
from datetime import date
import polars as pl
from deepalpha.loaders.company import AbstractCompanyLoader
from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord

class FMPCompanyLoader(AbstractCompanyLoader):
    async def get_profile(self, symbol: str) -> CompanyProfile:
        data = await self._get(f"/stable/profile-symbol/{symbol}")
        return CompanyProfile.model_validate(data)

    async def get_executives(self, symbol: str) -> pl.DataFrame:
        records = await self._get_list(f"/stable/company-executives/{symbol}")
        return self._to_df(records, Executive)

    async def get_peers(self, symbol: str) -> list[str]:
        data = await self._get(f"/stable/peers/{symbol}")
        return data.get("peersList", [])

    async def get_market_cap(
        self, symbol: str, start: date | None = None, end: date | None = None
    ) -> pl.DataFrame:
        if start is None and end is None:
            records = await self._get_list(f"/stable/market-cap/{symbol}")
        else:
            params: dict[str, str] = {}
            if start:
                params["from"] = str(start)
            if end:
                params["to"] = str(end)
            records = await self._get_list(f"/stable/historical-market-cap/{symbol}", **params)
        return self._to_df(records, MarketCapRecord)
```

- [ ] **Step 5: 实现 FMPAnalystLoader**

```python
# src/deepalpha/providers/fmp/loaders/analyst.py
import polars as pl
from deepalpha.loaders.analyst import AbstractAnalystLoader
from deepalpha.loaders.enums import StatementPeriod
from deepalpha.models.analyst import AnalystRating, PriceTarget, Estimate

class FMPAnalystLoader(AbstractAnalystLoader):
    async def get_ratings(self, symbol: str) -> pl.DataFrame:
        records = await self._get_list(f"/stable/historical-ratings/{symbol}")
        return self._to_df(records, AnalystRating)

    async def get_price_targets(self, symbol: str) -> pl.DataFrame:
        data = await self._get(f"/stable/price-target-summary/{symbol}")
        return self._to_df([data], PriceTarget)

    async def get_estimates(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL
    ) -> pl.DataFrame:
        params = {} if period == StatementPeriod.TTM else {"period": period.value}
        records = await self._get_list(f"/stable/financial-estimates/{symbol}", **params)
        return self._to_df(records, Estimate)
```

- [ ] **Step 6: 运行验证通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_company.py tests/unit/providers/fmp/loaders/test_analyst.py -v
```

Expected: 7 passed

- [ ] **Step 7: 提交**

```bash
git add src/deepalpha/providers/fmp/loaders/company.py src/deepalpha/providers/fmp/loaders/analyst.py tests/unit/providers/fmp/loaders/test_company.py tests/unit/providers/fmp/loaders/test_analyst.py
git commit -m "feat: implement FMPCompanyLoader and FMPAnalystLoader"
```

---

### Task 11: FMPCalendarLoader + FMPNewsLoader

**Files:**

- Create: `src/deepalpha/providers/fmp/loaders/calendar.py`

- Create: `src/deepalpha/providers/fmp/loaders/news.py`

- Create: `tests/unit/providers/fmp/loaders/test_calendar.py`

- Create: `tests/unit/providers/fmp/loaders/test_news.py`

- [ ] **Step 1: 写失败测试 — calendar**

```python
# tests/unit/providers/fmp/loaders/test_calendar.py
import pytest
from pytest_httpx import HTTPXMock
from datetime import date
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.calendar import FMPCalendarLoader

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_earnings_calendar_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-05-02", "eps": 1.53,
        "epsEstimated": 1.50, "time": "amc", "revenueEstimated": 90000000000,
    }])
    loader = FMPCalendarLoader(client)
    df = await loader.get_earnings_calendar(date(2024, 5, 1), date(2024, 5, 31))
    assert isinstance(df, pl.DataFrame)
    assert "symbol" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_dividend_calendar_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "date": "2024-05-10", "dividend": 0.25,
        "recordDate": "2024-05-13", "paymentDate": "2024-05-16",
    }])
    loader = FMPCalendarLoader(client)
    df = await loader.get_dividend_calendar(date(2024, 5, 1), date(2024, 5, 31))
    assert isinstance(df, pl.DataFrame)
    assert "dividend" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_ipo_calendar_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "XYZ", "company": "XYZ Corp", "date": "2024-05-15",
        "exchange": "NASDAQ", "priceRange": "$10-$12", "shares": 5000000,
    }])
    loader = FMPCalendarLoader(client)
    df = await loader.get_ipo_calendar(date(2024, 5, 1), date(2024, 5, 31))
    assert isinstance(df, pl.DataFrame)
    assert "company" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_splits_calendar_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "date": "2024-06-10", "numerator": 10.0, "denominator": 1.0,
    }])
    loader = FMPCalendarLoader(client)
    df = await loader.get_splits_calendar(date(2024, 6, 1), date(2024, 6, 30))
    assert isinstance(df, pl.DataFrame)
    assert "numerator" in df.columns
    await client.aclose()
```

- [ ] **Step 2: 写失败测试 — news**

```python
# tests/unit/providers/fmp/loaders/test_news.py
import pytest
from pytest_httpx import HTTPXMock
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.news import FMPNewsLoader
from deepalpha.loaders.enums import AssetClass

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

_ARTICLE = {
    "title": "Apple reports record earnings",
    "url": "https://example.com/apple",
    "publishedDate": "2024-05-02T18:00:00.000Z",
    "site": "Reuters",
    "text": "Apple Inc reported...",
    "symbol": "AAPL",
}

@pytest.mark.asyncio
async def test_get_news_by_symbols(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_ARTICLE])
    loader = FMPNewsLoader(client)
    df = await loader.get_news(symbols=["AAPL"], limit=5)
    assert isinstance(df, pl.DataFrame)
    assert "title" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_news_general(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_ARTICLE])
    loader = FMPNewsLoader(client)
    df = await loader.get_news(limit=10)
    assert isinstance(df, pl.DataFrame)
    await client.aclose()

@pytest.mark.asyncio
async def test_get_news_by_asset_class_crypto(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[_ARTICLE])
    loader = FMPNewsLoader(client)
    df = await loader.get_news(asset_class=AssetClass.CRYPTO, limit=5)
    assert isinstance(df, pl.DataFrame)
    await client.aclose()
```

- [ ] **Step 3: 运行验证失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_calendar.py tests/unit/providers/fmp/loaders/test_news.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 4: 实现 FMPCalendarLoader**

```python
# src/deepalpha/providers/fmp/loaders/calendar.py
from datetime import date
import polars as pl
from deepalpha.loaders.calendar import AbstractCalendarLoader
from deepalpha.models.calendar import EarningsEvent, DividendEvent, IPOEvent, SplitEvent

class FMPCalendarLoader(AbstractCalendarLoader):
    async def get_earnings_calendar(self, start: date, end: date) -> pl.DataFrame:
        records = await self._get_list(
            "/stable/earnings-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_df(records, EarningsEvent)

    async def get_dividend_calendar(self, start: date, end: date) -> pl.DataFrame:
        records = await self._get_list(
            "/stable/dividends-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_df(records, DividendEvent)

    async def get_ipo_calendar(self, start: date, end: date) -> pl.DataFrame:
        records = await self._get_list(
            "/stable/ipos-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_df(records, IPOEvent)

    async def get_splits_calendar(self, start: date, end: date) -> pl.DataFrame:
        records = await self._get_list(
            "/stable/splits-calendar", **{"from": str(start), "to": str(end)}
        )
        return self._to_df(records, SplitEvent)
```

- [ ] **Step 5: 实现 FMPNewsLoader**

```python
# src/deepalpha/providers/fmp/loaders/news.py
from datetime import date
import polars as pl
from deepalpha.loaders.news import AbstractNewsLoader
from deepalpha.loaders.enums import AssetClass
from deepalpha.models.news import NewsArticle

_ASSET_CLASS_PATHS: dict[AssetClass, str] = {
    AssetClass.CRYPTO: "crypto-news",
    AssetClass.FOREX:  "forex-news",
}

class FMPNewsLoader(AbstractNewsLoader):
    async def get_news(
        self,
        symbols: list[str] | None = None,
        asset_class: AssetClass | None = None,
        limit: int = 20,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame:
        params: dict[str, str | int] = {"limit": limit}
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)

        if symbols:
            params["tickers"] = ",".join(symbols)
            path = "/stable/search-stock-news"
        elif asset_class and asset_class in _ASSET_CLASS_PATHS:
            path = f"/stable/{_ASSET_CLASS_PATHS[asset_class]}"
        else:
            path = "/stable/general-news"

        records = await self._get_list(path, **params)
        return self._to_df(records, NewsArticle)
```

- [ ] **Step 6: 运行验证通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_calendar.py tests/unit/providers/fmp/loaders/test_news.py -v
```

Expected: 7 passed

- [ ] **Step 7: 提交**

```bash
git add src/deepalpha/providers/fmp/loaders/calendar.py src/deepalpha/providers/fmp/loaders/news.py tests/unit/providers/fmp/loaders/test_calendar.py tests/unit/providers/fmp/loaders/test_news.py
git commit -m "feat: implement FMPCalendarLoader and FMPNewsLoader"
```

---

### Task 12: FMPTechnicalIndicatorLoader + FMPEconomicsLoader

**Files:**

- Create: `src/deepalpha/providers/fmp/loaders/indicators.py`

- Create: `src/deepalpha/providers/fmp/loaders/economics.py`

- Create: `tests/unit/providers/fmp/loaders/test_indicators.py`

- Create: `tests/unit/providers/fmp/loaders/test_economics.py`

- [ ] **Step 1: 写失败测试 — indicators**

```python
# tests/unit/providers/fmp/loaders/test_indicators.py
import pytest
from pytest_httpx import HTTPXMock
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.indicators import FMPTechnicalIndicatorLoader
from deepalpha.providers.fmp.errors import FMPError
from deepalpha.loaders.enums import IndicatorType, Interval

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_sma_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-05-02", "value": 183.5, "open": 185.0, "high": 186.0, "low": 182.0, "close": 185.5, "volume": 50000000},
    ])
    loader = FMPTechnicalIndicatorLoader(client)
    df = await loader.get_indicator("AAPL", IndicatorType.SMA, period=20)
    assert isinstance(df, pl.DataFrame)
    assert "value" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_rsi_with_interval(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-05-02", "value": 62.3, "open": 185.0, "high": 186.0, "low": 182.0, "close": 185.5, "volume": 50000000},
    ])
    loader = FMPTechnicalIndicatorLoader(client)
    df = await loader.get_indicator(
        "AAPL", IndicatorType.RSI, period=14, interval=Interval.ONE_HOUR
    )
    assert isinstance(df, pl.DataFrame)
    assert "value" in df.columns
    await client.aclose()
```

- [ ] **Step 2: 写失败测试 — economics**

```python
# tests/unit/providers/fmp/loaders/test_economics.py
import pytest
from pytest_httpx import HTTPXMock
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.economics import FMPEconomicsLoader

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_cpi_indicator(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-03-01", "value": 3.5},
        {"date": "2024-02-01", "value": 3.2},
    ])
    loader = FMPEconomicsLoader(client)
    df = await loader.get_indicator("CPI")
    assert isinstance(df, pl.DataFrame)
    assert "value" in df.columns
    assert len(df) == 2
    await client.aclose()

@pytest.mark.asyncio
async def test_get_available_indicators_returns_list(httpx_mock: HTTPXMock, client):
    loader = FMPEconomicsLoader(client)
    indicators = await loader.get_available_indicators()
    assert isinstance(indicators, list)
    assert "CPI" in indicators
    await client.aclose()
```

- [ ] **Step 3: 运行验证失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_indicators.py tests/unit/providers/fmp/loaders/test_economics.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 4: 实现 FMPTechnicalIndicatorLoader**

FMP Start 支持 9 种指标，枚举名映射到 FMP 端点路径段：

```python
# src/deepalpha/providers/fmp/loaders/indicators.py
from datetime import date
import polars as pl
from deepalpha.loaders.indicators import AbstractTechnicalIndicatorLoader
from deepalpha.loaders.enums import IndicatorType, Interval
from deepalpha.models.indicators import IndicatorRow
from deepalpha.providers.fmp.errors import FMPError

_FMP_INDICATOR_PATHS: dict[IndicatorType, str] = {
    IndicatorType.SMA:      "simple-moving-average",
    IndicatorType.EMA:      "exponential-moving-average",
    IndicatorType.DEMA:     "double-exponential-moving-average",
    IndicatorType.TEMA:     "triple-exponential-moving-average",
    IndicatorType.WMA:      "weighted-moving-average",
    IndicatorType.RSI:      "relative-strength-index",
    IndicatorType.ADX:      "average-directional-index",
    IndicatorType.WILLIAMS: "williams-percent-range",
    IndicatorType.STD_DEV:  "standard-deviation",
}

class FMPTechnicalIndicatorLoader(AbstractTechnicalIndicatorLoader):
    async def get_indicator(
        self,
        symbol: str,
        indicator: IndicatorType,
        period: int,
        interval: Interval = Interval.ONE_DAY,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame:
        path_segment = _FMP_INDICATOR_PATHS.get(indicator)
        if path_segment is None:
            raise FMPError(
                f"FMP Start 不支持指标 {indicator}，请使用以下之一: "
                + ", ".join(_FMP_INDICATOR_PATHS.keys())
            )
        params: dict[str, str | int] = {
            "period": period,
            "type": interval.value,
        }
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)
        records = await self._get_list(
            f"/stable/{path_segment}/{symbol}", **params
        )
        return self._to_df(records, IndicatorRow)
```

- [ ] **Step 5: 实现 FMPEconomicsLoader**

```python
# src/deepalpha/providers/fmp/loaders/economics.py
from datetime import date
import polars as pl
from pydantic import BaseModel, Field
from deepalpha.loaders.economics import AbstractEconomicsLoader
from deepalpha.loaders.enums import Interval

_FMP_SUPPORTED: list[str] = [
    "CPI", "GDP", "REAL_GDP", "UNEMPLOYMENT",
    "FEDERAL_FUNDS_RATE", "TREASURY_YIELD", "RETAIL_SALES",
]

_FMP_ECON_PATHS: dict[str, str] = {
    "CPI":                 "cpi",
    "GDP":                 "gdp",
    "REAL_GDP":            "real-gdp",
    "UNEMPLOYMENT":        "unemployment",
    "FEDERAL_FUNDS_RATE":  "federal-funds-rate",
    "TREASURY_YIELD":      "treasury-yield",
    "RETAIL_SALES":        "retail-sales",
}

class _EconRow(BaseModel):
    date: date = Field(title="日期", description="经济指标数据对应的时间点")
    value: float | None = Field(None, title="指标值", description="经济指标的数值")

class FMPEconomicsLoader(AbstractEconomicsLoader):
    async def get_indicator(
        self,
        indicator_name: str,
        start: date | None = None,
        end: date | None = None,
        interval: Interval = Interval.ONE_MONTH,
    ) -> pl.DataFrame:
        path_seg = _FMP_ECON_PATHS.get(indicator_name.upper(), indicator_name.lower())
        params: dict[str, str] = {}
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)
        records = await self._get_list(f"/stable/{path_seg}", **params)
        return self._to_df(records, _EconRow)

    async def get_available_indicators(self) -> list[str]:
        return list(_FMP_SUPPORTED)
```

- [ ] **Step 6: 运行验证通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_indicators.py tests/unit/providers/fmp/loaders/test_economics.py -v
```

Expected: 4 passed

- [ ] **Step 7: 提交**

```bash
git add src/deepalpha/providers/fmp/loaders/indicators.py src/deepalpha/providers/fmp/loaders/economics.py tests/unit/providers/fmp/loaders/test_indicators.py tests/unit/providers/fmp/loaders/test_economics.py
git commit -m "feat: implement FMPTechnicalIndicatorLoader and FMPEconomicsLoader"
```

---

### Task 13: FMPInsiderTradeLoader + FMPSecFilingLoader + FMPMarketPerformanceLoader

**Files:**

- Create: `src/deepalpha/providers/fmp/loaders/insider.py`

- Create: `src/deepalpha/providers/fmp/loaders/filings.py`

- Create: `src/deepalpha/providers/fmp/loaders/performance.py`

- Create: `tests/unit/providers/fmp/loaders/test_insider.py`

- Create: `tests/unit/providers/fmp/loaders/test_filings.py`

- Create: `tests/unit/providers/fmp/loaders/test_performance.py`

- [ ] **Step 1: 写失败测试 — insider**

```python
# tests/unit/providers/fmp/loaders/test_insider.py
import pytest
from pytest_httpx import HTTPXMock
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.insider import FMPInsiderTradeLoader
from deepalpha.models.insider import InsiderStatistics

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_insider_trades_all_market(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "filingDate": "2024-05-01", "transactionDate": "2024-04-29",
        "reportingName": "Tim Cook", "typeOfSecurity": "Common Stock",
        "acquitionOrDisposition": "D", "shares": 100000, "price": 185.0,
    }])
    loader = FMPInsiderTradeLoader(client)
    df = await loader.get_insider_trades()
    assert isinstance(df, pl.DataFrame)
    assert "reporting_name" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_insider_trades_by_symbol(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "filingDate": "2024-05-01", "transactionDate": "2024-04-29",
        "reportingName": "Tim Cook", "typeOfSecurity": "Common Stock",
        "acquitionOrDisposition": "D", "shares": 100000, "price": 185.0,
    }])
    loader = FMPInsiderTradeLoader(client)
    df = await loader.get_insider_trades(symbol="AAPL", limit=10)
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 1
    await client.aclose()

@pytest.mark.asyncio
async def test_get_insider_statistics(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json={
        "symbol": "AAPL", "totalBought": 5, "totalSold": 20,
        "totalBoughtAmount": 900000.0, "totalSoldAmount": 3700000.0,
    })
    loader = FMPInsiderTradeLoader(client)
    stats = await loader.get_insider_statistics("AAPL")
    assert isinstance(stats, InsiderStatistics)
    assert stats.total_sold == 20
    await client.aclose()
```

- [ ] **Step 2: 写失败测试 — filings**

```python
# tests/unit/providers/fmp/loaders/test_filings.py
import pytest
from pytest_httpx import HTTPXMock
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.filings import FMPSecFilingLoader
from deepalpha.models.filings import SecCompanyProfile

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_filings_by_symbol(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL", "filingDate": "2024-05-02", "acceptedDate": "2024-05-02",
        "type": "10-Q", "link": "https://sec.gov/filing/aapl-10q.htm",
    }])
    loader = FMPSecFilingLoader(client)
    df = await loader.get_filings(symbol="AAPL", form_type="10-Q")
    assert isinstance(df, pl.DataFrame)
    assert "type" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sec_profile(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json={
        "cik": "0000320193", "symbol": "AAPL", "companyName": "Apple Inc.",
        "sic": "3674", "stateOfIncorporation": "CA", "fiscalYearEnd": "09",
    })
    loader = FMPSecFilingLoader(client)
    profile = await loader.get_sec_profile("AAPL")
    assert isinstance(profile, SecCompanyProfile)
    assert profile.cik == "0000320193"
    await client.aclose()
```

- [ ] **Step 3: 写失败测试 — performance**

```python
# tests/unit/providers/fmp/loaders/test_performance.py
import pytest
from pytest_httpx import HTTPXMock
from datetime import date
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.performance import FMPMarketPerformanceLoader
from deepalpha.loaders.enums import MoverDirection

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_movers_gainers(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "name": "NVIDIA", "change": 45.0,
        "price": 900.0, "changesPercentage": 5.26, "volume": 30000000,
    }])
    loader = FMPMarketPerformanceLoader(client)
    df = await loader.get_movers(MoverDirection.GAINERS, limit=10)
    assert isinstance(df, pl.DataFrame)
    assert "symbol" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sector_performance_snapshot(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"sector": "Technology", "changesPercentage": "1.23%"},
        {"sector": "Energy", "changesPercentage": "-0.45%"},
    ])
    loader = FMPMarketPerformanceLoader(client)
    df = await loader.get_sector_performance()
    assert isinstance(df, pl.DataFrame)
    assert "sector" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sector_pe_snapshot(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"date": "2024-05-02", "sector": "Technology", "pe": 32.5},
    ])
    loader = FMPMarketPerformanceLoader(client)
    df = await loader.get_sector_pe()
    assert isinstance(df, pl.DataFrame)
    assert "pe" in df.columns
    await client.aclose()
```

- [ ] **Step 4: 运行验证失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_insider.py tests/unit/providers/fmp/loaders/test_filings.py tests/unit/providers/fmp/loaders/test_performance.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 5: 实现 FMPInsiderTradeLoader**

```python
# src/deepalpha/providers/fmp/loaders/insider.py
import polars as pl
from deepalpha.loaders.insider import AbstractInsiderTradeLoader
from deepalpha.models.insider import InsiderTrade, InsiderStatistics

class FMPInsiderTradeLoader(AbstractInsiderTradeLoader):
    async def get_insider_trades(
        self, symbol: str | None = None, limit: int = 50, page: int = 0
    ) -> pl.DataFrame:
        if symbol:
            records = await self._get_list(
                "/stable/search-insider-trades",
                symbol=symbol, limit=limit, page=page,
            )
        else:
            records = await self._get_list(
                "/stable/latest-insider-trade", limit=limit, page=page
            )
        return self._to_df(records, InsiderTrade)

    async def get_insider_statistics(self, symbol: str) -> InsiderStatistics:
        data = await self._get(f"/stable/insider-trade-statistics/{symbol}")
        return InsiderStatistics.model_validate(data)
```

- [ ] **Step 6: 实现 FMPSecFilingLoader**

```python
# src/deepalpha/providers/fmp/loaders/filings.py
from datetime import date
import polars as pl
from deepalpha.loaders.filings import AbstractSecFilingLoader
from deepalpha.models.filings import SecFiling, SecCompanyProfile

class FMPSecFilingLoader(AbstractSecFilingLoader):
    async def get_filings(
        self,
        symbol: str | None = None,
        form_type: str | None = None,
        start: date | None = None,
        end: date | None = None,
        limit: int = 20,
    ) -> pl.DataFrame:
        params: dict[str, str | int] = {"limit": limit}
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)
        if symbol:
            params["symbol"] = symbol
            if form_type:
                params["type"] = form_type
            records = await self._get_list("/stable/search-by-symbol", **params)
        elif form_type:
            records = await self._get_list(
                "/stable/search-by-form-type", type=form_type, **params
            )
        else:
            records = await self._get_list("/stable/search-by-symbol", **params)
        return self._to_df(records, SecFiling)

    async def get_sec_profile(self, symbol: str) -> SecCompanyProfile:
        data = await self._get(f"/stable/sec-company-full-profile/{symbol}")
        return SecCompanyProfile.model_validate(data)
```

- [ ] **Step 7: 实现 FMPMarketPerformanceLoader**

```python
# src/deepalpha/providers/fmp/loaders/performance.py
from datetime import date
import polars as pl
from deepalpha.loaders.performance import AbstractMarketPerformanceLoader
from deepalpha.loaders.enums import MoverDirection
from deepalpha.models.performance import MarketMover, SectorPerformance, SectorPE

_MOVER_PATHS: dict[MoverDirection, str] = {
    MoverDirection.GAINERS: "biggest-gainers",
    MoverDirection.LOSERS:  "biggest-losers",
    MoverDirection.ACTIVE:  "most-active",
}

class FMPMarketPerformanceLoader(AbstractMarketPerformanceLoader):
    async def get_movers(
        self, direction: MoverDirection, limit: int = 20
    ) -> pl.DataFrame:
        path = _MOVER_PATHS[direction]
        records = await self._get_list(f"/stable/{path}", limit=limit)
        return self._to_df(records, MarketMover)

    async def get_sector_performance(self, date: date | None = None) -> pl.DataFrame:
        if date is None:
            records = await self._get_list("/stable/sector-performance-snapshot")
        else:
            records = await self._get_list(
                "/stable/historical-sector-performance", date=str(date)
            )
        return self._to_df(records, SectorPerformance)

    async def get_sector_pe(self, date: date | None = None) -> pl.DataFrame:
        if date is None:
            records = await self._get_list("/stable/sector-PE-snapshot")
        else:
            records = await self._get_list(
                "/stable/historical-sector-pe", date=str(date)
            )
        return self._to_df(records, SectorPE)
```

- [ ] **Step 8: 运行验证通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_insider.py tests/unit/providers/fmp/loaders/test_filings.py tests/unit/providers/fmp/loaders/test_performance.py -v
```

Expected: 8 passed

- [ ] **Step 9: 提交**

```bash
git add src/deepalpha/providers/fmp/loaders/insider.py src/deepalpha/providers/fmp/loaders/filings.py src/deepalpha/providers/fmp/loaders/performance.py tests/unit/providers/fmp/loaders/test_insider.py tests/unit/providers/fmp/loaders/test_filings.py tests/unit/providers/fmp/loaders/test_performance.py
git commit -m "feat: implement FMPInsiderTradeLoader, FMPSecFilingLoader, FMPMarketPerformanceLoader"
```

---

### Task 14: FMPCongressTradeLoader + FMPDirectoryLoader

**Files:**

- Create: `src/deepalpha/providers/fmp/loaders/congress.py`

- Create: `src/deepalpha/providers/fmp/loaders/directory.py`

- Create: `tests/unit/providers/fmp/loaders/test_congress.py`

- Create: `tests/unit/providers/fmp/loaders/test_directory.py`

- [ ] **Step 1: 写失败测试 — congress**

```python
# tests/unit/providers/fmp/loaders/test_congress.py
import pytest
from pytest_httpx import HTTPXMock
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.congress import FMPCongressTradeLoader
from deepalpha.loaders.enums import CongressChamber

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_senate_trades_latest(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "filingDate": "2024-04-15", "transactionDate": "2024-04-10",
        "representative": "John Smith", "district": None,
        "type": "Purchase", "amount": "$1,001 - $15,000", "assetDescription": "NVIDIA Corp",
    }])
    loader = FMPCongressTradeLoader(client)
    df = await loader.get_congress_trades(chamber=CongressChamber.SENATE)
    assert isinstance(df, pl.DataFrame)
    assert "representative" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_house_trades_by_symbol(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "NVDA", "filingDate": "2024-04-15", "transactionDate": "2024-04-10",
        "representative": "Jane Doe", "district": "CA-18",
        "type": "Sale", "amount": "$15,001 - $50,000", "assetDescription": "NVIDIA Corp",
    }])
    loader = FMPCongressTradeLoader(client)
    df = await loader.get_congress_trades(symbol="NVDA", chamber=CongressChamber.HOUSE)
    assert isinstance(df, pl.DataFrame)
    assert df["symbol"][0] == "NVDA"
    await client.aclose()
```

- [ ] **Step 2: 写失败测试 — directory**

```python
# tests/unit/providers/fmp/loaders/test_directory.py
import pytest
from pytest_httpx import HTTPXMock
import polars as pl
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders.directory import FMPDirectoryLoader
from deepalpha.loaders.enums import AssetClass

@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))

@pytest.mark.asyncio
async def test_get_symbols_stocks(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "exchangeShortName": "NASDAQ", "type": "stock"},
    ])
    loader = FMPDirectoryLoader(client)
    df = await loader.get_symbols(AssetClass.STOCK)
    assert isinstance(df, pl.DataFrame)
    assert "symbol" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_exchanges_returns_dataframe(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"exchange": "NASDAQ", "name": "NASDAQ", "country": "US", "currency": "USD"},
    ])
    loader = FMPDirectoryLoader(client)
    df = await loader.get_exchanges()
    assert isinstance(df, pl.DataFrame)
    assert "exchange" in df.columns
    await client.aclose()

@pytest.mark.asyncio
async def test_get_sectors_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"sector": "Technology"},
        {"sector": "Healthcare"},
    ])
    loader = FMPDirectoryLoader(client)
    sectors = await loader.get_sectors()
    assert isinstance(sectors, list)
    assert "Technology" in sectors
    await client.aclose()

@pytest.mark.asyncio
async def test_get_industries_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"industry": "Software"},
        {"industry": "Semiconductors"},
    ])
    loader = FMPDirectoryLoader(client)
    industries = await loader.get_industries()
    assert isinstance(industries, list)
    assert "Software" in industries
    await client.aclose()
```

- [ ] **Step 3: 运行验证失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_congress.py tests/unit/providers/fmp/loaders/test_directory.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 4: 实现 FMPCongressTradeLoader**

```python
# src/deepalpha/providers/fmp/loaders/congress.py
import polars as pl
from deepalpha.loaders.congress import AbstractCongressTradeLoader
from deepalpha.loaders.enums import CongressChamber
from deepalpha.models.congress import CongressTrade

class FMPCongressTradeLoader(AbstractCongressTradeLoader):
    async def get_congress_trades(
        self,
        symbol: str | None = None,
        chamber: CongressChamber = CongressChamber.SENATE,
        limit: int = 50,
        page: int = 0,
    ) -> pl.DataFrame:
        chamber_prefix = "senate" if chamber == CongressChamber.SENATE else "house-disclosure"
        if symbol:
            path = f"/stable/{chamber_prefix}-trading"
            params: dict[str, str | int] = {"symbol": symbol, "limit": limit, "page": page}
        else:
            path = f"/stable/{chamber_prefix}-latest"
            params = {"limit": limit, "page": page}
        records = await self._get_list(path, **params)
        return self._to_df(records, CongressTrade)
```

- [ ] **Step 5: 实现 FMPDirectoryLoader**

```python
# src/deepalpha/providers/fmp/loaders/directory.py
import polars as pl
from deepalpha.loaders.directory import AbstractDirectoryLoader
from deepalpha.loaders.enums import AssetClass
from deepalpha.models.directory import SymbolInfo, ExchangeInfo

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
    async def get_symbols(self, asset_class: AssetClass = AssetClass.STOCK) -> pl.DataFrame:
        path = _SYMBOL_PATHS.get(asset_class, "company-symbols-list")
        records = await self._get_list(f"/stable/{path}")
        return self._to_df(records, SymbolInfo)

    async def get_exchanges(self) -> pl.DataFrame:
        records = await self._get_list("/stable/available-exchanges")
        return self._to_df(records, ExchangeInfo)

    async def get_sectors(self) -> list[str]:
        records = await self._get_list("/stable/available-sectors")
        return [r.get("sector", "") for r in records if r.get("sector")]

    async def get_industries(self) -> list[str]:
        records = await self._get_list("/stable/available-industries")
        return [r.get("industry", "") for r in records if r.get("industry")]
```

- [ ] **Step 6: 运行验证通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_congress.py tests/unit/providers/fmp/loaders/test_directory.py -v
```

Expected: 6 passed

- [ ] **Step 7: 提交**

```bash
git add src/deepalpha/providers/fmp/loaders/congress.py src/deepalpha/providers/fmp/loaders/directory.py tests/unit/providers/fmp/loaders/test_congress.py tests/unit/providers/fmp/loaders/test_directory.py
git commit -m "feat: implement FMPCongressTradeLoader and FMPDirectoryLoader"
```

---

### Task 15: FMPDataHub 组装 + 包导出

**Files:**

- Modify: `src/deepalpha/providers/fmp/__init__.py`

- Modify: `src/deepalpha/providers/fmp/loaders/__init__.py`

- Modify: `src/deepalpha/models/__init__.py`

- Modify: `src/deepalpha/__init__.py`

- [ ] **Step 1: 写失败测试 — FMPDataHub 可实例化并实现 AbstractDataHub Protocol**

```python
# 在 tests/contracts/test_fmp_contracts.py 追加以下测试
import pytest
from deepalpha.providers.fmp import FMPDataHub
from deepalpha.loaders.hub import AbstractDataHub
from deepalpha.providers.fmp.config import FMPConfig

def test_fmp_data_hub_implements_abstract_data_hub():
    cfg = FMPConfig(api_key="test-key")
    hub = FMPDataHub(cfg)
    assert isinstance(hub, AbstractDataHub)

def test_fmp_data_hub_has_all_core_loaders():
    cfg = FMPConfig(api_key="test-key")
    hub = FMPDataHub(cfg)
    assert hasattr(hub, "market")
    assert hasattr(hub, "financial")
    assert hasattr(hub, "company")
    assert hasattr(hub, "analyst")
    assert hasattr(hub, "calendar")
    assert hasattr(hub, "news")

def test_fmp_data_hub_has_all_extended_loaders():
    cfg = FMPConfig(api_key="test-key")
    hub = FMPDataHub(cfg)
    assert hasattr(hub, "indicators")
    assert hasattr(hub, "economics")
    assert hasattr(hub, "insider")
    assert hasattr(hub, "filings")
    assert hasattr(hub, "performance")
    assert hasattr(hub, "congress")
    assert hasattr(hub, "directory")
```

- [ ] **Step 2: 运行验证失败**

```bash
uv run pytest tests/contracts/test_fmp_contracts.py -v
```

Expected: `ImportError: cannot import name 'FMPDataHub'`

- [ ] **Step 3: 实现 `providers/fmp/loaders/__init__.py`**

```python
# src/deepalpha/providers/fmp/loaders/__init__.py
from deepalpha.providers.fmp.loaders.market import FMPMarketLoader
from deepalpha.providers.fmp.loaders.financial import FMPFinancialLoader
from deepalpha.providers.fmp.loaders.company import FMPCompanyLoader
from deepalpha.providers.fmp.loaders.analyst import FMPAnalystLoader
from deepalpha.providers.fmp.loaders.calendar import FMPCalendarLoader
from deepalpha.providers.fmp.loaders.news import FMPNewsLoader
from deepalpha.providers.fmp.loaders.indicators import FMPTechnicalIndicatorLoader
from deepalpha.providers.fmp.loaders.economics import FMPEconomicsLoader
from deepalpha.providers.fmp.loaders.insider import FMPInsiderTradeLoader
from deepalpha.providers.fmp.loaders.filings import FMPSecFilingLoader
from deepalpha.providers.fmp.loaders.performance import FMPMarketPerformanceLoader
from deepalpha.providers.fmp.loaders.congress import FMPCongressTradeLoader
from deepalpha.providers.fmp.loaders.directory import FMPDirectoryLoader

__all__ = [
    "FMPMarketLoader", "FMPFinancialLoader", "FMPCompanyLoader",
    "FMPAnalystLoader", "FMPCalendarLoader", "FMPNewsLoader",
    "FMPTechnicalIndicatorLoader", "FMPEconomicsLoader",
    "FMPInsiderTradeLoader", "FMPSecFilingLoader",
    "FMPMarketPerformanceLoader", "FMPCongressTradeLoader", "FMPDirectoryLoader",
]
```

- [ ] **Step 4: 实现 `FMPDataHub` (`providers/fmp/__init__.py`)**

```python
# src/deepalpha/providers/fmp/__init__.py
from typing import Any
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders import (
    FMPMarketLoader, FMPFinancialLoader, FMPCompanyLoader,
    FMPAnalystLoader, FMPCalendarLoader, FMPNewsLoader,
    FMPTechnicalIndicatorLoader, FMPEconomicsLoader,
    FMPInsiderTradeLoader, FMPSecFilingLoader,
    FMPMarketPerformanceLoader, FMPCongressTradeLoader, FMPDirectoryLoader,
)

class FMPDataHub:
    """FMP 数据中枢，实现 AbstractDataHub Protocol（Core）并提供全部 Extended loader。

    使用 async with 上下文管理器确保 HTTP 连接正确关闭：

        async with FMPDataHub() as hub:
            quote = await hub.market.get_quote("AAPL")
    """

    def __init__(self, config: FMPConfig | None = None) -> None:
        cfg = config or FMPConfig()
        self._client = FMPAsyncClient(cfg)
        # Core loaders（AbstractDataHub Protocol 要求）
        self.market      = FMPMarketLoader(self._client)
        self.financial   = FMPFinancialLoader(self._client)
        self.company     = FMPCompanyLoader(self._client)
        self.analyst     = FMPAnalystLoader(self._client)
        self.calendar    = FMPCalendarLoader(self._client)
        self.news        = FMPNewsLoader(self._client)
        # Extended loaders（FMP Start 全部支持）
        self.indicators  = FMPTechnicalIndicatorLoader(self._client)
        self.economics   = FMPEconomicsLoader(self._client)
        self.insider     = FMPInsiderTradeLoader(self._client)
        self.filings     = FMPSecFilingLoader(self._client)
        self.performance = FMPMarketPerformanceLoader(self._client)
        self.congress    = FMPCongressTradeLoader(self._client)
        self.directory   = FMPDirectoryLoader(self._client)

    async def __aenter__(self) -> "FMPDataHub":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._client.aclose()
```

- [ ] **Step 5: 实现 `models/__init__.py`**

```python
# src/deepalpha/models/__init__.py
from deepalpha.models.market import Quote, PriceBar
from deepalpha.models.financial import (
    IncomeStatement, BalanceSheet, CashFlow,
    FinancialRatio, KeyMetrics, Valuation,
)
from deepalpha.models.company import CompanyProfile, Executive, MarketCapRecord
from deepalpha.models.analyst import AnalystRating, PriceTarget, Estimate
from deepalpha.models.calendar import EarningsEvent, DividendEvent, IPOEvent, SplitEvent
from deepalpha.models.news import NewsArticle
from deepalpha.models.indicators import IndicatorRow
from deepalpha.models.insider import InsiderTrade, InsiderStatistics
from deepalpha.models.filings import SecFiling, SecCompanyProfile
from deepalpha.models.performance import MarketMover, SectorPerformance, SectorPE
from deepalpha.models.congress import CongressTrade
from deepalpha.models.directory import SymbolInfo, ExchangeInfo

__all__ = [
    "Quote", "PriceBar",
    "IncomeStatement", "BalanceSheet", "CashFlow",
    "FinancialRatio", "KeyMetrics", "Valuation",
    "CompanyProfile", "Executive", "MarketCapRecord",
    "AnalystRating", "PriceTarget", "Estimate",
    "EarningsEvent", "DividendEvent", "IPOEvent", "SplitEvent",
    "NewsArticle", "IndicatorRow",
    "InsiderTrade", "InsiderStatistics",
    "SecFiling", "SecCompanyProfile",
    "MarketMover", "SectorPerformance", "SectorPE",
    "CongressTrade", "SymbolInfo", "ExchangeInfo",
]
```

- [ ] **Step 6: 更新顶层 `src/deepalpha/__init__.py`**

```python
# src/deepalpha/__init__.py
from deepalpha.providers.fmp import FMPDataHub
from deepalpha.loaders import AbstractDataHub
from deepalpha.loaders.enums import (
    AssetClass, Interval, StatementPeriod,
    IndicatorType, MoverDirection, CongressChamber,
)

__all__ = [
    "FMPDataHub",
    "AbstractDataHub",
    "AssetClass", "Interval", "StatementPeriod",
    "IndicatorType", "MoverDirection", "CongressChamber",
]
```

- [ ] **Step 7: 运行验证通过**

```bash
uv run pytest tests/contracts/test_fmp_contracts.py -v
```

Expected: 3 passed（新增的 3 条 + 原有 1 条 = 4 passed 合计）

- [ ] **Step 8: 提交**

```bash
git add src/deepalpha/ tests/contracts/test_fmp_contracts.py
git commit -m "feat: assemble FMPDataHub and wire all package exports"
```

---

### Task 16: 全量测试 + 集成测试脚手架

**Files:**

- Create: `tests/integration/test_fmp_integration.py`

- Modify: `pyproject.toml`（添加 pytest 配置）

- [ ] **Step 1: 写集成测试脚手架（用 mark.integration 保护，默认跳过）**

```python
# tests/integration/test_fmp_integration.py
"""集成测试 — 需要真实 FMP_API_KEY 环境变量，仅在 CI 中按需运行。

运行方式：
    FMP_API_KEY=your_key uv run pytest tests/integration/ -v -m integration
"""
import pytest
from deepalpha import FMPDataHub

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_quote_real_aapl():
    async with FMPDataHub() as hub:
        quote = await hub.market.get_quote("AAPL")
    assert quote.symbol == "AAPL"
    assert quote.price > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_income_statement_real():
    async with FMPDataHub() as hub:
        df = await hub.financial.get_income_statement("AAPL", limit=1)
    assert len(df) == 1
    assert "revenue" in df.columns

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_sector_performance_real():
    async with FMPDataHub() as hub:
        df = await hub.performance.get_sector_performance()
    assert len(df) > 0
    assert "sector" in df.columns
```

- [ ] **Step 2: 在 `pyproject.toml` 添加 pytest 配置**

在 `pyproject.toml` 末尾追加：

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: 需要真实 FMP API Key 才能运行（使用 -m integration 选择执行）",
]
```

- [ ] **Step 3: 运行全量单元测试**

```bash
uv run pytest tests/unit/ tests/contracts/ -v --tb=short
```

Expected: 全部 passed，无跳过，无报错。

- [ ] **Step 4: 确认集成测试被正确跳过**

```bash
uv run pytest tests/ -v --ignore=tests/integration/
```

Expected: 所有单元 + 契约测试 passed，integration/ 未被收集。

- [ ] **Step 5: 提交**

```bash
git add tests/integration/test_fmp_integration.py pyproject.toml
git commit -m "test: add integration test scaffold and pytest config"
```

---

## 实现完成后验证清单

运行以下命令确认全量通过：

```bash
# 所有单元测试 + 契约测试（无需 API Key）
uv run pytest tests/unit/ tests/contracts/ -v

# 类型检查
uv run mypy src/deepalpha/ --ignore-missing-imports

# 代码风格
uv run ruff check src/ tests/
```
