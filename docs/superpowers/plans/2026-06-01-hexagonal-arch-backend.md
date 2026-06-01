# DeepAlpha 六边形架构重构 Implementation Plan（Plan A: Backend）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `deepalpha` 包从扁平结构重组为六边形架构（domain / application / infrastructure / interface 四层），并新增 Claude API Agent 层，支持 4 种投研工具调用。

**Architecture:** 六边形架构（Ports-Adapters）— domain 层零外部依赖，通过 `typing.Protocol` 定义接口；infrastructure 实现这些接口；application 通过构造函数注入使用接口；interface 是唯一驱动适配器（FastAPI + 调度任务）。采用"先建新结构 → 迁移旧文件 → 清理"的安全策略，每步测试验证，不破坏现有功能。

**Tech Stack:** Python 3.11+, asyncpg, valkey, FastAPI, sse-starlette, anthropic SDK (Claude claude-sonnet-4-6), pydantic v2

---

## 文件映射总览

### 新建文件
```
src/deepalpha/domain/
  concept/  __init__.py · models.py · protocols.py
  market/   __init__.py · models.py · protocols.py · enums.py
  financial/__init__.py · models.py · protocols.py
  analyst/  __init__.py · models.py · protocols.py
  company/  __init__.py · models.py · protocols.py
  __init__.py

src/deepalpha/infrastructure/
  providers/
    base.py                          ← 平移自 loaders/base.py
    fmp/   (整目录平移)
    finnhub/(整目录平移)
    etfdb/ __init__.py · scraper.py  ← 平移自 pipeline/concept/etfdb_scraper.py
    __init__.py
  db/  __init__.py · concept_repo.py ← 平移+重命名 pipeline/concept/db.py
  cache/__init__.py · concept_cache.py ← 平移 pipeline/concept/cache.py
  __init__.py

src/deepalpha/application/
  services/
    __init__.py · concept_service.py · market_service.py
    financial_service.py · analyst_service.py
  agent/
    __init__.py · tools.py · runner.py · prompts.py
  __init__.py

src/deepalpha/interface/
  web/
    __init__.py · app.py · deps.py
    routers/ __init__.py · concept.py · market.py · agent.py
  pipeline/concept/
    __init__.py · build_concept_map.py · update_holdings.py
  __init__.py

tests/unit/domain/concept/
  __init__.py · test_models.py · test_protocols.py
tests/unit/application/
  __init__.py
  services/ __init__.py · test_concept_service.py · test_market_service.py
  agent/ __init__.py · test_tools.py
tests/unit/infrastructure/
  __init__.py
  cache/ __init__.py · test_concept_cache.py
  db/   __init__.py · test_concept_repo.py
```

### 删除文件（Task 12 最后清理）
```
src/deepalpha/models/          ← 内容已迁移至 domain/*/models.py
src/deepalpha/loaders/         ← hub.py 拆入 domain/*/protocols.py, base.py 迁移至 infrastructure/
src/deepalpha/providers/       ← 迁移至 infrastructure/providers/
src/deepalpha/pipeline/        ← 迁移至 infrastructure/ + interface/pipeline/
```

---

## Task 1: domain/concept — models + protocols

**Files:**
- Create: `src/deepalpha/domain/__init__.py`
- Create: `src/deepalpha/domain/concept/__init__.py`
- Create: `src/deepalpha/domain/concept/models.py`
- Create: `src/deepalpha/domain/concept/protocols.py`
- Create: `tests/unit/domain/__init__.py`
- Create: `tests/unit/domain/concept/__init__.py`
- Create: `tests/unit/domain/concept/test_models.py`
- Create: `tests/unit/domain/concept/test_protocols.py`

- [ ] **Step 1: 建立目录并写失败测试**

```bash
mkdir -p src/deepalpha/domain/concept
touch src/deepalpha/domain/__init__.py src/deepalpha/domain/concept/__init__.py
mkdir -p tests/unit/domain/concept
touch tests/unit/domain/__init__.py tests/unit/domain/concept/__init__.py
```

写 `tests/unit/domain/concept/test_models.py`：
```python
import datetime
import pytest
from deepalpha.domain.concept.models import ConceptEtfMap, ConceptStock, ConceptSummary


def test_concept_stock_instantiation():
    stock = ConceptStock(
        date=datetime.date(2026, 6, 1),
        concept="AI",
        symbol="NVDA",
        etf_count=5,
        total_weight=10.0,
        etfs=["BOTZ", "AIQ"],
    )
    assert stock.symbol == "NVDA"
    assert stock.etfs == ["BOTZ", "AIQ"]


def test_concept_etf_map_optional_fields():
    m = ConceptEtfMap(
        concept="AI",
        etf_symbol="BOTZ",
        updated_at=datetime.date(2026, 6, 1),
    )
    assert m.etf_name is None
    assert m.aum_million is None


def test_concept_summary_top_symbols():
    s = ConceptSummary(
        concept="AI",
        etf_count=4,
        stock_count=120,
        top_symbols=["NVDA", "MSFT"],
        last_updated=datetime.date(2026, 6, 1),
    )
    assert s.top_symbols == ["NVDA", "MSFT"]
```

- [ ] **Step 2: 运行测试，确认 FAIL（模块不存在）**

```bash
pytest tests/unit/domain/concept/test_models.py -v
```
期望输出：`ModuleNotFoundError: No module named 'deepalpha.domain'`

- [ ] **Step 3: 创建 domain/concept/models.py（内容与 models/concept.py 相同）**

写 `src/deepalpha/domain/concept/models.py`：
```python
"""概念股池领域模型（domain 层，零外部依赖）"""
import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConceptEtfMap(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    concept: str = Field(title="概念名称")
    etf_symbol: str = Field(title="ETF 代码")
    etf_name: str | None = Field(None, title="ETF 名称")
    aum_million: float | None = Field(None, title="AUM（百万美元）")
    etfdb_slug: str | None = Field(None, title="ETFdb 分类标识")
    updated_at: datetime.date = Field(title="更新日期")


class ConceptStock(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: datetime.date = Field(title="日期")
    concept: str = Field(title="概念名称")
    symbol: str = Field(title="股票代码")
    name: str | None = Field(None, title="公司名称")
    etf_count: int = Field(title="ETF 覆盖数")
    total_weight: float = Field(title="合计权重")
    etfs: list[str] = Field(title="持有 ETF 列表")


class ConceptSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    concept: str = Field(title="概念名称")
    etf_count: int = Field(title="ETF 数量")
    stock_count: int = Field(title="成分股数量")
    top_symbols: list[str] = Field(title="核心成分股")
    last_updated: datetime.date = Field(title="最后更新日")
```

- [ ] **Step 4: 运行测试，确认 PASS**

```bash
pytest tests/unit/domain/concept/test_models.py -v
```
期望：3 个测试全部 PASS

- [ ] **Step 5: 写 protocols 失败测试**

写 `tests/unit/domain/concept/test_protocols.py`：
```python
import pytest
from deepalpha.domain.concept.protocols import IConceptRepo, IConceptCache
from deepalpha.domain.concept.models import ConceptEtfMap, ConceptStock, ConceptSummary
import datetime


class _MockRepo:
    async def load_etf_map(self) -> list[ConceptEtfMap]: return []
    async def upsert_etf_map(self, records: list[ConceptEtfMap]) -> None: pass
    async def get_latest_stocks(self, concept: str) -> list[ConceptStock]: return []
    async def upsert_stocks(self, date: datetime.date, records: list[ConceptStock]) -> None: pass
    async def get_all_summaries(self) -> list[ConceptSummary]: return []


class _MockCache:
    async def get_concept(self, name: str) -> list[ConceptStock] | None: return None
    async def set_concept(self, name: str, stocks: list[ConceptStock]) -> None: pass
    async def get_list(self) -> list[ConceptSummary] | None: return None
    async def set_list(self, summaries: list[ConceptSummary]) -> None: pass


def test_mock_repo_satisfies_protocol():
    assert isinstance(_MockRepo(), IConceptRepo)


def test_mock_cache_satisfies_protocol():
    assert isinstance(_MockCache(), IConceptCache)
```

```bash
pytest tests/unit/domain/concept/test_protocols.py -v
```
期望：`ModuleNotFoundError: No module named 'deepalpha.domain.concept.protocols'`

- [ ] **Step 6: 创建 domain/concept/protocols.py**

写 `src/deepalpha/domain/concept/protocols.py`：
```python
"""concept 领域端口协议（由 infrastructure 层实现）"""
import datetime
from typing import Protocol, runtime_checkable

from .models import ConceptEtfMap, ConceptStock, ConceptSummary


@runtime_checkable
class IConceptRepo(Protocol):
    async def load_etf_map(self) -> list[ConceptEtfMap]: ...
    async def upsert_etf_map(self, records: list[ConceptEtfMap]) -> None: ...
    async def get_latest_stocks(self, concept: str) -> list[ConceptStock]: ...
    async def upsert_stocks(self, date: datetime.date, records: list[ConceptStock]) -> None: ...
    async def get_all_summaries(self) -> list[ConceptSummary]: ...


@runtime_checkable
class IConceptCache(Protocol):
    async def get_concept(self, name: str) -> list[ConceptStock] | None: ...
    async def set_concept(self, name: str, stocks: list[ConceptStock]) -> None: ...
    async def get_list(self) -> list[ConceptSummary] | None: ...
    async def set_list(self, summaries: list[ConceptSummary]) -> None: ...
```

- [ ] **Step 7: 运行 PASS + commit**

```bash
pytest tests/unit/domain/concept/ -v
```
期望：5 个测试全部 PASS

```bash
git add src/deepalpha/domain/ tests/unit/domain/
git commit -m "feat: add domain/concept models and protocols"
```

---

## Task 2: domain/{market, financial, analyst, company} — models + protocols + enums

**Files:**
- Create: `src/deepalpha/domain/market/__init__.py`
- Create: `src/deepalpha/domain/market/enums.py`
- Create: `src/deepalpha/domain/market/models.py`
- Create: `src/deepalpha/domain/market/protocols.py`
- Create: `src/deepalpha/domain/financial/__init__.py`
- Create: `src/deepalpha/domain/financial/models.py`
- Create: `src/deepalpha/domain/financial/protocols.py`
- Create: `src/deepalpha/domain/analyst/__init__.py`
- Create: `src/deepalpha/domain/analyst/models.py`
- Create: `src/deepalpha/domain/analyst/protocols.py`
- Create: `src/deepalpha/domain/company/__init__.py`
- Create: `src/deepalpha/domain/company/models.py`
- Create: `src/deepalpha/domain/company/protocols.py`

- [ ] **Step 1: 建目录**

```bash
mkdir -p src/deepalpha/domain/market src/deepalpha/domain/financial \
         src/deepalpha/domain/analyst src/deepalpha/domain/company
touch src/deepalpha/domain/market/__init__.py \
      src/deepalpha/domain/financial/__init__.py \
      src/deepalpha/domain/analyst/__init__.py \
      src/deepalpha/domain/company/__init__.py
```

- [ ] **Step 2: 创建 domain/market/enums.py（从 loaders/enums.py 复制内容）**

写 `src/deepalpha/domain/market/enums.py`（完整内容，与 `loaders/enums.py` 相同）：
```python
"""市场领域枚举（domain 层，零外部依赖）"""
from enum import Enum


class AssetClass(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    MUTUAL_FUND = "mutual_fund"


class Interval(str, Enum):
    ONE_MIN     = "1m"
    FIVE_MIN    = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN  = "30m"
    ONE_HOUR    = "1h"
    FOUR_HOUR   = "4h"
    ONE_DAY     = "1d"
    ONE_WEEK    = "1w"
    ONE_MONTH   = "1M"


class StatementPeriod(str, Enum):
    ANNUAL    = "annual"
    QUARTERLY = "quarter"
    TTM       = "ttm"
```

- [ ] **Step 3: 创建 domain/market/models.py（复制 models/market.py 内容）**

写 `src/deepalpha/domain/market/models.py`，内容与 `src/deepalpha/models/market.py` 完全相同（只更新模块 docstring）：

```bash
cp src/deepalpha/models/market.py src/deepalpha/domain/market/models.py
```

然后将文件顶部 docstring 改为 `"""市场领域模型（domain 层）"""`，其余内容不变。

- [ ] **Step 4: 创建 domain/market/protocols.py**

写 `src/deepalpha/domain/market/protocols.py`：
```python
"""market 领域端口协议"""
import datetime
from typing import Protocol, runtime_checkable

from .enums import AssetClass, Interval
from .models import PriceBar, Quote


@runtime_checkable
class IMarketProvider(Protocol):
    async def get_quote(self, symbol: str) -> Quote: ...
    async def get_quotes(self, symbols: list[str]) -> list[Quote]: ...
    async def get_price_history(
        self,
        symbol: str,
        start: datetime.date,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY,
        adjusted: bool = True,
    ) -> list[PriceBar]: ...
    async def get_market_snapshot(
        self, asset_class: AssetClass = AssetClass.STOCK
    ) -> list[Quote]: ...
```

- [ ] **Step 5: 创建 domain/financial/models.py + protocols.py**

```bash
cp src/deepalpha/models/financial.py src/deepalpha/domain/financial/models.py
```

写 `src/deepalpha/domain/financial/protocols.py`：
```python
"""financial 领域端口协议"""
from typing import Protocol, runtime_checkable

from deepalpha.domain.market.enums import StatementPeriod
from .models import BalanceSheet, CashFlow, IncomeStatement


@runtime_checkable
class IFinancialProvider(Protocol):
    async def get_income_statement(
        self, symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[IncomeStatement]: ...
    async def get_balance_sheet(
        self, symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[BalanceSheet]: ...
    async def get_cash_flow(
        self, symbol: str,
        period: StatementPeriod = StatementPeriod.ANNUAL,
        limit: int = 5,
    ) -> list[CashFlow]: ...
```

- [ ] **Step 6: 创建 domain/analyst/models.py + protocols.py**

```bash
cp src/deepalpha/models/analyst.py src/deepalpha/domain/analyst/models.py
```

写 `src/deepalpha/domain/analyst/protocols.py`：
```python
"""analyst 领域端口协议"""
from typing import Protocol, runtime_checkable

from .models import AnalystRating, PriceTarget


@runtime_checkable
class IAnalystProvider(Protocol):
    async def get_ratings(self, symbol: str) -> list[AnalystRating]: ...
    async def get_price_target(self, symbol: str) -> PriceTarget | None: ...
```

- [ ] **Step 7: 创建 domain/company/models.py + protocols.py**

```bash
cp src/deepalpha/models/company.py src/deepalpha/domain/company/models.py
```

写 `src/deepalpha/domain/company/protocols.py`（根据 company models 中的 CompanyProfile 类定义）：
```python
"""company 领域端口协议"""
from typing import Protocol, runtime_checkable

from .models import CompanyProfile


@runtime_checkable
class ICompanyProvider(Protocol):
    async def get_profile(self, symbol: str) -> CompanyProfile: ...
    async def get_peers(self, symbol: str) -> list[str]: ...
```

- [ ] **Step 8: 快速验证新增导入正常**

```bash
python -c "
from deepalpha.domain.market.models import Quote, PriceBar
from deepalpha.domain.market.protocols import IMarketProvider
from deepalpha.domain.market.enums import Interval, AssetClass, StatementPeriod
from deepalpha.domain.financial.models import IncomeStatement
from deepalpha.domain.financial.protocols import IFinancialProvider
from deepalpha.domain.analyst.models import AnalystRating
from deepalpha.domain.analyst.protocols import IAnalystProvider
from deepalpha.domain.company.protocols import ICompanyProvider
print('All domain imports OK')
"
```
期望输出：`All domain imports OK`

- [ ] **Step 9: 运行现有测试，确认无回归**

```bash
pytest tests/unit/ -v --ignore=tests/unit/domain -q
```
期望：全部 PASS（现有测试仍从旧路径导入，旧路径未改动）

- [ ] **Step 10: commit**

```bash
git add src/deepalpha/domain/
git commit -m "feat: add domain models and protocols for market, financial, analyst, company"
```

---

## Task 3: infrastructure/providers — 平移 FMP + Finnhub + BaseLoader

**Files:**
- Create: `src/deepalpha/infrastructure/__init__.py`
- Create: `src/deepalpha/infrastructure/providers/__init__.py`
- Create: `src/deepalpha/infrastructure/providers/base.py`
- Move all: `src/deepalpha/providers/fmp/` → `src/deepalpha/infrastructure/providers/fmp/`
- Move all: `src/deepalpha/providers/finnhub/` → `src/deepalpha/infrastructure/providers/finnhub/`
- Modify: all FMP/Finnhub files — update imports

- [ ] **Step 1: 建立 infrastructure 目录结构**

```bash
mkdir -p src/deepalpha/infrastructure/providers
touch src/deepalpha/infrastructure/__init__.py \
      src/deepalpha/infrastructure/providers/__init__.py
```

- [ ] **Step 2: 复制 BaseLoader 到 infrastructure/providers/base.py**

```bash
cp src/deepalpha/loaders/base.py src/deepalpha/infrastructure/providers/base.py
```

- [ ] **Step 3: 复制 providers 目录到 infrastructure**

```bash
cp -r src/deepalpha/providers/fmp src/deepalpha/infrastructure/providers/fmp
cp -r src/deepalpha/providers/finnhub src/deepalpha/infrastructure/providers/finnhub
```

- [ ] **Step 4: 更新 infrastructure/providers/fmp/loaders/ 中所有文件的导入**

每个 FMP loader 文件顶部有类似这些导入，需要全部替换：

将 `from deepalpha.loaders.base import BaseLoader` → `from deepalpha.infrastructure.providers.base import BaseLoader`

将 `from deepalpha.loaders.market_loader import AbstractMarketLoader` 等 → 删除（FMP loaders 不再显式继承，改为鸭子类型满足 Protocol）

将 `from deepalpha.models.market import ...` → `from deepalpha.domain.market.models import ...`

将 `from deepalpha.models.financial import ...` → `from deepalpha.domain.financial.models import ...`

将 `from deepalpha.models.analyst import ...` → `from deepalpha.domain.analyst.models import ...`

将 `from deepalpha.models.company import ...` → `from deepalpha.domain.company.models import ...`

将 `from deepalpha.loaders.enums import Interval, StatementPeriod, AssetClass` → `from deepalpha.domain.market.enums import Interval, StatementPeriod, AssetClass`

对 `infrastructure/providers/fmp/` 下所有 `.py` 文件执行此替换（使用 sed 批量替换）：

```bash
# 更新 FMP loaders 的导入
find src/deepalpha/infrastructure/providers/fmp -name "*.py" -exec sed -i '' \
  -e 's|from deepalpha\.loaders\.base import BaseLoader|from deepalpha.infrastructure.providers.base import BaseLoader|g' \
  -e 's|from deepalpha\.loaders\.[a-z_]*_loader import Abstract[A-Za-z]*Loader||g' \
  -e 's|from deepalpha\.models\.market import|from deepalpha.domain.market.models import|g' \
  -e 's|from deepalpha\.models\.financial import|from deepalpha.domain.financial.models import|g' \
  -e 's|from deepalpha\.models\.analyst import|from deepalpha.domain.analyst.models import|g' \
  -e 's|from deepalpha\.models\.company import|from deepalpha.domain.company.models import|g' \
  -e 's|from deepalpha\.models\.calendar import|from deepalpha.domain.calendar.models import|g' \
  -e 's|from deepalpha\.models\.news import|from deepalpha.domain.news.models import|g' \
  -e 's|from deepalpha\.models\.congress import|from deepalpha.domain.congress.models import|g' \
  -e 's|from deepalpha\.models\.indicators import|from deepalpha.domain.indicators.models import|g' \
  -e 's|from deepalpha\.models\.insider import|from deepalpha.domain.insider.models import|g' \
  -e 's|from deepalpha\.models\.performance import|from deepalpha.domain.performance.models import|g' \
  -e 's|from deepalpha\.models\.directory import|from deepalpha.domain.directory.models import|g' \
  -e 's|from deepalpha\.models\.filings import|from deepalpha.domain.filings.models import|g' \
  -e 's|from deepalpha\.loaders\.enums import|from deepalpha.domain.market.enums import|g' \
  {} \;

# 更新 FMP loaders 中的继承关系（去除 AbstractXxxLoader 基类，改用 BaseLoader 直接继承）
# 检查每个 loader 文件的类定义行，将 class FMPXxxLoader(AbstractXxxLoader): 改为 class FMPXxxLoader(BaseLoader):
find src/deepalpha/infrastructure/providers/fmp/loaders -name "*.py" -exec grep -l "Abstract" {} \;
```

对于继承关系，手动检查并更新每个文件：将 `class FMPXxxLoader(AbstractXxxLoader):` 改为 `class FMPXxxLoader(BaseLoader):`（BaseLoader 已从 infrastructure/providers/base.py 导入）

- [ ] **Step 5: 更新 infrastructure/providers/finnhub/ 导入**

```bash
find src/deepalpha/infrastructure/providers/finnhub -name "*.py" -exec sed -i '' \
  -e 's|from deepalpha\.models\.|from deepalpha.domain.|g' \
  {} \;
```

- [ ] **Step 6: 更新现有测试文件中的 providers 导入路径**

现有测试在 `tests/unit/providers/`，需要更新导入：

```bash
find tests/unit/providers -name "*.py" -exec sed -i '' \
  -e 's|from deepalpha\.providers\.|from deepalpha.infrastructure.providers.|g' \
  -e 's|from deepalpha\.loaders\.base import|from deepalpha.infrastructure.providers.base import|g' \
  -e 's|from deepalpha\.models\.|from deepalpha.domain.|g' \
  -e 's|from deepalpha\.loaders\.enums import|from deepalpha.domain.market.enums import|g' \
  {} \;
```

- [ ] **Step 7: 验证新路径导入正常**

```bash
python -c "
from deepalpha.infrastructure.providers.fmp.client import FMPClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.market_loader import FMPMarketLoader
from deepalpha.infrastructure.providers.finnhub.client import FinnhubClient
print('infrastructure/providers imports OK')
"
```

- [ ] **Step 8: 运行 providers 相关测试**

```bash
pytest tests/unit/providers/ -v -q
```
期望：全部 PASS

- [ ] **Step 9: commit**

```bash
git add src/deepalpha/infrastructure/
git add tests/unit/providers/
git commit -m "feat: migrate providers to infrastructure/providers, update imports"
```

---

## Task 4: infrastructure/providers/etfdb — 平移 etfdb_scraper + finnhub etf_loader

**Files:**
- Create: `src/deepalpha/infrastructure/providers/etfdb/__init__.py`
- Create: `src/deepalpha/infrastructure/providers/etfdb/scraper.py`
- Modify: `src/deepalpha/infrastructure/providers/finnhub/` — 添加 `etf_loader.py`

- [ ] **Step 1: 建立 etfdb 目录并复制 scraper**

```bash
mkdir -p src/deepalpha/infrastructure/providers/etfdb
touch src/deepalpha/infrastructure/providers/etfdb/__init__.py
cp src/deepalpha/pipeline/concept/etfdb_scraper.py \
   src/deepalpha/infrastructure/providers/etfdb/scraper.py
```

- [ ] **Step 2: 更新 scraper.py 导入（如有 deepalpha.models 导入）**

```bash
sed -i '' \
  -e 's|from deepalpha\.models\.|from deepalpha.domain.|g' \
  -e 's|from deepalpha\.pipeline\.concept\.|from deepalpha.infrastructure.providers.etfdb.|g' \
  src/deepalpha/infrastructure/providers/etfdb/scraper.py
```

- [ ] **Step 3: 复制 finnhub_loader.py 到 infrastructure/providers/finnhub/etf_loader.py**

```bash
cp src/deepalpha/pipeline/concept/finnhub_loader.py \
   src/deepalpha/infrastructure/providers/finnhub/etf_loader.py
```

- [ ] **Step 4: 更新 etf_loader.py 导入**

将 `etf_loader.py` 中对 `deepalpha.models.concept` 的引用改为 `deepalpha.domain.concept.models`，对 `deepalpha.providers.finnhub` 改为 `deepalpha.infrastructure.providers.finnhub`：

```bash
sed -i '' \
  -e 's|from deepalpha\.models\.concept import|from deepalpha.domain.concept.models import|g' \
  -e 's|from deepalpha\.providers\.finnhub|from deepalpha.infrastructure.providers.finnhub|g' \
  -e 's|from deepalpha\.pipeline\.concept\.config import|from deepalpha.infrastructure.providers.finnhub.config import|g' \
  src/deepalpha/infrastructure/providers/finnhub/etf_loader.py
```

- [ ] **Step 5: 更新 etfdb + finnhub_loader 相关测试的导入**

```bash
sed -i '' \
  -e 's|from deepalpha\.pipeline\.concept\.etfdb_scraper|from deepalpha.infrastructure.providers.etfdb.scraper|g' \
  -e 's|from deepalpha\.pipeline\.concept\.finnhub_loader|from deepalpha.infrastructure.providers.finnhub.etf_loader|g' \
  tests/unit/pipeline/concept/test_etfdb_scraper.py \
  tests/unit/pipeline/concept/test_finnhub_loader.py
```

- [ ] **Step 6: 运行这两个测试文件确认 PASS**

```bash
pytest tests/unit/pipeline/concept/test_etfdb_scraper.py \
       tests/unit/pipeline/concept/test_finnhub_loader.py -v
```

- [ ] **Step 7: commit**

```bash
git add src/deepalpha/infrastructure/providers/etfdb/ \
        src/deepalpha/infrastructure/providers/finnhub/etf_loader.py \
        tests/unit/pipeline/concept/test_etfdb_scraper.py \
        tests/unit/pipeline/concept/test_finnhub_loader.py
git commit -m "feat: migrate etfdb scraper and finnhub etf_loader to infrastructure"
```

---

## Task 5: infrastructure/db/concept_repo — 平移并重命名 ConceptDb

**Files:**
- Create: `src/deepalpha/infrastructure/db/__init__.py`
- Create: `src/deepalpha/infrastructure/db/concept_repo.py`
- Create: `tests/unit/infrastructure/__init__.py`
- Create: `tests/unit/infrastructure/db/__init__.py`
- Create: `tests/unit/infrastructure/db/test_concept_repo.py`
- Modify: `tests/unit/pipeline/concept/test_db.py` — 更新导入

- [ ] **Step 1: 建目录**

```bash
mkdir -p src/deepalpha/infrastructure/db tests/unit/infrastructure/db
touch src/deepalpha/infrastructure/db/__init__.py \
      tests/unit/infrastructure/__init__.py \
      tests/unit/infrastructure/db/__init__.py
```

- [ ] **Step 2: 写失败测试（验证新路径）**

写 `tests/unit/infrastructure/db/test_concept_repo.py`：
```python
import pytest
from deepalpha.infrastructure.db.concept_repo import ConceptRepo
from deepalpha.domain.concept.protocols import IConceptRepo


def test_concept_repo_satisfies_protocol():
    # ConceptRepo 实例化需要 dsn，用虚假值测试 Protocol 满足
    repo = ConceptRepo.__new__(ConceptRepo)
    assert isinstance(repo, IConceptRepo)
```

```bash
pytest tests/unit/infrastructure/db/test_concept_repo.py -v
```
期望：`ModuleNotFoundError`

- [ ] **Step 3: 创建 infrastructure/db/concept_repo.py**

写 `src/deepalpha/infrastructure/db/concept_repo.py`（内容基于现有 `pipeline/concept/db.py`，更新导入并重命名类）：

```python
"""概念股池 PostgreSQL 数据层（实现 IConceptRepo protocol）"""
import datetime
from collections import defaultdict
from typing import Any

import asyncpg

from deepalpha.domain.concept.models import ConceptEtfMap, ConceptStock, ConceptSummary

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS concept_etf_map (
    concept        VARCHAR(100) NOT NULL,
    etf_symbol     VARCHAR(20)  NOT NULL,
    etf_name       VARCHAR(200),
    aum_million    FLOAT,
    etfdb_slug     VARCHAR(100),
    updated_at     DATE         NOT NULL,
    PRIMARY KEY (concept, etf_symbol)
);

CREATE TABLE IF NOT EXISTS concept_stocks (
    date           DATE         NOT NULL,
    concept        VARCHAR(100) NOT NULL,
    symbol         VARCHAR(20)  NOT NULL,
    name           VARCHAR(200),
    etf_count      INT          NOT NULL,
    total_weight   FLOAT        NOT NULL,
    etfs           TEXT,
    PRIMARY KEY (date, concept, symbol)
);
"""


class ConceptRepo:
    """asyncpg DB 适配器，实现 IConceptRepo protocol。"""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None  # type: ignore[type-arg]

    async def __aenter__(self) -> "ConceptRepo":
        self._pool = await asyncpg.create_pool(self._dsn)
        async with self._pool.acquire() as conn:
            await conn.execute(_CREATE_TABLES_SQL)
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._pool:
            await self._pool.close()

    async def upsert_etf_map(self, records: list[ConceptEtfMap]) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO concept_etf_map
                  (concept, etf_symbol, etf_name, aum_million, etfdb_slug, updated_at)
                VALUES ($1,$2,$3,$4,$5,$6)
                ON CONFLICT (concept, etf_symbol) DO UPDATE
                  SET etf_name=EXCLUDED.etf_name, aum_million=EXCLUDED.aum_million,
                      etfdb_slug=EXCLUDED.etfdb_slug, updated_at=EXCLUDED.updated_at
                """,
                [(r.concept, r.etf_symbol, r.etf_name, r.aum_million,
                  r.etfdb_slug, r.updated_at) for r in records],
            )

    async def load_etf_map(self) -> list[ConceptEtfMap]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT concept,etf_symbol,etf_name,aum_million,etfdb_slug,updated_at"
                " FROM concept_etf_map"
            )
        return [ConceptEtfMap(
            concept=r["concept"], etf_symbol=r["etf_symbol"], etf_name=r["etf_name"],
            aum_million=r["aum_million"], etfdb_slug=r["etfdb_slug"], updated_at=r["updated_at"],
        ) for r in rows]

    async def upsert_stocks(self, date: datetime.date, records: list[ConceptStock]) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO concept_stocks
                  (date,concept,symbol,name,etf_count,total_weight,etfs)
                VALUES ($1,$2,$3,$4,$5,$6,$7)
                ON CONFLICT (date,concept,symbol) DO UPDATE
                  SET name=EXCLUDED.name, etf_count=EXCLUDED.etf_count,
                      total_weight=EXCLUDED.total_weight, etfs=EXCLUDED.etfs
                """,
                [(r.date, r.concept, r.symbol, r.name, r.etf_count,
                  r.total_weight, ",".join(r.etfs)) for r in records],
            )

    async def get_latest_stocks(self, concept: str) -> list[ConceptStock]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT date,concept,symbol,name,etf_count,total_weight,etfs
                FROM concept_stocks
                WHERE concept=$1
                  AND date=(SELECT MAX(date) FROM concept_stocks WHERE concept=$1)
                ORDER BY etf_count DESC, total_weight DESC
                """,
                concept,
            )
        return [_row_to_stock(r) for r in rows]

    async def get_all_summaries(self) -> list[ConceptSummary]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            etf_rows = await conn.fetch(
                "SELECT concept, COUNT(*) as cnt FROM concept_etf_map GROUP BY concept"
            )
            etf_counts = {r["concept"]: r["cnt"] for r in etf_rows}
            stock_rows = await conn.fetch(
                """
                WITH latest AS (
                    SELECT concept, MAX(date) as max_date
                    FROM concept_stocks GROUP BY concept
                )
                SELECT cs.concept, cs.date, cs.symbol, cs.etf_count
                FROM concept_stocks cs
                JOIN latest l ON cs.concept=l.concept AND cs.date=l.max_date
                ORDER BY cs.concept, cs.etf_count DESC, cs.total_weight DESC
                """
            )
        concept_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"date": None, "symbols": []}
        )
        for r in stock_rows:
            concept_data[r["concept"]]["date"] = r["date"]
            concept_data[r["concept"]]["symbols"].append(r["symbol"])
        return [
            ConceptSummary(
                concept=concept,
                etf_count=etf_counts.get(concept, 0),
                stock_count=len(data["symbols"]),
                top_symbols=data["symbols"][:5],
                last_updated=data["date"],
            )
            for concept, data in concept_data.items()
        ]

    async def get_stocks_history(
        self, concept: str, start: datetime.date, end: datetime.date
    ) -> list[ConceptStock]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT date,concept,symbol,name,etf_count,total_weight,etfs
                FROM concept_stocks
                WHERE concept=$1 AND date>=$2 AND date<=$3
                ORDER BY date DESC, etf_count DESC
                """,
                concept, start, end,
            )
        return [_row_to_stock(r) for r in rows]


def _row_to_stock(row: Any) -> ConceptStock:
    return ConceptStock(
        date=row["date"], concept=row["concept"], symbol=row["symbol"],
        name=row["name"], etf_count=row["etf_count"], total_weight=row["total_weight"],
        etfs=row["etfs"].split(",") if row["etfs"] else [],
    )
```

- [ ] **Step 4: 运行新测试 PASS**

```bash
pytest tests/unit/infrastructure/db/test_concept_repo.py -v
```
期望：PASS

- [ ] **Step 5: 更新 tests/unit/pipeline/concept/test_db.py 的导入**

```bash
sed -i '' \
  -e 's|from deepalpha\.pipeline\.concept\.db import ConceptDb|from deepalpha.infrastructure.db.concept_repo import ConceptRepo as ConceptDb|g' \
  -e 's|from deepalpha\.models\.concept import|from deepalpha.domain.concept.models import|g' \
  tests/unit/pipeline/concept/test_db.py
```

```bash
pytest tests/unit/pipeline/concept/test_db.py -v
```
期望：全部 PASS

- [ ] **Step 6: commit**

```bash
git add src/deepalpha/infrastructure/db/ \
        tests/unit/infrastructure/ \
        tests/unit/pipeline/concept/test_db.py
git commit -m "feat: add infrastructure/db/concept_repo (renamed from ConceptDb)"
```

---

## Task 6: infrastructure/cache/concept_cache — 平移 ConceptCache

**Files:**
- Create: `src/deepalpha/infrastructure/cache/__init__.py`
- Create: `src/deepalpha/infrastructure/cache/concept_cache.py`
- Create: `tests/unit/infrastructure/cache/__init__.py`
- Create: `tests/unit/infrastructure/cache/test_concept_cache.py`
- Modify: `tests/unit/pipeline/concept/test_cache.py` — 更新导入

- [ ] **Step 1: 建目录并写失败测试**

```bash
mkdir -p src/deepalpha/infrastructure/cache tests/unit/infrastructure/cache
touch src/deepalpha/infrastructure/cache/__init__.py \
      tests/unit/infrastructure/cache/__init__.py
```

写 `tests/unit/infrastructure/cache/test_concept_cache.py`：
```python
from deepalpha.infrastructure.cache.concept_cache import ConceptCache
from deepalpha.domain.concept.protocols import IConceptCache


def test_concept_cache_satisfies_protocol():
    cache = ConceptCache.__new__(ConceptCache)
    assert isinstance(cache, IConceptCache)
```

```bash
pytest tests/unit/infrastructure/cache/test_concept_cache.py -v
```
期望：`ModuleNotFoundError`

- [ ] **Step 2: 创建 infrastructure/cache/concept_cache.py**

写 `src/deepalpha/infrastructure/cache/concept_cache.py`：
```python
"""概念股池 Valkey 缓存适配器（实现 IConceptCache protocol）"""
import json

import valkey.asyncio as valkey_asyncio

from deepalpha.domain.concept.models import ConceptStock, ConceptSummary


class ConceptCache:
    """Valkey 缓存适配器，实现 IConceptCache protocol。"""

    def __init__(
        self, host: str, port: int, password: str, ssl: bool, ttl: int = 172800
    ) -> None:
        self._client = valkey_asyncio.Valkey(
            host=host, port=port, password=password, ssl=ssl, decode_responses=True
        )
        self._ttl = ttl

    async def get_concept(self, name: str) -> list[ConceptStock] | None:
        data = await self._client.get(f"concept:{name}")
        if data is None:
            return None
        return [ConceptStock.model_validate(item) for item in json.loads(data)]

    async def set_concept(self, name: str, stocks: list[ConceptStock]) -> None:
        payload = json.dumps([s.model_dump(mode="json") for s in stocks])
        await self._client.set(f"concept:{name}", payload, ex=self._ttl)

    async def get_list(self) -> list[ConceptSummary] | None:
        data = await self._client.get("concept:__list__")
        if data is None:
            return None
        return [ConceptSummary.model_validate(item) for item in json.loads(data)]

    async def set_list(self, summaries: list[ConceptSummary]) -> None:
        payload = json.dumps([s.model_dump(mode="json") for s in summaries])
        await self._client.set("concept:__list__", payload, ex=self._ttl)

    async def close(self) -> None:
        await self._client.aclose()
```

- [ ] **Step 3: 运行新测试 PASS**

```bash
pytest tests/unit/infrastructure/cache/test_concept_cache.py -v
```

- [ ] **Step 4: 更新旧测试的导入路径**

```bash
sed -i '' \
  -e 's|from deepalpha\.pipeline\.concept\.cache import ConceptCache|from deepalpha.infrastructure.cache.concept_cache import ConceptCache|g' \
  -e 's|from deepalpha\.models\.concept import|from deepalpha.domain.concept.models import|g' \
  -e 's|deepalpha\.pipeline\.concept\.cache\.valkey_asyncio|deepalpha.infrastructure.cache.concept_cache.valkey_asyncio|g' \
  tests/unit/pipeline/concept/test_cache.py
```

```bash
pytest tests/unit/pipeline/concept/test_cache.py -v
```
期望：全部 PASS（5 个测试）

- [ ] **Step 5: commit**

```bash
git add src/deepalpha/infrastructure/cache/ \
        tests/unit/infrastructure/cache/ \
        tests/unit/pipeline/concept/test_cache.py
git commit -m "feat: add infrastructure/cache/concept_cache"
```

---

## Task 7: application/services/concept_service

**Files:**
- Create: `src/deepalpha/application/__init__.py`
- Create: `src/deepalpha/application/services/__init__.py`
- Create: `src/deepalpha/application/services/concept_service.py`
- Create: `tests/unit/application/__init__.py`
- Create: `tests/unit/application/services/__init__.py`
- Create: `tests/unit/application/services/test_concept_service.py`

- [ ] **Step 1: 建目录 + 写失败测试**

```bash
mkdir -p src/deepalpha/application/services tests/unit/application/services
touch src/deepalpha/application/__init__.py \
      src/deepalpha/application/services/__init__.py \
      tests/unit/application/__init__.py \
      tests/unit/application/services/__init__.py
```

写 `tests/unit/application/services/test_concept_service.py`：
```python
import datetime
import pytest
from unittest.mock import AsyncMock

from deepalpha.application.services.concept_service import ConceptService
from deepalpha.domain.concept.models import ConceptStock, ConceptSummary


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.get_latest_stocks = AsyncMock(return_value=[
        ConceptStock(
            date=datetime.date(2026, 6, 1), concept="AI", symbol="NVDA",
            etf_count=5, total_weight=10.0, etfs=["BOTZ"],
        )
    ])
    repo.get_all_summaries = AsyncMock(return_value=[
        ConceptSummary(
            concept="AI", etf_count=4, stock_count=10,
            top_symbols=["NVDA"], last_updated=datetime.date(2026, 6, 1),
        )
    ])
    return repo


@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get_concept = AsyncMock(return_value=None)
    cache.set_concept = AsyncMock()
    cache.get_list = AsyncMock(return_value=None)
    cache.set_list = AsyncMock()
    return cache


@pytest.mark.asyncio
async def test_get_concept_cache_miss_queries_repo_and_fills_cache(mock_repo, mock_cache):
    svc = ConceptService(mock_repo, mock_cache)
    result = await svc.get_concept("AI")
    mock_repo.get_latest_stocks.assert_called_once_with("AI")
    mock_cache.set_concept.assert_called_once()
    assert len(result) == 1
    assert result[0].symbol == "NVDA"


@pytest.mark.asyncio
async def test_get_concept_cache_hit_skips_repo(mock_repo, mock_cache):
    cached = [ConceptStock(
        date=datetime.date(2026, 6, 1), concept="AI", symbol="MSFT",
        etf_count=3, total_weight=8.0, etfs=["AIQ"],
    )]
    mock_cache.get_concept = AsyncMock(return_value=cached)
    svc = ConceptService(mock_repo, mock_cache)
    result = await svc.get_concept("AI")
    mock_repo.get_latest_stocks.assert_not_called()
    assert result[0].symbol == "MSFT"


@pytest.mark.asyncio
async def test_list_summaries_cache_miss_queries_repo(mock_repo, mock_cache):
    svc = ConceptService(mock_repo, mock_cache)
    result = await svc.list_summaries()
    mock_repo.get_all_summaries.assert_called_once()
    mock_cache.set_list.assert_called_once()
    assert len(result) == 1
```

```bash
pytest tests/unit/application/services/test_concept_service.py -v
```
期望：`ModuleNotFoundError`

- [ ] **Step 2: 实现 ConceptService**

写 `src/deepalpha/application/services/concept_service.py`：
```python
"""概念股池业务逻辑服务"""
import datetime

from deepalpha.domain.concept.models import ConceptStock, ConceptSummary
from deepalpha.domain.concept.protocols import IConceptCache, IConceptRepo


class ConceptService:
    def __init__(self, repo: IConceptRepo, cache: IConceptCache) -> None:
        self._repo = repo
        self._cache = cache

    async def get_concept(self, name: str) -> list[ConceptStock]:
        hit = await self._cache.get_concept(name)
        if hit is not None:
            return hit
        rows = await self._repo.get_latest_stocks(name)
        if rows:
            await self._cache.set_concept(name, rows)
        return rows

    async def list_summaries(self) -> list[ConceptSummary]:
        hit = await self._cache.get_list()
        if hit is not None:
            return hit
        summaries = await self._repo.get_all_summaries()
        if summaries:
            await self._cache.set_list(summaries)
        return summaries

    async def get_concept_history(
        self, name: str, start: datetime.date, end: datetime.date
    ) -> list[ConceptStock]:
        return await self._repo.get_stocks_history(name, start, end)
```

- [ ] **Step 3: 运行测试 PASS**

```bash
pytest tests/unit/application/services/test_concept_service.py -v
```
期望：3 个测试全部 PASS

- [ ] **Step 4: commit**

```bash
git add src/deepalpha/application/ tests/unit/application/
git commit -m "feat: add application/services/concept_service with cache-aside"
```

---

## Task 8: application/services/{market, financial, analyst}_service

**Files:**
- Create: `src/deepalpha/application/services/market_service.py`
- Create: `src/deepalpha/application/services/financial_service.py`
- Create: `src/deepalpha/application/services/analyst_service.py`
- Create: `tests/unit/application/services/test_market_service.py`

- [ ] **Step 1: 写 market_service 失败测试**

写 `tests/unit/application/services/test_market_service.py`：
```python
import datetime
import pytest
from unittest.mock import AsyncMock

from deepalpha.application.services.market_service import MarketService
from deepalpha.domain.market.models import Quote


@pytest.fixture
def mock_provider():
    p = AsyncMock()
    p.get_quote = AsyncMock(return_value=Quote(
        symbol="AAPL", price=190.5, change=1.2,
    ))
    return p


@pytest.mark.asyncio
async def test_get_quote_delegates_to_provider(mock_provider):
    svc = MarketService(mock_provider)
    q = await svc.get_quote("AAPL")
    mock_provider.get_quote.assert_called_once_with("AAPL")
    assert q.symbol == "AAPL"
    assert q.price == 190.5
```

```bash
pytest tests/unit/application/services/test_market_service.py -v
```
期望：`ModuleNotFoundError`

- [ ] **Step 2: 实现三个 service**

写 `src/deepalpha/application/services/market_service.py`：
```python
"""市场行情业务逻辑服务"""
import datetime

from deepalpha.domain.market.enums import Interval
from deepalpha.domain.market.models import PriceBar, Quote
from deepalpha.domain.market.protocols import IMarketProvider


class MarketService:
    def __init__(self, provider: IMarketProvider) -> None:
        self._provider = provider

    async def get_quote(self, symbol: str) -> Quote:
        return await self._provider.get_quote(symbol)

    async def get_price_history(
        self, symbol: str,
        start: datetime.date,
        end: datetime.date | None = None,
        interval: Interval = Interval.ONE_DAY,
    ) -> list[PriceBar]:
        return await self._provider.get_price_history(symbol, start, end, interval)
```

写 `src/deepalpha/application/services/financial_service.py`：
```python
"""财务数据业务逻辑服务"""
from deepalpha.domain.financial.models import IncomeStatement
from deepalpha.domain.financial.protocols import IFinancialProvider
from deepalpha.domain.market.enums import StatementPeriod


class FinancialService:
    def __init__(self, provider: IFinancialProvider) -> None:
        self._provider = provider

    async def get_latest_income(self, symbol: str) -> IncomeStatement | None:
        stmts = await self._provider.get_income_statement(
            symbol, period=StatementPeriod.ANNUAL, limit=1
        )
        return stmts[0] if stmts else None
```

写 `src/deepalpha/application/services/analyst_service.py`：
```python
"""分析师数据业务逻辑服务"""
from deepalpha.domain.analyst.models import AnalystRating, PriceTarget
from deepalpha.domain.analyst.protocols import IAnalystProvider


class AnalystService:
    def __init__(self, provider: IAnalystProvider) -> None:
        self._provider = provider

    async def get_ratings(self, symbol: str) -> list[AnalystRating]:
        return await self._provider.get_ratings(symbol)

    async def get_price_target(self, symbol: str) -> PriceTarget | None:
        return await self._provider.get_price_target(symbol)
```

- [ ] **Step 3: 运行测试 PASS**

```bash
pytest tests/unit/application/services/ -v
```
期望：4 个测试全部 PASS

- [ ] **Step 4: commit**

```bash
git add src/deepalpha/application/services/
git commit -m "feat: add market, financial, analyst services"
```

---

## Task 9: application/agent — tools + runner + prompts + 新增 anthropic 依赖

**Files:**
- Modify: `pyproject.toml`
- Create: `src/deepalpha/application/agent/__init__.py`
- Create: `src/deepalpha/application/agent/prompts.py`
- Create: `src/deepalpha/application/agent/tools.py`
- Create: `src/deepalpha/application/agent/runner.py`
- Create: `tests/unit/application/agent/__init__.py`
- Create: `tests/unit/application/agent/test_tools.py`

- [ ] **Step 1: 添加 anthropic 依赖**

在 `pyproject.toml` 的 `dependencies` 列表中添加：
```toml
"anthropic>=0.40.0",
"sse-starlette>=2.0",
```

```bash
uv sync
```

- [ ] **Step 2: 建目录 + 写工具调度失败测试**

```bash
mkdir -p src/deepalpha/application/agent tests/unit/application/agent
touch src/deepalpha/application/agent/__init__.py \
      tests/unit/application/agent/__init__.py
```

写 `tests/unit/application/agent/test_tools.py`：
```python
import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock

from deepalpha.application.agent.tools import dispatch_tool, TOOLS
from deepalpha.domain.concept.models import ConceptStock
from deepalpha.domain.market.models import Quote


class FakeServices:
    def __init__(self):
        self.concept = AsyncMock()
        self.market = AsyncMock()
        self.financial = AsyncMock()
        self.analyst = AsyncMock()


@pytest.mark.asyncio
async def test_search_concept_returns_formatted_list():
    svc = FakeServices()
    svc.concept.get_concept = AsyncMock(return_value=[
        ConceptStock(
            date=datetime.date(2026, 6, 1), concept="AI", symbol="NVDA",
            etf_count=5, total_weight=10.0, etfs=["BOTZ"],
        )
    ])
    result = await dispatch_tool("search_concept", {"concept": "AI"}, svc)
    assert "NVDA" in result
    assert "5" in result


@pytest.mark.asyncio
async def test_search_concept_empty_returns_message():
    svc = FakeServices()
    svc.concept.get_concept = AsyncMock(return_value=[])
    result = await dispatch_tool("search_concept", {"concept": "Unknown"}, svc)
    assert "不存在" in result


@pytest.mark.asyncio
async def test_get_quote_returns_price_info():
    svc = FakeServices()
    svc.market.get_quote = AsyncMock(return_value=Quote(
        symbol="AAPL", price=190.5, change=1.2, changes_percentage=0.63,
    ))
    result = await dispatch_tool("get_quote", {"symbol": "AAPL"}, svc)
    assert "190.5" in result
    assert "AAPL" in result


def test_tools_list_has_four_entries():
    assert len(TOOLS) == 4
    names = {t["name"] for t in TOOLS}
    assert names == {"search_concept", "get_quote", "get_financials", "generate_report"}
```

```bash
pytest tests/unit/application/agent/test_tools.py -v
```
期望：`ModuleNotFoundError`

- [ ] **Step 3: 创建 prompts.py**

写 `src/deepalpha/application/agent/prompts.py`：
```python
"""Agent 系统提示词"""

SYSTEM_PROMPT = """你是 DeepAlpha 投研助手，专注于美股市场分析。

你可以调用以下工具获取实时数据：
- search_concept：查询概念股池成分股（如 AI、清洁能源、生物科技等50+概念）
- get_quote：获取个股实时报价和市值
- get_financials：获取公司最新财务报表（营收、净利润、EPS）
- generate_report：生成综合投研报告（整合行情、财务、分析师评级）

回答时请：
1. 优先调用工具获取最新数据，不要凭记忆回答行情类问题
2. 数据以中文呈现，数字保留合理精度
3. 回答简洁、有洞察力，避免泛泛而谈
"""
```

- [ ] **Step 4: 创建 tools.py**

写 `src/deepalpha/application/agent/tools.py`：
```python
"""Agent 工具定义与调度"""
from typing import TYPE_CHECKING, Any

from anthropic.types import ToolParam

if TYPE_CHECKING:
    from deepalpha.application.services.concept_service import ConceptService
    from deepalpha.application.services.market_service import MarketService
    from deepalpha.application.services.financial_service import FinancialService
    from deepalpha.application.services.analyst_service import AnalystService

TOOLS: list[ToolParam] = [
    {
        "name": "search_concept",
        "description": "查询美股概念股池，返回该概念下成分股列表（含ETF覆盖数和权重）",
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "概念名称，如 'AI / Machine Learning'"}
            },
            "required": ["concept"],
        },
    },
    {
        "name": "get_quote",
        "description": "获取美股股票实时报价、涨跌幅、市值",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "股票代码，如 'AAPL'"}
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_financials",
        "description": "获取公司最新年度财务报表（营收、净利润、EPS）",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "股票代码"}
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "generate_report",
        "description": "生成指定股票的结构化投研报告，综合行情、财务、分析师评级",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "股票代码"}
            },
            "required": ["symbol"],
        },
    },
]


class Services:
    def __init__(
        self,
        concept: "ConceptService",
        market: "MarketService",
        financial: "FinancialService",
        analyst: "AnalystService",
    ) -> None:
        self.concept = concept
        self.market = market
        self.financial = financial
        self.analyst = analyst


async def dispatch_tool(name: str, inputs: dict[str, Any], services: Services) -> str:
    if name == "search_concept":
        stocks = await services.concept.get_concept(inputs["concept"])
        if not stocks:
            return f"概念 '{inputs['concept']}' 不存在或暂无数据"
        lines = [
            f"{s.symbol}: ETF覆盖={s.etf_count}, 权重={s.total_weight:.1f}%"
            for s in stocks[:20]
        ]
        return f"概念 '{inputs['concept']}' 共 {len(stocks)} 只成分股（显示前20）：\n" + "\n".join(lines)

    if name == "get_quote":
        q = await services.market.get_quote(inputs["symbol"])
        pct = f"{q.changes_percentage:.2f}%" if q.changes_percentage is not None else "N/A"
        cap = f"{q.market_cap/1e9:.1f}B" if q.market_cap else "N/A"
        return f"{q.symbol}: 价格={q.price}, 涨跌幅={pct}, 市值={cap}"

    if name == "get_financials":
        stmt = await services.financial.get_latest_income(inputs["symbol"])
        if stmt is None:
            return f"{inputs['symbol']} 暂无财务数据"
        rev = f"{stmt.revenue/1e9:.1f}B" if stmt.revenue else "N/A"
        ni = f"{stmt.net_income/1e9:.1f}B" if stmt.net_income else "N/A"
        return (
            f"{inputs['symbol']} ({stmt.date} {stmt.period}): "
            f"营收={rev}, 净利润={ni}, EPS={stmt.eps}"
        )

    if name == "generate_report":
        symbol = inputs["symbol"]
        q = await services.market.get_quote(symbol)
        stmt = await services.financial.get_latest_income(symbol)
        ratings = await services.analyst.get_ratings(symbol)
        rating_str = ratings[0].rating_recommendation if ratings else "N/A"
        pct = f"{q.changes_percentage:.2f}%" if q.changes_percentage is not None else "N/A"
        rev = f"{stmt.revenue/1e9:.1f}B" if stmt and stmt.revenue else "N/A"
        ni = f"{stmt.net_income/1e9:.1f}B" if stmt and stmt.net_income else "N/A"
        return (
            f"# {symbol} 投研报告\n\n"
            f"**行情**: 现价={q.price}, 涨跌幅={pct}\n"
            f"**财务**: 营收={rev}, 净利润={ni}\n"
            f"**分析师评级**: {rating_str}"
        )

    return f"未知工具: {name}"
```

- [ ] **Step 5: 创建 runner.py**

写 `src/deepalpha/application/agent/runner.py`：
```python
"""Claude API Agent 主循环"""
from collections.abc import AsyncIterator
from typing import Any

import anthropic

from deepalpha.application.agent.prompts import SYSTEM_PROMPT
from deepalpha.application.agent.tools import TOOLS, Services, dispatch_tool


class AgentRunner:
    def __init__(self, services: Services) -> None:
        self._services = services
        self._client = anthropic.AsyncAnthropic()

    async def run(self, messages: list[dict[str, Any]]) -> AsyncIterator[str]:
        while True:
            async with self._client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=8096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                final = await stream.get_final_message()

            if final.stop_reason == "end_turn":
                break

            tool_results: list[dict[str, Any]] = []
            for block in final.content:
                if block.type == "tool_use":
                    result = await dispatch_tool(block.name, block.input, self._services)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages = messages + [
                {"role": "assistant", "content": final.content},
                {"role": "user", "content": tool_results},
            ]
```

- [ ] **Step 6: 运行工具测试 PASS**

```bash
pytest tests/unit/application/agent/test_tools.py -v
```
期望：4 个测试全部 PASS

- [ ] **Step 7: commit**

```bash
git add src/deepalpha/application/agent/ \
        tests/unit/application/agent/ \
        pyproject.toml uv.lock
git commit -m "feat: add agent tools, runner, prompts + anthropic and sse-starlette deps"
```

---

## Task 10: interface/web — FastAPI app + deps + routers（含 SSE Agent 端点）

**Files:**
- Create: `src/deepalpha/interface/__init__.py`
- Create: `src/deepalpha/interface/web/__init__.py`
- Create: `src/deepalpha/interface/web/app.py`
- Create: `src/deepalpha/interface/web/deps.py`
- Create: `src/deepalpha/interface/web/routers/__init__.py`
- Create: `src/deepalpha/interface/web/routers/concept.py`
- Create: `src/deepalpha/interface/web/routers/market.py`
- Create: `src/deepalpha/interface/web/routers/agent.py`
- Modify: `tests/unit/pipeline/concept/test_router.py` — 更新导入

- [ ] **Step 1: 建目录**

```bash
mkdir -p src/deepalpha/interface/web/routers
touch src/deepalpha/interface/__init__.py \
      src/deepalpha/interface/web/__init__.py \
      src/deepalpha/interface/web/routers/__init__.py
```

- [ ] **Step 2: 创建 deps.py（依赖注入组装）**

写 `src/deepalpha/interface/web/deps.py`：
```python
"""FastAPI 依赖注入：组装 infrastructure → services → agent"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

import asyncpg
from fastapi import FastAPI

from deepalpha.infrastructure.cache.concept_cache import ConceptCache
from deepalpha.infrastructure.db.concept_repo import ConceptRepo
from deepalpha.infrastructure.providers.fmp.client import FMPClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.market_loader import FMPMarketLoader
from deepalpha.infrastructure.providers.fmp.loaders.financial_loader import FMPFinancialLoader
from deepalpha.infrastructure.providers.fmp.loaders.analyst_loader import FMPAnalystLoader
from deepalpha.pipeline.concept.config import ConceptPipelineConfig
from deepalpha.application.services.concept_service import ConceptService
from deepalpha.application.services.market_service import MarketService
from deepalpha.application.services.financial_service import FinancialService
from deepalpha.application.services.analyst_service import AnalystService
from deepalpha.application.agent.runner import AgentRunner
from deepalpha.application.agent.tools import Services


@lru_cache(maxsize=1)
def get_config() -> ConceptPipelineConfig:
    return ConceptPipelineConfig()


# 应用级单例（在 lifespan 中初始化）
_pool: asyncpg.Pool | None = None  # type: ignore[type-arg]
_services: Services | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _pool, _services
    cfg = get_config()

    _pool = await asyncpg.create_pool(cfg.asyncpg_dsn())
    repo = ConceptRepo.__new__(ConceptRepo)
    repo._dsn = cfg.asyncpg_dsn()
    repo._pool = _pool

    cache = ConceptCache(
        host=cfg.valkey_host, port=cfg.valkey_port,
        password=cfg.valkey_password, ssl=cfg.valkey_ssl,
    )

    fmp_cfg = FMPConfig()
    fmp_client = FMPClient(fmp_cfg)

    _services = Services(
        concept=ConceptService(repo, cache),
        market=MarketService(FMPMarketLoader(fmp_client)),
        financial=FinancialService(FMPFinancialLoader(fmp_client)),
        analyst=AnalystService(FMPAnalystLoader(fmp_client)),
    )

    yield

    await cache.close()
    await _pool.close()


def get_services() -> Services:
    assert _services is not None, "Services not initialized — call inside lifespan"
    return _services


def get_runner() -> AgentRunner:
    return AgentRunner(get_services())
```

- [ ] **Step 3: 创建 routers/concept.py（从旧 router.py 迁移，改用 ConceptService）**

写 `src/deepalpha/interface/web/routers/concept.py`：
```python
"""概念股池 API 路由（使用 ConceptService）"""
import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from deepalpha.application.services.concept_service import ConceptService
from deepalpha.domain.concept.models import ConceptStock, ConceptSummary
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/concept", tags=["concept"])


def _get_concept_service(
    services: Annotated[object, Depends(get_services)],
) -> ConceptService:
    return services.concept  # type: ignore[attr-defined]


@router.get("/list", response_model=list[ConceptSummary])
async def list_concepts(
    svc: Annotated[ConceptService, Depends(_get_concept_service)],
) -> list[ConceptSummary]:
    return await svc.list_summaries()


@router.get("/{name}", response_model=list[ConceptStock])
async def get_concept(
    name: str,
    svc: Annotated[ConceptService, Depends(_get_concept_service)],
    min_etf_count: int = Query(1, ge=1),
) -> list[ConceptStock]:
    stocks = await svc.get_concept(name)
    if not stocks:
        raise HTTPException(status_code=404, detail=f"概念 '{name}' 不存在")
    return [s for s in stocks if s.etf_count >= min_etf_count]


@router.get("/{name}/history", response_model=list[ConceptStock])
async def get_concept_history(
    name: str,
    svc: Annotated[ConceptService, Depends(_get_concept_service)],
    start: datetime.date = Query(...),
    end: datetime.date = Query(...),
) -> list[ConceptStock]:
    return await svc.get_concept_history(name, start, end)
```

- [ ] **Step 4: 创建 routers/market.py**

写 `src/deepalpha/interface/web/routers/market.py`：
```python
"""行情数据 API 路由"""
from typing import Annotated

from fastapi import APIRouter, Depends

from deepalpha.application.services.market_service import MarketService
from deepalpha.domain.market.models import Quote
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/market", tags=["market"])


def _get_market_service(
    services: Annotated[object, Depends(get_services)],
) -> MarketService:
    return services.market  # type: ignore[attr-defined]


@router.get("/quote/{symbol}", response_model=Quote)
async def get_quote(
    symbol: str,
    svc: Annotated[MarketService, Depends(_get_market_service)],
) -> Quote:
    return await svc.get_quote(symbol)
```

- [ ] **Step 5: 创建 routers/agent.py（SSE Agent 端点）**

写 `src/deepalpha/interface/web/routers/agent.py`：
```python
"""AI Agent SSE 流式端点"""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from deepalpha.application.agent.runner import AgentRunner
from deepalpha.interface.web.deps import get_runner

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    messages: list[dict]


@router.post("/stream")
async def agent_stream(
    req: ChatRequest,
    runner: Annotated[AgentRunner, Depends(get_runner)],
) -> EventSourceResponse:
    async def event_generator():
        async for text in runner.run(req.messages):
            yield {"data": text}

    return EventSourceResponse(event_generator())
```

- [ ] **Step 6: 创建 app.py（FastAPI 应用入口）**

写 `src/deepalpha/interface/web/app.py`：
```python
"""FastAPI 应用入口"""
from fastapi import FastAPI

from deepalpha.interface.web.deps import lifespan
from deepalpha.interface.web.routers import agent, concept, market

app = FastAPI(title="DeepAlpha API", lifespan=lifespan)

app.include_router(concept.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")
```

- [ ] **Step 7: 更新旧 router 测试的导入**

```bash
sed -i '' \
  -e 's|from deepalpha\.pipeline\.concept\.api\.router|from deepalpha.interface.web.routers.concept|g' \
  -e 's|from deepalpha\.models\.concept import|from deepalpha.domain.concept.models import|g' \
  tests/unit/pipeline/concept/test_router.py
```

```bash
pytest tests/unit/pipeline/concept/test_router.py -v
```
期望：全部 PASS

- [ ] **Step 8: 验证 app 可导入（不启动服务）**

```bash
python -c "from deepalpha.interface.web.app import app; print('App OK, routes:', [r.path for r in app.routes])"
```
期望输出包含 `/api/v1/concept/list`、`/api/v1/market/quote/{symbol}`、`/api/v1/agent/stream`

- [ ] **Step 9: commit**

```bash
git add src/deepalpha/interface/ tests/unit/pipeline/concept/test_router.py
git commit -m "feat: add interface/web with FastAPI app, concept/market/agent routers"
```

---

## Task 11: interface/pipeline — 调度任务瘦身

**Files:**
- Create: `src/deepalpha/interface/pipeline/__init__.py`
- Create: `src/deepalpha/interface/pipeline/concept/__init__.py`
- Create: `src/deepalpha/interface/pipeline/concept/build_concept_map.py`
- Create: `src/deepalpha/interface/pipeline/concept/update_holdings.py`

- [ ] **Step 1: 建目录**

```bash
mkdir -p src/deepalpha/interface/pipeline/concept
touch src/deepalpha/interface/pipeline/__init__.py \
      src/deepalpha/interface/pipeline/concept/__init__.py
```

- [ ] **Step 2: 创建 build_concept_map.py**

写 `src/deepalpha/interface/pipeline/concept/build_concept_map.py`：
```python
"""月度任务入口：构建概念 → ETF 映射（每月 1 日 02:00 SGT）"""
import asyncio
import datetime

import asyncpg

from deepalpha.infrastructure.cache.concept_cache import ConceptCache
from deepalpha.infrastructure.db.concept_repo import ConceptRepo
from deepalpha.infrastructure.providers.etfdb.scraper import ETFdbScraper
from deepalpha.infrastructure.providers.finnhub.etf_loader import FinnhubEtfLoader
from deepalpha.pipeline.concept.config import ConceptPipelineConfig


async def main() -> None:
    cfg = ConceptPipelineConfig()
    pool = await asyncpg.create_pool(cfg.asyncpg_dsn())
    try:
        repo = ConceptRepo.__new__(ConceptRepo)
        repo._dsn = cfg.asyncpg_dsn()
        repo._pool = pool

        scraper = ETFdbScraper()
        loader = FinnhubEtfLoader(cfg)

        candidates = await scraper.fetch_all_concepts()
        etf_maps = await loader.filter_by_aum(candidates, min_aum_million=100)
        await repo.upsert_etf_map(etf_maps)

        print(
            f"[{datetime.date.today()}] build_concept_map: "
            f"{len(etf_maps)} ETF maps upserted across "
            f"{len({m.concept for m in etf_maps})} concepts"
        )
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: 创建 update_holdings.py**

写 `src/deepalpha/interface/pipeline/concept/update_holdings.py`：
```python
"""日度任务入口：更新概念成分股持仓（每交易日 04:30 SGT）"""
import asyncio
import datetime

import asyncpg

from deepalpha.infrastructure.cache.concept_cache import ConceptCache
from deepalpha.infrastructure.db.concept_repo import ConceptRepo
from deepalpha.infrastructure.providers.finnhub.etf_loader import FinnhubEtfLoader
from deepalpha.pipeline.concept.config import ConceptPipelineConfig


async def main() -> None:
    cfg = ConceptPipelineConfig()
    pool = await asyncpg.create_pool(cfg.asyncpg_dsn())
    cache = ConceptCache(
        host=cfg.valkey_host, port=cfg.valkey_port,
        password=cfg.valkey_password, ssl=cfg.valkey_ssl,
    )
    try:
        repo = ConceptRepo.__new__(ConceptRepo)
        repo._dsn = cfg.asyncpg_dsn()
        repo._pool = pool

        loader = FinnhubEtfLoader(cfg)
        etf_map = await repo.load_etf_map()
        today = datetime.date.today()

        stocks = await loader.build_concept_stocks(etf_map, date=today)
        await repo.upsert_stocks(today, stocks)

        summaries = await repo.get_all_summaries()
        await cache.set_list(summaries)
        for s in summaries:
            concept_stocks = [st for st in stocks if st.concept == s.concept]
            await cache.set_concept(s.concept, concept_stocks)

        print(
            f"[{today}] update_holdings: "
            f"{len(stocks)} stock records across "
            f"{len(summaries)} concepts"
        )
    finally:
        await cache.close()
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: 验证可导入**

```bash
python -c "
from deepalpha.interface.pipeline.concept.build_concept_map import main
from deepalpha.interface.pipeline.concept.update_holdings import main as main2
print('Pipeline tasks importable OK')
"
```

- [ ] **Step 5: commit**

```bash
git add src/deepalpha/interface/pipeline/
git commit -m "feat: add interface/pipeline concept tasks using infrastructure adapters"
```

---

## Task 12: 清理旧文件 + 最终验证

**Files:**
- Delete: `src/deepalpha/models/`（内容已全部迁移到 `domain/*/models.py`）
- Delete: `src/deepalpha/loaders/`（hub.py 已拆分为 domain protocols，base.py 已迁移）
- Delete: `src/deepalpha/providers/`（已迁移至 `infrastructure/providers/`）
- Delete: `src/deepalpha/pipeline/`（已迁移至 `infrastructure/` + `interface/pipeline/`）
- Modify: `src/deepalpha/__init__.py`（更新公开导出）
- Modify: `tests/unit/models/` — 更新所有旧路径导入

- [ ] **Step 1: 更新 tests/unit/models/ 中的旧路径导入**

```bash
find tests/unit/models -name "*.py" -exec sed -i '' \
  -e 's|from deepalpha\.models\.|from deepalpha.domain.|g' \
  -e 's|from deepalpha\.loaders\.base import|from deepalpha.infrastructure.providers.base import|g' \
  -e 's|from deepalpha\.loaders\.enums import|from deepalpha.domain.market.enums import|g' \
  {} \;
find tests/unit -name "*.py" -exec sed -i '' \
  -e 's|import deepalpha\.models\.|import deepalpha.domain.|g' \
  {} \;
```

- [ ] **Step 2: 运行全量测试（删除旧文件前的最后检查）**

```bash
pytest tests/unit/ -v -q 2>&1 | tail -20
```
期望：全部 PASS，无旧路径导入错误

- [ ] **Step 3: 确认所有测试无旧路径导入**

```bash
grep -r "from deepalpha\.models\." tests/ || echo "OK: no old model imports"
grep -r "from deepalpha\.loaders\." tests/ || echo "OK: no old loader imports"
grep -r "from deepalpha\.providers\." tests/ || echo "OK: no old provider imports"
grep -r "from deepalpha\.pipeline\." tests/ || echo "OK: no old pipeline imports"
```
全部输出 `OK:...` 才可以继续。若有残留，手动修改对应测试文件。

- [ ] **Step 4: 确认 src 中无旧路径交叉引用**

```bash
grep -r "from deepalpha\.models\." src/deepalpha/domain/ src/deepalpha/application/ \
     src/deepalpha/infrastructure/ src/deepalpha/interface/ || echo "OK"
grep -r "from deepalpha\.loaders\." src/deepalpha/domain/ src/deepalpha/application/ \
     src/deepalpha/infrastructure/ src/deepalpha/interface/ || echo "OK"
```

- [ ] **Step 5: 删除旧目录**

```bash
rm -rf src/deepalpha/models/
rm -rf src/deepalpha/loaders/
rm -rf src/deepalpha/providers/
rm -rf src/deepalpha/pipeline/
```

- [ ] **Step 6: 运行全量测试（删除后确认无回归）**

```bash
pytest tests/unit/ -v -q 2>&1 | tail -20
```
期望：全部 PASS

- [ ] **Step 7: 运行全量测试包含集成测试（如有 API Key）**

```bash
pytest tests/ -v --ignore=tests/integration -q 2>&1 | tail -20
```

- [ ] **Step 8: 更新 src/deepalpha/__init__.py**

写 `src/deepalpha/__init__.py`：
```python
"""DeepAlpha — 六边形架构分层数据平台"""
```

- [ ] **Step 9: 最终 commit**

```bash
git add -A
git commit -m "refactor: complete hexagonal architecture migration, remove legacy layers"
```

---

## 自审核查清单

经过对规范文档 `docs/superpowers/specs/2026-06-01-hexagonal-arch-and-frontend-design.md` 的逐节核查：

| 规范要求 | 计划任务 | 状态 |
|---|---|---|
| domain/concept models + protocols | Task 1 | ✅ |
| domain/market/financial/analyst/company | Task 2 | ✅ |
| infrastructure/providers (fmp + finnhub) | Task 3 | ✅ |
| infrastructure/providers/etfdb + etf_loader | Task 4 | ✅ |
| infrastructure/db/concept_repo | Task 5 | ✅ |
| infrastructure/cache/concept_cache | Task 6 | ✅ |
| application/services/concept_service | Task 7 | ✅ |
| application/services/market + financial + analyst | Task 8 | ✅ |
| application/agent tools + runner + prompts | Task 9 | ✅ |
| interface/web FastAPI + routers (concept/market/agent SSE) | Task 10 | ✅ |
| interface/pipeline 调度任务 | Task 11 | ✅ |
| 旧文件清理 + 全量测试 | Task 12 | ✅ |
| anthropic + sse-starlette 依赖 | Task 9 Step 1 | ✅ |

**注意**：
- `calendar`, `news`, `congress`, `indicators`, `insider`, `performance`, `directory`, `filings` 等 FMP 扩展领域（models/protocols）未在本计划中单独建 domain 子包，因为 Agent 工具不依赖它们。这些模型在 Task 3 中随 FMP 整目录迁移时会自动处理（cp 命令），只需在 Task 12 的导入清理步骤中确保无遗漏引用。
- `ConceptRepo.get_stocks_history()` 在 Task 5 中已实现，`ConceptService.get_concept_history()` 在 Task 7 中调用它，类型一致。

---

**Plan B（前端）**将作为独立计划，在本计划完成后编写，覆盖 `frontend/` Next.js + shadcn/ui + Vercel AI SDK 脚手架和组件开发。
