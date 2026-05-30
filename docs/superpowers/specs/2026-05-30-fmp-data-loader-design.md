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

### 3.2 Abstract Loader 示例

```python
# src/deepalpha/loaders/market.py
from abc import abstractmethod
import polars as pl
from deepalpha.loaders.base import BaseLoader
from deepalpha.models.market import StockQuote, PriceBar

class AbstractMarketLoader(BaseLoader):
    @abstractmethod
    async def get_quote(self, symbol: str) -> StockQuote: ...

    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> pl.DataFrame: ...

    @abstractmethod
    async def get_historical_prices(
        self, symbol: str, from_date: str, to_date: str
    ) -> pl.DataFrame: ...

    @abstractmethod
    async def get_intraday(
        self, symbol: str, interval: str, from_date: str, to_date: str
    ) -> pl.DataFrame: ...
```

### 3.3 `FMPAsyncClient`

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

### 3.4 `FMPConfig`

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

### 3.5 Pydantic 模型规范

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

### 3.6 `FMPDataHub`

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

| 方法 | 返回类型 | 说明 |
|---|---|---|
| `get_quote(symbol)` | `StockQuote` | 单股实时报价 |
| `get_quotes(symbols)` | `DataFrame[StockQuote]` | 批量实时报价 |
| `get_quote_short(symbol)` | `StockQuoteShort` | 简版报价（价格+成交量） |
| `get_price_change(symbol)` | `PriceChange` | 多周期涨跌幅 |
| `get_aftermarket_quote(symbol)` | `AfterMarketQuote` | 盘后报价 |
| `get_aftermarket_trade(symbol)` | `AfterMarketTrade` | 盘后成交 |
| `get_historical_prices(symbol, from_date, to_date)` | `DataFrame[PriceBar]` | 日线历史（复权） |
| `get_historical_prices_unadjusted(symbol, ...)` | `DataFrame[PriceBar]` | 日线历史（不复权） |
| `get_intraday(symbol, interval, ...)` | `DataFrame[PriceBar]` | 日内K线（1/5/15/30min, 1h, 4h） |
| `get_full_exchange_quotes(exchange)` | `DataFrame[StockQuote]` | 某交易所所有股票报价 |
| `get_full_etf_quotes()` | `DataFrame[StockQuote]` | 全部 ETF 报价 |
| `get_full_index_quotes()` | `DataFrame[IndexQuote]` | 全部指数报价 |
| `get_full_crypto_quotes()` | `DataFrame[CryptoQuote]` | 全部加密货币报价 |
| `get_full_forex_quotes()` | `DataFrame[ForexQuote]` | 全部外汇报价 |
| `get_full_commodity_quotes()` | `DataFrame[CommodityQuote]` | 全部大宗商品报价 |

### 4.2 FinancialLoader — 财务报表

| 方法 | 返回类型 | 说明 |
|---|---|---|
| `get_income_statements(symbol, period, limit)` | `DataFrame[IncomeStatement]` | 利润表 |
| `get_income_statements_ttm(symbol)` | `IncomeStatementTTM` | 利润表 TTM |
| `get_income_statement_growth(symbol, period)` | `DataFrame[StatementGrowth]` | 利润表增长率 |
| `get_balance_sheets(symbol, period, limit)` | `DataFrame[BalanceSheet]` | 资产负债表 |
| `get_balance_sheets_ttm(symbol)` | `BalanceSheetTTM` | 资产负债表 TTM |
| `get_cash_flows(symbol, period, limit)` | `DataFrame[CashFlow]` | 现金流量表 |
| `get_cash_flows_ttm(symbol)` | `CashFlowTTM` | 现金流量表 TTM |
| `get_financial_ratios(symbol, period, limit)` | `DataFrame[FinancialRatios]` | 财务比率 |
| `get_financial_ratios_ttm(symbol)` | `FinancialRatiosTTM` | 财务比率 TTM |
| `get_key_metrics(symbol, period, limit)` | `DataFrame[KeyMetrics]` | 关键指标 |
| `get_key_metrics_ttm(symbol)` | `KeyMetricsTTM` | 关键指标 TTM |
| `get_enterprise_values(symbol, period)` | `DataFrame[EnterpriseValue]` | 企业价值 |
| `get_financial_scores(symbol)` | `FinancialScores` | 财务评分（Piotroski 等） |
| `get_dcf(symbol)` | `DCFValuation` | DCF 估值 |
| `get_dcf_levered(symbol)` | `DCFValuation` | 杠杆 DCF 估值 |
| `get_owner_earnings(symbol)` | `DataFrame[OwnerEarnings]` | 所有者收益 |
| `get_revenue_by_geography(symbol)` | `DataFrame[RevenueSegment]` | 地区收入分布 |
| `get_revenue_by_product(symbol)` | `DataFrame[RevenueSegment]` | 产品收入分布 |
| `get_as_reported_income(symbol)` | `DataFrame[AsReportedStatement]` | 原始申报利润表 |
| `get_as_reported_balance(symbol)` | `DataFrame[AsReportedStatement]` | 原始申报资产负债表 |
| `get_as_reported_cashflow(symbol)` | `DataFrame[AsReportedStatement]` | 原始申报现金流量表 |

### 4.3 CompanyLoader — 公司数据

| 方法 | 说明 |
|---|---|
| `get_profile(symbol)` | 公司概况（单对象） |
| `get_profile_by_cik(cik)` | 按 CIK 查询公司概况 |
| `get_executives(symbol)` | 高管团队列表 |
| `get_employee_count(symbol)` | 最新员工数 |
| `get_historical_employee_count(symbol)` | 历史员工数 DataFrame |
| `get_market_cap(symbol)` | 当前市值 |
| `get_historical_market_cap(symbol, ...)` | 历史市值 DataFrame |
| `get_batch_market_cap(symbols)` | 批量市值 DataFrame |
| `get_shares_float(symbol)` | 流通股本 |
| `get_peers(symbol)` | 同业对比列表 |
| `get_mergers_acquisitions(limit)` | 最新并购事件 DataFrame |
| `get_executive_compensation(symbol)` | 高管薪酬 DataFrame |
| `get_company_notes(symbol)` | 公司备注 |

### 4.4 AnalystLoader — 分析师数据

| 方法 | 说明 |
|---|---|
| `get_grades(symbol)` | 当前评级 |
| `get_grades_summary(symbol)` | 评级汇总 |
| `get_historical_grades(symbol)` | 历史评级 DataFrame |
| `get_ratings_snapshot(symbol)` | 评级快照 |
| `get_historical_ratings(symbol)` | 历史综合评分 DataFrame |
| `get_price_target_consensus(symbol)` | 目标价共识 |
| `get_price_target_summary(symbol)` | 目标价汇总 |
| `get_financial_estimates(symbol, period)` | 盈利/营收预期 DataFrame |

### 4.5 CalendarLoader — 市场日历

| 方法 | 说明 |
|---|---|
| `get_earnings_calendar(from_date, to_date)` | 全市场财报日历 DataFrame |
| `get_company_earnings(symbol)` | 某公司历史财报日期 DataFrame |
| `get_dividends_calendar(from_date, to_date)` | 分红日历 DataFrame |
| `get_company_dividends(symbol)` | 某公司历史分红 DataFrame |
| `get_ipo_calendar(from_date, to_date)` | IPO 日历 DataFrame |
| `get_ipo_prospectus(from_date, to_date)` | IPO 招股说明书 DataFrame |
| `get_ipo_disclosure(from_date, to_date)` | IPO 披露 DataFrame |
| `get_splits_calendar(from_date, to_date)` | 拆股日历 DataFrame |
| `get_company_splits(symbol)` | 某公司历史拆股记录 DataFrame |

### 4.6 NewsLoader — 新闻

| 方法 | 说明 |
|---|---|
| `get_stock_news(limit, from_date, to_date)` | 全市场股票新闻 DataFrame |
| `get_stock_news_by_symbols(symbols, ...)` | 指定标的新闻 DataFrame |
| `get_general_news(limit, ...)` | 通用财经新闻 DataFrame |
| `get_crypto_news(limit, ...)` | 加密货币新闻 DataFrame |
| `get_forex_news(limit, ...)` | 外汇新闻 DataFrame |
| `get_press_releases(limit, ...)` | 新闻稿 DataFrame |
| `get_press_releases_by_symbol(symbol, ...)` | 指定公司新闻稿 DataFrame |
| `get_fmp_articles(limit, ...)` | FMP 自制文章 DataFrame |

### 4.7 TechnicalLoader — 技术指标

所有方法签名：`get_xxx(symbol, period_length, timeframe, from_date, to_date) -> DataFrame`

支持时间周期：`1min / 5min / 15min / 30min / 1hour / 4hour / 1day`

| 方法 | 指标 |
|---|---|
| `get_sma` | 简单移动平均线 |
| `get_ema` | 指数移动平均线 |
| `get_dema` | 双重指数移动平均线 |
| `get_tema` | 三重指数移动平均线 |
| `get_wma` | 加权移动平均线 |
| `get_rsi` | 相对强弱指数 |
| `get_adx` | 平均趋向指数 |
| `get_williams` | 威廉指标 %R |
| `get_std_dev` | 标准差 |

### 4.8 InsiderLoader — 内部人交易

| 方法 | 说明 |
|---|---|
| `get_latest_trades(limit, page)` | 最新内部人交易 DataFrame |
| `get_trades_by_symbol(symbol, ...)` | 某标的内部人交易 DataFrame |
| `get_trades_by_reporting_name(name, ...)` | 按申报人姓名查询 DataFrame |
| `get_statistics(symbol)` | 内部人交易统计（单对象） |
| `get_acquisition_ownership(symbol)` | 收购持股变动 DataFrame |
| `get_transaction_types()` | 所有交易类型参考列表 |

### 4.9 SecFilingLoader — SEC 文件

| 方法 | 说明 |
|---|---|
| `get_filings_by_symbol(symbol, ...)` | 按标的查询 SEC 文件 DataFrame |
| `get_filings_by_cik(cik, ...)` | 按 CIK 查询 DataFrame |
| `get_filings_by_form_type(form_type, ...)` | 按表格类型查询 DataFrame |
| `get_filings_by_name(company, ...)` | 按公司名查询 DataFrame |
| `get_latest_financial_filings(limit)` | 最新财务文件 DataFrame |
| `get_latest_8k(limit)` | 最新 8-K DataFrame |
| `get_sec_company_profile(symbol)` | SEC 公司完整档案（单对象） |
| `get_industry_classification(symbol)` | 行业 SIC 分类（单对象） |
| `get_all_industry_classifications()` | 全部行业分类 DataFrame |

### 4.10 MarketPerfLoader — 市场表现

| 方法 | 说明 |
|---|---|
| `get_gainers()` | 涨幅榜 DataFrame |
| `get_losers()` | 跌幅榜 DataFrame |
| `get_most_active()` | 成交最活跃 DataFrame |
| `get_sector_pe_snapshot(date)` | 板块 PE 快照 DataFrame |
| `get_industry_pe_snapshot(date)` | 行业 PE 快照 DataFrame |
| `get_sector_performance_snapshot(date)` | 板块涨跌快照 DataFrame |
| `get_industry_performance_snapshot(date)` | 行业涨跌快照 DataFrame |
| `get_historical_sector_pe(sector, ...)` | 板块历史 PE DataFrame |
| `get_historical_industry_pe(industry, ...)` | 行业历史 PE DataFrame |
| `get_historical_sector_performance(sector, ...)` | 板块历史涨跌 DataFrame |
| `get_historical_industry_performance(industry, ...)` | 行业历史涨跌 DataFrame |

### 4.11 CongressLoader — 国会交易披露

| 方法 | 说明 |
|---|---|
| `get_senate_latest(limit, page)` | 参议院最新披露 DataFrame |
| `get_senate_trades_by_symbol(symbol, ...)` | 按标的查参议院交易 DataFrame |
| `get_senate_trades_by_name(name, ...)` | 按议员姓名查参议院交易 DataFrame |
| `get_house_latest(limit, page)` | 众议院最新披露 DataFrame |
| `get_house_trades_by_symbol(symbol, ...)` | 按标的查众议院交易 DataFrame |
| `get_house_trades_by_name(name, ...)` | 按议员姓名查众议院交易 DataFrame |

### 4.12 DirectoryLoader — 参考目录

| 方法 | 说明 |
|---|---|
| `get_actively_trading_list()` | 活跃交易标的列表 DataFrame |
| `get_company_symbols()` | 全部公司标的列表 DataFrame |
| `get_etf_list()` | 全部 ETF 列表 DataFrame |
| `get_available_exchanges()` | 可用交易所列表 |
| `get_available_sectors()` | 可用板块列表 |
| `get_available_industries()` | 可用行业列表 |
| `get_available_countries()` | 可用国家列表 |
| `get_cik_list(limit, page)` | CIK 列表 DataFrame |
| `get_symbol_changes()` | 标的代码变更记录 DataFrame |

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
