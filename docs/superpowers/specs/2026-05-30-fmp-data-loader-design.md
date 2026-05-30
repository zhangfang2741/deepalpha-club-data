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
│   ├── base.py               # BaseLoader ABC + AsyncDataClient Protocol
│   ├── enums.py              # AssetClass / Interval / StatementPeriod / IndicatorType 等枚举
│   ├── hub.py                # AbstractDataHub Protocol（Core loader 契约）
│   ├── market.py             # AbstractMarketLoader               [Core]
│   ├── financial.py          # AbstractFinancialLoader             [Core]
│   ├── company.py            # AbstractCompanyLoader               [Core]
│   ├── analyst.py            # AbstractAnalystLoader               [Core]
│   ├── calendar.py           # AbstractCalendarLoader              [Core]
│   ├── news.py               # AbstractNewsLoader                  [Core]
│   ├── indicators.py         # AbstractTechnicalIndicatorLoader    [Extended]
│   ├── economics.py          # AbstractEconomicsLoader             [Extended]
│   ├── insider.py            # AbstractInsiderTradeLoader          [Extended]
│   ├── filings.py            # AbstractSecFilingLoader             [Extended 🇺🇸]
│   ├── performance.py        # AbstractMarketPerformanceLoader     [Extended]
│   ├── congress.py           # AbstractCongressTradeLoader         [Extended 🇺🇸]
│   └── directory.py          # AbstractDirectoryLoader             [Extended]
│
└── providers/
    ├── fmp/                  # FMP 提供商实现
    │   ├── __init__.py       # 导出 FMPDataHub
    │   ├── client.py         # FMPAsyncClient
    │   ├── config.py         # FMPConfig
    │   └── loaders/          # FMP 对各 AbstractLoader 的实现
    │       ├── __init__.py
    │       ├── market.py     # FMPMarketLoader
    │       ├── financial.py  # FMPFinancialLoader
    │       ├── company.py    # FMPCompanyLoader
    │       ├── analyst.py    # FMPAnalystLoader
    │       ├── calendar.py   # FMPCalendarLoader
    │       ├── news.py       # FMPNewsLoader
    │       ├── indicators.py # FMPTechnicalIndicatorLoader
    │       ├── economics.py  # FMPEconomicsLoader
    │       ├── insider.py    # FMPInsiderTradeLoader
    │       ├── filings.py    # FMPSecFilingLoader
    │       ├── performance.py # FMPMarketPerformanceLoader
    │       ├── congress.py   # FMPCongressTradeLoader
    │       └── directory.py  # FMPDirectoryLoader
    └── yfinance/             # 未来扩展（实现 AbstractDataHub Protocol）
```

### 分层职责

| 层 | 职责 | 依赖 |
|---|---|---|
| `models/` | 规范数据结构，含中文字段标注 | 仅 pydantic |
| `loaders/base.py` | BaseLoader ABC、AsyncDataClient Protocol | httpx, polars |
| `loaders/hub.py` | AbstractDataHub Protocol（Core loader 契约） | loaders/ |
| `loaders/enums.py` | 共享枚举（AssetClass、Interval 等） | — |
| `loaders/*.py` | 各类别 Abstract Loader（Core + Extended） | models/, base |
| `providers/fmp/client.py` | FMP HTTP 连接、速率限制、重试 | httpx |
| `providers/fmp/loaders/` | FMP JSON → 规范模型的映射实现 | loaders/, client |
| `providers/fmp/FMPDataHub` | 实现 AbstractDataHub，聚合全部 FMP loader | 所有 FMP loaders |

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
    # 均线系列（Trend Following）
    SMA      = "sma"       # 简单移动平均
    EMA      = "ema"       # 指数移动平均
    DEMA     = "dema"      # 双重指数移动平均
    TEMA     = "tema"      # 三重指数移动平均
    WMA      = "wma"       # 加权移动平均

    # 动量/震荡指标（Momentum / Oscillator）
    RSI      = "rsi"       # 相对强弱指数
    MACD     = "macd"      # 指数平滑异同移动平均线
    STOCH    = "stoch"     # 随机震荡指标（KD）
    CCI      = "cci"       # 顺势指标
    WILLIAMS = "williams"  # 威廉指标 %R

    # 趋势强度指标（Trend Strength）
    ADX      = "adx"       # 平均趋向指数
    AROON    = "aroon"     # 阿隆指标

    # 波动率指标（Volatility）
    BBANDS   = "bbands"    # 布林带
    ATR      = "atr"       # 真实波幅
    STD_DEV  = "std_dev"   # 标准差

    # 成交量指标（Volume）
    OBV      = "obv"       # 能量潮

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
    """行情数据加载器抽象基类。
    
    负责所有资产类别（股票、ETF、指数、加密货币、外汇、大宗商品）的实时报价与历史价格数据。
    不同 provider 通过实现此类，将自身 API 端点映射到统一接口，调用方无需感知底层差异。
    """
    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        """获取单个标的实时报价，返回含价格、涨跌幅、成交量等字段的 Pydantic 对象。"""
        ...

    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> pl.DataFrame:
        """批量获取多个标的实时报价，返回 DataFrame，每行对应一个标的。"""
        ...

    @abstractmethod
    async def get_price_history(
        self,
        symbol: str,
        start: date,
        end: date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> pl.DataFrame:
        """获取历史 OHLCV 数据。interval="1d" 返回日线，"1h"/"5m" 等返回日内K线。
        不同 provider 内部路由到各自端点，调用方无需感知差异。
        adjusted=True 表示复权价格（默认）。
        """
        ...

    @abstractmethod
    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> pl.DataFrame:
        """获取指定资产类别的全市场实时报价快照，返回该类别所有标的的当前行情 DataFrame。"""
        ...
```

> **FMP 实现映射**：`interval=ONE_DAY` → `historical-price-eod-full`；`interval=ONE_HOUR` → `intraday-1-hour`；`adjusted=False` → `historical-price-eod-non-split-adjusted`；`asset_class=CRYPTO` → `full-cryptocurrency-quotes`。

---

#### `AbstractFinancialLoader`

```python
class AbstractFinancialLoader(BaseLoader):
    """财务基本面数据加载器抽象基类。
    
    覆盖上市公司三张核心财务报表（利润表、资产负债表、现金流量表）及衍生指标
    （财务比率、关键指标、估值模型）。period 参数统一支持 annual/quarter/ttm，
    由具体实现路由到 provider 对应端点。
    """
    @abstractmethod
    async def get_income_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame:
        """获取利润表。period 支持 annual/quarter/ttm，ttm 为滚动12个月合并数据。"""
        ...

    @abstractmethod
    async def get_balance_sheet(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame:
        """获取资产负债表。period 支持 annual/quarter/ttm。"""
        ...

    @abstractmethod
    async def get_cash_flow_statement(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame:
        """获取现金流量表。period 支持 annual/quarter/ttm。"""
        ...

    @abstractmethod
    async def get_financial_ratios(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame:
        """获取财务比率，包含流动比率、毛利率、ROE、ROA、负债率等衍生指标。"""
        ...

    @abstractmethod
    async def get_key_metrics(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL, limit: int = 5
    ) -> pl.DataFrame:
        """获取关键财务指标，包含 EPS、市销率、企业价值倍数、自由现金流收益率等。"""
        ...

    @abstractmethod
    async def get_valuation(self, symbol: str) -> Valuation:
        """获取估值模型结果，包含 DCF 内在价值和当前价格的溢折价比较。"""
        ...
```

---

#### `AbstractCompanyLoader`

```python
class AbstractCompanyLoader(BaseLoader):
    """公司基础信息加载器抽象基类。
    
    提供与公司实体本身相关的非财务数据，包括公司概况、管理层、同业对比和市值。
    与 AbstractFinancialLoader 的区别：本类关注公司静态属性和结构信息，
    财务数字由 FinancialLoader 负责。
    """
    @abstractmethod
    async def get_profile(self, symbol: str) -> CompanyProfile:
        """获取公司基本信息，包含行业、交易所、员工数、描述、官网等。"""
        ...

    @abstractmethod
    async def get_executives(self, symbol: str) -> pl.DataFrame:
        """获取公司高管团队列表，包含姓名、职位、薪酬等信息。"""
        ...

    @abstractmethod
    async def get_peers(self, symbol: str) -> list[str]:
        """获取同行业可比公司的股票代码列表。"""
        ...

    @abstractmethod
    async def get_market_cap(
        self, symbol: str, start: date | None = None, end: date | None = None
    ) -> pl.DataFrame:
        """获取市值数据。start/end 均为 None 时返回当前市值；提供日期范围则返回历史市值序列。"""
        ...
```

---

#### `AbstractAnalystLoader`

```python
class AbstractAnalystLoader(BaseLoader):
    """卖方分析师研究数据加载器抽象基类。
    
    聚合来自机构分析师的主观判断数据，包括股票评级、目标价和财务预测。
    这类数据反映市场对股票未来表现的预期共识，与历史财务数据（FinancialLoader）互补。
    """
    @abstractmethod
    async def get_ratings(self, symbol: str) -> pl.DataFrame:
        """获取分析师评级历史，包含机构名称、买入/持有/卖出评级及变化时间。"""
        ...

    @abstractmethod
    async def get_price_targets(self, symbol: str) -> pl.DataFrame:
        """获取分析师目标价，包含最高/最低/平均/共识目标价及各机构预测值。"""
        ...

    @abstractmethod
    async def get_estimates(
        self, symbol: str, period: StatementPeriod = StatementPeriod.ANNUAL
    ) -> pl.DataFrame:
        """获取盈利与营收预期，包含 EPS 共识预测、营收预测及与实际值的对比。"""
        ...
```

---

#### `AbstractCalendarLoader`

```python
class AbstractCalendarLoader(BaseLoader):
    """市场事件日历加载器抽象基类。
    
    提供具有明确时间节点的公司事件数据，包括财报发布、分红除息、新股上市和股票拆合。
    所有方法均要求 start/end 日期范围，返回该区间内的全市场事件列表。
    """
    @abstractmethod
    async def get_earnings_calendar(self, start: date, end: date) -> pl.DataFrame:
        """获取指定日期范围内全市场的财报发布日历，包含预计发布日期、EPS 预期等。"""
        ...

    @abstractmethod
    async def get_dividend_calendar(self, start: date, end: date) -> pl.DataFrame:
        """获取指定日期范围内的分红除息日历，包含除息日、派息金额、股息率等。"""
        ...

    @abstractmethod
    async def get_ipo_calendar(self, start: date, end: date) -> pl.DataFrame:
        """获取指定日期范围内的 IPO 日历，包含公司名称、预计上市日期、发行价区间等。"""
        ...

    @abstractmethod
    async def get_splits_calendar(self, start: date, end: date) -> pl.DataFrame:
        """获取指定日期范围内的股票拆/合股日历，包含标的代码、拆股比例、生效日期等。"""
        ...
```

---

#### `AbstractNewsLoader`

```python
class AbstractNewsLoader(BaseLoader):
    """财经新闻加载器抽象基类。
    
    通过统一的 get_news 方法覆盖股票、加密货币、外汇及通用财经新闻。
    symbols 和 asset_class 参数组合控制过滤范围，避免为每种资产类别定义独立方法。
    """
    @abstractmethod
    async def get_news(
        self,
        symbols: list[str] | None = None,
        asset_class: AssetClass | None = None,
        limit: int = 20,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame:
        """获取财经新闻。symbols 有值时返回指定标的相关新闻；
        asset_class 指定时按资产类别过滤（如 CRYPTO 返回加密货币新闻）；
        两者均为 None 时返回全市场通用财经新闻。
        """
        ...
```

---

#### `AbstractTechnicalIndicatorLoader`

```python
class AbstractTechnicalIndicatorLoader(BaseLoader):
    """技术指标加载器抽象基类。
    
    通过单一 get_indicator 方法覆盖所有技术分析指标（均线系列、震荡指标、趋势指标等），
    以 IndicatorType 枚举和 period 参数替代为每种指标定义独立方法，降低接口膨胀风险。
    interval 参数支持从分钟级到日线的多粒度K线。
    """
    @abstractmethod
    async def get_indicator(
        self,
        symbol: str,
        indicator: IndicatorType,
        period: int,
        interval: Interval = Interval.ONE_DAY,
        start: date | None = None,
        end: date | None = None,
    ) -> pl.DataFrame:
        """计算并返回技术指标时间序列。indicator 指定指标类型（SMA/EMA/RSI/ADX 等），
        period 为计算周期数（如 RSI-14 传入 14），interval 指定K线粒度。
        返回 DataFrame 包含时间戳和对应指标值。
        """
        ...
```

---

#### `AbstractInsiderTradeLoader`

```python
class AbstractInsiderTradeLoader(BaseLoader):
    """内部人交易加载器抽象基类。
    
    提供公司内部人（高管、董事、持股超5%的大股东）依法披露的股票买卖记录。
    内部人交易是研究公司基本面的重要另类数据信号，反映公司内部人对股票价值的判断。
    """

    @abstractmethod
    async def get_insider_trades(
        self, symbol: str | None = None, limit: int = 50, page: int = 0
    ) -> pl.DataFrame:
        """获取内部人交易记录。
        symbol=None 时返回全市场最新交易；指定 symbol 时过滤至该标的。
        """
        ...

    @abstractmethod
    async def get_insider_statistics(self, symbol: str) -> InsiderStatistics:
        """获取指定标的的内部人交易统计摘要，包含买入/卖出笔数、净买卖方向等聚合信息。"""
        ...
```

---

#### `AbstractSecFilingLoader`

```python
class AbstractSecFilingLoader(BaseLoader):
    """SEC 监管文件加载器抽象基类。【美国市场专用】
    
    提供美国证监会（SEC）的公开申报文件查询能力，包括年报（10-K）、季报（10-Q）、
    重大事项披露（8-K）等。适用于需要原始监管披露文本或结构化申报数据的场景。
    注意：get_sec_profile 返回 SEC 系统档案，有别于 CompanyLoader.get_profile 的市场信息。
    
    **Provider 适配说明**：此 Loader 为美国市场专用，Alpha Vantage 不提供 SEC 文件查询，
    FactSet 有类似能力但通过不同模块实现。非美国市场 provider 可不实现此抽象类。
    """

    @abstractmethod
    async def get_filings(
        self,
        symbol: str | None = None,
        form_type: str | None = None,
        start: date | None = None,
        end: date | None = None,
        limit: int = 20,
    ) -> pl.DataFrame:
        """查询 SEC 申报文件列表。symbol/form_type 均可选，组合使用时取交集过滤。
        form_type 示例：'10-K'、'10-Q'、'8-K'、'SC 13G' 等。
        """
        ...

    @abstractmethod
    async def get_sec_profile(self, symbol: str) -> SecCompanyProfile:
        """获取公司在 SEC 系统中的注册档案，包含 CIK、SIC 行业代码、注册地址等。
        与 CompanyLoader.get_profile 的区别：本方法返回监管注册信息，而非市场基本面数据。
        """
        ...
```

---

#### `AbstractMarketPerformanceLoader`

```python
class AbstractMarketPerformanceLoader(BaseLoader):
    """市场表现数据加载器抽象基类。
    
    提供宏观市场层面的表现数据，包括个股涨跌榜（量化热度信号）和
    板块 PE/涨跌表现（行业轮动分析的基础数据）。
    与 MarketLoader 的区别：MarketLoader 关注个股行情，本类关注市场结构和板块整体表现。
    """
    @abstractmethod
    async def get_movers(
        self, direction: MoverDirection, limit: int = 20
    ) -> pl.DataFrame:
        """获取市场涨跌榜或成交活跃榜。
        direction=GAINERS 返回涨幅榜，LOSERS 返回跌幅榜，ACTIVE 返回成交额最活跃榜单。
        """
        ...

    @abstractmethod
    async def get_sector_performance(self, date: date | None = None) -> pl.DataFrame:
        """获取各板块涨跌表现。date=None 返回当日快照；指定日期返回该日历史数据。"""
        ...

    @abstractmethod
    async def get_sector_pe(self, date: date | None = None) -> pl.DataFrame:
        """获取各板块市盈率（PE）。date=None 返回当前快照；指定日期返回历史 PE 数据。"""
        ...
```

---

#### `AbstractCongressTradeLoader`

```python
class AbstractCongressTradeLoader(BaseLoader):
    """美国国会议员交易披露加载器抽象基类。【美国市场专用】
    
    提供依据《STOCK Act》强制披露的美国参众两院议员股票交易记录。
    议员交易数据被广泛用于政策敏感行业的情绪分析和另类信号研究。
    chamber 枚举统一参议院与众议院，无需定义独立方法。
    
    **Provider 适配说明**：此数据为美国特有监管披露，Alpha Vantage、FactSet 均不提供。
    仅限支持美国市场政治交易数据的 provider（如 FMP、Quiver Quant）实现此抽象类。
    """

    @abstractmethod
    async def get_congress_trades(
        self,
        symbol: str | None = None,
        chamber: CongressChamber = CongressChamber.SENATE,
        limit: int = 50,
        page: int = 0,
    ) -> pl.DataFrame:
        """获取国会议员股票交易披露记录。
        chamber 区分参议院（SENATE）和众议院（HOUSE）；
        symbol=None 返回最新全量披露，指定时过滤至该标的相关交易。
        """
        ...
```

---

#### `AbstractDirectoryLoader`

```python
class AbstractDirectoryLoader(BaseLoader):
    """参考数据目录加载器抽象基类。
    
    提供静态参考数据，包括可交易标的列表、交易所信息、板块和行业分类。
    这类数据变动频率低，通常用于初始化过滤条件、构建标的池或验证代码合法性。
    """
    @abstractmethod
    async def get_symbols(self, asset_class: AssetClass = AssetClass.STOCK) -> pl.DataFrame:
        """获取指定资产类别的全量标的列表，包含代码、名称、交易所等基础信息。"""
        ...

    @abstractmethod
    async def get_exchanges(self) -> pl.DataFrame:
        """获取数据源支持的全部交易所列表，包含交易所代码、名称、所在国家等。"""
        ...

    @abstractmethod
    async def get_sectors(self) -> list[str]:
        """获取数据源支持的全部板块名称列表，用于筛选或分类时的合法值参考。"""
        ...

    @abstractmethod
    async def get_industries(self) -> list[str]:
        """获取数据源支持的全部行业名称列表，粒度比板块更细，用于行业级别筛选。"""
        ...
```

---

#### `AbstractEconomicsLoader`

```python
class AbstractEconomicsLoader(BaseLoader):
    """宏观经济数据加载器抽象基类。
    
    提供宏观经济时间序列数据，包括 CPI、GDP、失业率、利率、国债收益率等。
    Alpha Vantage 和 FactSet 均有对应能力；FMP 可覆盖其支持的子集。
    
    indicator_name 使用标准化字符串（如 "CPI"、"UNEMPLOYMENT"），
    各 provider 在实现时负责映射到自身的端点参数。
    """

    @abstractmethod
    async def get_indicator(
        self,
        indicator_name: str,
        start: date | None = None,
        end: date | None = None,
        interval: Interval = Interval.ONE_MONTH,
    ) -> pl.DataFrame:
        """获取宏观经济指标时间序列。
        indicator_name 示例：'CPI'、'REAL_GDP'、'UNEMPLOYMENT'、
        'FEDERAL_FUNDS_RATE'、'TREASURY_YIELD_10Y'、'RETAIL_SALES'。
        各 provider 支持的指标集合不同，可通过 get_available_indicators() 查询。
        返回 DataFrame 包含日期列和对应指标值列。
        """
        ...

    @abstractmethod
    async def get_available_indicators(self) -> list[str]:
        """返回当前 provider 支持查询的全部宏观经济指标名称列表。"""
        ...
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

### 3.7 `AbstractDataHub` Protocol 与 Core / Extended 分层

不同 provider 的能力范围不同（例如 Alpha Vantage 无国会交易，FactSet 无技术指标），
因此将 loader 分为两层，并通过 `AbstractDataHub` Protocol 约束属性名一致性：

```python
# src/deepalpha/loaders/hub.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class AbstractDataHub(Protocol):
    """所有 provider DataHub 必须实现的 Core loader 集合（6 个）。
    
    Core loader 是跨 provider 通用的能力，任何主流金融数据源均可覆盖。
    Extended loader（indicators、insider、filings、performance、congress、economics）
    按 provider 实际支持情况选择性实现，通过 hasattr(hub, "indicators") 判断是否可用。
    """
    # ── Core loaders（所有 provider 必须实现）──────────────────────
    market:      AbstractMarketLoader
    financial:   AbstractFinancialLoader
    company:     AbstractCompanyLoader
    analyst:     AbstractAnalystLoader
    calendar:    AbstractCalendarLoader
    news:        AbstractNewsLoader

    async def __aenter__(self) -> "AbstractDataHub": ...
    async def __aexit__(self, *_) -> None: ...
```

**Extended loader 支持矩阵：**

| Loader 属性 | FMP Start | Alpha Vantage | FactSet |
|---|---|---|---|
| `market` | ✅ | ✅ | ✅ |
| `financial` | ✅ | ✅ | ✅ |
| `company` | ✅ | ✅ | ✅ |
| `analyst` | ✅ | ✅ | ✅ |
| `calendar` | ✅ | ✅ | ✅ |
| `news` | ✅ | ✅ | ✅ |
| `indicators` | ✅（9 种） | ✅（50+ 种） | ❌ |
| `economics` | ✅（有限） | ✅ | ✅ |
| `performance` | ✅ | ❌ | ✅ |
| `insider` | ✅ | ⚠️（仅单标的） | ✅ |
| `directory` | ✅ | ⚠️（有限） | ✅ |
| `filings` | ✅ 🇺🇸 | ❌ | ✅（全球） |
| `congress` | ✅ 🇺🇸 | ❌ | ❌ |

> 🇺🇸 = 美国市场专用数据

---

### 3.8 `FMPDataHub`

`FMPDataHub` 实现 `AbstractDataHub` Protocol，并额外提供所有 Extended loader：

```python
# src/deepalpha/providers/fmp/__init__.py
from deepalpha.providers.fmp.config import FMPConfig
from deepalpha.providers.fmp.client import FMPAsyncClient
from deepalpha.providers.fmp.loaders import (
    FMPMarketLoader, FMPFinancialLoader, FMPCompanyLoader,
    FMPAnalystLoader, FMPCalendarLoader, FMPNewsLoader,
    FMPTechnicalIndicatorLoader, FMPInsiderTradeLoader, FMPSecFilingLoader,
    FMPMarketPerformanceLoader, FMPCongressTradeLoader, FMPDirectoryLoader,
    FMPEconomicsLoader,
)

class FMPDataHub:
    """FMP 数据中枢，实现 AbstractDataHub Protocol（Core）并提供全部 Extended loader。
    
    使用 async with 上下文管理器确保 HTTP 连接正确关闭。
    通过 FMPConfig 或环境变量 FMP_API_KEY 传入认证信息。
    """

    def __init__(self, config: FMPConfig | None = None) -> None:
        cfg = config or FMPConfig()
        self._client = FMPAsyncClient(cfg)
        # Core loaders
        self.market      = FMPMarketLoader(self._client)
        self.financial   = FMPFinancialLoader(self._client)
        self.company     = FMPCompanyLoader(self._client)
        self.analyst     = FMPAnalystLoader(self._client)
        self.calendar    = FMPCalendarLoader(self._client)
        self.news        = FMPNewsLoader(self._client)
        # Extended loaders
        self.indicators  = FMPTechnicalIndicatorLoader(self._client)
        self.economics   = FMPEconomicsLoader(self._client)
        self.insider     = FMPInsiderTradeLoader(self._client)
        self.filings     = FMPSecFilingLoader(self._client)
        self.performance = FMPMarketPerformanceLoader(self._client)
        self.congress    = FMPCongressTradeLoader(self._client)
        self.directory   = FMPDirectoryLoader(self._client)

    async def __aenter__(self): return self
    async def __aexit__(self, *_): await self._client.aclose()
```

**使用示例：**

```python
async with FMPDataHub() as hub:
    # Core loader — 任何 provider 都支持
    quote = await hub.market.get_quote("AAPL")

    # Extended loader — 使用前检查 provider 支持情况
    if hasattr(hub, "indicators"):
        df = await hub.indicators.get_indicator(
            "AAPL", IndicatorType.MACD, period=12, interval=Interval.ONE_DAY
        )

    # 经济数据
    cpi = await hub.economics.get_indicator("CPI")
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

### 4.7 TechnicalIndicatorLoader — 技术指标

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_indicator(symbol, indicator, period, interval, ...)` | `indicator` 值路由到对应端点：`SMA`→`simple-moving-average`，`RSI`→`relative-strength-index`，等 |

**FMP Start 支持的 `IndicatorType` 值**：`SMA`、`EMA`、`DEMA`、`TEMA`、`WMA`、`RSI`、`ADX`、`WILLIAMS`、`STD_DEV`（共 9 种）

> **注意**：`MACD`、`BBANDS`、`ATR`、`OBV`、`STOCH`、`CCI`、`AROON` 在枚举中已定义，FMP Start 不支持，由 Alpha Vantage 等 provider 实现时覆盖。

### 4.8 InsiderTradeLoader — 内部人交易

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_insider_trades(symbol=None, limit, page)` | `symbol=None` → `latest-insider-trade`；有值 → `search-insider-trades?symbol=...` |
| `get_insider_statistics(symbol)` | `insider-trade-statistics` |

> **FMP 额外方法**：`get_trades_by_reporting_name`、`get_acquisition_ownership`。

### 4.9 SecFilingLoader — SEC 文件

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_filings(symbol, form_type, start, end, limit)` | 参数组合路由：有 `symbol` → `search-by-symbol`；有 `form_type` → `search-by-form-type`；都有 → 优先 symbol，form_type 作过滤 |
| `get_sec_profile(symbol)` | `sec-company-full-profile` |

> **FMP 额外方法**：`get_latest_8k`、`get_latest_financial_filings`、`get_industry_classification`、`get_filings_by_cik`、`get_filings_by_name`。

### 4.10 MarketPerformanceLoader — 市场表现

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_movers(direction=GAINERS\|LOSERS\|ACTIVE, limit)` | `biggest-gainers` / `biggest-losers` / `most-active` |
| `get_sector_performance(date=None)` | `date=None` → `sector-performance-snapshot`；有值 → `historical-sector-performance` |
| `get_sector_pe(date=None)` | `date=None` → `sector-PE-snapshot`；有值 → `historical-sector-pe` |

> **FMP 额外方法**：`get_industry_performance`、`get_industry_pe`（行业级别，抽象层暂只定义板块级）。

### 4.11 CongressTradeLoader — 国会交易披露

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_congress_trades(symbol=None, chamber=SENATE\|HOUSE, limit, page)` | `chamber=SENATE + symbol=None` → `senate-latest`；有 symbol → `senate-trading`；`HOUSE` 同理路由 |

### 4.12 DirectoryLoader — 参考目录

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_symbols(asset_class=STOCK)` | `STOCK` → `actively-trading-list`；`ETF` → `ETFs-list`；其他 → `company-symbols-list` |
| `get_exchanges()` | `available-exchanges` |
| `get_sectors()` | `available-sectors` |
| `get_industries()` | `available-industries` |

### 4.13 EconomicsLoader — 宏观经济数据

| 抽象方法 | FMP 实现映射 |
|---|---|
| `get_indicator(indicator_name, start, end, interval)` | `indicator_name` 路由到 FMP Economics 端点；FMP Start 支持有限子集 |
| `get_available_indicators()` | 返回 FMP 当前支持的经济指标名称列表 |

**FMP 支持的常见 `indicator_name`**（部分）：`'CPI'`、`'GDP'`、`'UNEMPLOYMENT'`、`'FEDERAL_FUNDS_RATE'`、`'TREASURY_YIELD'`

> **跨 provider 说明**：Alpha Vantage 通过 `REAL_GDP`、`CPI`、`UNEMPLOYMENT` 等端点覆盖；FactSet 通过 Economics Formula API 支持 100万+ 全球经济时间序列。`get_available_indicators()` 使调用方在运行时感知各 provider 支持范围。

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

### 接入新 Provider 的步骤

以 Alpha Vantage 为例：
1. 在 `providers/alpha_vantage/` 下创建 `AlphaVantageAsyncClient` 和 `AlphaVantageConfig`
2. 实现 6 个 **Core loader**（实现 `AbstractDataHub` Protocol 的必要条件）
3. 按 Alpha Vantage 实际能力选择性实现 **Extended loader**：
   - ✅ 实现：`AbstractTechnicalIndicatorLoader`（50+ 指标）、`AbstractEconomicsLoader`、`AbstractInsiderTradeLoader`（有限）
   - ❌ 跳过：`AbstractSecFilingLoader`、`AbstractCongressTradeLoader`（无数据）
4. 创建 `AlphaVantageDataHub`，满足 `isinstance(hub, AbstractDataHub)` 检查即可上线

### Provider 适配能力对比

| Provider | Core | indicators | economics | insider | filings 🇺🇸 | congress 🇺🇸 |
|---|---|---|---|---|---|---|
| FMP Start | ✅ | ✅（9 种） | ✅（有限） | ✅ | ✅ | ✅ |
| Alpha Vantage | ✅ | ✅（50+） | ✅ | ⚠️ | ❌ | ❌ |
| FactSet | ✅ | ❌ | ✅ | ✅ | ✅（全球） | ❌ |
| yfinance | ✅ | ❌（需 pandas-ta） | ❌ | ❌ | ❌ | ❌ |

> 🇺🇸 = 美国市场专用数据；`models/` 和 `loaders/`（ABC 层）在任何 provider 接入时均无需修改。
