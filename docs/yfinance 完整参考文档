# yfinance 完整参考文档

> 基于 [官方文档](https://ranaroussi.github.io/yfinance/) 整理，包含高级用法与完整 API 参考  
> Yahoo Finance 非官方 Python 数据获取库

---

## 目录

### 一、高级用法
1. [Logging — 日志配置](#1-logging--日志配置)
2. [Config — 全局配置](#2-config--全局配置)
3. [Caching — 本地缓存](#3-caching--本地缓存)
4. [Multi-Level Column Index — 多级列索引](#4-multi-level-column-index--多级列索引)
5. [Price Repair — 价格修复](#5-price-repair--价格修复)
6. [Rate Limiting — 速率限制](#6-rate-limiting--速率限制)

### 二、API 参考
7. [Ticker / Tickers — 入口类](#7-ticker--tickers--入口类)
8. [Stock — 行情与基本信息](#8-stock--行情与基本信息)
9. [Financials — 财务报表](#9-financials--财务报表)
10. [Analysis & Holdings — 分析与持股](#10-analysis--holdings--分析与持股)
11. [Market / Calendars — 市场与日历](#11-market--calendars--市场与日历)
12. [Search & Lookup — 搜索查找](#12-search--lookup--搜索查找)
13. [WebSocket — 实时数据流](#13-websocket--实时数据流)
14. [Sector & Industry — 行业板块](#14-sector--industry--行业板块)
15. [Screener & Query — 股票筛选器](#15-screener--query--股票筛选器)
16. [Functions & Utilities — 工具函数](#16-functions--utilities--工具函数)
17. [FundsData — 基金数据类](#17-fundsdata--基金数据类)
18. [PriceHistory — 底层历史类](#18-pricehistory--底层历史类)

### 三、附录
18. [常用代码速查](#18-常用代码速查)

---

# 一、高级用法

---

## 1. Logging — 日志配置

yfinance 内部使用标准 `logging` 模块处理消息，**默认只记录错误级别**。

调试时可开启 debug 模式，输出所有 HTTP 请求与响应的详细信息：

```python
import yfinance as yf

yf.config.debug.logging = True
```

开启后会打印每次请求的 URL、响应状态码、耗时等，便于排查网络问题或数据异常。

---

## 2. Config — 全局配置

yfinance 提供全局配置对象 `yf.config`，用于在所有请求中共享通用参数，无需每次单独传参。

### 查看当前配置

```python
import yfinance as yf

print(yf.config)
# {
#   "network": {
#     "proxy": null,
#     "retries": 0
#   },
#   "debug": {
#     "hide_exceptions": true,
#     "logging": false
#   }
# }

print(yf.config.network)
# {
#   "proxy": null,
#   "retries": 0
# }
```

### network — 网络配置

#### `yf.config.network.proxy`

为所有 yfinance 数据请求统一设置代理服务器，无需在每个方法调用中单独传 `proxy` 参数。

```python
# 设置全局代理
yf.config.network.proxy = "http://your-proxy-server:8080"

# 此后所有请求均走代理，无需单独传参
aapl = yf.Ticker("AAPL")
df = aapl.history(period="1y")   # 自动使用代理

# 也可在单次调用中临时覆盖
df = aapl.history(period="1y", proxy="http://other-proxy:8080")
```

#### `yf.config.network.retries`

配置网络瞬时错误（如超时、连接重置）的自动重试次数。重试机制使用**指数退避**策略：第1次重试等1秒，第2次等2秒，第3次等4秒，依此类推。

```python
# 设置自动重试2次
yf.config.network.retries = 2

# 重试间隔: 1s → 2s → 4s...
```

### debug — 调试配置

#### `yf.config.debug.hide_exceptions`

控制 yfinance 是否隐藏内部异常。默认为 `True`（隐藏，静默失败）。设为 `False` 可让异常正常抛出，便于调试。

```python
# 停止隐藏异常，让错误正常抛出
yf.config.debug.hide_exceptions = False
```

#### `yf.config.debug.logging`

开启详细调试日志，等价于 `yf.enable_debug_mode()`。

```python
yf.config.debug.logging = True
```

---

## 3. Caching — 本地缓存

yfinance 会在本地缓存部分数据（时区信息、Cookie）以减少重复网络请求，加快后续调用速度。

### 默认缓存位置

| 操作系统 | 默认缓存路径 |
|----------|-------------|
| Windows | `C:/Users/<USER>/AppData/Local/py-yfinance` |
| Linux | `/home/<USER>/.cache/py-yfinance` |
| macOS | `/Users/<USER>/Library/Caches/py-yfinance` |

### 自定义缓存路径

使用 `set_tz_cache_location()` 将缓存重定向到指定目录：

```python
import yfinance as yf

# 自定义缓存位置（需在其他 yfinance 操作之前调用）
yf.set_tz_cache_location("/data/yfinance_cache")

# 常见场景：Docker 容器中统一缓存位置
yf.set_tz_cache_location("/tmp/yf_cache")

# 或放在项目目录内
yf.set_tz_cache_location("./cache/yfinance")
```

> **注意：** 应在程序启动时、任何数据请求之前调用，否则部分缓存可能已写入默认位置。

---

## 4. Multi-Level Column Index — 多级列索引

当使用 `yf.download()` 下载多支股票时，返回的 DataFrame 使用**多级列索引（MultiIndex）**。

### 数据结构说明

```python
import yfinance as yf

df = yf.download(["AAPL", "MSFT", "GOOGL"], period="1mo")
print(df.columns)
# MultiIndex([( 'Close', 'AAPL'),
#             ( 'Close', 'MSFT'),
#             ( 'Close', 'GOOGL'),
#             (  'High', 'AAPL'),
#             ...],
#            names=['Price', 'Ticker'])
```

### 访问多级列数据

```python
# 按价格类型访问（第一级）
df["Close"]               # 所有股票的收盘价，列名为 ticker
df["Close"]["AAPL"]       # AAPL 收盘价 Series
df[["Close", "Volume"]]   # 多个价格类型

# 按 ticker 访问（先切换 group_by）
df_by_ticker = yf.download(["AAPL", "MSFT"], period="1mo", group_by="ticker")
df_by_ticker["AAPL"]             # AAPL 的所有价格列
df_by_ticker["AAPL"]["Close"]    # AAPL 收盘价

# 使用 xs 跨级切片
df.xs("AAPL", level=1, axis=1)   # 获取 AAPL 所有列
df.xs("Close", level=0, axis=1)  # 获取所有股票收盘价
```

### 保存与读取 CSV

多级列索引保存到 CSV 后再读回，需特殊处理：

```python
# 保存
df.to_csv("prices.csv")

# 读回（需指定 header 行数和 index_col）
import pandas as pd
df_loaded = pd.read_csv("prices.csv", header=[0, 1], index_col=0, parse_dates=True)
```

### 转为单级列索引

```python
# 方式1：下载单支股票（自动为单级）
df_single = yf.download("AAPL", period="1mo")

# 方式2：下载多支但 multi_level_index=False
df_flat = yf.download(["AAPL", "MSFT"], period="1mo", multi_level_index=False)
# 此时列名为 "Close_AAPL", "Close_MSFT" 等

# 方式3：手动展平
df.columns = ["_".join(col) for col in df.columns]
```

---

## 5. Price Repair — 价格修复

Yahoo Finance 数据存在多种已知错误，尤其是非美国市场。在 `history()` 和 `download()` 中传入 `repair=True` 可启用自动修复。

修复后的 DataFrame 会新增 `Repaired?` 列，标记哪些行被修复过。

```python
import yfinance as yf

# 启用价格修复
df = yf.Ticker("8TRA.DE").history(period="1y", repair=True)
df = yf.download("MOB.ST", period="2y", repair=True)

# 查看哪些行被修复
print(df[df["Repaired?"] == True])
```

### 价格修复 (Price repair)

#### 缺失分红调整 (Missing dividend adjustment)

**现象：** 数据中存在分红记录，但前一天的 `Adj Close` = `Close`（未做复权调整）。  
**修复：** 手动对 `Adj Close` 补充分红调整。  
**注意：** `Repaired?` 列不会置为 `True`，因为只修改了 `Adj Close`，原始 `Close` 未变。

```
# 修复前（1398.HK）
                           Close  Adj Close  Dividends
2024-07-08               4.33       4.33       0.335715
2024-07-04               4.83       4.83       0.000000

# 修复后
                           Close  Adj Close  Dividends
2024-07-08               4.33    4.330000    0.335715
2024-07-04               4.83    4.494285    0.000000
```

#### 缺失拆股调整 (Missing split adjustment)

**现象：** 数据中存在拆股记录，但前期价格数据未做相应调整。  
**修复：** 手动对拆股前的历史价格应用拆股比例。  
**注意：** 需要数据范围包含拆股日后至少1天，用于校准（Yahoo 有时在拆股当天未能及时调整价格）。

```
# 修复前（MOB.ST）：拆股前价格未调整，出现价格跳变
# 修复后：历史价格统一按拆股比例调整
```

#### 缺失或损坏的数据 (Missing data)

**现象：** 某行/某列价格数据明显缺失或异常（如成交量为0但价格大幅波动）。  
**修复：** 自动用更小粒度的数据重建，例如用 `1h` 数据修复 `1d` 数据的缺失行。

```
# 常见场景（1COV.DE）：
# - 整行价格缺失
# - 成交量缺失但当日价格有变化
# - 收盘价异常（0316.HK 案例）
```

#### 100倍错误 (100x errors)

**现象：** Yahoo 混淆了货币单位（如美元/美分，英镑/便士），导致部分价格偏差100倍。  
**两种模式：**
- 随机分散在数据中 → 使用 `scipy` 统计检测
- 连续出现（Yahoo 某天永久切换货币单位）→ 检测连续块并统一修复

```
# 修复前（AET.L）：部分日期价格为正常值的100倍
# 修复后：统一恢复到正确量级
```

#### 价格重建算法说明

- 为减少额外请求，会批量分组获取修复所需的精细数据
- 会注意数据的时间限制，例如 `1h` 数据只能回溯最近2年
- 如果 Yahoo 事后修正了原始数据，重建的价格可能与修正后略有差异，成交量差异尤为明显

---

### 分红修复 (Dividend repair) — 新功能

修复以下几类分红数据错误：

#### 支持的修复类型

| 错误类型 | 说明 |
|----------|------|
| 调整缺失或100倍偏差 | `Adj Close` 未反映分红，或调整幅度差100倍 |
| 重复分红（7天内） | 同一分红在相邻日期重复出现 |
| 分红金额100倍偏差 | 相对除息日价格跌幅，分红金额差100倍 |
| 除息日期错误 | 价格跌幅发生在分红记录日期的数天/数周后 |
| 资本利得重复计算（新） | 分红与资本利得被叠加计算，导致调整过度 |

#### 关于误判（False Positives）

> **重要：** 修复逻辑依赖价格行为来判断分红是否异常，有极低概率将正常数据误判为错误。
>
> - 误判率随K线周期增大而上升，因此**只对 `1d` 周期进行分红修复**
> - 对多日周期（周线、月线）的请求：先获取 `1d` 数据并修复，再重采样 — 这同时解决了 Yahoo 对多日周期分红复权方式有缺陷的问题
> - `1d` 周期的误判率极低，主要发生在极小分红（如股息率0.5%）的情况下，正常价格波动被误认为是100倍异常的除息跌幅
> - 风险规避方式：获取至少6-12个月、含2次以上分红的数据，通过对比多次分红记录来识别误判

#### 修复示例

**调整缺失（1398.HK）**

```
# 修复前
                           Close  Adj Close  Dividends
2024-07-08               4.33       4.33       0.335715
2024-07-04               4.83       4.83       0.000000

# 修复后
                           Close  Adj Close  Dividends
2024-07-08               4.33    4.330000    0.335715
2024-07-04               4.83    4.494285    0.000000
```

**调整倍数偏小（3IN.L）**

```
# 修复前
                           Close  Adj Close  Dividends
2024-06-13               3.185   3.185000    0.05950
2024-06-12               3.270   3.269405    0.00000

# 修复后
                           Close  Adj Close  Dividends
2024-06-13               3.185   3.185000    0.05950
2024-06-12               3.270   3.210500    0.00000
```

**重复分红（ALC.SW，7天内重复）**

```
# 修复前
                               Close  Adj Close  Dividends
2023-05-10               70.580002  70.352142       0.21
2023-05-09               65.739998  65.318443       0.21   ← 重复
2023-05-08               66.379997  65.745682       0.00

# 修复后
                               Close  Adj Close  Dividends
2023-05-10               70.580002  70.352142       0.00
2023-05-09               65.739998  65.527764       0.21   ← 保留真实除息日
2023-05-08               66.379997  65.956371       0.00
```

**分红金额100倍偏大（HLCL.L）**

```
# 修复前
                           Close  Adj Close  Dividends
2024-06-27               2.360     2.3600       1.78   ← 应为 0.0178
2024-06-26               2.375     2.3572       0.00

# 修复后
                           Close  Adj Close  Dividends
2024-06-27               2.360     2.3600     0.0178
2024-06-26               2.375     2.3572     0.0000
```

**分红金额100倍偏小（BVT.L）**

```
# 修复前
                            Close  Adj Close  Dividends
2022-02-03               0.7534   0.675197    0.00001   ← 应为 0.001
2022-02-01               0.7844   0.702970    0.00000

# 修复后
                            Close  Adj Close  Dividends
2022-02-03               0.7534   0.675197    0.001
2022-02-01               0.7844   0.702075    0.000
```

**除息日期错误（TETY.ST）**

```
# 修复前（价格跌幅发生在 2022-06-22，但分红记录在 2022-06-20）
                               Close  Adj Close  Dividends
2022-06-22               66.699997  60.085415        0.0
2022-06-21               71.599998  64.499489        0.0
2022-06-20               71.800003  64.679657        5.0   ← 日期有误
2022-06-17               71.000000  59.454838        0.0

# 修复后（分红移至正确的除息日 2022-06-22）
                               Close  Adj Close  Dividends
2022-06-22               66.699997  60.085415        5.0   ← 正确
2022-06-21               71.599998  60.007881        0.0
2022-06-20               71.800003  60.175503        0.0
2022-06-17               71.000000  59.505021        0.0
```

**资本利得重复计算（DODFX）**

```
# 修复前（分红 0.837 实际应只含 0.42，其余 0.417 属于资本利得，被重复计算）
                               Close  Adj Close  Dividends  Capital Gains
2025-12-18               16.219999  16.219999      0.837          0.417
2025-12-17               16.920000  15.665999      0.000          0.000

# 修复后
                               Close  Adj Close  Dividends  Capital Gains
2025-12-18               16.219999  16.219999       0.42          0.417
2025-12-17               16.920000  16.083000       0.00          0.000
```

---

# 二、API 参考

---

## 6. Ticker / Tickers — 入口类

### `yf.Ticker(ticker, session=None)`

**类型：** class  
**说明：** 核心入口类，创建单个股票对象。所有属性和方法均挂载于此实例上。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `ticker` | str | 股票代码，如 `"AAPL"` |
| `session` | requests.Session | 可选，自定义 HTTP session（用于代理、自定义 headers 等） |

```python
import yfinance as yf

aapl = yf.Ticker("AAPL")           # 美股
baba = yf.Ticker("9988.HK")        # 港股
ping = yf.Ticker("601318.SS")      # A股（上交所）
sz   = yf.Ticker("000001.SZ")      # A股（深交所）
tsla = yf.Ticker("TSLA")           # 美股
spy  = yf.Ticker("SPY")            # ETF

# 使用自定义 session（如需设置代理或 headers）
import requests
session = requests.Session()
session.proxies = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
t = yf.Ticker("AAPL", session=session)

# 或通过全局配置设置代理（推荐）
yf.config.network.proxy = "http://proxy:8080"
```

---

### `yf.Tickers(tickers, session=None)`

**类型：** class  
**说明：** 批量管理多个股票对象，传入空格分隔字符串或列表。

```python
ts = yf.Tickers("AAPL MSFT GOOGL")
# 或
ts = yf.Tickers(["AAPL", "MSFT", "GOOGL"])

# 访问单个
ts.tickers["AAPL"].info
ts.tickers["MSFT"].history(period="1mo")
ts.tickers["GOOG"].actions

# WebSocket 实时数据
ts.live()
```

---

## 7. Stock — 行情与基本信息

> 以下所有属性/方法均通过 `Ticker` 实例访问，例如 `aapl.history()`

---

### `Ticker.isin` / `Ticker.get_isin()`

**类型：** property / method  
**说明：** 获取国际证券识别码（ISIN，12位字母数字）。  
**返回值：** `str`

```python
aapl.isin
# → 'US0378331005'
```

---

### `Ticker.history()` ★ 最常用

**类型：** method  
**说明：** 获取历史 OHLCV K线数据，返回 pandas DataFrame。`period` 和 `start/end` 二选一。

**完整签名：**
```python
Ticker.history(
    period='1mo',
    interval='1d',
    start=None,
    end=None,
    prepost=False,
    actions=True,
    auto_adjust=True,
    back_adjust=False,
    repair=False,
    keepna=False,
    rounding=False,
    timeout=10,
    raise_errors=False
)
```

**参数说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `period` | `'1mo'` | 预设时间段：`1d` `5d` `1mo` `3mo` `6mo` `1y` `2y` `5y` `10y` `ytd` `max` |
| `interval` | `'1d'` | K线周期：`1m` `2m` `5m` `15m` `30m` `60m` `90m` `1h` `1d` `5d` `1wk` `1mo` `3mo`（分钟级数据仅限最近60天） |
| `start` | `None` | 开始日期，格式 `YYYY-MM-DD`，**包含**当天 |
| `end` | `None` | 结束日期，格式 `YYYY-MM-DD`，**不含**当天 |
| `prepost` | `False` | 是否包含盘前盘后数据 |
| `actions` | `True` | 是否在 DataFrame 中包含分红/拆股列 |
| `auto_adjust` | `True` | 自动前复权（调整 OHLC 以反映分红/拆股） |
| `back_adjust` | `False` | 后复权（向后调整历史价格） |
| `repair` | `False` | 修复 Yahoo 数据中的异常价格（100x错误、缺失值、错误的复权调整等，详见第5节） |
| `keepna` | `False` | 是否保留 Yahoo 返回的 NaN 行 |
| `rounding` | `False` | 是否将价格四舍五入到2位小数 |
| `timeout` | `10` | 请求超时秒数 |
| `raise_errors` | `False` | 若 `True`，将错误以异常抛出而非仅记录日志 |

**返回值：** `pd.DataFrame`，列名为 `Open` `High` `Low` `Close` `Volume` `Dividends` `Stock Splits`  
（启用 `repair=True` 时额外包含 `Repaired?` 列）

```python
# 基本用法
df = aapl.history(period="1y")
df = aapl.history(start="2024-01-01", end="2024-12-31")

# 分钟级数据（仅最近60天）
df = aapl.history(period="5d", interval="1m")

# 含盘前盘后
df = aapl.history(period="5d", interval="1h", prepost=True)

# 启用价格修复（非美股推荐开启）
df = yf.Ticker("8TRA.DE").history(period="1y", repair=True)

# 不自动复权（获取原始价格）
df = aapl.history(period="1y", auto_adjust=False)
```

---

### `Ticker.get_history_metadata()`

**类型：** method  
**说明：** 获取历史数据的元信息字典，包含货币、时区、交易所、首个交易日等。  
**返回值：** `dict`

```python
meta = aapl.get_history_metadata()
# {
#   'currency': 'USD',
#   'exchangeName': 'NMS',
#   'timezone': 'America/New_York',
#   'instrumentType': 'EQUITY',
#   'firstTradeDate': 345479400,
#   'regularMarketTime': 1716825600,
#   'gmtoffset': -14400,
#   ...
# }
```

---

### `Ticker.dividends` / `Ticker.get_dividends(period='max')`

**类型：** property / method  
**说明：** 历史分红记录，以日期为索引的 Series。  
**返回值：** `pd.Series`

```python
aapl.dividends
aapl.get_dividends(period="5y")
# Date
# 2023-02-10    0.23
# 2023-05-12    0.24
# dtype: float64
```

---

### `Ticker.splits` / `Ticker.get_splits(period='max')`

**类型：** property / method  
**说明：** 历史股票拆分记录（如 `4.0` 表示 4:1 拆股）。  
**返回值：** `pd.Series`

```python
aapl.splits
# Date
# 2020-08-31    4.0
# dtype: float64
```

---

### `Ticker.actions` / `Ticker.get_actions(period='max')`

**类型：** property / method  
**说明：** 将分红（dividends）和拆股（splits）合并到一张表。  
**返回值：** `pd.DataFrame`，列为 `Dividends` `Stock Splits`

```python
aapl.actions
```

---

### `Ticker.capital_gains` / `Ticker.get_capital_gains(period='max')`

**类型：** property / method  
**说明：** 资本利得分配，主要用于 ETF 和共同基金，普通股票通常为空。  
**返回值：** `pd.Series`

```python
spy = yf.Ticker("SPY")
spy.capital_gains
```

---

### `Ticker.get_shares_full(start=None, end=None)`

**类型：** method  
**说明：** 获取高频历史总发行股数时序（比 `info["sharesOutstanding"]` 粒度更细）。  
**返回值：** `pd.Series`

```python
shares = aapl.get_shares_full(start="2020-01-01")
```

---

### `Ticker.info` / `Ticker.get_info()`

**类型：** property / method  
**说明：** 返回包含 100+ 字段的完整公司信息字典，含市值、估值倍数、行业、公司简介等。速度较慢，有本地缓存。  
**返回值：** `dict`

```python
info = aapl.info

# 标识信息
info["symbol"]                       # "AAPL"
info["shortName"]                    # "Apple Inc."
info["longName"]                     # "Apple Inc."
info["sector"]                       # "Technology"
info["industry"]                     # "Consumer Electronics"
info["country"]                      # "United States"
info["currency"]                     # "USD"
info["exchange"]                     # "NMS"
info["quoteType"]                    # "EQUITY"
info["website"]                      # 官网
info["fullTimeEmployees"]            # 员工数

# 市值与估值
info["marketCap"]                    # 市值（整数，单位：美元）
info["enterpriseValue"]              # 企业价值
info["trailingPE"]                   # 市盈率（TTM）
info["forwardPE"]                    # 市盈率（预测）
info["priceToBook"]                  # 市净率
info["priceToSalesTrailing12Months"] # 市销率（TTM）
info["enterpriseToRevenue"]          # EV/Revenue
info["enterpriseToEbitda"]           # EV/EBITDA

# 股息
info["dividendYield"]                # 股息率（小数，如 0.005 = 0.5%）
info["dividendRate"]                 # 年度股息额（每股）
info["exDividendDate"]               # 除息日（Unix 时间戳）
info["payoutRatio"]                  # 分红派息比例

# 技术指标
info["beta"]                         # Beta 系数
info["52WeekChange"]                 # 近52周涨跌幅
info["fiftyTwoWeekHigh"]             # 52周最高价
info["fiftyTwoWeekLow"]              # 52周最低价
info["fiftyDayAverage"]              # 50日均价
info["twoHundredDayAverage"]         # 200日均价

# 成交
info["volume"]                       # 最新交易日成交量
info["averageVolume"]                # 10日平均成交量
info["averageVolume10days"]          # 同上

# 股本
info["sharesOutstanding"]            # 总发行股数
info["floatShares"]                  # 流通股数
info["sharesShort"]                  # 融券做空股数
info["shortRatio"]                   # 空头比率
info["heldPercentInsiders"]          # 内部人士持股比例
info["heldPercentInstitutions"]      # 机构持股比例

# 公司描述
info["longBusinessSummary"]          # 业务描述
info["address1"]                     # 公司地址
info["city"]                         # 城市
info["zip"]                          # 邮编
info["phone"]                        # 电话
```

---

### `Ticker.fast_info` / `Ticker.get_fast_info()`

**类型：** property / method  
**说明：** 轻量快速信息对象，只含核心字段，速度远快于 `.info`。适合只需要价格/市值的场景。  
**返回值：** `FastInfo` 对象

```python
fi = aapl.fast_info

fi.last_price                # 最新成交价
fi.last_volume               # 最新成交量
fi.previous_close            # 前收盘价
fi.open                      # 今日开盘价
fi.day_high                  # 今日最高价
fi.day_low                   # 今日最低价
fi.fifty_day_average         # 50日均价
fi.two_hundred_day_average   # 200日均价
fi.year_high                 # 52周最高价
fi.year_low                  # 52周最低价
fi.market_cap                # 市值
fi.shares                    # 总股数
fi.currency                  # 货币（如 "USD"）
fi.exchange                  # 交易所代码
fi.quote_type                # 品种类型（EQUITY / ETF / INDEX ...）
fi.timezone                  # 时区（如 "America/New_York"）
```

---

### `Ticker.news` / `Ticker.get_news(count=10, tab='news')`

**类型：** property / method  
**说明：** 获取与该股票相关的新闻列表。

**参数：**

| 参数 | 说明 |
|------|------|
| `count` | 返回条数，默认 10 |
| `tab` | `"news"`（默认）/ `"all"` / `"press releases"` |

**返回值：** `list[dict]`

```python
news = aapl.get_news(count=5)
for n in news:
    print(n["title"])
    print(n["link"])
    print(n["publisher"])
    print(n["providerPublishTime"])  # Unix 时间戳

# 获取新闻稿
press = aapl.get_news(count=5, tab="press releases")
```

---

## 8. Financials — 财务报表

---

### 利润表 Income Statement

#### `Ticker.income_stmt`

**类型：** property — 年报利润表  
**返回值：** `pd.DataFrame`（行=财务指标，列=报告期日期）

```python
df = aapl.income_stmt
# 常见行名:
# Total Revenue（总收入）
# Cost Of Revenue（营业成本）
# Gross Profit（毛利润）
# Operating Expense（运营费用）
# Operating Income（营业利润）
# EBITDA
# Net Income（净利润）
# Diluted EPS（摊薄每股收益）
# Basic EPS（基本每股收益）
# Interest Expense（利息费用）
# Tax Provision（所得税）
```

#### `Ticker.quarterly_income_stmt`

**类型：** property — 季报利润表（最近4个季度）

```python
aapl.quarterly_income_stmt
```

#### `Ticker.ttm_income_stmt`

**类型：** property — 滚动12个月（TTM）利润表

```python
aapl.ttm_income_stmt
```

#### `Ticker.get_income_stmt(as_dict=False, pretty=False, freq='yearly')`

**类型：** method  
**参数：**

| 参数 | 说明 |
|------|------|
| `as_dict` | 是否返回字典而非 DataFrame |
| `pretty` | 是否格式化行名（更易读） |
| `freq` | `'yearly'` / `'quarterly'` / `'ttm'` |

**返回值：** `pd.DataFrame`

---

### 资产负债表 Balance Sheet

#### `Ticker.balance_sheet`

**类型：** property — 年报资产负债表

```python
df = aapl.balance_sheet
# 常见行名:
# Total Assets（总资产）
# Total Liabilities Net Minority Interest（总负债）
# Stockholders Equity（股东权益）
# Total Debt（总债务）
# Net Debt（净债务）
# Cash And Cash Equivalents（现金及等价物）
# Current Assets（流动资产）
# Current Liabilities（流动负债）
# Net PPE（固定资产净值）
# Goodwill（商誉）
# Retained Earnings（留存收益）
```

#### `Ticker.quarterly_balance_sheet`

**类型：** property — 季报资产负债表

```python
aapl.quarterly_balance_sheet
```

#### `Ticker.get_balance_sheet(as_dict=False, pretty=False, freq='yearly')`

**类型：** method — 参数同 `get_income_stmt`  
**返回值：** `pd.DataFrame`

---

### 现金流量表 Cash Flow

#### `Ticker.cashflow`

**类型：** property — 年报现金流量表

```python
df = aapl.cashflow
# 常见行名:
# Operating Cash Flow（经营活动现金流）
# Investing Cash Flow（投资活动现金流）
# Financing Cash Flow（融资活动现金流）
# Free Cash Flow（自由现金流）
# Capital Expenditure（资本开支）
# Issuance Of Debt（债务发行）
# Repayment Of Debt（债务偿还）
# Repurchase Of Capital Stock（股票回购）
# Changes In Cash（现金净变化）
```

#### `Ticker.quarterly_cashflow`

**类型：** property — 季报现金流量表

```python
aapl.quarterly_cashflow
```

#### `Ticker.ttm_cashflow`

**类型：** property — 滚动12个月现金流量表

```python
aapl.ttm_cashflow
```

#### `Ticker.get_cashflow(as_dict=False, pretty=False, freq='yearly')`

**类型：** method — 参数同 `get_income_stmt`  
**返回值：** `pd.DataFrame`

---

### 盈利与日历

#### `Ticker.earnings` / `Ticker.get_earnings(as_dict=False, freq='yearly')`

**类型：** property / method  
**说明：** 年度/季度 EPS 与营收汇总表（比完整利润表更简洁）。  
**返回值：** `pd.DataFrame`，列为 `Revenue` `Earnings`

```python
aapl.earnings
aapl.get_earnings(freq="quarterly")
```

#### `Ticker.calendar`

**类型：** property  
**说明：** 下次财报日期、预期 EPS/营收、股利日期等。  
**返回值：** `dict`

```python
cal = aapl.calendar
cal["Earnings Date"]       # 下次财报日期（列表，含范围）
cal["Earnings Average"]    # 平均预期 EPS
cal["Earnings Low"]        # 预期 EPS 下限
cal["Earnings High"]       # 预期 EPS 上限
cal["Revenue Average"]     # 平均预期营收
cal["Revenue Low"]
cal["Revenue High"]
cal["Dividend Date"]       # 股利支付日
cal["Ex-Dividend Date"]    # 除息日
```

#### `Ticker.earnings_dates` / `Ticker.get_earnings_dates(limit=12, offset=0)`

**类型：** property / method  
**说明：** 历史财报发布日期及 EPS 实际值 vs 预期值对比。  
**返回值：** `pd.DataFrame`

```python
df = aapl.get_earnings_dates(limit=8)
# Columns: EPS Estimate  Reported EPS  Surprise(%)
```

#### `Ticker.sec_filings` / `Ticker.get_sec_filings()`

**类型：** property / method  
**说明：** 向 SEC 提交的历史文件列表（10-K 年报、10-Q 季报、8-K 重大事件等）。  
**返回值：** `list[dict]`

```python
filings = aapl.sec_filings
for f in filings:
    print(f["type"])      # 10-K / 10-Q / 8-K ...
    print(f["date"])      # 提交日期
    print(f["url"])       # 文件链接
    print(f["exhibits"])  # 附件列表
```

---

## 9. Analysis & Holdings — 分析与持股

---

### 分析师评级

#### `Ticker.recommendations` / `Ticker.get_recommendations()`

**类型：** property / method  
**返回值：** `pd.DataFrame`，列为 `Firm` `To Grade` `From Grade` `Action`

```python
df = aapl.recommendations
```

#### `Ticker.recommendations_summary` / `Ticker.get_recommendations_summary()`

**类型：** property / method  
**说明：** 评级汇总，按周期统计 buy / hold / sell 数量。  
**返回值：** `pd.DataFrame`

```python
df = aapl.recommendations_summary
# Columns: strongBuy  buy  hold  sell  strongSell
```

#### `Ticker.upgrades_downgrades` / `Ticker.get_upgrades_downgrades()`

**类型：** property / method  
**说明：** 评级上调/下调记录，含来源机构和日期。  
**返回值：** `pd.DataFrame`

```python
aapl.upgrades_downgrades
```

#### `Ticker.analyst_price_targets` / `Ticker.get_analyst_price_targets()`

**类型：** property / method  
**说明：** 分析师目标价统计（高/低/均值/当前）。  
**返回值：** `dict`

```python
apt = aapl.analyst_price_targets
apt["current"]           # 当前价格
apt["mean"]              # 均值目标价
apt["high"]              # 最高目标价
apt["low"]               # 最低目标价
apt["numberOfAnalysts"]  # 覆盖分析师人数
```

#### `Ticker.sustainability` / `Ticker.get_sustainability()`

**类型：** property / method  
**说明：** ESG 评分（环境、社会、治理三维度）及争议评分。  
**返回值：** `pd.DataFrame`

```python
df = aapl.sustainability
# totalEsg            # 综合 ESG 分
# environmentScore    # 环境分
# socialScore         # 社会分
# governanceScore     # 治理分
# controversyLevel    # 争议等级
# peerEsgScorePerformance  # 同行对比
```

---

### 盈利预测

#### `Ticker.earnings_estimate` / `Ticker.get_earnings_estimate()`

**类型：** property / method  
**说明：** EPS 预测，按周期（当季/下季/当年/明年）列出均值、上下限及同比。  
**返回值：** `pd.DataFrame`

```python
df = aapl.earnings_estimate
# Index: 0q（当季）1q（下季）0y（当年）1y（明年）
# Columns: avg  low  high  yearAgoEps  numberOfAnalysts  growth
```

#### `Ticker.revenue_estimate` / `Ticker.get_revenue_estimate()`

**类型：** property / method  
**说明：** 营收预测，结构同 `earnings_estimate`。  
**返回值：** `pd.DataFrame`

```python
df = aapl.revenue_estimate
# Columns: avg  low  high  yearAgoRevenue  numberOfAnalysts  growth
```

#### `Ticker.earnings_history` / `Ticker.get_earnings_history()`

**类型：** property / method  
**说明：** 历史各季度 EPS 实际值 vs 预期值及超预期百分比。  
**返回值：** `pd.DataFrame`

```python
df = aapl.earnings_history
# Columns: epsEstimate  epsActual  epsDifference  surprisePercent
```

#### `Ticker.eps_trend` / `Ticker.get_eps_trend()`

**类型：** property / method  
**说明：** EPS 预测趋势，对比7天前、30天前、60天前、90天前的预测变化。  
**返回值：** `pd.DataFrame`

```python
df = aapl.eps_trend
# Columns: current  7daysAgo  30daysAgo  60daysAgo  90daysAgo
```

#### `Ticker.eps_revisions` / `Ticker.get_eps_revisions()`

**类型：** property / method  
**说明：** EPS 预测修正次数（最近7天/30天内上调/下调的分析师数量）。  
**返回值：** `pd.DataFrame`

```python
df = aapl.eps_revisions
# Columns: upLast7days  upLast30days  downLast30days  downLast90days
```

#### `Ticker.growth_estimates` / `Ticker.get_growth_estimates()`

**类型：** property / method  
**说明：** 增长率预测，对比该股票与所属行业、板块、标普500的增长预期。  
**返回值：** `pd.DataFrame`

```python
df = aapl.growth_estimates
```

---

### 持股信息

#### `Ticker.major_holders` / `Ticker.get_major_holders()`

**类型：** property / method  
**说明：** 主要持股比例概览（内部人士持股%、机构持股%等）。  
**返回值：** `pd.DataFrame`

```python
df = aapl.major_holders
# insidersPercentHeld      内部人士持股比例
# institutionsPercentHeld  机构持股比例
# institutionsFloatPercentHeld  机构持流通股比例
# institutionsCount        机构持股数量
```

#### `Ticker.institutional_holders` / `Ticker.get_institutional_holders()`

**类型：** property / method  
**返回值：** `pd.DataFrame`，列为 `Holder` `Shares` `Date Reported` `% Out` `Value`

```python
df = aapl.institutional_holders
print(df.head(10))
```

#### `Ticker.mutualfund_holders` / `Ticker.get_mutualfund_holders()`

**类型：** property / method  
**返回值：** `pd.DataFrame`

```python
df = aapl.mutualfund_holders
```

#### `Ticker.insider_transactions` / `Ticker.get_insider_transactions()`

**类型：** property / method  
**说明：** 内部人士（高管、董事）历史交易记录（买入/卖出）。  
**返回值：** `pd.DataFrame`

```python
df = aapl.insider_transactions
# Columns: Insider  Shares  Value  Transaction  Start Date  URL
```

#### `Ticker.insider_purchases` / `Ticker.get_insider_purchases()`

**类型：** property / method  
**说明：** 内部人士买入行为汇总统计。  
**返回值：** `pd.DataFrame`

```python
df = aapl.insider_purchases
```

#### `Ticker.insider_roster_holders` / `Ticker.get_insider_roster_holders()`

**类型：** property / method  
**说明：** 内部人士名单及其持股数量。  
**返回值：** `pd.DataFrame`，列为 `Name` `Position` `Shares` `% Out` `Value` `Latest Transaction`

```python
df = aapl.insider_roster_holders
```

---

### 基金/ETF 数据

#### `Ticker.funds_data` / `Ticker.get_funds_data()`

**类型：** property / method  
**说明：** 返回 `FundsData` 对象，仅适用于 ETF 和共同基金（详见第16节）。  
**返回值：** `FundsData` 对象

```python
spy = yf.Ticker("SPY")
fd = spy.funds_data
fd.description          # 基金描述
fd.fund_overview        # 概览字典
fd.fund_operations      # 运营数据 DataFrame
fd.asset_classes        # 资产类别分配 dict
fd.top_holdings         # 前十持仓 DataFrame
fd.equity_holdings      # 权益持仓详情
fd.bond_holdings        # 债券持仓
fd.bond_ratings         # 债券评级分布 dict
fd.sector_weightings    # 行业权重 dict
fd.quote_type()         # "ETF" / "MUTUALFUND"
```

---

## 10. Market / Calendars — 市场与日历

### `yf.Market(market)`

**类型：** class  
**说明：** 获取特定市场的整体行情摘要和开市状态。  
**返回值：** `Market` 对象

```python
m = yf.Market("us_market")
m.status    # 'open' / 'closed' / 'pre' / 'post'
m.summary   # 主要指数行情字典
```

常用市场代码：`us_market` `gb_market` `jp_market` `hk_market` `cn_market`

---

### `yf.Calendars(country)`

**类型：** class  
**说明：** 获取特定国家/市场的交易日历（节假日、交易时间等）。  
**返回值：** `Calendars` 对象

```python
cal = yf.Calendars("US")
```

---

## 11. Search & Lookup — 搜索查找

### `yf.Search(query, news_count=8, ...)`

**类型：** class  
**说明：** 按关键词模糊搜索股票和相关新闻。  
**返回值：** `Search` 对象

```python
res = yf.Search("Apple")
res.quotes    # 匹配股票列表，每项含 symbol / shortname / exchange / type
res.news      # 相关新闻列表

for q in res.quotes:
    print(q["symbol"], q["shortname"], q["exchange"])
```

---

### `yf.Lookup(query)`

**类型：** class  
**说明：** 精确查找特定 symbol 类型的信息。  
**返回值：** `Lookup` 对象

```python
lk = yf.Lookup("AAPL")
lk.get_stock()    # 股票
lk.get_etf()      # ETF
lk.get_fund()     # 共同基金
lk.get_index()    # 指数
lk.get_future()   # 期货
```

---

## 12. WebSocket — 实时数据流

### `yf.WebSocket()`

**类型：** class  
**说明：** 同步模式订阅实时行情推送（阻塞式监听）。

```python
ws = yf.WebSocket()
ws.subscribe(["AAPL", "MSFT", "GOOGL"])

def on_message(data):
    print(data["id"], data["price"], data["time"])

ws.listen(on_message)

# 快捷方式（通过 Ticker）
aapl = yf.Ticker("AAPL")
aapl.live()

# 多股票快捷方式
ts = yf.Tickers("AAPL MSFT")
ts.live()
```

---

### `yf.AsyncWebSocket()`

**类型：** class  
**说明：** 异步模式订阅实时行情推送，配合 `asyncio` 使用。

```python
import asyncio
import yfinance as yf

async def on_message(data):
    print(data["id"], data["price"])

async def main():
    ws = yf.AsyncWebSocket()
    await ws.subscribe(["AAPL", "TSLA"], callback=on_message)
    await ws.listen()

asyncio.run(main())
```

---

## 13. Sector & Industry — 行业板块

### `yf.Sector(sector_key)`

**类型：** class  
**说明：** 获取特定板块的概览、龙头公司和相关 ETF。  
**返回值：** `Sector` 对象

**可用板块键：**

| 键 | 板块名称 |
|----|----------|
| `technology` | 科技 |
| `healthcare` | 医疗保健 |
| `financial-services` | 金融服务 |
| `consumer-cyclical` | 非必需消费 |
| `industrials` | 工业 |
| `communication-services` | 通信服务 |
| `consumer-defensive` | 必需消费 |
| `energy` | 能源 |
| `real-estate` | 房地产 |
| `basic-materials` | 基础材料 |
| `utilities` | 公用事业 |

```python
tech = yf.Sector("technology")
tech.key               # "technology"
tech.name              # "Technology"
tech.symbol            # 板块基准 ETF symbol
tech.overview          # 概况字典
tech.top_companies     # 龙头公司 DataFrame（含市值、涨幅等）
tech.top_etfs          # 相关 ETF DataFrame
tech.top_mutual_funds  # 相关基金 DataFrame
tech.industries        # 子行业列表
tech.research_reports  # 研究报告
```

---

### `yf.Industry(industry_key)`

**类型：** class  
**说明：** 获取特定细分行业的概览和龙头公司，比 Sector 粒度更精细。  
**返回值：** `Industry` 对象

```python
semi = yf.Industry("semiconductors")
semi.key                        # "semiconductors"
semi.name                       # "Semiconductors"
semi.sector_key                 # "technology"
semi.top_companies              # 龙头公司 DataFrame
semi.top_growth_companies       # 增速最快公司
semi.top_performing_companies   # 表现最佳公司
semi.overview                   # 行业概况
```

---

## 14. Screener & Query — 股票筛选器

### `yf.EquityQuery(operator, operands)`

**类型：** class  
**说明：** 构建股票筛选条件，支持比较运算符和逻辑组合。

**支持的运算符：**

| 运算符 | 说明 | 示例 |
|--------|------|------|
| `"gt"` | 大于 | `EquityQuery("gt", ["eodprice", 10])` |
| `"lt"` | 小于 | `EquityQuery("lt", ["peratio.lasttwelvemonths", 20])` |
| `"gte"` | 大于等于 | `EquityQuery("gte", ["dividendyield.lasttwelvemonths", 0.02])` |
| `"lte"` | 小于等于 | `EquityQuery("lte", ["pricetobook", 3])` |
| `"eq"` | 等于 | `EquityQuery("eq", ["region", "us"])` |
| `"btwn"` | 介于 | `EquityQuery("btwn", ["eodprice", 10, 100])` |
| `"in"` / `"isin"` | 在列表中 | `EquityQuery("in", ["exchange", ["NMS", "NYQ"]])` |
| `"and"` | 逻辑与 | `EquityQuery("and", [q1, q2, q3])` |
| `"or"` | 逻辑或 | `EquityQuery("or", [q1, q2])` |

**常用筛选字段：**

| 字段名 | 说明 |
|--------|------|
| `eodprice` | 收盘价 |
| `marketcap` | 市值 |
| `peratio.lasttwelvemonths` | 市盈率（TTM） |
| `pricetobook` | 市净率 |
| `pricetosales` | 市销率 |
| `dividendyield.lasttwelvemonths` | 股息率（TTM） |
| `epsgrowth.lasttwelvemonths` | EPS 增速 |
| `revenuegrowth.lasttwelvemonths` | 营收增速 |
| `region` | 地区（如 `"us"` `"europe"` `"asia"` `"cn"`） |
| `exchange` | 交易所（如 `"NMS"` `"NYQ"` `"PCX"`） |
| `sector` | 板块（如 `"Technology"` `"Healthcare"`） |
| `country` | 国家（如 `"United States"` `"China"`） |

```python
from yfinance import EquityQuery, screen

# 示例1：高股息低估值
q = EquityQuery("and", [
    EquityQuery("eq",  ["region", "us"]),
    EquityQuery("gt",  ["eodprice", 10]),
    EquityQuery("lt",  ["peratio.lasttwelvemonths", 15]),
    EquityQuery("gte", ["dividendyield.lasttwelvemonths", 0.03])
])

# 示例2：嵌套逻辑（PE<20 或 PB<2）且市值>100亿
q2 = EquityQuery("and", [
    EquityQuery("or", [
        EquityQuery("lt", ["peratio.lasttwelvemonths", 20]),
        EquityQuery("lt", ["pricetobook", 2])
    ]),
    EquityQuery("gt", ["marketcap", 10_000_000_000])
])

# 示例3：价格区间
q3 = EquityQuery("btwn", ["eodprice", 50, 200])
```

---

### `yf.FundQuery(operator, operands)`

**类型：** class  
**说明：** 构建共同基金筛选条件，用法同 `EquityQuery`。

```python
from yfinance import FundQuery
q = FundQuery("gt", ["fundsize", 1_000_000_000])
```

---

### `yf.ETFQuery(operator, operands)`

**类型：** class  
**说明：** 构建 ETF 筛选条件，用法同 `EquityQuery`。

```python
from yfinance import ETFQuery
q = ETFQuery("eq", ["exchange", "NYQ"])
```

---

### `yf.screen(query, sortField, sortAsc, offset, size)`

**类型：** function  
**说明：** 执行筛选查询，返回匹配的证券列表。

**参数：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `query` | — | EquityQuery / FundQuery / ETFQuery 对象 |
| `sortField` | `"marketcap"` | 排序字段（同筛选字段名） |
| `sortAsc` | `False` | 是否升序排序，默认降序 |
| `offset` | `0` | 分页起始位置（用于翻页） |
| `size` | `25` | 返回最大条数 |

**返回值：** `dict`，含 `quotes`（结果列表）和 `total`（符合条件总数）

```python
results = yf.screen(
    q,
    sortField="marketcap",
    sortAsc=False,
    offset=0,
    size=25
)

total = results["total"]
quotes = results["quotes"]

for stock in quotes:
    print(stock["symbol"], stock["shortName"], stock.get("marketCap"))

# 翻页获取更多结果
results_p2 = yf.screen(q, offset=25, size=25)
```

---

## 15. Functions & Utilities — 工具函数

### `yf.download(tickers, ...)`

**类型：** function  
**说明：** 批量下载多支股票的历史价格数据，内部使用多线程并发，比循环调用 `.history()` 效率更高。

**完整签名：**
```python
yf.download(
    tickers,
    period='1mo',
    interval='1d',
    start=None,
    end=None,
    group_by='column',
    auto_adjust=False,
    back_adjust=False,
    repair=False,
    keepna=False,
    progress=True,
    multi_level_index=True,
    threads=True,
    timeout=10
)
```

**参数说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tickers` | — | 股票代码列表或空格分隔字符串 |
| `group_by` | `'column'` | `"column"`：第一级为价格类型，子列为 ticker；`"ticker"`：第一级为 ticker |
| `multi_level_index` | `True` | 多支股票时是否使用 MultiIndex 列（`False` 时列名为 `Close_AAPL` 格式） |
| `progress` | `True` | 是否显示下载进度条 |
| `threads` | `True` | 是否使用多线程并发下载 |
| `repair` | `False` | 启用价格修复（详见第5节） |

**返回值：** `pd.DataFrame`（单支股票为普通 DataFrame，多支为 MultiIndex DataFrame）

```python
# 单支股票（普通 DataFrame）
df = yf.download("AAPL", period="1y")
df["Close"]

# 多支，按价格类型分组（默认）
df = yf.download(["AAPL", "MSFT", "GOOGL"], period="1y", group_by="column")
df["Close"]           # 所有股票收盘价，列名为 ticker
df["Close"]["AAPL"]   # AAPL 收盘价

# 多支，按 ticker 分组
df = yf.download(["AAPL", "MSFT"], period="1y", group_by="ticker")
df["AAPL"]            # AAPL 所有价格列
df["AAPL"]["Close"]   # AAPL 收盘价

# 单级列名（multi_level_index=False）
df = yf.download(["AAPL", "MSFT"], period="1y", multi_level_index=False)
df["Close_AAPL"]      # 列名为 "价格类型_Ticker"
```

---

### `yf.enable_debug_mode()`

**类型：** function  
**说明：** 开启详细 HTTP 请求/响应日志，用于调试网络问题（等价于 `yf.config.debug.logging = True`）。  
**返回值：** `None`

```python
yf.enable_debug_mode()

# 等价写法（推荐）
yf.config.debug.logging = True
```

---

### `yf.set_tz_cache_location(tz_cache_location)`

**类型：** function  
**说明：** 设置时区数据的本地缓存目录路径，避免每次运行重复从网络获取时区信息。应在任何数据请求之前调用。  
**返回值：** `None`

```python
yf.set_tz_cache_location("/tmp/yf_tz_cache")
yf.set_tz_cache_location("/data/cache/yfinance")
```

---

## 16. FundsData — 基金数据类

> 通过 `Ticker.funds_data` 获取，仅适用于 ETF 和共同基金。

**完整类名：** `yfinance.scrapers.funds.FundsData`

---

### 属性（Properties）

#### `FundsData.description`

**返回值：** `str` — 基金/ETF 的文字描述

```python
spy = yf.Ticker("SPY")
fd = spy.funds_data
print(fd.description)
```

#### `FundsData.fund_overview`

**返回值：** `dict` — 基金概览（名称、类型、基准指数、基金经理、晨星评级等）

```python
fd.fund_overview
# {
#   "fundFamily": "SPDR State Street Global Advisors",
#   "legalType": "Exchange Traded Fund",
#   "morningStarOverallRating": 4,
#   "categoryName": "Large Blend",
#   ...
# }
```

#### `FundsData.fund_operations`

**返回值：** `pd.DataFrame` — 运营数据（费率、换手率、净资产规模等）

```python
fd.fund_operations
# annualReportExpenseRatio   年度总费率
# annualHoldingsTurnover     年度换手率
# totalNetAssets             净资产规模（AUM）
```

#### `FundsData.asset_classes`

**返回值：** `dict[str, float]` — 各资产类别的配置比例

```python
fd.asset_classes
# {
#   "cashPosition": 0.0051,
#   "stockPosition": 0.9949,
#   "bondPosition": 0.0,
#   "otherPosition": 0.0,
#   "preferredPosition": 0.0,
#   "convertiblePosition": 0.0
# }
```

#### `FundsData.top_holdings`

**返回值：** `pd.DataFrame` — 前十大持仓明细

```python
fd.top_holdings
# Columns: symbol  holdingName  holdingPercent
```

#### `FundsData.equity_holdings`

**返回值：** `pd.DataFrame` — 权益类持仓分析（加权平均 PE、PB 等指标）

```python
fd.equity_holdings
```

#### `FundsData.bond_holdings`

**返回值：** `pd.DataFrame` — 债券类持仓分析（久期、信用质量等）

```python
fd.bond_holdings
```

#### `FundsData.bond_ratings`

**返回值：** `dict[str, float]` — 债券评级分布（各评级占比）

```python
fd.bond_ratings
# {"aaa": 0.63, "aa": 0.05, "a": 0.12, "bbb": 0.18, ...}
```

#### `FundsData.sector_weightings`

**返回值：** `dict[str, float]` — 各行业板块的持仓权重

```python
fd.sector_weightings
# {
#   "technology": 0.3102,
#   "healthcare": 0.1278,
#   "financial-services": 0.1265,
#   "consumer-cyclical": 0.1023,
#   ...
# }
```

---

### 方法（Methods）

#### `FundsData.quote_type()`

**返回值：** `str` — `"ETF"` 或 `"MUTUALFUND"`

```python
fd.quote_type()
# → "ETF"
```

---

## 17. PriceHistory — 底层历史类

> 这是 `Ticker.history()` 背后的实现类，通常不需要直接使用，了解其参数签名有助于调试。

**完整类名：** `yfinance.scrapers.history.PriceHistory`

### 方法列表

| 方法 | 签名 | 说明 |
|------|------|------|
| `history()` | `history(period, interval, start, end, prepost, actions, auto_adjust, back_adjust, repair, keepna, rounding, timeout, raise_errors)` | 获取历史 OHLCV（参数完全同 `Ticker.history()`） |
| `get_dividends()` | `get_dividends(period='max', repair=False)` | 获取分红历史 |
| `get_splits()` | `get_splits(period='max', repair=False)` | 获取拆股历史 |
| `get_capital_gains()` | `get_capital_gains(period='max', repair=False)` | 获取资本利得（基金） |
| `get_actions()` | `get_actions(period='max')` | 获取公司行动（分红+拆股合并） |
| `get_history_metadata()` | `get_history_metadata()` | 获取历史数据元信息字典 |

---

# 三、附录

---

## 18. 常用代码速查

### 快速开始

```python
import yfinance as yf

# 推荐在启动时配置一次
yf.config.network.retries = 2           # 自动重试
yf.set_tz_cache_location("/tmp/yf")     # 统一缓存位置

# 单股基本用法
aapl = yf.Ticker("AAPL")
df = aapl.history(period="1y")
print(aapl.fast_info.last_price)
print(aapl.info["marketCap"])
```

---

### 全局配置最佳实践

```python
import yfinance as yf

# 程序入口处统一配置
yf.config.network.proxy = "http://proxy:8080"  # 代理（如需）
yf.config.network.retries = 3                   # 重试3次
yf.config.debug.hide_exceptions = False         # 不隐藏异常（生产环境可改回 True）
yf.config.debug.logging = False                 # 关闭调试日志（排错时改为 True）
yf.set_tz_cache_location("/data/yf_cache")

# 此后所有 Ticker/download 均自动使用上述配置
```

---

### 价格数据获取

```python
import yfinance as yf

t = yf.Ticker("AAPL")

# 日K，最近1年
df = t.history(period="1y")

# 指定日期区间
df = t.history(start="2023-01-01", end="2024-01-01")

# 1小时K线（最近60天内）
df = t.history(period="30d", interval="1h")

# 1分钟K线（最近7天内）
df = t.history(period="5d", interval="1m")

# 含盘前盘后
df = t.history(period="5d", interval="30m", prepost=True)

# 启用价格修复（非美股强烈建议）
df = yf.Ticker("8TRA.DE").history(period="2y", repair=True)
print(df[df["Repaired?"] == True])  # 查看被修复的行

# 不复权（原始价格）
df = t.history(period="1y", auto_adjust=False)
```

---

### 多级列索引处理

```python
import yfinance as yf
import pandas as pd

# 批量下载
df = yf.download(["AAPL", "MSFT", "GOOGL"], period="1y")

# 获取所有股票收盘价
closes = df["Close"]

# 获取单只股票
aapl_close = df["Close"]["AAPL"]
aapl_all = df.xs("AAPL", level=1, axis=1)

# 扁平化列名
df.columns = ["_".join(col) for col in df.columns]
# 列名变为: Close_AAPL, Close_MSFT, High_AAPL...

# 直接获取扁平列名
df = yf.download(["AAPL", "MSFT"], period="1y", multi_level_index=False)

# 保存/读取 CSV
df.to_csv("prices.csv")
df_loaded = pd.read_csv("prices.csv", header=[0, 1], index_col=0, parse_dates=True)
```

---

### 财务分析

```python
t = yf.Ticker("AAPL")

# 三张财务报表
income   = t.income_stmt           # 年报利润表
balance  = t.balance_sheet         # 年报资产负债表
cashflow = t.cashflow              # 年报现金流量表

# 季报
q_income   = t.quarterly_income_stmt
q_balance  = t.quarterly_balance_sheet
q_cashflow = t.quarterly_cashflow

# TTM（滚动12个月）
ttm_income   = t.ttm_income_stmt
ttm_cashflow = t.ttm_cashflow

# 财报日历和历史
cal          = t.calendar           # 下次财报日期
dates        = t.get_earnings_dates(limit=8)  # 历史财报日期+EPS
sec          = t.sec_filings        # SEC 文件列表

# 提取具体指标
revenue    = income.loc["Total Revenue"]
net_income = income.loc["Net Income"]
fcf        = cashflow.loc["Free Cash Flow"]
total_debt = balance.loc["Total Debt"]
```

---

### 分析师与市场情绪

```python
t = yf.Ticker("AAPL")

# 分析师评级
print(t.recommendations_summary)
print(t.analyst_price_targets)
print(t.upgrades_downgrades.head(10))

# 盈利预测
print(t.earnings_estimate)      # EPS 预测
print(t.revenue_estimate)       # 营收预测
print(t.eps_trend)              # EPS 预测趋势
print(t.eps_revisions)          # EPS 修正次数

# 持股结构
print(t.major_holders)
print(t.institutional_holders.head(10))
print(t.insider_transactions.head(10))

# ESG
print(t.sustainability)
```

---

### ETF 分析

```python
spy = yf.Ticker("SPY")
fd = spy.funds_data

print(fd.description)
print(fd.fund_overview)
print(fd.fund_operations)      # 费率、换手率
print(fd.top_holdings)         # 前十持仓
print(fd.sector_weightings)    # 行业权重
print(fd.asset_classes)        # 资产类别分配
print(fd.equity_holdings)      # 权益持仓估值指标
print(fd.quote_type())         # "ETF"
```

---

### 股票筛选器

```python
from yfinance import EquityQuery, screen

# 高股息低估值策略（美股）
q = EquityQuery("and", [
    EquityQuery("eq",  ["region", "us"]),
    EquityQuery("lt",  ["peratio.lasttwelvemonths", 15]),
    EquityQuery("gte", ["dividendyield.lasttwelvemonths", 0.03]),
    EquityQuery("gt",  ["marketcap", 1_000_000_000])
])

results = screen(q, sortField="dividendyield.lasttwelvemonths", sortAsc=False, size=20)
print(f"符合条件共 {results['total']} 只")
for s in results["quotes"]:
    print(s["symbol"], s.get("trailingPE"), s.get("dividendYield"))

# 翻页
page2 = screen(q, offset=20, size=20)
```

---

### 行业研究

```python
import yfinance as yf

# 板块概览
tech = yf.Sector("technology")
print(tech.top_companies)
print(tech.top_etfs)
print(tech.industries)    # 查看子行业列表

# 细分行业
semi = yf.Industry("semiconductors")
print(semi.top_companies)
print(semi.top_performing_companies)
```

---

### 实时数据

```python
import yfinance as yf
import asyncio

# 同步监听
ws = yf.WebSocket()
ws.subscribe(["AAPL", "MSFT", "TSLA"])

def on_tick(data):
    print(f"{data['id']}: {data['price']}")

ws.listen(on_tick)

# 异步监听（推荐用于生产环境）
async def on_tick_async(data):
    print(f"{data['id']}: {data['price']}")

async def main():
    ws = yf.AsyncWebSocket()
    await ws.subscribe(["AAPL", "MSFT"], callback=on_tick_async)
    await ws.listen()

asyncio.run(main())
```

---

### 搜索与查找

```python
import yfinance as yf

# 模糊搜索
res = yf.Search("Apple")
for q in res.quotes:
    print(q["symbol"], q["shortname"])

# 精确查找
lk = yf.Lookup("AAPL")
print(lk.get_stock())

# 搜索带新闻
res = yf.Search("Tesla", news_count=5)
for n in res.news:
    print(n["title"])
```

---

*文档生成日期：2026-05-22*  
*官方文档：https://ranaroussi.github.io/yfinance/*
