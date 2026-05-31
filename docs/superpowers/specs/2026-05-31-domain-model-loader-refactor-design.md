# 设计规格：Loader 返回领域对象 + BaseLoader 转换工具

**日期：** 2026-05-31  
**状态：** 待实施

---

## 背景与目标

当前所有批量 loader 方法直接返回 `pl.DataFrame`，将 Pydantic 验证与 Polars 转换耦合在 `BaseLoader._to_df()` 一步完成。这使得调用方无法直接访问强类型领域对象的属性，也无法在不依赖 Polars 的场景下使用数据。

**目标：**

- loader 方法返回 `list[DomainModel]`（强类型领域对象列表）
- 在 `BaseLoader` 上暴露一个公共静态方法 `to_dataframe()`，供需要 DataFrame 的调用方自行转换
- 不引入新模块、不新增 class，改动范围精确

**不变的范围：** 单记录方法（`get_quote()`、`get_profile()`、`get_sec_profile()`、`get_valuation()` 等）已经返回领域对象，不受影响。`list[str]` 返回类型（`get_peers()`、`get_sectors()`、`get_available_indicators()` 等）同样不受影响。

---

## 数据流变化

**变更前：**

```text
API 原始 JSON
  → BaseLoader._to_df(records, Model)
  → Pydantic 验证 + model_dump() + pl.DataFrame()
  → pl.DataFrame  ← loader 直接返回
```

**变更后：**

```text
API 原始 JSON
  → BaseLoader._to_models(records, Model)   ← 只做 Pydantic 验证
  → list[DomainModel]                       ← loader 返回
          ↓ 调用方按需
  BaseLoader.to_dataframe(records)
  → pl.DataFrame
```

---

## BaseLoader 变更

### 1. `_to_df()` 改名为 `_to_models()`

移除最后一行 DataFrame 转换，返回类型改为 `list[M]`。引入模块级 TypeVar 让 mypy 推断返回类型与入参 `model` 绑定。

```python
M = TypeVar("M", bound=BaseModel)

def _to_models(self, records: list[dict[str, Any]], model: type[M]) -> list[M]:
    if not records:
        return []
    clean = [{k: (None if v == "" else v) for k, v in r.items()} for r in records]
    return [model.model_validate(r) for r in clean]
```

空字符串清洗逻辑保留不变（FMP 对未填写日期字段返回空字符串）。

### 2. 新增公共静态方法 `to_dataframe()`

```python
@staticmethod
def to_dataframe(records: Sequence[BaseModel]) -> pl.DataFrame:
    if not records:
        return pl.DataFrame()
    return pl.DataFrame([r.model_dump() for r in records])
```

- `Sequence[BaseModel]` 接受 `list`、`tuple`（需在 `base.py` 顶部加 `from collections.abc import Sequence`）
- 空输入返回 `pl.DataFrame()`，与原行为一致

---

## Abstract Loader 签名变更全量表

| Loader 文件 | 方法 | 旧返回类型 | 新返回类型 |
| --- | --- | --- | --- |
| `loaders/market_loader.py` | `get_quotes` | `pl.DataFrame` | `list[Quote]` |
| `loaders/market_loader.py` | `get_price_history` | `pl.DataFrame` | `list[PriceBar]` |
| `loaders/market_loader.py` | `get_market_snapshot` | `pl.DataFrame` | `list[Quote]` |
| `loaders/financial_loader.py` | `get_income_statement` | `pl.DataFrame` | `list[IncomeStatement]` |
| `loaders/financial_loader.py` | `get_balance_sheet` | `pl.DataFrame` | `list[BalanceSheet]` |
| `loaders/financial_loader.py` | `get_cash_flow_statement` | `pl.DataFrame` | `list[CashFlow]` |
| `loaders/financial_loader.py` | `get_financial_ratios` | `pl.DataFrame` | `list[FinancialRatio]` |
| `loaders/financial_loader.py` | `get_key_metrics` | `pl.DataFrame` | `list[KeyMetrics]` |
| `loaders/company_loader.py` | `get_executives` | `pl.DataFrame` | `list[Executive]` |
| `loaders/company_loader.py` | `get_market_cap` | `pl.DataFrame` | `list[MarketCapRecord]` |
| `loaders/analyst_loader.py` | `get_ratings` | `pl.DataFrame` | `list[AnalystRating]` |
| `loaders/analyst_loader.py` | `get_price_targets` | `pl.DataFrame` | `list[PriceTarget]` |
| `loaders/analyst_loader.py` | `get_estimates` | `pl.DataFrame` | `list[Estimate]` |
| `loaders/calendar_loader.py` | `get_earnings_calendar` | `pl.DataFrame` | `list[EarningsEvent]` |
| `loaders/calendar_loader.py` | `get_dividend_calendar` | `pl.DataFrame` | `list[DividendEvent]` |
| `loaders/calendar_loader.py` | `get_ipo_calendar` | `pl.DataFrame` | `list[IPOEvent]` |
| `loaders/calendar_loader.py` | `get_splits_calendar` | `pl.DataFrame` | `list[SplitEvent]` |
| `loaders/news_loader.py` | `get_news` | `pl.DataFrame` | `list[NewsArticle]` |
| `loaders/insider_loader.py` | `get_insider_trades` | `pl.DataFrame` | `list[InsiderTrade]` |
| `loaders/insider_loader.py` | `get_insider_statistics` | `pl.DataFrame` | `list[InsiderStatistics]` |
| `loaders/congress_loader.py` | `get_congress_trades` | `pl.DataFrame` | `list[CongressTrade]` |
| `loaders/filings_loader.py` | `get_filings` | `pl.DataFrame` | `list[SecFiling]` |
| `loaders/indicators_loader.py` | `get_indicator` | `pl.DataFrame` | `list[IndicatorRow]` |
| `loaders/economics_loader.py` | `get_indicator` | `pl.DataFrame` | `list[IndicatorRow]` |
| `loaders/performance_loader.py` | `get_movers` | `pl.DataFrame` | `list[MarketMover]` |
| `loaders/performance_loader.py` | `get_sector_performance` | `pl.DataFrame` | `list[SectorPerformance]` |
| `loaders/performance_loader.py` | `get_sector_pe` | `pl.DataFrame` | `list[SectorPE]` |
| `loaders/directory_loader.py` | `get_symbols` | `pl.DataFrame` | `list[SymbolInfo]` |
| `loaders/directory_loader.py` | `get_exchanges` | `pl.DataFrame` | `list[ExchangeInfo]` |

**注意：** `economics_loader.get_indicator()` 与 `indicators_loader.get_indicator()` 共用 `IndicatorRow`（`date` + `value` + OHLCV 结构一致）。`models/indicators.py` 中的 `IndicatorRow` 已能覆盖经济指标时间序列。

---

## FMP 具体实现变更模式

所有 FMP loader 中的批量方法统一替换模式，以 `FMPInsiderTradeLoader` 为例：

```python
# 改前
async def get_insider_trades(self, ...) -> pl.DataFrame:
    records = await self._get_list(...)
    return self._to_df(records, InsiderTrade)

# 改后
async def get_insider_trades(self, ...) -> list[InsiderTrade]:
    records = await self._get_list(...)
    return self._to_models(records, InsiderTrade)
```

对含 `try/except FMPNotFoundError` 的方法，异常捕获时返回 `[]`（已与 `_to_models` 空列表行为一致）：

```python
async def get_insider_trades(self, ...) -> list[InsiderTrade]:
    try:
        records = await self._get_list(...)
    except FMPNotFoundError:
        return []
    return self._to_models(records, InsiderTrade)
```

---

## 调用方使用示例

```python
# 只需要领域对象
trades = await hub.insider.get_insider_trades("AAPL")
buyer_names = [t.reporting_name for t in trades if t.acquisition_or_disposition == "A"]

# 需要 DataFrame 做计算
df = BaseLoader.to_dataframe(trades)
df.filter(pl.col("acquisition_or_disposition") == "A").select("reporting_name", "price")

# 历史价格
bars = await hub.market.get_price_history("AAPL", start=date(2024, 1, 1))
df = BaseLoader.to_dataframe(bars)
df.with_columns((pl.col("close") / pl.col("close").shift(1) - 1).alias("return"))
```

---

## 测试策略

### 单元测试（现有文件原地修改）

- `tests/unit/providers/fmp/loaders/` 各文件：
  - 断言从 `assert isinstance(result, pl.DataFrame)` 改为 `assert isinstance(result, list)`
  - 加 `assert isinstance(result[0], XxxModel)`（非空结果验证类型）
  - FMP 空结果：断言 `result == []`

### 新增测试点

1. `BaseLoader.to_dataframe([])` → 返回 `pl.DataFrame()`
2. `BaseLoader.to_dataframe([InsiderTrade(...)])` → 列名与 `model_dump()` 键一致
3. `_to_models([], Model)` → 返回 `[]`，不抛异常
4. `_to_models` 仍正确清洗空字符串日期字段为 `None`

### 集成测试

- `tests/integration/test_fmp_integration.py`：
  - `.shape`、`.columns` 断言替换为对 list 元素属性的断言
  - 需要 DataFrame 的断言改为先 `BaseLoader.to_dataframe(result)` 再检查

---

## 文件变更范围汇总

| 类别 | 文件数 | 变更内容 |
| --- | --- | --- |
| `loaders/base.py` | 1 | `_to_df` 改名 + 新增 `to_dataframe` 静态方法 |
| `loaders/*.py`（abstract） | 13 | 批量方法返回类型签名 + import 更新（移除 `pl`，添加 model 导入） |
| `providers/fmp/loaders/*.py` | 13 | `_to_df` → `_to_models`，返回类型 |
| `tests/unit/` | 5 | 断言类型更新 |
| `tests/integration/` | 1 | 断言更新 |
