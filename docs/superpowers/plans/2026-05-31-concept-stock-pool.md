# Concept Stock Pool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `deepalpha` 包内构建自动化美股概念股池系统，通过 ETFdb 分类 + Finnhub ETF 持仓，每日生成并缓存概念→成分股映射，通过 FastAPI 对外提供查询接口。

**Architecture:** 新增 `providers/finnhub/`（HTTP 客户端）、`pipeline/concept/`（抓取/DB/缓存/任务/API）模块，与现有 `providers/fmp/` 分层风格保持一致；数据持久化至 Neon PostgreSQL，热数据缓存至 Upstash Valkey，TTL 2 天。

**Tech Stack:** asyncpg（PostgreSQL 异步驱动）、valkey（Valkey/Redis 异步客户端）、httpx + lxml（ETFdb HTML 抓取）、pydantic-settings（配置）、FastAPI（查询接口）、pytest-httpx（HTTP mock 测试）。

---

## 文件结构

```
新建：
  src/deepalpha/models/concept.py
  src/deepalpha/providers/finnhub/__init__.py
  src/deepalpha/providers/finnhub/config.py
  src/deepalpha/providers/finnhub/client.py
  src/deepalpha/pipeline/__init__.py
  src/deepalpha/pipeline/concept/__init__.py
  src/deepalpha/pipeline/concept/config.py
  src/deepalpha/pipeline/concept/etfdb_scraper.py
  src/deepalpha/pipeline/concept/finnhub_loader.py
  src/deepalpha/pipeline/concept/db.py
  src/deepalpha/pipeline/concept/cache.py
  src/deepalpha/pipeline/concept/tasks/__init__.py
  src/deepalpha/pipeline/concept/tasks/build_concept_map.py
  src/deepalpha/pipeline/concept/tasks/update_holdings.py
  src/deepalpha/pipeline/concept/api/__init__.py
  src/deepalpha/pipeline/concept/api/router.py
  tests/unit/pipeline/__init__.py
  tests/unit/pipeline/concept/__init__.py
  tests/unit/pipeline/concept/test_models.py
  tests/unit/pipeline/concept/test_etfdb_scraper.py
  tests/unit/pipeline/concept/test_finnhub_loader.py
  tests/unit/pipeline/concept/test_db.py
  tests/unit/pipeline/concept/test_cache.py
  tests/unit/pipeline/concept/test_router.py
  tests/unit/providers/finnhub/__init__.py
  tests/unit/providers/finnhub/test_client.py

修改：
  pyproject.toml        — 新增 asyncpg、valkey 依赖
  .env                  — 新增 PostgreSQL/Valkey/Finnhub 环境变量
```

---

## Task 1: 依赖与环境变量

**Files:**
- Modify: `pyproject.toml`
- Modify: `.env`

- [ ] **Step 1: 在 `pyproject.toml` 的 `dependencies` 中新增两行**

```toml
# 在现有依赖列表末尾加入：
    "asyncpg>=0.29.0",
    "valkey>=6.0.0",
```

完整 dependencies 块结尾应为：
```toml
    "requests-ratelimiter",
    "asyncpg>=0.29.0",
    "valkey>=6.0.0",
```

- [ ] **Step 2: 在 `.env` 末尾追加以下环境变量**

```env
# PostgreSQL (Neon, SSL required)
POSTGRES_HOST=ep-cold-silence-apl6e8tx.c-7.us-east-1.aws.neon.tech
POSTGRES_PORT=5432
POSTGRES_DB=neondb
POSTGRES_USER=neondb_owner
POSTGRES_PASSWORD=npg_xhAfdp2IEKG3
POSTGRES_SSL=true

# Valkey (Upstash, SSL required)
VALKEY_HOST=grand-doberman-114359.upstash.io
VALKEY_PORT=6379
VALKEY_PASSWORD=gQAAAAAAAb63AAIgcDExY2VjN2FjNDZhYTQ0ZmZkOTNhNDA2YjExYTU3ZWE3ZQ
VALKEY_SSL=true

# Finnhub
FINNHUB_API_KEY=d22pa8pr01qi437f6jh0d22pa8pr01qi437f6jhg
```

- [ ] **Step 3: 安装新依赖**

```bash
cd /Users/zhangfang/deepalpha-club-data
pip install asyncpg>=0.29.0 valkey>=0.6.0
```

Expected: 安装成功，无错误

- [ ] **Step 4: 验证导入正常**

```bash
python -c "import asyncpg; import valkey; print('OK')"
```

Expected: 输出 `OK`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env
git commit -m "feat: add asyncpg and valkey dependencies, configure env vars"
```

---

## Task 2: Pydantic 数据模型 (`models/concept.py`)

**Files:**
- Create: `src/deepalpha/models/concept.py`
- Create: `tests/unit/pipeline/concept/test_models.py`
- Create: `tests/unit/pipeline/__init__.py`
- Create: `tests/unit/pipeline/concept/__init__.py`

- [ ] **Step 1: 创建测试目录 `__init__.py`**

创建以下空文件：
- `tests/unit/pipeline/__init__.py`
- `tests/unit/pipeline/concept/__init__.py`

- [ ] **Step 2: 写失败测试**

创建 `tests/unit/pipeline/concept/test_models.py`：

```python
import datetime
import pytest
from deepalpha.models.concept import ConceptEtfMap, ConceptStock, ConceptSummary


def test_concept_etf_map_required_fields():
    m = ConceptEtfMap(
        concept="Artificial Intelligence",
        etf_symbol="BOTZ",
        updated_at=datetime.date(2026, 5, 31),
    )
    assert m.concept == "Artificial Intelligence"
    assert m.etf_symbol == "BOTZ"
    assert m.etf_name is None
    assert m.aum_million is None


def test_concept_stock_etfs_as_list():
    s = ConceptStock(
        date=datetime.date(2026, 5, 31),
        concept="Artificial Intelligence",
        symbol="NVDA",
        etf_count=3,
        total_weight=15.5,
        etfs=["BOTZ", "AIQ", "IRBO"],
    )
    assert s.etfs == ["BOTZ", "AIQ", "IRBO"]
    assert s.etf_count == 3
    assert s.name is None


def test_concept_summary_top_symbols():
    summary = ConceptSummary(
        concept="Artificial Intelligence",
        etf_count=4,
        stock_count=120,
        top_symbols=["NVDA", "AMD", "MSFT", "GOOGL", "META"],
        last_updated=datetime.date(2026, 5, 31),
    )
    assert len(summary.top_symbols) == 5
    assert summary.stock_count == 120
```

- [ ] **Step 3: 运行确认失败**

```bash
pytest tests/unit/pipeline/concept/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'deepalpha.models.concept'`

- [ ] **Step 4: 创建 `src/deepalpha/models/concept.py`**

```python
"""
概念股池数据模型

包含 ETFdb 概念分类映射、概念成分股快照及概念摘要信息。
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConceptEtfMap(BaseModel):
    """概念 → ETF 映射记录（月度更新）"""
    model_config = ConfigDict(populate_by_name=True)

    concept: str = Field(title="概念名称", description="ETFdb 主题分类名")
    etf_symbol: str = Field(title="ETF 代码", description="ETF 股票代码")
    etf_name: str | None = Field(None, title="ETF 名称", description="ETF 完整名称")
    aum_million: float | None = Field(None, title="AUM（百万美元）", description="ETF 管理资产规模")
    etfdb_slug: str | None = Field(None, title="ETFdb 分类标识", description="ETFdb URL 中的分类 slug")
    updated_at: datetime.date = Field(title="更新日期", description="数据写入日期")


class ConceptStock(BaseModel):
    """概念成分股快照（日度更新）"""
    model_config = ConfigDict(populate_by_name=True)

    date: datetime.date = Field(title="日期", description="持仓快照日期")
    concept: str = Field(title="概念名称", description="ETFdb 主题分类名")
    symbol: str = Field(title="股票代码", description="成分股 ticker")
    name: str | None = Field(None, title="公司名称", description="公司完整名称")
    etf_count: int = Field(title="ETF 覆盖数", description="持有该股的独立 ETF 数量")
    total_weight: float = Field(title="合计权重", description="在所有持有 ETF 中权重之和（%）")
    etfs: list[str] = Field(title="持有 ETF 列表", description="持有该股的 ETF 代码列表")


class ConceptSummary(BaseModel):
    """概念摘要（/concept/list 接口用）"""
    model_config = ConfigDict(populate_by_name=True)

    concept: str = Field(title="概念名称", description="ETFdb 主题分类名")
    etf_count: int = Field(title="ETF 数量", description="该概念下通过 AUM 过滤的 ETF 数量")
    stock_count: int = Field(title="成分股数量", description="最新日期的成分股总数")
    top_symbols: list[str] = Field(title="核心成分股", description="etf_count 最高的前 5 只股票代码")
    last_updated: datetime.date = Field(title="最后更新日", description="最新持仓快照日期")
```

- [ ] **Step 5: 运行确认通过**

```bash
pytest tests/unit/pipeline/concept/test_models.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 6: Commit**

```bash
git add src/deepalpha/models/concept.py tests/unit/pipeline/
git commit -m "feat: add ConceptEtfMap, ConceptStock, ConceptSummary pydantic models"
```

---

## Task 3: Finnhub 配置与 HTTP 客户端

**Files:**
- Create: `src/deepalpha/providers/finnhub/__init__.py`
- Create: `src/deepalpha/providers/finnhub/config.py`
- Create: `src/deepalpha/providers/finnhub/client.py`
- Create: `tests/unit/providers/finnhub/__init__.py`
- Create: `tests/unit/providers/finnhub/test_client.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/unit/providers/finnhub/__init__.py`（空文件）

创建 `tests/unit/providers/finnhub/test_client.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.providers.finnhub.client import FinnhubClient
from deepalpha.providers.finnhub.config import FinnhubConfig


@pytest.fixture
def config():
    return FinnhubConfig(finnhub_api_key="test-key")


@pytest.mark.asyncio
async def test_get_etf_profile_attaches_token(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(json={"name": "Global X Robotics", "mktCap": 2500000000.0})
    async with FinnhubClient(config) as client:
        result = await client.get_etf_profile("BOTZ")
    request = httpx_mock.get_request()
    assert "token=test-key" in str(request.url)
    assert result["name"] == "Global X Robotics"


@pytest.mark.asyncio
async def test_get_etf_holdings_returns_list(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(json={
        "symbol": "BOTZ",
        "holdings": [
            {"symbol": "NVDA", "name": "NVIDIA Corp", "percent": 8.5},
            {"symbol": "ISRG", "name": "Intuitive Surgical", "percent": 5.2},
        ]
    })
    async with FinnhubClient(config) as client:
        result = await client.get_etf_holdings("BOTZ")
    assert len(result) == 2
    assert result[0]["symbol"] == "NVDA"
    assert result[0]["percent"] == 8.5


@pytest.mark.asyncio
async def test_get_etf_holdings_empty_on_no_holdings_key(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(json={"symbol": "BOTZ"})
    async with FinnhubClient(config) as client:
        result = await client.get_etf_holdings("BOTZ")
    assert result == []


@pytest.mark.asyncio
async def test_raises_on_http_error(httpx_mock: HTTPXMock, config):
    httpx_mock.add_response(status_code=429)
    async with FinnhubClient(config) as client:
        with pytest.raises(Exception):
            await client.get_etf_profile("BOTZ")
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/unit/providers/finnhub/test_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'deepalpha.providers.finnhub'`

- [ ] **Step 3: 创建 `src/deepalpha/providers/finnhub/__init__.py`**（空文件）

- [ ] **Step 4: 创建 `src/deepalpha/providers/finnhub/config.py`**

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FinnhubConfig(BaseSettings):
    finnhub_api_key: str = Field(title="API 密钥", description="Finnhub API Key")
    base_url: str = Field("https://finnhub.io", title="API 基础地址")
    timeout: float = Field(30.0, title="超时时间（秒）")
    rate_limit_interval: float = Field(1.1, title="请求最小间隔（秒）", description="免费版 60次/分钟")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

- [ ] **Step 5: 创建 `src/deepalpha/providers/finnhub/client.py`**

```python
import asyncio
import time
from typing import Any

import httpx

from deepalpha.providers.finnhub.config import FinnhubConfig


class FinnhubClient:
    """Finnhub HTTP 客户端，内置令牌桶限速（免费版 60次/分钟）。"""

    def __init__(self, config: FinnhubConfig) -> None:
        self._config = config
        self._http = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self._last_request_at: float = 0.0

    async def _get(self, path: str, **params: Any) -> Any:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._config.rate_limit_interval:
            await asyncio.sleep(self._config.rate_limit_interval - elapsed)
        response = await self._http.get(path, params={"token": self._config.finnhub_api_key, **params})
        response.raise_for_status()
        self._last_request_at = time.monotonic()
        return response.json()

    async def get_etf_profile(self, symbol: str) -> dict[str, Any]:
        """获取 ETF 概况（含 mktCap 字段，单位美元）。"""
        return await self._get("/api/v1/stock/profile2", symbol=symbol)

    async def get_etf_holdings(self, symbol: str) -> list[dict[str, Any]]:
        """获取 ETF 全量持仓列表。"""
        data = await self._get("/api/v1/etf/holdings", symbol=symbol)
        if isinstance(data, dict):
            return data.get("holdings", [])
        return []

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "FinnhubClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
```

- [ ] **Step 6: 运行确认通过**

```bash
pytest tests/unit/providers/finnhub/test_client.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 7: Commit**

```bash
git add src/deepalpha/providers/finnhub/ tests/unit/providers/finnhub/
git commit -m "feat: add FinnhubConfig and FinnhubClient with rate limiting"
```

---

## Task 4: Pipeline 配置 (`pipeline/concept/config.py`)

**Files:**
- Create: `src/deepalpha/pipeline/__init__.py`
- Create: `src/deepalpha/pipeline/concept/__init__.py`
- Create: `src/deepalpha/pipeline/concept/config.py`

- [ ] **Step 1: 创建空 `__init__.py` 文件**

创建以下空文件：
- `src/deepalpha/pipeline/__init__.py`
- `src/deepalpha/pipeline/concept/__init__.py`

- [ ] **Step 2: 创建 `src/deepalpha/pipeline/concept/config.py`**

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConceptPipelineConfig(BaseSettings):
    """概念股池 pipeline 全局配置，从环境变量读取。"""

    postgres_host: str = Field(title="PostgreSQL 主机")
    postgres_port: int = Field(5432, title="PostgreSQL 端口")
    postgres_db: str = Field(title="数据库名")
    postgres_user: str = Field(title="数据库用户名")
    postgres_password: str = Field(title="数据库密码")
    postgres_ssl: bool = Field(False, title="是否启用 SSL")

    valkey_host: str = Field(title="Valkey 主机")
    valkey_port: int = Field(6379, title="Valkey 端口")
    valkey_password: str = Field("", title="Valkey 密码")
    valkey_ssl: bool = Field(False, title="是否启用 Valkey SSL")

    finnhub_api_key: str = Field(title="Finnhub API Key")

    concept_cache_ttl: int = Field(172800, title="缓存 TTL（秒）", description="默认 2 天")
    concept_aum_threshold_million: float = Field(100.0, title="AUM 过滤阈值（百万美元）")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def asyncpg_dsn(self) -> str:
        ssl_param = "?sslmode=require" if self.postgres_ssl else ""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}{ssl_param}"
        )
```

- [ ] **Step 3: 快速验证 config 可实例化（用实际 .env 读取）**

```bash
python -c "
from deepalpha.pipeline.concept.config import ConceptPipelineConfig
c = ConceptPipelineConfig()
print('DSN prefix:', c.asyncpg_dsn()[:30])
print('Valkey host:', c.valkey_host)
print('OK')
"
```

Expected: 输出 DSN 前缀和 Valkey host，最后输出 `OK`

- [ ] **Step 4: Commit**

```bash
git add src/deepalpha/pipeline/
git commit -m "feat: add ConceptPipelineConfig with asyncpg DSN builder"
```

---

## Task 5: ETFdb 抓取器 (`etfdb_scraper.py`)

**Files:**
- Create: `src/deepalpha/pipeline/concept/etfdb_scraper.py`
- Create: `tests/unit/pipeline/concept/test_etfdb_scraper.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/unit/pipeline/concept/test_etfdb_scraper.py`：

```python
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.pipeline.concept.etfdb_scraper import (
    ConceptEtfCandidate,
    _parse_theme_slugs,
    _parse_etf_symbols,
)

# 模拟 ETFdb 主题页 HTML
THEMES_HTML = """
<html><body>
  <div class="etf-category-list">
    <a href="/type/artificial-intelligence-etfs/">Artificial Intelligence</a>
    <a href="/type/robotics-etfs/">Robotics</a>
    <a href="/other-link/">Ignore This</a>
  </div>
</body></html>
"""

# 模拟单个主题下的 ETF 列表页 HTML
ETF_LIST_HTML = """
<html><body>
  <table id="etfs-table">
    <tbody>
      <tr><td><a href="/etf/BOTZ/">BOTZ</a></td><td>Global X Robotics & AI ETF</td></tr>
      <tr><td><a href="/etf/AIQ/">AIQ</a></td><td>Global X AI & Technology ETF</td></tr>
    </tbody>
  </table>
</body></html>
"""


def test_parse_theme_slugs_extracts_concept_and_slug():
    result = _parse_theme_slugs(THEMES_HTML)
    assert "Artificial Intelligence" in result
    assert result["Artificial Intelligence"] == "artificial-intelligence-etfs"
    assert "Robotics" in result
    assert "Ignore This" not in result


def test_parse_etf_symbols_extracts_tickers():
    result = _parse_etf_symbols(ETF_LIST_HTML)
    assert "BOTZ" in result
    assert "AIQ" in result
    assert len(result) == 2
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/unit/pipeline/concept/test_etfdb_scraper.py -v
```

Expected: `ImportError` 或 `ModuleNotFoundError`

- [ ] **Step 3: 创建 `src/deepalpha/pipeline/concept/etfdb_scraper.py`**

```python
"""
ETFdb 主题分类抓取器

月度运行，抓取 ETFdb 全部主题分类及各分类下的 ETF 列表。
请求间隔 2 秒，每月只运行一次，对 ETFdb 无明显压力。
"""

import asyncio
import random
from dataclasses import dataclass

import httpx
from lxml import html

ETFDB_BASE = "https://etfdb.com"

_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
]


@dataclass
class ConceptEtfCandidate:
    """ETFdb 抓取到的原始 concept→etf 候选（AUM 过滤前）。"""
    concept: str
    etf_symbol: str
    etfdb_slug: str


def _parse_theme_slugs(page_html: str) -> dict[str, str]:
    """从主题列表页 HTML 中解析 {concept_name: slug}。"""
    tree = html.fromstring(page_html)
    result: dict[str, str] = {}
    for link in tree.xpath("//a[contains(@href, '/type/')]"):
        href: str = link.get("href", "")
        text: str = link.text_content().strip()
        if not href or not text:
            continue
        # href 格式: /type/artificial-intelligence-etfs/
        parts = [p for p in href.strip("/").split("/") if p]
        if len(parts) >= 2 and parts[0] == "type":
            slug = parts[1]
            result[text] = slug
    return result


def _parse_etf_symbols(page_html: str) -> list[str]:
    """从主题详情页 HTML 中解析 ETF symbol 列表。"""
    tree = html.fromstring(page_html)
    symbols: list[str] = []
    # ETFdb 在 ETF 列表表格中，ticker 在链接文本里，href 格式: /etf/BOTZ/
    for link in tree.xpath("//a[contains(@href, '/etf/')]"):
        href: str = link.get("href", "")
        parts = [p for p in href.strip("/").split("/") if p]
        if len(parts) >= 2 and parts[0] == "etf":
            symbol = parts[1].upper()
            if symbol and symbol not in symbols:
                symbols.append(symbol)
    return symbols


async def scrape_concept_etf_candidates(delay: float = 2.0) -> list[ConceptEtfCandidate]:
    """抓取 ETFdb 所有主题分类的 ETF 候选列表（AUM 过滤前）。"""
    headers = {"User-Agent": random.choice(_USER_AGENTS)}
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        resp = await client.get(f"{ETFDB_BASE}/etfs/themes/", headers=headers)
        resp.raise_for_status()
        slugs = _parse_theme_slugs(resp.text)

        candidates: list[ConceptEtfCandidate] = []
        for concept, slug in slugs.items():
            await asyncio.sleep(delay)
            headers = {"User-Agent": random.choice(_USER_AGENTS)}
            try:
                resp = await client.get(f"{ETFDB_BASE}/type/{slug}/", headers=headers)
                resp.raise_for_status()
                symbols = _parse_etf_symbols(resp.text)
                for sym in symbols:
                    candidates.append(ConceptEtfCandidate(concept=concept, etf_symbol=sym, etfdb_slug=slug))
            except httpx.HTTPError:
                continue

    return candidates
```

- [ ] **Step 4: 运行确认通过**

```bash
pytest tests/unit/pipeline/concept/test_etfdb_scraper.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/pipeline/concept/etfdb_scraper.py tests/unit/pipeline/concept/test_etfdb_scraper.py
git commit -m "feat: add ETFdb scraper with HTML parsing for theme slugs and ETF symbols"
```

---

## Task 6: Finnhub 持仓加载器 (`finnhub_loader.py`)

**Files:**
- Create: `src/deepalpha/pipeline/concept/finnhub_loader.py`
- Create: `tests/unit/pipeline/concept/test_finnhub_loader.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/unit/pipeline/concept/test_finnhub_loader.py`：

```python
import datetime
import pytest
from unittest.mock import AsyncMock

from deepalpha.models.concept import ConceptEtfMap
from deepalpha.pipeline.concept.etfdb_scraper import ConceptEtfCandidate
from deepalpha.pipeline.concept.finnhub_loader import filter_etfs_by_aum, aggregate_holdings


@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.get_etf_profile = AsyncMock(return_value={"name": "Global X Robotics", "mktCap": 2_500_000_000.0})
    client.get_etf_holdings = AsyncMock(return_value=[
        {"symbol": "NVDA", "name": "NVIDIA Corp", "percent": 8.5},
        {"symbol": "ISRG", "name": "Intuitive Surgical", "percent": 5.2},
    ])
    return client


@pytest.mark.asyncio
async def test_filter_etfs_by_aum_passes_large_etf(mock_client):
    candidates = [ConceptEtfCandidate(concept="Robotics", etf_symbol="BOTZ", etfdb_slug="robotics-etfs")]
    result = await filter_etfs_by_aum(candidates, mock_client, aum_threshold_million=100.0)
    assert len(result) == 1
    assert result[0].etf_symbol == "BOTZ"
    assert result[0].aum_million == pytest.approx(2500.0)


@pytest.mark.asyncio
async def test_filter_etfs_by_aum_blocks_small_etf(mock_client):
    # AUM = $50M，低于 $100M 阈值
    mock_client.get_etf_profile = AsyncMock(return_value={"name": "Tiny ETF", "mktCap": 50_000_000.0})
    candidates = [ConceptEtfCandidate(concept="Robotics", etf_symbol="TINY", etfdb_slug="robotics-etfs")]
    result = await filter_etfs_by_aum(candidates, mock_client, aum_threshold_million=100.0)
    assert result == []


@pytest.mark.asyncio
async def test_aggregate_holdings_calculates_etf_count_and_total_weight():
    today = datetime.date(2026, 5, 31)
    etf_maps = [
        ConceptEtfMap(concept="AI", etf_symbol="BOTZ", updated_at=today),
        ConceptEtfMap(concept="AI", etf_symbol="AIQ", updated_at=today),
    ]
    holdings_by_etf = {
        "BOTZ": [{"symbol": "NVDA", "name": "NVIDIA", "percent": 8.5}],
        "AIQ": [{"symbol": "NVDA", "name": "NVIDIA", "percent": 6.0}, {"symbol": "AMD", "name": "AMD", "percent": 4.0}],
    }
    result = await aggregate_holdings(etf_maps, holdings_by_etf, date=today)

    nvda = next(s for s in result if s.symbol == "NVDA")
    assert nvda.etf_count == 2
    assert nvda.total_weight == pytest.approx(14.5)
    assert set(nvda.etfs) == {"BOTZ", "AIQ"}

    amd = next(s for s in result if s.symbol == "AMD")
    assert amd.etf_count == 1
    assert amd.total_weight == pytest.approx(4.0)
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/unit/pipeline/concept/test_finnhub_loader.py -v
```

Expected: `ImportError` 或 `ModuleNotFoundError`

- [ ] **Step 3: 创建 `src/deepalpha/pipeline/concept/finnhub_loader.py`**

```python
"""
Finnhub ETF 持仓加载器

负责 AUM 过滤和持仓数据聚合（etf_count / total_weight）。
"""

import csv
import datetime
import io
from collections import defaultdict
from typing import Any, Protocol

import httpx

from deepalpha.models.concept import ConceptEtfMap, ConceptStock
from deepalpha.pipeline.concept.etfdb_scraper import ConceptEtfCandidate


class _EtfClient(Protocol):
    async def get_etf_profile(self, symbol: str) -> dict[str, Any]: ...
    async def get_etf_holdings(self, symbol: str) -> list[dict[str, Any]]: ...


async def filter_etfs_by_aum(
    candidates: list[ConceptEtfCandidate],
    client: _EtfClient,
    aum_threshold_million: float = 100.0,
) -> list[ConceptEtfMap]:
    """对候选 ETF 列表做 AUM 过滤，返回规模 >= 阈值的 ConceptEtfMap 列表。"""
    today = datetime.date.today()
    result: list[ConceptEtfMap] = []
    seen: set[tuple[str, str]] = set()

    for candidate in candidates:
        key = (candidate.concept, candidate.etf_symbol)
        if key in seen:
            continue
        seen.add(key)
        try:
            profile = await client.get_etf_profile(candidate.etf_symbol)
            mkt_cap = profile.get("mktCap")
            aum_million = mkt_cap / 1_000_000 if mkt_cap else None
            if aum_million is None or aum_million >= aum_threshold_million:
                result.append(ConceptEtfMap(
                    concept=candidate.concept,
                    etf_symbol=candidate.etf_symbol,
                    etf_name=profile.get("name"),
                    aum_million=aum_million,
                    etfdb_slug=candidate.etfdb_slug,
                    updated_at=today,
                ))
        except Exception:
            continue

    return result


async def aggregate_holdings(
    etf_maps: list[ConceptEtfMap],
    holdings_by_etf: dict[str, list[dict[str, Any]]],
    date: datetime.date,
) -> list[ConceptStock]:
    """将各 ETF 持仓合并，计算每只股票的 etf_count 和 total_weight。"""
    # concept -> symbol -> [(etf_symbol, weight, name)]
    data: dict[str, dict[str, list[tuple[str, float, str | None]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    etf_to_concepts: dict[str, list[str]] = defaultdict(list)
    for em in etf_maps:
        etf_to_concepts[em.etf_symbol].append(em.concept)

    for etf_symbol, concepts in etf_to_concepts.items():
        for holding in holdings_by_etf.get(etf_symbol, []):
            symbol: str = holding.get("symbol", "").upper()
            if not symbol:
                continue
            name: str | None = holding.get("name")
            weight: float = float(holding.get("percent", 0))
            for concept in concepts:
                data[concept][symbol].append((etf_symbol, weight, name))

    results: list[ConceptStock] = []
    for concept, symbol_data in data.items():
        for symbol, entries in symbol_data.items():
            name = next((e[2] for e in entries if e[2]), None)
            results.append(ConceptStock(
                date=date,
                concept=concept,
                symbol=symbol,
                name=name,
                etf_count=len(entries),
                total_weight=round(sum(e[1] for e in entries), 4),
                etfs=[e[0] for e in entries],
            ))

    return results


async def fetch_holdings_with_fallback(etf_symbol: str, client: _EtfClient) -> list[dict[str, Any]]:
    """拉取 ETF 持仓，Finnhub 失败时回落 ETF 官网 CSV。"""
    try:
        holdings = await client.get_etf_holdings(etf_symbol)
        if holdings:
            return holdings
    except Exception:
        pass
    return await _fetch_csv_fallback(etf_symbol)


# ETF 官网 CSV 兜底映射（Global X 等），可按需扩展
_CSV_URLS: dict[str, str] = {
    "BOTZ": "https://www.globalxetfs.com/funds/botz/holdings.csv",
    "AIQ": "https://www.globalxetfs.com/funds/aiq/holdings.csv",
}


async def _fetch_csv_fallback(etf_symbol: str) -> list[dict[str, Any]]:
    url = _CSV_URLS.get(etf_symbol.upper())
    if not url:
        return []
    try:
        async with httpx.AsyncClient(timeout=30.0) as http:
            resp = await http.get(url)
            resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))
        return [
            {"symbol": row.get("Ticker", "").upper(), "name": row.get("Name"), "percent": float(row.get("Weight (%)", 0) or 0)}
            for row in reader
            if row.get("Ticker")
        ]
    except Exception:
        return []
```

- [ ] **Step 4: 运行确认通过**

```bash
pytest tests/unit/pipeline/concept/test_finnhub_loader.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/pipeline/concept/finnhub_loader.py tests/unit/pipeline/concept/test_finnhub_loader.py
git commit -m "feat: add Finnhub ETF AUM filter and holdings aggregation logic"
```

---

## Task 7: PostgreSQL 数据层 (`db.py`)

**Files:**
- Create: `src/deepalpha/pipeline/concept/db.py`
- Create: `tests/unit/pipeline/concept/test_db.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/unit/pipeline/concept/test_db.py`：

```python
import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from deepalpha.models.concept import ConceptEtfMap, ConceptStock
from deepalpha.pipeline.concept.db import ConceptDb


def _make_mock_pool(mock_conn: AsyncMock) -> MagicMock:
    """构造模拟 asyncpg Pool，acquire() 返回给定 conn。"""
    pool = MagicMock()
    pool.close = AsyncMock()
    acm = MagicMock()
    acm.__aenter__ = AsyncMock(return_value=mock_conn)
    acm.__aexit__ = AsyncMock(return_value=False)
    pool.acquire.return_value = acm
    return pool


@pytest.mark.asyncio
async def test_upsert_etf_map_calls_executemany():
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()  # CREATE TABLE 调用
    mock_conn.executemany = AsyncMock()
    mock_pool = _make_mock_pool(mock_conn)

    records = [
        ConceptEtfMap(
            concept="Artificial Intelligence",
            etf_symbol="BOTZ",
            etf_name="Global X Robotics & AI",
            aum_million=2500.0,
            etfdb_slug="artificial-intelligence-etfs",
            updated_at=datetime.date(2026, 5, 31),
        )
    ]

    with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        async with ConceptDb("postgresql://test") as db:
            await db.upsert_etf_map(records)

    mock_conn.executemany.assert_called_once()
    call_args = mock_conn.executemany.call_args
    rows = call_args[0][1]
    assert rows[0][0] == "Artificial Intelligence"
    assert rows[0][1] == "BOTZ"


@pytest.mark.asyncio
async def test_upsert_stocks_serializes_etfs_as_comma_string():
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.executemany = AsyncMock()
    mock_pool = _make_mock_pool(mock_conn)

    records = [
        ConceptStock(
            date=datetime.date(2026, 5, 31),
            concept="AI",
            symbol="NVDA",
            etf_count=3,
            total_weight=15.5,
            etfs=["BOTZ", "AIQ", "IRBO"],
        )
    ]

    with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        async with ConceptDb("postgresql://test") as db:
            await db.upsert_stocks(records)

    call_args = mock_conn.executemany.call_args
    rows = call_args[0][1]
    assert rows[0][6] == "BOTZ,AIQ,IRBO"  # etfs 字段序列化为逗号分隔字符串


@pytest.mark.asyncio
async def test_load_etf_map_parses_rows():
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {"concept": "AI", "etf_symbol": "BOTZ", "etf_name": "Global X", "aum_million": 2500.0, "etfdb_slug": "ai-etfs", "updated_at": datetime.date(2026, 5, 1)},
    ])
    mock_pool = _make_mock_pool(mock_conn)

    with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        async with ConceptDb("postgresql://test") as db:
            result = await db.load_etf_map()

    assert len(result) == 1
    assert result[0].concept == "AI"
    assert result[0].etf_symbol == "BOTZ"
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/unit/pipeline/concept/test_db.py -v
```

Expected: `ImportError` 或 `ModuleNotFoundError`

- [ ] **Step 3: 创建 `src/deepalpha/pipeline/concept/db.py`**

```python
"""
概念股池 PostgreSQL 数据层

使用 asyncpg 进行异步读写，所有写入操作均为幂等（ON CONFLICT DO UPDATE）。
"""

import datetime
from typing import Any

import asyncpg

from deepalpha.models.concept import ConceptEtfMap, ConceptStock, ConceptSummary

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


class ConceptDb:
    """asyncpg-based PostgreSQL 数据层，管理 concept_etf_map 和 concept_stocks 两张表。"""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None  # type: ignore[type-arg]

    async def __aenter__(self) -> "ConceptDb":
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
                INSERT INTO concept_etf_map (concept, etf_symbol, etf_name, aum_million, etfdb_slug, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (concept, etf_symbol) DO UPDATE
                SET etf_name = EXCLUDED.etf_name,
                    aum_million = EXCLUDED.aum_million,
                    etfdb_slug = EXCLUDED.etfdb_slug,
                    updated_at = EXCLUDED.updated_at
                """,
                [(r.concept, r.etf_symbol, r.etf_name, r.aum_million, r.etfdb_slug, r.updated_at) for r in records],
            )

    async def load_etf_map(self) -> list[ConceptEtfMap]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT concept, etf_symbol, etf_name, aum_million, etfdb_slug, updated_at FROM concept_etf_map"
            )
        return [
            ConceptEtfMap(
                concept=r["concept"],
                etf_symbol=r["etf_symbol"],
                etf_name=r["etf_name"],
                aum_million=r["aum_million"],
                etfdb_slug=r["etfdb_slug"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    async def upsert_stocks(self, records: list[ConceptStock]) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO concept_stocks (date, concept, symbol, name, etf_count, total_weight, etfs)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (date, concept, symbol) DO UPDATE
                SET name = EXCLUDED.name,
                    etf_count = EXCLUDED.etf_count,
                    total_weight = EXCLUDED.total_weight,
                    etfs = EXCLUDED.etfs
                """,
                [(r.date, r.concept, r.symbol, r.name, r.etf_count, r.total_weight, ",".join(r.etfs)) for r in records],
            )

    async def get_latest_stocks(self, concept: str) -> list[ConceptStock]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT date, concept, symbol, name, etf_count, total_weight, etfs
                FROM concept_stocks
                WHERE concept = $1
                  AND date = (SELECT MAX(date) FROM concept_stocks WHERE concept = $1)
                ORDER BY etf_count DESC, total_weight DESC
                """,
                concept,
            )
        return [_row_to_stock(r) for r in rows]

    async def get_all_concept_summaries(self) -> list[ConceptSummary]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            etf_rows = await conn.fetch(
                "SELECT concept, COUNT(*) as cnt FROM concept_etf_map GROUP BY concept"
            )
            etf_counts = {r["concept"]: r["cnt"] for r in etf_rows}

            stock_rows = await conn.fetch(
                """
                WITH latest AS (
                    SELECT concept, MAX(date) as max_date FROM concept_stocks GROUP BY concept
                )
                SELECT cs.concept, cs.date, cs.symbol, cs.etf_count
                FROM concept_stocks cs
                JOIN latest l ON cs.concept = l.concept AND cs.date = l.max_date
                ORDER BY cs.concept, cs.etf_count DESC, cs.total_weight DESC
                """
            )

        from collections import defaultdict
        concept_data: dict[str, dict[str, Any]] = defaultdict(lambda: {"date": None, "symbols": []})
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
                SELECT date, concept, symbol, name, etf_count, total_weight, etfs
                FROM concept_stocks
                WHERE concept = $1 AND date >= $2 AND date <= $3
                ORDER BY date DESC, etf_count DESC
                """,
                concept, start, end,
            )
        return [_row_to_stock(r) for r in rows]


def _row_to_stock(row: Any) -> ConceptStock:
    return ConceptStock(
        date=row["date"],
        concept=row["concept"],
        symbol=row["symbol"],
        name=row["name"],
        etf_count=row["etf_count"],
        total_weight=row["total_weight"],
        etfs=row["etfs"].split(",") if row["etfs"] else [],
    )
```

- [ ] **Step 4: 运行确认通过**

```bash
pytest tests/unit/pipeline/concept/test_db.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/pipeline/concept/db.py tests/unit/pipeline/concept/test_db.py
git commit -m "feat: add ConceptDb asyncpg data layer with idempotent upserts"
```

---

## Task 8: Valkey 缓存层 (`cache.py`)

**Files:**
- Create: `src/deepalpha/pipeline/concept/cache.py`
- Create: `tests/unit/pipeline/concept/test_cache.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/unit/pipeline/concept/test_cache.py`：

```python
import datetime
import json
import pytest
from unittest.mock import AsyncMock, patch

from deepalpha.models.concept import ConceptStock, ConceptSummary
from deepalpha.pipeline.concept.cache import ConceptCache


@pytest.fixture
def mock_valkey():
    """返回一个模拟的 valkey.asyncio.Valkey 实例。"""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def cache(mock_valkey):
    with patch("deepalpha.pipeline.concept.cache.valkey_asyncio.Valkey", return_value=mock_valkey):
        return ConceptCache(host="localhost", port=6379, password="", ssl=False)


@pytest.mark.asyncio
async def test_get_concept_returns_none_on_cache_miss(cache, mock_valkey):
    mock_valkey.get.return_value = None
    result = await cache.get_concept("AI")
    assert result is None


@pytest.mark.asyncio
async def test_get_concept_deserializes_cached_data(cache, mock_valkey):
    stock = ConceptStock(
        date=datetime.date(2026, 5, 31),
        concept="AI",
        symbol="NVDA",
        etf_count=3,
        total_weight=15.5,
        etfs=["BOTZ", "AIQ", "IRBO"],
    )
    mock_valkey.get.return_value = json.dumps([stock.model_dump(mode="json")])
    result = await cache.get_concept("AI")
    assert result is not None
    assert len(result) == 1
    assert result[0].symbol == "NVDA"
    assert result[0].etfs == ["BOTZ", "AIQ", "IRBO"]


@pytest.mark.asyncio
async def test_set_concept_serializes_with_ttl(cache, mock_valkey):
    stocks = [
        ConceptStock(date=datetime.date(2026, 5, 31), concept="AI", symbol="NVDA",
                     etf_count=3, total_weight=15.5, etfs=["BOTZ"])
    ]
    await cache.set_concept("AI", stocks)
    mock_valkey.set.assert_called_once()
    call_args = mock_valkey.set.call_args
    assert call_args[0][0] == "concept:AI"
    assert call_args[1]["ex"] == 172800


@pytest.mark.asyncio
async def test_get_list_returns_none_on_cache_miss(cache, mock_valkey):
    mock_valkey.get.return_value = None
    result = await cache.get_list()
    assert result is None


@pytest.mark.asyncio
async def test_set_list_uses_correct_key(cache, mock_valkey):
    summaries = [
        ConceptSummary(concept="AI", etf_count=4, stock_count=120,
                       top_symbols=["NVDA"], last_updated=datetime.date(2026, 5, 31))
    ]
    await cache.set_list(summaries)
    call_args = mock_valkey.set.call_args
    assert call_args[0][0] == "concept:__list__"
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/unit/pipeline/concept/test_cache.py -v
```

Expected: `ImportError` 或 `ModuleNotFoundError`

- [ ] **Step 3: 创建 `src/deepalpha/pipeline/concept/cache.py`**

```python
"""
概念股池 Valkey 缓存层

KEY 规范：
  concept:__list__       → list[ConceptSummary] JSON，TTL 2 天
  concept:{name}         → list[ConceptStock] JSON，TTL 2 天
"""

import json

import valkey.asyncio as valkey_asyncio

from deepalpha.models.concept import ConceptStock, ConceptSummary


class ConceptCache:
    """Valkey（Upstash）缓存层，管理概念摘要列表和各概念成分股列表。"""

    def __init__(self, host: str, port: int, password: str, ssl: bool, ttl: int = 172800) -> None:
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

- [ ] **Step 4: 运行确认通过**

```bash
pytest tests/unit/pipeline/concept/test_cache.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add src/deepalpha/pipeline/concept/cache.py tests/unit/pipeline/concept/test_cache.py
git commit -m "feat: add ConceptCache Valkey layer with JSON serialization"
```

---

## Task 9: 月度任务 (`build_concept_map.py`)

**Files:**
- Create: `src/deepalpha/pipeline/concept/tasks/__init__.py`
- Create: `src/deepalpha/pipeline/concept/tasks/build_concept_map.py`

- [ ] **Step 1: 创建 `src/deepalpha/pipeline/concept/tasks/__init__.py`**（空文件）

- [ ] **Step 2: 创建 `src/deepalpha/pipeline/concept/tasks/build_concept_map.py`**

```python
"""
月度任务：构建概念 → ETF 映射表

调度：每月 1 日 02:00（新加坡时间）
流程：ETFdb 抓取 → Finnhub AUM 过滤 → concept_etf_map 写入
"""

import asyncio
import logging

from deepalpha.pipeline.concept.config import ConceptPipelineConfig
from deepalpha.pipeline.concept.db import ConceptDb
from deepalpha.pipeline.concept.etfdb_scraper import scrape_concept_etf_candidates
from deepalpha.pipeline.concept.finnhub_loader import filter_etfs_by_aum
from deepalpha.providers.finnhub.client import FinnhubClient
from deepalpha.providers.finnhub.config import FinnhubConfig

logger = logging.getLogger(__name__)


async def run(config: ConceptPipelineConfig | None = None) -> None:
    if config is None:
        config = ConceptPipelineConfig()

    logger.info("开始抓取 ETFdb 主题分类...")
    candidates = await scrape_concept_etf_candidates(delay=2.0)
    logger.info("抓取完成，候选 ETF 条目数: %d", len(candidates))

    finnhub_config = FinnhubConfig(finnhub_api_key=config.finnhub_api_key)
    async with FinnhubClient(finnhub_config) as client:
        logger.info("开始 AUM 过滤（阈值: %.0fM）...", config.concept_aum_threshold_million)
        etf_maps = await filter_etfs_by_aum(candidates, client, config.concept_aum_threshold_million)

    logger.info("AUM 过滤完成，通过 %d 条，写入数据库...", len(etf_maps))
    async with ConceptDb(config.asyncpg_dsn()) as db:
        await db.upsert_etf_map(etf_maps)

    concepts = len({em.concept for em in etf_maps})
    etfs = len({em.etf_symbol for em in etf_maps})
    logger.info("月度任务完成：%d 个概念，%d 只 ETF", concepts, etfs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run())
```

- [ ] **Step 3: 验证脚本语法无误**

```bash
python -c "from deepalpha.pipeline.concept.tasks.build_concept_map import run; print('OK')"
```

Expected: 输出 `OK`

- [ ] **Step 4: Commit**

```bash
git add src/deepalpha/pipeline/concept/tasks/
git commit -m "feat: add build_concept_map monthly pipeline task"
```

---

## Task 10: 日度任务 (`update_holdings.py`)

**Files:**
- Create: `src/deepalpha/pipeline/concept/tasks/update_holdings.py`

- [ ] **Step 1: 创建 `src/deepalpha/pipeline/concept/tasks/update_holdings.py`**

```python
"""
日度任务：更新 ETF 持仓并刷新 Valkey 缓存

调度：每个交易日 04:30（新加坡时间，对应美东收盘后 16:30）
流程：读取 concept_etf_map → Finnhub 持仓拉取 → 合并聚合 → DB 写入 → 缓存刷新
"""

import asyncio
import datetime
import logging

from deepalpha.pipeline.concept.cache import ConceptCache
from deepalpha.pipeline.concept.config import ConceptPipelineConfig
from deepalpha.pipeline.concept.db import ConceptDb
from deepalpha.pipeline.concept.finnhub_loader import (
    aggregate_holdings,
    fetch_holdings_with_fallback,
)
from deepalpha.providers.finnhub.client import FinnhubClient
from deepalpha.providers.finnhub.config import FinnhubConfig

logger = logging.getLogger(__name__)


async def run(config: ConceptPipelineConfig | None = None) -> None:
    if config is None:
        config = ConceptPipelineConfig()

    today = datetime.date.today()
    finnhub_config = FinnhubConfig(finnhub_api_key=config.finnhub_api_key)

    async with ConceptDb(config.asyncpg_dsn()) as db:
        etf_maps = await db.load_etf_map()
        if not etf_maps:
            logger.warning("concept_etf_map 为空，请先运行 build_concept_map.py")
            return

        logger.info("读取到 %d 条 ETF 映射，开始拉取持仓...", len(etf_maps))
        unique_etfs = list({em.etf_symbol for em in etf_maps})

        holdings_by_etf: dict[str, list] = {}
        async with FinnhubClient(finnhub_config) as client:
            for etf_symbol in unique_etfs:
                holdings = await fetch_holdings_with_fallback(etf_symbol, client)
                holdings_by_etf[etf_symbol] = holdings
                logger.debug("  %s: %d 条持仓", etf_symbol, len(holdings))

        logger.info("持仓拉取完成，开始聚合...")
        stocks = await aggregate_holdings(etf_maps, holdings_by_etf, date=today)
        logger.info("聚合完成，%d 条成分股记录，写入数据库...", len(stocks))

        await db.upsert_stocks(stocks)
        logger.info("数据库写入完成，刷新 Valkey 缓存...")

        summaries = await db.get_all_concept_summaries()

    cache = ConceptCache(
        host=config.valkey_host,
        port=config.valkey_port,
        password=config.valkey_password,
        ssl=config.valkey_ssl,
        ttl=config.concept_cache_ttl,
    )
    try:
        await cache.set_list(summaries)
        async with ConceptDb(config.asyncpg_dsn()) as db:
            for summary in summaries:
                concept_stocks = await db.get_latest_stocks(summary.concept)
                await cache.set_concept(summary.concept, concept_stocks)
        logger.info("缓存刷新完成，共 %d 个概念", len(summaries))
    finally:
        await cache.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run())
```

- [ ] **Step 2: 验证脚本语法无误**

```bash
python -c "from deepalpha.pipeline.concept.tasks.update_holdings import run; print('OK')"
```

Expected: 输出 `OK`

- [ ] **Step 3: Commit**

```bash
git add src/deepalpha/pipeline/concept/tasks/update_holdings.py
git commit -m "feat: add update_holdings daily pipeline task with cache refresh"
```

---

## Task 11: FastAPI 查询接口 (`api/router.py`)

**Files:**
- Create: `src/deepalpha/pipeline/concept/api/__init__.py`
- Create: `src/deepalpha/pipeline/concept/api/router.py`
- Create: `tests/unit/pipeline/concept/test_router.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/unit/pipeline/concept/test_router.py`：

```python
import datetime
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from deepalpha.models.concept import ConceptStock, ConceptSummary
from deepalpha.pipeline.concept.api.router import router, get_cache, get_config
from deepalpha.pipeline.concept.config import ConceptPipelineConfig


@pytest.fixture
def test_config():
    return ConceptPipelineConfig(
        postgres_host="localhost", postgres_db="test", postgres_user="u", postgres_password="p",
        valkey_host="localhost", finnhub_api_key="test",
    )


@pytest.fixture
def sample_summaries():
    return [
        ConceptSummary(concept="Artificial Intelligence", etf_count=4, stock_count=120,
                       top_symbols=["NVDA", "AMD"], last_updated=datetime.date(2026, 5, 31)),
        ConceptSummary(concept="Robotics", etf_count=2, stock_count=60,
                       top_symbols=["ISRG", "ABB"], last_updated=datetime.date(2026, 5, 31)),
    ]


@pytest.fixture
def sample_stocks():
    return [
        ConceptStock(date=datetime.date(2026, 5, 31), concept="Artificial Intelligence",
                     symbol="NVDA", name="NVIDIA", etf_count=4, total_weight=20.0, etfs=["BOTZ","AIQ","IRBO","ROBT"]),
        ConceptStock(date=datetime.date(2026, 5, 31), concept="Artificial Intelligence",
                     symbol="AMD", name="AMD", etf_count=2, total_weight=8.0, etfs=["AIQ","IRBO"]),
    ]


@pytest.fixture
def mock_cache(sample_summaries, sample_stocks):
    cache = AsyncMock()
    cache.get_list = AsyncMock(return_value=sample_summaries)
    cache.get_concept = AsyncMock(return_value=sample_stocks)
    cache.set_list = AsyncMock()
    cache.set_concept = AsyncMock()
    cache.close = AsyncMock()
    return cache


@pytest.fixture
def client(test_config, mock_cache):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_config] = lambda: test_config
    app.dependency_overrides[get_cache] = lambda: mock_cache
    return TestClient(app)


def test_list_concepts_returns_all(client, sample_summaries):
    resp = client.get("/concept/list")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    concepts = [d["concept"] for d in data]
    assert "Artificial Intelligence" in concepts
    assert "Robotics" in concepts


def test_get_concept_returns_stocks(client, sample_stocks):
    resp = client.get("/concept/Artificial Intelligence")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["symbol"] == "NVDA"


def test_get_concept_filters_by_min_etf_count(client, sample_stocks):
    resp = client.get("/concept/Artificial Intelligence?min_etf_count=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "NVDA"  # etf_count=4，通过; AMD etf_count=2，被过滤
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/unit/pipeline/concept/test_router.py -v
```

Expected: `ImportError` 或 `ModuleNotFoundError`

- [ ] **Step 3: 创建 `src/deepalpha/pipeline/concept/api/__init__.py`**（空文件）

- [ ] **Step 4: 创建 `src/deepalpha/pipeline/concept/api/router.py`**

```python
"""
概念股池 FastAPI 查询接口

挂载方式：
    from deepalpha.pipeline.concept.api.router import router
    app.include_router(router, prefix="/api/v1")
"""

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from deepalpha.models.concept import ConceptStock, ConceptSummary
from deepalpha.pipeline.concept.cache import ConceptCache
from deepalpha.pipeline.concept.config import ConceptPipelineConfig
from deepalpha.pipeline.concept.db import ConceptDb

router = APIRouter(prefix="/concept", tags=["concept"])


def get_config() -> ConceptPipelineConfig:
    return ConceptPipelineConfig()


def get_cache(config: Annotated[ConceptPipelineConfig, Depends(get_config)]) -> ConceptCache:
    return ConceptCache(
        host=config.valkey_host,
        port=config.valkey_port,
        password=config.valkey_password,
        ssl=config.valkey_ssl,
        ttl=config.concept_cache_ttl,
    )


@router.get("/list", response_model=list[ConceptSummary])
async def list_concepts(
    config: Annotated[ConceptPipelineConfig, Depends(get_config)],
    cache: Annotated[ConceptCache, Depends(get_cache)],
) -> list[ConceptSummary]:
    """返回所有概念摘要，包含 ETF 数量、成分股数、top5 成分股和最后更新日。"""
    cached = await cache.get_list()
    if cached is not None:
        return cached
    async with ConceptDb(config.asyncpg_dsn()) as db:
        summaries = await db.get_all_concept_summaries()
    await cache.set_list(summaries)
    return summaries


@router.get("/{name}", response_model=list[ConceptStock])
async def get_concept(
    name: str,
    config: Annotated[ConceptPipelineConfig, Depends(get_config)],
    cache: Annotated[ConceptCache, Depends(get_cache)],
    min_etf_count: int = Query(1, ge=1, description="最低 ETF 覆盖数，用于控制成分股纯度"),
) -> list[ConceptStock]:
    """返回指定概念的最新成分股列表，按 etf_count 降序排列。"""
    cached = await cache.get_concept(name)
    if cached is None:
        async with ConceptDb(config.asyncpg_dsn()) as db:
            cached = await db.get_latest_stocks(name)
        if cached:
            await cache.set_concept(name, cached)

    filtered = [s for s in (cached or []) if s.etf_count >= min_etf_count]
    if not filtered and not cached:
        raise HTTPException(status_code=404, detail=f"概念 '{name}' 不存在")
    return filtered


@router.get("/{name}/history", response_model=list[ConceptStock])
async def get_concept_history(
    name: str,
    config: Annotated[ConceptPipelineConfig, Depends(get_config)],
    start: datetime.date = Query(..., description="开始日期（含），格式 YYYY-MM-DD"),
    end: datetime.date = Query(..., description="结束日期（含），格式 YYYY-MM-DD"),
) -> list[ConceptStock]:
    """返回指定概念在日期范围内的历史成分股快照。"""
    async with ConceptDb(config.asyncpg_dsn()) as db:
        return await db.get_stocks_history(name, start, end)
```

- [ ] **Step 5: 运行确认通过**

```bash
pytest tests/unit/pipeline/concept/test_router.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 6: 运行全量测试确认无回归**

```bash
pytest tests/unit/ -v --tb=short
```

Expected: 所有 unit tests PASSED

- [ ] **Step 7: Commit**

```bash
git add src/deepalpha/pipeline/concept/api/ tests/unit/pipeline/concept/test_router.py
git commit -m "feat: add FastAPI concept stock pool query router with cache-aside pattern"
```

---

## 自检结果

### 规格覆盖检查

| 规格要求 | 对应任务 |
|----------|---------|
| Pydantic 模型（ConceptEtfMap / ConceptStock / ConceptSummary） | Task 2 |
| Finnhub 客户端（限速 60次/分钟） | Task 3 |
| Pipeline 配置（DB/Valkey/Finnhub 环境变量） | Task 4 |
| ETFdb HTML 抓取（httpx + lxml） | Task 5 |
| AUM 过滤 + 持仓聚合（etf_count / total_weight） | Task 6 |
| PostgreSQL 数据层（幂等写入） | Task 7 |
| Valkey 缓存层（TTL 2 天，JSON 序列化） | Task 8 |
| 月度任务 `build_concept_map` | Task 9 |
| 日度任务 `update_holdings` + 缓存刷新 | Task 10 |
| FastAPI 接口（/list、/{name}、/{name}/history） | Task 11 |
| min_etf_count 过滤参数 | Task 11 |
| ETF 官网 CSV 兜底 | Task 6（`fetch_holdings_with_fallback` + `_fetch_csv_fallback`） |
| `.env` 新增连接配置 | Task 1 |
| asyncpg + valkey 新增依赖 | Task 1 |

所有规格要求均有对应任务，无遗漏。
