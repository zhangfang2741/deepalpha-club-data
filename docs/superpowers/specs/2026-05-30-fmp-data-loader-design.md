# FMP 数据加载能力设计文档

**日期**：2026-05-30  
**状态**：已批准  
**覆盖范围**：FMP Start 会员全部可访问数据类别

---

## 1. 背景与目标

在 `deepalpha` Python 包中构建一套基于 FMP（Financial Modeling Prep）Start 会员的分类数据加载能力。该能力需满足：

- 覆盖 FMP Start 会员 12 个数据类别的全部可访问 API 端点
- 使用面向对象设计，职责分层清晰
- 数据模型（`models/`）和抽象接口（`loaders/`）与具体数据提供商解耦，支持未来接入 yfinance 等其他数据源
- 所有 Pydantic 模型字段通过 `Field(title="中文名", description="...")` 提供中文语义标注
- 单条查询返回 Pydantic 对象，批量查询返回 Polars DataFrame
- HTTP 层使用 httpx 异步客户端，支持速率限制和指数退避重试

---

## 2. 整体架构

### 分层结构

```
src/deepalpha/
├── models/                   # 规范数据模型（与数据源无关）
│   ├── __init__.py
│   ├── market.py
│   ├── financial.py
│   ├── company.py
│   ├── analyst.py
│   ├── calendar.py
│   ├── news.py
│   ├── indicators.py
│   ├── insider.py
│   ├── filings.py
│   ├── performance.py
│   ├── congress.py
│   └── directory.py
│
├── loaders/                  # 抽象基础 Loader（各类别接口契约）
│   ├── __init__.py
│   ├── base.py               # BaseLoader ABC
│   ├── market.py             # AbstractMarketLoader
│   ├── financial.py          # AbstractFinancialLoader
│   ├── company.py            # AbstractCompanyLoader
│   ├── analyst.py            # AbstractAnalystLoader
│   ├── calendar.py           # AbstractCalendarLoader
│   ├── news.py               # AbstractNewsLoader
│   ├── indicators.py         # AbstractTechnicalLoader
│   ├── insider.py            # AbstractInsiderLoader
│   ├── filings.py            # AbstractSecFilingLoader
│   ├── performance.py        # AbstractMarketPerfLoader
│   ├── congress.py           # AbstractCongressLoader
│   └── directory.py          # AbstractDirectoryLoader
│
└── providers/
    ├── fmp/                  # FMP 提供商实现
    │   ├── __init__.py       # 导出 FMPDataHub
    │   ├── client.py         # FMPAsyncClient
    │   ├── config.py         # FMPConfig
    │   └── loaders/          # FMP 对各 AbstractLoader 的实现
    │       ├── __init__.py
    │       ├── market.py
    │       ├── financial.py
    │       ├── company.py
    │       ├── analyst.py
    │       ├── calendar.py
    │       ├── news.py
    │       ├── indicators.py
    │       ├── insider.py
    │       ├── filings.py
    │       ├── performance.py
    │       ├── congress.py
    │       └── directory.py
    └── yfinance/             # 未来扩展（实现相同 AbstractLoader 接口）
```

### 分层职责

| 层 | 职责 | 依赖 |
|---|---|---|
| `models/` | 规范数据结构，含中文字段标注 | 仅 pydantic |
| `loaders/base.py` | HTTP 调用、错误处理、DataFrame 转换 | httpx, polars |
| `loaders/*.py` | 定义各类别业务方法的抽象签名 | models/, base |
| `providers/fmp/client.py` | FMP HTTP 连接、速率限制、重试 | httpx |
| `providers/fmp/loaders/` | FMP JSON → 规范模型的映射实现 | loaders/, client |
| `providers/fmp/FMPDataHub` | 聚合所有 FMP loader，作为唯一入口 | 所有 FMP loaders |

---

## 3. 核心组件设计

### 3.1 `BaseLoader` ABC

`BaseLoader` 通过 `AsyncDataClient` Protocol 接受任意 provider 的客户端，保持通用层与 FMP 实现解耦。

```python
# src/deepalpha/loaders/base.py
from abc import ABC
from typing import Protocol, Any
import polars as pl
from pydantic import BaseModel

class AsyncDataClient(Protocol):
    """任意异步数据客户端需实现的最小接口"""
    async def get(self, path: str, **params: Any) -> Any: ...

class BaseLoader(ABC):
    def __init__(self, client: AsyncDataClient) -> None:
        self._client = client

    async def _get(self, endpoint: str, **params) -> dict:
        """发起单对象请求，返回原始 dict，空响应抛出 FMPNotFoundError"""
        ...

    async def _get_list(self, endpoint: str, **params) -> list[dict]:
        """发起列表请求，返回原始 list[dict]"""
        ...

    def _to_df(self, records: list[dict], model: type[BaseModel]) -> pl.DataFrame:
        """将 list[dict] 通过 model.model_validate 解析后转换为 Polars DataFrame"""
        validated = [model.model_validate(r) for r in records]
        return pl.DataFrame([v.model_dump() for v in validated])
```

### 3.2 共享枚举类型（`loaders/enums.py`）

抽象接口使用枚举约束参数，避免魔术字符串，也便于不同 provider 验证自身支持范围：

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
    ONE_MIN    = "1m"
    FIVE_MIN   = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN = "30m"
    ONE_HOUR   = "1h"
    FOUR_HOUR  = "4h"
    ONE_DAY    = "1d"
    ONE_WEEK   = "1w"
    ONE_MONTH  = "1mo"

class StatementPeriod(StrEnum):
    ANNUAL  = "annual"
    QUARTER = "quarter"
    TTM     = "ttm"      # Trailing Twelve Months

class IndicatorType(StrEnum):
    SMA     = "sma"
    EMA     = "ema"
    DEMA    = "dema"
    TEMA    = "tema"
    WMA     = "wma"
    RSI     = "rsi"
    ADX     = "adx"
    WILLIAMS = "williams"
    STD_DEV = "std_dev"

class MoverDirection(StrEnum):
    GAINERS = "gainers"
    LOSERS  = "losers"
    ACTIVE  = "active"

class CongressChamber(StrEnum):
    SENATE = "senate"
    HOUSE  = "house"
```

---

### 3.3 Abstract Loader 接口设计

**设计原则**：方法签名以金融领域语义为中心，不绑定任何 provider 的 endpoint 结构。同一个抽象方法可由不同 provider 通过不同端点或参数组合实现。

#### `AbstractMarketLoader`

```python
class AbstractMarketLoader(BaseLoader):
    # 单条报价 → Pydantic 对象
    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote: ...

    # 批量报价 → DataFrame
    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> pl.DataFrame: ...

    # 统一历史行情：interval="1d" 为日线，"1h"/"5m" 等为日内
    # 不同 provider 内部路由到各自端点，调用方无感知
    @abstractmethod
    async def get_price_history(
        self,
        symbol: str,
        start: date,
        end: date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> pl.DataFrame: ...

    # 全市场快照，按资产类别区分
    @abstractmethod
    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> pl.DataFrame: ...
```

> **FMP 实现映射**：`interval=ONE_DAY` → `historical-price-eod-full`；`interval=ONE_HOUR` → `intraday-1-hour`；`adjusted=False` → `historical-price-eod-non-split-adjusted`；`asset_class=CRYPTO` → `full-cryptocurrency-quotes`。

---

#### `AbstractFinancialLoader`

```python
class AbstractFinancialLoader(BaseLoader):
    # 三张表统一用 period 参数，"ttm" 即 TTM，不需要独立方法
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

---

#### `AbstractCompanyLoader`

```python
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

---

#### `AbstractAnalystLoader`

```python
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

---

#### `AbstractCalendarLoader`

```python
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

---

#### `AbstractNewsLoader`

```python
class AbstractNewsLoader(BaseLoader):
    # symbols=None 表示全市场新闻；asset_class 用于过滤加密/外汇等
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

---

#### `AbstractTechnicalLoader`

```python
class AbstractTechnicalLoader(BaseLoader):
    # 统一接口，indicator 参数决定计算类型
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

---

#### `AbstractInsiderLoader`

```python
class AbstractInsiderLoader(BaseLoader):
    # symbol=None 返回全市场最新；有 symbol 则过滤
    @abstractmethod
    async def get_trades(
        self, symbol: str | None = None, limit: int = 50, page: int = 0
    ) -> pl.DataFrame: ...

    @abstractmethod
    async def get_statistics(self, symbol: str) -> InsiderStatistics: ...
```

---

#### `AbstractSecFilingLoader`

```python
class AbstractSecFilingLoader(BaseLoader):
    # 统一查询入口，symbol/form_type 可选
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
    async def get_company_profile(self, symbol: str) -> SecCompanyProfile: ...
```

---

#### `AbstractMarketPerfLoader`

```python
class AbstractMarketPerfLoader(BaseLoader):
    # direction 枚举统一三种榜单
    @abstractmethod
    async def get_movers(
        self, direction: MoverDirection, limit: int = 20
    ) -> pl.DataFrame: ...

    @abstractmethod
    async def get_sector_performance(self, date: date | None = None) -> pl.DataFrame: ...

    @abstractmethod
    async def get_sector_pe(self, date: date | None = None) -> pl.DataFrame: ...
```

---

#### `AbstractCongressLoader`

```python
class AbstractCongressLoader(BaseLoader):
    # chamber 枚举统一参众两院
    @abstractmethod
    async def get_trades(
        self,
        symbol: str | None = None,
        chamber: CongressChamber = CongressChamber.SENATE,
        limit: int = 50,
        page: int = 0,
    ) -> pl.DataFrame: ...
```

---

#### `AbstractDirectoryLoader`

```python
class AbstractDirectoryLoader(BaseLoader):
    # asset_class 过滤标的类别
    @abstractmethod
    async def get_symbols(self, asset_class: AssetClass = AssetClass.STOCK) -> pl.DataFrame: ...

    @abstractmethod
    async def get_exchanges(self) -> pl.DataFrame: ...

    @abstractmethod
    async def get_sectors(self) -> list[str]: ...

    @abstractmethod
    async def get_industries(self) -> list[str]: ...
```

### 3.4 `FMPAsyncClient`

```python
# src/deepalpha/providers/fmp/client.py
import httpx
from deepalpha.providers.fmp.config import FMPConfig

class FMPAsyncClient:
    def __init__(self, config: FMPConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            limits=httpx.Limits(max_connections=config.max_connections),
        )

    async def get(self, path: str, **params) -> Any:
        """发起 GET 请求，自动附加 apikey，处理 HTTP 错误，支持指数退避重试"""
        ...

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self): return self
    async def __aexit__(self, *_): await self.aclose()
```

**重试策略**：遇到 5xx 错误时使用指数退避（初始 1s，最多 `max_retries` 次），429 错误等待 `Retry-After` 响应头指定的时间后重试。

### 3.5 `FMPConfig`

```python
# src/deepalpha/providers/fmp/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class FMPConfig(BaseSettings):
    api_key: str = Field(title="API 密钥", description="FMP API Key，从环境变量 FMP_API_KEY 读取")
    base_url: str = Field("https://financialmodelingprep.com/api", title="API 基础地址")
    timeout: float = Field(30.0, title="超时时间", description="单次请求超时秒数")
    max_connections: int = Field(10, title="最大并发连接数")
    max_retries: int = Field(3, title="最大重试次数", description="5xx 时的指数退避重试次数")

    model_config = SettingsConfigDict(env_prefix="FMP_", env_file=".env")
```

### 3.6 Pydantic 模型规范

所有模型继承 `pydantic.BaseModel`，使用 `model_config = ConfigDict(populate_by_name=True)` 以兼容 FMP camelCase 字段名。

字段标注示例：

```python
# src/deepalpha/models/market.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class StockQuote(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symbol: str = Field(title="股票代码", description="交易所上市代码，如 AAPL")
    price: float = Field(title="最新价格", description="最近一次成交价格（美元）")
    change: float = Field(title="涨跌额", description="相对上一收盘价的价格变动")
    change_percent: float = Field(title="涨跌幅", description="涨跌额占上一收盘价的百分比")
    volume: int = Field(title="成交量", description="当日已成交股数")
    market_cap: float | None = Field(None, title="市值", description="总市值（美元）")
    pe_ratio: float | None = Field(None, title="市盈率", description="Price/Earnings 比率")
    eps: float | None = Field(None, title="每股收益", description="Earnings Per Share（美元）")
    timestamp: datetime = Field(title="时间戳", description="报价数据的生成时间（UTC）")
```

### 3.7 `FMPDataHub`

```python
# src/deepalpha/providers/fmp/__init__.py
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders import (
    FMPMarketLoader, FMPFinancialLoader, FMPCompanyLoader,
    FMPAnalystLoader, FMPCalendarLoader, FMPNewsLoader,
    FMPTechnicalLoader, FMPInsiderLoader, FMPSecFilingLoader,
    FMPMarketPerfLoader, FMPCongressLoader, FMPDirectoryLoader,
)

class FMPDataHub:
    def __init__(self, config: FMPConfig | None = None) -> None:
        cfg = config or FMPConfig()
        self._client = FMPAsyncClient(cfg)
        self.market      = FMPMarketLoader(self._client)
        self.financial   = FMPFinancialLoader(self._client)
        self.company     = FMPCompanyLoader(self._client)
        self.analyst     = FMPAnalystLoader(self._client)
        self.calendar    = FMPCalendarLoader(self._client)
        self.news        = FMPNewsLoader(self._client)
        self.indicators  = FMPTechnicalLoader(self._client)
        self.insider     = FMPInsiderLoader(self._client)
        self.filings     = FMPSecFilingLoader(self._client)
        self.performance = FMPMarketPerfLoader(self._client)
        self.congress    = FMPCongressLoader(self._client)
        self.directory   = FMPDirectoryLoader(self._client)

    async def __aenter__(self): return self
    async def __aexit__(self, *_): await self._client.aclose()
```

**使用示例：**

```python
async with FMPDataHub() as hub:
    # 单条 → Pydantic 对象
    quote = await hub.market.get_quote("AAPL")
    print(quote.price, quote.change_percent)

    # 批量 → Polars DataFrame
    df = await hub.financial.get_income_statements("TSLA", period="quarter", limit=8)
    print(df.schema)
```

---

## 4. FMP Start 会员数据覆盖范围

### 4.1 MarketLoader — 行情数据

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_quote(symbol)` | `GET /stable/quote/{symbol}` |
| `get_quotes(symbols)` | `GET /stable/quotes-batch` |
| `get_price_history(symbol, interval="1d", adjusted=True)` | `historical-price-eod-full`；`adjusted=False` → `non-split-adjusted` |
| `get_price_history(symbol, interval="1h"\|"5m"\|...)` | `intraday-1-hour` / `intraday-5-min` 等，由 interval 值路由 |
| `get_market_snapshot(asset_class=STOCK)` | `full-exchange-quotes`；CRYPTO→`full-cryptocurrency-quotes`；ETF→`full-etf-quotes` 等 |

> **FMP 具体实现可额外提供** `get_aftermarket_quote`、`get_price_change` 等非抽象方法，供需要 FMP 特有数据时调用，不影响接口契约。

### 4.2 FinancialLoader — 财务报表

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_income_statement(symbol, period="annual"\|"quarter"\|"ttm")` | `income-statement`；`ttm` → `income-statements-ttm` |
| `get_balance_sheet(symbol, period, limit)` | `balance-sheet-statement`；`ttm` → `balance-sheet-statements-ttm` |
| `get_cash_flow_statement(symbol, period, limit)` | `cashflow-statement`；`ttm` → `cashflow-statements-ttm` |
| `get_financial_ratios(symbol, period, limit)` | `metrics-ratios`；`ttm` → `metrics-ratios-ttm` |
| `get_key_metrics(symbol, period, limit)` | `key-metrics`；`ttm` → `key-metrics-ttm` |
| `get_valuation(symbol)` | `dcf-advanced`（返回 DCF + 企业价值合并对象） |

> **FMP 额外方法**（非抽象）：`get_owner_earnings`、`get_revenue_segments`、`get_financial_scores`、`get_as_reported_statements`、`get_statement_growth`。

### 4.3 CompanyLoader — 公司数据

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_profile(symbol)` | `profile-symbol` |
| `get_executives(symbol)` | `company-executives` |
| `get_peers(symbol)` | `peers` |
| `get_market_cap(symbol, start, end)` | `start/end=None` → `market-cap`；有日期范围 → `historical-market-cap` |

> **FMP 额外方法**：`get_profile_by_cik`、`get_shares_float`、`get_employee_count`、`get_mergers_acquisitions`、`get_executive_compensation`。

### 4.4 AnalystLoader — 分析师数据

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_ratings(symbol)` | `historical-ratings`（含历史综合评分） |
| `get_price_targets(symbol)` | `price-target-summary` + `price-target-consensus` 合并 |
| `get_estimates(symbol, period)` | `financial-estimates` |

> **FMP 额外方法**：`get_grades`、`get_grades_summary`、`get_ratings_snapshot`。

### 4.5 CalendarLoader — 市场日历

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_earnings_calendar(start, end)` | `earnings-calendar`；可附加 `earnings-company(symbol)` 作为可选参数路由 |
| `get_dividend_calendar(start, end)` | `dividends-calendar` |
| `get_ipo_calendar(start, end)` | `ipos-calendar` |
| `get_splits_calendar(start, end)` | `splits-calendar` |

> **FMP 额外方法**：`get_ipo_prospectus`、`get_ipo_disclosure`、`get_company_dividends`、`get_company_splits`。

### 4.6 NewsLoader — 新闻

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_news(symbols=None, asset_class=None, ...)` | `symbols` 有值 → `search-stock-news`；`asset_class=CRYPTO` → `crypto-news`；`asset_class=FOREX` → `forex-news`；无参数 → `general-news` |

> **FMP 额外方法**：`get_press_releases`、`get_fmp_articles`。

### 4.7 TechnicalLoader — 技术指标

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_indicator(symbol, indicator, period, interval, ...)` | `indicator` 值路由到对应端点：`SMA`→`simple-moving-average`，`RSI`→`relative-strength-index`，等 |

FMP 支持的 `indicator` 值：`SMA`、`EMA`、`DEMA`、`TEMA`、`WMA`、`RSI`、`ADX`、`WILLIAMS`、`STD_DEV`

### 4.8 InsiderLoader — 内部人交易

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_trades(symbol=None, limit, page)` | `symbol=None` → `latest-insider-trade`；有值 → `search-insider-trades?symbol=...` |
| `get_statistics(symbol)` | `insider-trade-statistics` |

> **FMP 额外方法**：`get_trades_by_reporting_name`、`get_acquisition_ownership`。

### 4.9 SecFilingLoader — SEC 文件

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_filings(symbol, form_type, start, end, limit)` | 参数组合路由：有 `symbol` → `search-by-symbol`；有 `form_type` → `search-by-form-type`；都有 → 优先 symbol，form_type 作过滤 |
| `get_company_profile(symbol)` | `sec-company-full-profile` |

> **FMP 额外方法**：`get_latest_8k`、`get_latest_financial_filings`、`get_industry_classification`、`get_filings_by_cik`、`get_filings_by_name`。

### 4.10 MarketPerfLoader — 市场表现

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_movers(direction=GAINERS\|LOSERS\|ACTIVE, limit)` | `biggest-gainers` / `biggest-losers` / `most-active` |
| `get_sector_performance(date=None)` | `date=None` → `sector-performance-snapshot`；有值 → `historical-sector-performance` |
| `get_sector_pe(date=None)` | `date=None` → `sector-PE-snapshot`；有值 → `historical-sector-pe` |

> **FMP 额外方法**：`get_industry_performance`、`get_industry_pe`（行业级别，抽象层暂只定义板块级）。

### 4.11 CongressLoader — 国会交易披露

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_trades(symbol=None, chamber=SENATE\|HOUSE, limit, page)` | `chamber=SENATE + symbol=None` → `senate-latest`；有 symbol → `senate-trading`；`HOUSE` 同理路由 |

### 4.12 DirectoryLoader — 参考目录

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_symbols(asset_class=STOCK)` | `STOCK` → `actively-trading-list`；`ETF` → `ETFs-list`；其他 → `company-symbols-list` |
| `get_exchanges()` | `available-exchanges` |
| `get_sectors()` | `available-sectors` |
| `get_industries()` | `available-industries` |

---

## 5. 错误处理

```python
class FMPError(Exception): ...          # 基类
class FMPAuthError(FMPError): ...       # 401 — API Key 无效或过期
class FMPRateLimitError(FMPError): ...  # 429 — 超出速率限制
class FMPNotFoundError(FMPError): ...   # 404 或空响应 — 标的不存在
class FMPServerError(FMPError): ...     # 5xx — FMP 服务端错误
```

- `FMPAsyncClient.get()` 统一处理 HTTP 状态码并抛出对应异常
- 空列表响应视为 `FMPNotFoundError`
- Loader 方法不捕获异常，直接向上传播
- 重试策略：5xx 使用指数退避（初始 1s，最多 `max_retries` 次）；429 等待 `Retry-After` 响应头指定时间

---

## 6. 测试策略

| 测试类型 | 工具 | 覆盖内容 |
|---|---|---|
| 单元测试 | `pytest` + `pytest-httpx` | mock HTTP 响应，验证每个 Loader 的字段映射和解析逻辑 |
| 模型测试 | `pytest` | 通过 `model_json_schema()` 断言所有字段具有非空 `title` 和 `description` |
| 集成测试 | `pytest` + `@pytest.mark.integration` | 需真实 API Key，验证 FMP 端点可达，仅 CI 中按需运行 |
| 契约测试 | `pytest` | 验证每个 FMP Loader 完整实现对应 AbstractLoader 的所有抽象方法 |

---

## 7. 未来扩展

接入新数据提供商（如 yfinance）只需：
1. 在 `providers/yfinance/` 下实现对应 `AbstractXxxLoader` 子类
2. 创建 `YFinanceDataHub`，聚合所有 YFinance loader
3. `models/` 和 `loaders/`（ABC 层）无需修改
