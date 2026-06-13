# 财报电话会议日历 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增独立 `/earnings` 页面，左侧月历选日期，右侧展示该日期纳斯达克 100 成分股的财报电话会议（公司简介、主要产品、AI 摘要、全文中文翻译）。

**Architecture:** 完整六边形架构，新建 `earnings_call` domain（models + protocols）；`FMPEarningsCallLoader` 拉数据；`EarningsCallRepo` 缓存 PG；`EarningsCallService` 编排翻译；FastAPI router 暴露两个接口；Next.js `(pages)/earnings/page.tsx` 渲染页面。

**Tech Stack:** Python 3.11 / FastAPI / asyncpg / httpx / MiniMax-Text-01 / Next.js App Router / TypeScript / Tailwind CSS

---

## 文件清单

### 新建
| 文件 | 职责 |
|------|------|
| `src/deepalpha/domain/earnings_call/__init__.py` | 模块入口 |
| `src/deepalpha/domain/earnings_call/models.py` | 三个领域模型 |
| `src/deepalpha/domain/earnings_call/protocols.py` | Loader / Repo 抽象接口 |
| `src/deepalpha/infrastructure/providers/fmp/loaders/earnings_call_loader.py` | FMP 数据拉取 |
| `src/deepalpha/infrastructure/providers/minimax/earnings_call_processor.py` | MiniMax 四个处理函数 |
| `src/deepalpha/infrastructure/db/earnings_call_repo.py` | PG 缓存读写 |
| `src/deepalpha/application/services/earnings_call_service.py` | 业务编排 |
| `src/deepalpha/interface/web/routers/earnings_call.py` | FastAPI 路由 |
| `tests/unit/domain/earnings_call/__init__.py` | 测试包 |
| `tests/unit/domain/earnings_call/test_models.py` | domain 模型测试 |
| `tests/unit/providers/fmp/loaders/test_earnings_call_loader.py` | loader 测试 |
| `tests/unit/providers/minimax/test_earnings_call_processor.py` | MiniMax 函数测试 |
| `tests/unit/infrastructure/db/test_earnings_call_repo.py` | repo 协议测试 |
| `tests/unit/application/services/test_earnings_call_service.py` | service 测试 |
| `frontend/app/(pages)/earnings/page.tsx` | 前端页面 |

### 修改
| 文件 | 变更 |
|------|------|
| `src/deepalpha/application/agent/tools.py` | `Services` 新增 `earnings_call` 字段 |
| `src/deepalpha/interface/web/deps.py` | 注入 `EarningsCallService` |
| `src/deepalpha/interface/web/app.py` | 注册 `earnings_call.router` |
| `frontend/lib/types.ts` | 新增两个 TypeScript 接口 |
| `frontend/lib/api.ts` | 新增两个 API 函数 |
| `frontend/components/layout/AppShell.tsx` | 导航栏新增「财报日历」链接 |

---

## Task 1: Domain 层 — models + protocols

**Files:**
- Create: `src/deepalpha/domain/earnings_call/__init__.py`
- Create: `src/deepalpha/domain/earnings_call/models.py`
- Create: `src/deepalpha/domain/earnings_call/protocols.py`
- Create: `tests/unit/domain/earnings_call/__init__.py`
- Create: `tests/unit/domain/earnings_call/test_models.py`

- [ ] **Step 1.1: 写失败测试**

```python
# tests/unit/domain/earnings_call/test_models.py
import datetime
from deepalpha.domain.earnings_call.models import (
    EarningsCallEvent,
    EarningsCallTranscript,
    EarningsCallDetail,
)


def test_earnings_call_event_fields():
    event = EarningsCallEvent(
        symbol="AAPL",
        date=datetime.date(2026, 6, 14),
        year=2026,
        quarter=2,
        has_transcript=True,
    )
    assert event.symbol == "AAPL"
    assert event.quarter == 2
    assert event.has_transcript is True


def test_earnings_call_transcript_fields():
    t = EarningsCallTranscript(
        symbol="AAPL",
        year=2026,
        quarter=2,
        date=datetime.date(2026, 6, 14),
        content="Good morning everyone...",
    )
    assert t.content == "Good morning everyone..."


def test_earnings_call_detail_fields():
    d = EarningsCallDetail(
        symbol="AAPL",
        year=2026,
        quarter=2,
        date=datetime.date(2026, 6, 14),
        company_name="苹果公司",
        description_zh="苹果是全球最大科技公司之一",
        products_zh="iPhone, Mac, iPad, Apple Watch",
        summary_zh="本季度营收创历史新高...",
        transcript_zh="大家好，欢迎参加苹果公司...",
        translated_at=datetime.datetime(2026, 6, 14, 10, 0, 0),
    )
    assert d.company_name == "苹果公司"
```

- [ ] **Step 1.2: 运行测试，确认失败**

```bash
uv run pytest tests/unit/domain/earnings_call/test_models.py -v
```

预期：`ModuleNotFoundError: No module named 'deepalpha.domain.earnings_call'`

- [ ] **Step 1.3: 创建 `__init__.py` 文件（两个）**

```python
# src/deepalpha/domain/earnings_call/__init__.py
# （空文件）
```

```python
# tests/unit/domain/earnings_call/__init__.py
# （空文件）
```

- [ ] **Step 1.4: 创建 models.py**

```python
# src/deepalpha/domain/earnings_call/models.py
import datetime

from pydantic import BaseModel, Field


class EarningsCallEvent(BaseModel):
    """日历上某场财报电话会议（可能尚未召开）"""

    symbol: str = Field(title="股票代码")
    date: datetime.date = Field(title="会议日期")
    year: int = Field(title="财年")
    quarter: int = Field(title="季度", ge=1, le=4)
    has_transcript: bool = Field(title="是否已有原文")


class EarningsCallTranscript(BaseModel):
    """FMP API 返回的英文原文"""

    symbol: str = Field(title="股票代码")
    year: int = Field(title="财年")
    quarter: int = Field(title="季度")
    date: datetime.date = Field(title="会议日期")
    content: str = Field(title="英文全文")


class EarningsCallDetail(BaseModel):
    """完整处理结果，翻译后缓存到 PostgreSQL"""

    symbol: str = Field(title="股票代码")
    year: int = Field(title="财年")
    quarter: int = Field(title="季度")
    date: datetime.date = Field(title="会议日期")
    company_name: str = Field(title="公司名称")
    description_zh: str = Field(title="公司简介（中文）")
    products_zh: str = Field(title="主要产品（中文）")
    summary_zh: str = Field(title="AI 摘要（中文，约400字）")
    transcript_zh: str = Field(title="完整原文中文翻译")
    translated_at: datetime.datetime = Field(title="翻译时间")
```

- [ ] **Step 1.5: 创建 protocols.py**

```python
# src/deepalpha/domain/earnings_call/protocols.py
import datetime
from typing import Protocol

from deepalpha.domain.earnings_call.models import (
    EarningsCallDetail,
    EarningsCallEvent,
    EarningsCallTranscript,
)


class AbstractEarningsCallLoader(Protocol):
    async def get_events(
        self, start: datetime.date, end: datetime.date
    ) -> list[EarningsCallEvent]: ...

    async def get_transcript(
        self, symbol: str, year: int, quarter: int
    ) -> EarningsCallTranscript | None: ...


class AbstractEarningsCallRepo(Protocol):
    async def get_detail(
        self, symbol: str, year: int, quarter: int
    ) -> EarningsCallDetail | None: ...

    async def save_detail(self, detail: EarningsCallDetail) -> None: ...
```

- [ ] **Step 1.6: 运行测试，确认通过**

```bash
uv run pytest tests/unit/domain/earnings_call/test_models.py -v
```

预期：3 passed

- [ ] **Step 1.7: Commit**

```bash
git add src/deepalpha/domain/earnings_call/ tests/unit/domain/earnings_call/
git commit -m "feat(earnings-call): add domain models and protocols"
```

---

## Task 2: FMP EarningsCallLoader

**Files:**
- Create: `src/deepalpha/infrastructure/providers/fmp/loaders/earnings_call_loader.py`
- Create: `tests/unit/providers/fmp/loaders/test_earnings_call_loader.py`

> ⚠️ **注意**：FMP transcript 端点路径 `/stable/earning-call-transcript` 需在实际 API key 下验证。若返回 404，请查阅 FMP 文档确认正确路径。

- [ ] **Step 2.1: 写失败测试**

```python
# tests/unit/providers/fmp/loaders/test_earnings_call_loader.py
import datetime

import pytest
from pytest_httpx import HTTPXMock

from deepalpha.domain.earnings_call.models import EarningsCallEvent, EarningsCallTranscript
from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient
from deepalpha.infrastructure.providers.fmp.config import FMPConfig
from deepalpha.infrastructure.providers.fmp.loaders.earnings_call_loader import (
    FMPEarningsCallLoader,
)

START = datetime.date(2026, 6, 1)
END = datetime.date(2026, 6, 30)


@pytest.fixture
def client():
    return FMPAsyncClient(FMPConfig(api_key="test-key"))


@pytest.mark.asyncio
async def test_get_events_returns_list(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[
        {"symbol": "AAPL", "date": "2026-06-14", "epsEstimated": None, "eps": None},
        {"symbol": "FAKECO", "date": "2026-06-14"},  # 不在 nasdaq100，会被过滤
    ])
    loader = FMPEarningsCallLoader(client, allowed_tickers=frozenset(["AAPL", "MSFT"]))
    events = await loader.get_events(START, END)
    assert len(events) == 1
    assert isinstance(events[0], EarningsCallEvent)
    assert events[0].symbol == "AAPL"
    assert events[0].has_transcript is True  # 2026-06-14 <= today (2026-06-13 在测试中视为过去)
    await client.aclose()


@pytest.mark.asyncio
async def test_get_transcript_returns_model(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[{
        "symbol": "AAPL",
        "date": "2026-05-01",
        "year": 2026,
        "quarter": 2,
        "content": "Good morning everyone, welcome to Apple's Q2 2026 earnings call.",
    }])
    loader = FMPEarningsCallLoader(client, allowed_tickers=frozenset(["AAPL"]))
    result = await loader.get_transcript("AAPL", 2026, 2)
    assert isinstance(result, EarningsCallTranscript)
    assert result.symbol == "AAPL"
    assert result.quarter == 2
    assert "Apple" in result.content
    await client.aclose()


@pytest.mark.asyncio
async def test_get_transcript_returns_none_on_empty(httpx_mock: HTTPXMock, client):
    httpx_mock.add_response(json=[])
    loader = FMPEarningsCallLoader(client, allowed_tickers=frozenset(["AAPL"]))
    result = await loader.get_transcript("AAPL", 2026, 3)
    assert result is None
    await client.aclose()
```

- [ ] **Step 2.2: 运行测试，确认失败**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_earnings_call_loader.py -v
```

预期：`ModuleNotFoundError: No module named '...earnings_call_loader'`

- [ ] **Step 2.3: 实现 earnings_call_loader.py**

```python
# src/deepalpha/infrastructure/providers/fmp/loaders/earnings_call_loader.py
import datetime

from deepalpha.domain.earnings_call.models import EarningsCallEvent, EarningsCallTranscript
from deepalpha.infrastructure.providers.base import BaseLoader


def _date_to_year_quarter(d: datetime.date) -> tuple[int, int]:
    """将日期转换为（财年, 季度），以日历季度计。"""
    quarter = (d.month - 1) // 3 + 1
    return d.year, quarter


class FMPEarningsCallLoader(BaseLoader):
    """FMP 财报电话会议数据加载器。"""

    def __init__(self, client, allowed_tickers: frozenset[str]) -> None:
        super().__init__(client)
        self._allowed = allowed_tickers

    async def get_events(
        self, start: datetime.date, end: datetime.date
    ) -> list[EarningsCallEvent]:
        """获取日期范围内的财报电话会议事件，过滤到 allowed_tickers。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            EarningsCallEvent 列表，仅包含 allowed_tickers 中的公司
        """
        today = datetime.date.today()
        records = await self._get_list(
            "/stable/earnings-calendar", **{"from": str(start), "to": str(end)}
        )
        events = []
        for r in records:
            symbol = r.get("symbol", "")
            if symbol not in self._allowed:
                continue
            raw_date = r.get("date", "")
            if not raw_date:
                continue
            try:
                d = datetime.date.fromisoformat(raw_date)
            except ValueError:
                continue
            year, quarter = _date_to_year_quarter(d)
            events.append(
                EarningsCallEvent(
                    symbol=symbol,
                    date=d,
                    year=year,
                    quarter=quarter,
                    has_transcript=d <= today,
                )
            )
        return events

    async def get_transcript(
        self, symbol: str, year: int, quarter: int
    ) -> EarningsCallTranscript | None:
        """获取指定公司、财年、季度的电话会议原文。

        Args:
            symbol: 股票代码
            year: 财年
            quarter: 季度 1-4

        Returns:
            EarningsCallTranscript，若 FMP 无数据则返回 None
        """
        records = await self._get_list(
            "/stable/earning-call-transcript",
            symbol=symbol,
            year=year,
            quarter=quarter,
        )
        if not records:
            return None
        r = records[0]
        raw_date = r.get("date", "")
        try:
            d = datetime.date.fromisoformat(raw_date[:10])
        except (ValueError, TypeError):
            d = datetime.date.today()
        return EarningsCallTranscript(
            symbol=r.get("symbol", symbol),
            year=r.get("year", year),
            quarter=r.get("quarter", quarter),
            date=d,
            content=r.get("content", ""),
        )
```

- [ ] **Step 2.4: 运行测试，确认通过**

```bash
uv run pytest tests/unit/providers/fmp/loaders/test_earnings_call_loader.py -v
```

预期：3 passed

- [ ] **Step 2.5: Commit**

```bash
git add src/deepalpha/infrastructure/providers/fmp/loaders/earnings_call_loader.py \
        tests/unit/providers/fmp/loaders/test_earnings_call_loader.py
git commit -m "feat(earnings-call): add FMPEarningsCallLoader"
```

---

## Task 3: MiniMax 财报处理器

**Files:**
- Create: `src/deepalpha/infrastructure/providers/minimax/earnings_call_processor.py`
- Create: `tests/unit/providers/minimax/test_earnings_call_processor.py`

- [ ] **Step 3.1: 写失败测试**

```python
# tests/unit/providers/minimax/test_earnings_call_processor.py
import pytest
from pytest_httpx import HTTPXMock

from deepalpha.infrastructure.providers.minimax.earnings_call_processor import (
    translate_description,
    extract_products,
    summarize_transcript,
    translate_transcript,
)

_FAKE_RESPONSE = {
    "choices": [{"message": {"content": "翻译结果文本"}}]
}


@pytest.mark.asyncio
async def test_translate_description_returns_string(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=_FAKE_RESPONSE)
    result = await translate_description("fake-key", "Apple Inc. designs iPhones.")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_translate_description_fallback_on_empty_key():
    result = await translate_description("", "Apple Inc.")
    assert isinstance(result, str)  # 返回原文兜底


@pytest.mark.asyncio
async def test_extract_products_returns_string(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=_FAKE_RESPONSE)
    result = await extract_products("fake-key", "Apple makes iPhone, Mac, and iPad.")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_summarize_transcript_returns_string(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=_FAKE_RESPONSE)
    result = await summarize_transcript("fake-key", "AAPL", "Good morning everyone...")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_translate_transcript_chunks_long_text(httpx_mock: HTTPXMock):
    # 超过 8000 字时应分两段调用
    long_text = "word " * 2000  # ~10000 chars
    httpx_mock.add_response(json=_FAKE_RESPONSE)
    httpx_mock.add_response(json=_FAKE_RESPONSE)
    result = await translate_transcript("fake-key", long_text)
    assert isinstance(result, str)
    assert len(httpx_mock.get_requests()) == 2
```

- [ ] **Step 3.2: 运行测试，确认失败**

```bash
uv run pytest tests/unit/providers/minimax/test_earnings_call_processor.py -v
```

预期：`ModuleNotFoundError`

- [ ] **Step 3.3: 实现 earnings_call_processor.py**

```python
# src/deepalpha/infrastructure/providers/minimax/earnings_call_processor.py
"""
MiniMax AI 财报电话会议处理器

提供四个独立函数：
- translate_description: 翻译公司简介
- extract_products: 提炼主要产品
- summarize_transcript: 生成约 400 字摘要
- translate_transcript: 全文翻译（超长时分段处理）
"""
import logging

import httpx

logger = logging.getLogger(__name__)

_API_URL = "https://api.minimax.chat/v1/chat/completions"
_MODEL = "MiniMax-Text-01"
_CHUNK_SIZE = 8000  # 单次翻译最大字符数


async def _chat(api_key: str, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=90.0, trust_env=False) as client:
        resp = await client.post(
            _API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": _MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 4000,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


async def translate_description(api_key: str, description: str) -> str:
    """将 FMP 公司简介（英文）翻译为中文。

    无 api_key 时返回原文兜底。
    """
    if not api_key or not description:
        return description or ""
    prompt = (
        f"请将以下美股公司简介翻译为流畅的中文，保留所有关键信息，直接输出译文：\n\n{description[:3000]}"
    )
    try:
        return await _chat(api_key, prompt)
    except Exception as exc:
        logger.warning("translate_description 失败: %s", exc)
        return description[:500]


async def extract_products(api_key: str, description: str) -> str:
    """从英文公司简介中提炼主要产品/服务列表（中文，逗号分隔）。

    无 api_key 时返回空字符串。
    """
    if not api_key or not description:
        return ""
    prompt = (
        "请从以下公司简介中提炼出该公司的主要产品和服务，用中文列出，以逗号分隔，"
        "不超过 10 项，直接输出结果，不要前缀或解释：\n\n"
        f"{description[:3000]}"
    )
    try:
        return await _chat(api_key, prompt)
    except Exception as exc:
        logger.warning("extract_products 失败: %s", exc)
        return ""


async def summarize_transcript(api_key: str, symbol: str, content: str) -> str:
    """从财报电话会议原文生成约 400 字中文摘要。

    无 api_key 时返回截断原文。
    """
    if not api_key:
        return content[:400]
    prompt = (
        f"以下是 {symbol} 财报电话会议原文（英文）。\n"
        "请用中文撰写一份约 400 字的摘要，要求：\n"
        "1. 包含本季度核心财务数据（营收、利润、EPS）\n"
        "2. 管理层重点强调的战略方向\n"
        "3. 下季度业绩指引\n"
        "4. 语言专业简洁，直接输出摘要正文\n\n"
        f"{content[:_CHUNK_SIZE]}"
    )
    try:
        return await _chat(api_key, prompt)
    except Exception as exc:
        logger.warning("summarize_transcript 失败 [%s]: %s", symbol, exc)
        return content[:400]


async def translate_transcript(api_key: str, content: str) -> str:
    """将财报电话会议全文翻译为中文。

    超过 _CHUNK_SIZE 字符时分段翻译后拼接。
    无 api_key 时返回原文。
    """
    if not api_key:
        return content

    chunks = [content[i: i + _CHUNK_SIZE] for i in range(0, len(content), _CHUNK_SIZE)]
    translated_parts: list[str] = []

    for i, chunk in enumerate(chunks):
        prompt = (
            "请将以下财报电话会议原文（英文）翻译为中文，保留说话人称谓，"
            "语言专业准确，直接输出译文：\n\n"
            f"{chunk}"
        )
        try:
            part = await _chat(api_key, prompt)
            translated_parts.append(part)
        except Exception as exc:
            logger.warning("translate_transcript 第 %d 段失败: %s", i + 1, exc)
            translated_parts.append(chunk)  # 降级为原文

    return "\n\n".join(translated_parts)
```

- [ ] **Step 3.4: 运行测试，确认通过**

```bash
uv run pytest tests/unit/providers/minimax/test_earnings_call_processor.py -v
```

预期：5 passed

- [ ] **Step 3.5: Commit**

```bash
git add src/deepalpha/infrastructure/providers/minimax/earnings_call_processor.py \
        tests/unit/providers/minimax/test_earnings_call_processor.py
git commit -m "feat(earnings-call): add MiniMax earnings call processor"
```

---

## Task 4: EarningsCallRepo（PostgreSQL 缓存）

**Files:**
- Create: `src/deepalpha/infrastructure/db/earnings_call_repo.py`
- Create: `tests/unit/infrastructure/db/test_earnings_call_repo.py`

- [ ] **Step 4.1: 写协议一致性测试**

```python
# tests/unit/infrastructure/db/test_earnings_call_repo.py
from deepalpha.domain.earnings_call.protocols import AbstractEarningsCallRepo
from deepalpha.infrastructure.db.earnings_call_repo import EarningsCallRepo


def test_earnings_call_repo_satisfies_protocol():
    repo = EarningsCallRepo.__new__(EarningsCallRepo)
    assert isinstance(repo, AbstractEarningsCallRepo)
```

- [ ] **Step 4.2: 运行测试，确认失败**

```bash
uv run pytest tests/unit/infrastructure/db/test_earnings_call_repo.py -v
```

预期：`ModuleNotFoundError`

- [ ] **Step 4.3: 实现 earnings_call_repo.py**

```python
# src/deepalpha/infrastructure/db/earnings_call_repo.py
"""PostgreSQL 缓存仓库：存储已翻译的财报电话会议详情。"""
import datetime
import logging

import asyncpg

from deepalpha.domain.earnings_call.models import EarningsCallDetail

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS earnings_call_details (
    symbol          TEXT        NOT NULL,
    year            INT         NOT NULL,
    quarter         INT         NOT NULL,
    date            DATE        NOT NULL,
    company_name    TEXT        NOT NULL,
    description_zh  TEXT        NOT NULL,
    products_zh     TEXT        NOT NULL,
    summary_zh      TEXT        NOT NULL,
    transcript_zh   TEXT        NOT NULL,
    translated_at   TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (symbol, year, quarter)
);
"""

_UPSERT = """
INSERT INTO earnings_call_details
    (symbol, year, quarter, date, company_name,
     description_zh, products_zh, summary_zh, transcript_zh, translated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
ON CONFLICT (symbol, year, quarter) DO NOTHING;
"""

_SELECT = """
SELECT symbol, year, quarter, date, company_name,
       description_zh, products_zh, summary_zh, transcript_zh, translated_at
FROM earnings_call_details
WHERE symbol = $1 AND year = $2 AND quarter = $3;
"""


class EarningsCallRepo:
    """PostgreSQL 财报电话会议详情缓存仓库。"""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None  # type: ignore[type-arg]

    async def initialize(self) -> None:
        """创建缓存表（如不存在）。"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._dsn)
        async with self._pool.acquire() as conn:
            await conn.execute(_CREATE_TABLE)

    async def get_detail(
        self, symbol: str, year: int, quarter: int
    ) -> EarningsCallDetail | None:
        """查询缓存。命中返回 EarningsCallDetail，未命中返回 None。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(_SELECT, symbol, year, quarter)
        if row is None:
            return None
        return EarningsCallDetail(
            symbol=row["symbol"],
            year=row["year"],
            quarter=row["quarter"],
            date=row["date"],
            company_name=row["company_name"],
            description_zh=row["description_zh"],
            products_zh=row["products_zh"],
            summary_zh=row["summary_zh"],
            transcript_zh=row["transcript_zh"],
            translated_at=row["translated_at"].replace(tzinfo=None),
        )

    async def save_detail(self, detail: EarningsCallDetail) -> None:
        """写入缓存（已存在则跳过，不覆盖）。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                _UPSERT,
                detail.symbol,
                detail.year,
                detail.quarter,
                detail.date,
                detail.company_name,
                detail.description_zh,
                detail.products_zh,
                detail.summary_zh,
                detail.transcript_zh,
                detail.translated_at,
            )
```

- [ ] **Step 4.4: 运行测试，确认通过**

```bash
uv run pytest tests/unit/infrastructure/db/test_earnings_call_repo.py -v
```

预期：1 passed

- [ ] **Step 4.5: Commit**

```bash
git add src/deepalpha/infrastructure/db/earnings_call_repo.py \
        tests/unit/infrastructure/db/test_earnings_call_repo.py
git commit -m "feat(earnings-call): add EarningsCallRepo with PG caching"
```

---

## Task 5: EarningsCallService

**Files:**
- Create: `src/deepalpha/application/services/earnings_call_service.py`
- Create: `tests/unit/application/services/test_earnings_call_service.py`

- [ ] **Step 5.1: 写失败测试**

```python
# tests/unit/application/services/test_earnings_call_service.py
import datetime
from unittest.mock import AsyncMock

import pytest

from deepalpha.application.services.earnings_call_service import EarningsCallService
from deepalpha.domain.company.models import CompanyProfile
from deepalpha.domain.earnings_call.models import (
    EarningsCallDetail,
    EarningsCallEvent,
    EarningsCallTranscript,
)

_TODAY = datetime.date(2026, 6, 13)
_EVENT = EarningsCallEvent(
    symbol="AAPL", date=_TODAY, year=2026, quarter=2, has_transcript=True
)
_TRANSCRIPT = EarningsCallTranscript(
    symbol="AAPL", year=2026, quarter=2, date=_TODAY,
    content="Good morning everyone...",
)
_PROFILE = CompanyProfile(
    symbol="AAPL",
    companyName="Apple Inc.",
    description="Apple Inc. designs and sells iPhones.",
    sector="Technology",
    industry="Consumer Electronics",
)
_DETAIL = EarningsCallDetail(
    symbol="AAPL", year=2026, quarter=2, date=_TODAY,
    company_name="Apple Inc.",
    description_zh="苹果公司简介",
    products_zh="iPhone, Mac, iPad",
    summary_zh="本季度摘要",
    transcript_zh="大家好...",
    translated_at=datetime.datetime(2026, 6, 13, 10, 0),
)


@pytest.fixture
def mocks():
    loader = AsyncMock()
    repo = AsyncMock()
    company_loader = AsyncMock()
    return loader, repo, company_loader


@pytest.mark.asyncio
async def test_get_calendar_groups_by_date(mocks):
    loader, repo, company_loader = mocks
    loader.get_events.return_value = [_EVENT]
    svc = EarningsCallService(
        loader=loader, repo=repo, company_loader=company_loader, minimax_api_key=""
    )
    result = await svc.get_calendar(
        datetime.date(2026, 6, 1), datetime.date(2026, 6, 30)
    )
    assert "2026-06-13" in result
    assert result["2026-06-13"][0].symbol == "AAPL"


@pytest.mark.asyncio
async def test_get_detail_returns_cached(mocks):
    loader, repo, company_loader = mocks
    repo.get_detail.return_value = _DETAIL
    svc = EarningsCallService(
        loader=loader, repo=repo, company_loader=company_loader, minimax_api_key=""
    )
    result = await svc.get_detail("AAPL", 2026, 2)
    assert result.symbol == "AAPL"
    loader.get_transcript.assert_not_called()


@pytest.mark.asyncio
async def test_get_detail_raises_404_on_no_transcript(mocks):
    from fastapi import HTTPException
    loader, repo, company_loader = mocks
    repo.get_detail.return_value = None
    loader.get_transcript.return_value = None  # 无 transcript（未来场次）
    svc = EarningsCallService(
        loader=loader, repo=repo, company_loader=company_loader, minimax_api_key=""
    )
    with pytest.raises(HTTPException) as exc_info:
        await svc.get_detail("AAPL", 2026, 3)
    assert exc_info.value.status_code == 404
```

- [ ] **Step 5.2: 运行测试，确认失败**

```bash
uv run pytest tests/unit/application/services/test_earnings_call_service.py -v
```

预期：`ModuleNotFoundError`

- [ ] **Step 5.3: 实现 earnings_call_service.py**

```python
# src/deepalpha/application/services/earnings_call_service.py
"""财报电话会议业务服务：编排数据加载、翻译和缓存。"""
import asyncio
import datetime
import logging

from fastapi import HTTPException

from deepalpha.domain.earnings_call.models import EarningsCallDetail, EarningsCallEvent
from deepalpha.domain.earnings_call.protocols import (
    AbstractEarningsCallLoader,
    AbstractEarningsCallRepo,
)
from deepalpha.infrastructure.providers.minimax.earnings_call_processor import (
    extract_products,
    summarize_transcript,
    translate_description,
    translate_transcript,
)

logger = logging.getLogger(__name__)


class EarningsCallService:
    """财报电话会议服务，编排 FMP 数据加载、MiniMax 翻译和 PG 缓存。"""

    def __init__(
        self,
        loader: AbstractEarningsCallLoader,
        repo: AbstractEarningsCallRepo,
        company_loader,  # FMPCompanyLoader，AbstractCompanyLoader Protocol
        minimax_api_key: str,
    ) -> None:
        self._loader = loader
        self._repo = repo
        self._company_loader = company_loader
        self._api_key = minimax_api_key

    async def get_calendar(
        self, start: datetime.date, end: datetime.date
    ) -> dict[str, list[EarningsCallEvent]]:
        """获取日期范围内的财报日历，按日期字符串分组。

        Returns:
            {"2026-06-14": [EarningsCallEvent, ...], ...}
        """
        events = await self._loader.get_events(start, end)
        grouped: dict[str, list[EarningsCallEvent]] = {}
        for e in events:
            key = str(e.date)
            grouped.setdefault(key, []).append(e)
        return grouped

    async def get_detail(
        self, symbol: str, year: int, quarter: int
    ) -> EarningsCallDetail:
        """获取财报电话会议完整详情。

        优先返回 PG 缓存；缓存未命中时拉取数据、翻译并缓存。

        Raises:
            HTTPException 404: transcript 不存在（未来场次或 FMP 无数据）
        """
        # 1. 尝试缓存
        cached = await self._repo.get_detail(symbol, year, quarter)
        if cached is not None:
            return cached

        # 2. 拉取 transcript
        transcript = await self._loader.get_transcript(symbol, year, quarter)
        if transcript is None:
            raise HTTPException(
                status_code=404,
                detail=f"{symbol} Q{quarter} {year} 暂无电话会议原文",
            )

        # 3. 拉取公司信息
        profile = await self._company_loader.get_profile(symbol)

        # 4. MiniMax 处理（description 翻译 + 产品提炼并发；摘要 + 全文翻译并发）
        logger.info("开始翻译 %s Q%d %d，原文长度 %d 字符", symbol, quarter, year, len(transcript.content))
        description_zh, products_zh = await asyncio.gather(
            translate_description(self._api_key, profile.description or ""),
            extract_products(self._api_key, profile.description or ""),
        )
        summary_zh, transcript_zh = await asyncio.gather(
            summarize_transcript(self._api_key, symbol, transcript.content),
            translate_transcript(self._api_key, transcript.content),
        )

        # 5. 构建并缓存
        detail = EarningsCallDetail(
            symbol=symbol,
            year=year,
            quarter=quarter,
            date=transcript.date,
            company_name=profile.companyName or symbol,
            description_zh=description_zh,
            products_zh=products_zh,
            summary_zh=summary_zh,
            transcript_zh=transcript_zh,
            translated_at=datetime.datetime.utcnow(),
        )
        await self._repo.save_detail(detail)
        return detail
```

- [ ] **Step 5.4: 运行测试，确认通过**

```bash
uv run pytest tests/unit/application/services/test_earnings_call_service.py -v
```

预期：3 passed

- [ ] **Step 5.5: Commit**

```bash
git add src/deepalpha/application/services/earnings_call_service.py \
        tests/unit/application/services/test_earnings_call_service.py
git commit -m "feat(earnings-call): add EarningsCallService"
```

---

## Task 6: FastAPI 路由 + 依赖注入 + 注册

**Files:**
- Create: `src/deepalpha/interface/web/routers/earnings_call.py`
- Modify: `src/deepalpha/application/agent/tools.py` (Services class)
- Modify: `src/deepalpha/interface/web/deps.py`
- Modify: `src/deepalpha/interface/web/app.py`

- [ ] **Step 6.1: 创建 earnings_call.py router**

```python
# src/deepalpha/interface/web/routers/earnings_call.py
"""财报电话会议 API 路由"""
import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from deepalpha.application.agent.tools import Services
from deepalpha.application.services.earnings_call_service import EarningsCallService
from deepalpha.domain.earnings_call.models import EarningsCallDetail, EarningsCallEvent
from deepalpha.interface.web.deps import get_services

router = APIRouter(prefix="/earnings-call", tags=["earnings-call"])


def _svc(svc: Annotated[Services, Depends(get_services)]) -> EarningsCallService:
    return svc.earnings_call


@router.get("/calendar", response_model=dict[str, list[EarningsCallEvent]])
async def get_earnings_calendar(
    start: datetime.date = Query(..., description="开始日期，格式 YYYY-MM-DD"),
    end: datetime.date = Query(..., description="结束日期，格式 YYYY-MM-DD"),
    svc: Annotated[EarningsCallService, Depends(_svc)] = ...,
) -> dict[str, list[EarningsCallEvent]]:
    """获取日期范围内纳斯达克100成分股的财报电话会议，按日期分组返回。"""
    return await svc.get_calendar(start, end)


@router.get("/detail/{symbol}", response_model=EarningsCallDetail)
async def get_earnings_call_detail(
    symbol: str,
    year: int = Query(..., description="财年，如 2026"),
    quarter: int = Query(..., ge=1, le=4, description="季度 1-4"),
    svc: Annotated[EarningsCallService, Depends(_svc)] = ...,
) -> EarningsCallDetail:
    """获取指定公司财报电话会议完整详情（含中文翻译）。首次请求约 30-90 秒。"""
    return await svc.get_detail(symbol, year, quarter)
```

- [ ] **Step 6.2: 在 Services 中新增 earnings_call 字段**

修改 `src/deepalpha/application/agent/tools.py`，在 `Services.__init__` 末尾添加：

```python
# 在 TYPE_CHECKING 块中添加：
from deepalpha.application.services.earnings_call_service import EarningsCallService

# 在 Services.__init__ 参数列表末尾添加：
earnings_call: EarningsCallService,

# 在 __init__ 方法体末尾添加：
self.earnings_call = earnings_call
```

完整修改后的 `Services.__init__` 签名：

```python
class Services:
    def __init__(
        self,
        concept: ConceptService,
        market: MarketService,
        financial: FinancialService,
        analyst: AnalystService,
        company: CompanyService,
        news: NewsService,
        performance: PerformanceService,
        insider: InsiderService,
        calendar: CalendarService,
        earnings_call: "EarningsCallService",
    ) -> None:
        self.concept = concept
        self.market = market
        self.financial = financial
        self.analyst = analyst
        self.company = company
        self.news = news
        self.performance = performance
        self.insider = insider
        self.calendar = calendar
        self.earnings_call = earnings_call
```

- [ ] **Step 6.3: 在 deps.py 中注入 EarningsCallService**

在 `src/deepalpha/interface/web/deps.py` 中添加如下 import：

```python
import yaml
from deepalpha.application.services.earnings_call_service import EarningsCallService
from deepalpha.infrastructure.db.earnings_call_repo import EarningsCallRepo
from deepalpha.infrastructure.providers.fmp.loaders.earnings_call_loader import FMPEarningsCallLoader
```

在 `lifespan` 函数中，`fmp = FMPAsyncClient(fmp_cfg)` 之后，`_services = Services(...)` 之前添加：

```python
    # 加载纳斯达克100名单
    with open("config/nasdaq100_tickers.yaml") as f:
        nasdaq100 = frozenset(yaml.safe_load(f)["tickers"])

    # 初始化 EarningsCallRepo
    earnings_call_repo = EarningsCallRepo(cfg.asyncpg_dsn())
    earnings_call_repo._pool = _pool
    await earnings_call_repo.initialize()
```

在 `_services = Services(...)` 调用中添加最后一个参数：

```python
        earnings_call=EarningsCallService(
            loader=FMPEarningsCallLoader(fmp, allowed_tickers=nasdaq100),
            repo=earnings_call_repo,
            company_loader=FMPCompanyLoader(fmp),
            minimax_api_key=cfg.minimax_api_key,
        ),
```

- [ ] **Step 6.4: 在 app.py 中注册路由**

修改 `src/deepalpha/interface/web/app.py`：

```python
from deepalpha.interface.web.routers import (
    agent, analyst, calendar, company,
    concept, earnings_call, financial, insider, market, news, signal_radar,
)

# 在现有 include_router 调用末尾添加：
app.include_router(earnings_call.router, prefix="/api/v1")
```

- [ ] **Step 6.5: 启动服务器验证路由存在**

```bash
uv run fastapi dev src/deepalpha/interface/web/app.py
```

在浏览器访问 `http://localhost:8000/docs`，确认 `earnings-call` 分类下有两个端点：
- `GET /api/v1/earnings-call/calendar`
- `GET /api/v1/earnings-call/detail/{symbol}`

按 Ctrl+C 停止服务器。

- [ ] **Step 6.6: 运行全量单元测试**

```bash
uv run pytest tests/unit/ -v --tb=short
```

预期：所有已有测试 + 新增测试全部通过，无失败。

- [ ] **Step 6.7: Commit**

```bash
git add src/deepalpha/interface/web/routers/earnings_call.py \
        src/deepalpha/application/agent/tools.py \
        src/deepalpha/interface/web/deps.py \
        src/deepalpha/interface/web/app.py
git commit -m "feat(earnings-call): add FastAPI router and wire dependencies"
```

---

## Task 7: 前端类型定义 + API 函数

**Files:**
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/lib/api.ts`

- [ ] **Step 7.1: 在 types.ts 末尾追加两个接口**

在 `frontend/lib/types.ts` 文件末尾添加：

```typescript
export interface EarningsCallEvent {
  symbol: string
  date: string           // "YYYY-MM-DD"
  year: number
  quarter: number        // 1-4
  has_transcript: boolean
}

export interface EarningsCallDetail {
  symbol: string
  year: number
  quarter: number
  date: string
  company_name: string
  description_zh: string
  products_zh: string    // 逗号分隔的产品列表
  summary_zh: string
  transcript_zh: string
  translated_at: string
}
```

- [ ] **Step 7.2: 在 api.ts 末尾追加两个函数**

在 `frontend/lib/api.ts` 文件末尾添加：

```typescript
import type { EarningsCallEvent, EarningsCallDetail } from './types'

export async function getEarningsCalendar(
  start: string,
  end: string,
): Promise<Record<string, EarningsCallEvent[]>> {
  const params = new URLSearchParams({ start, end })
  const res = await fetch(
    `${backendUrl()}/api/v1/earnings-call/calendar?${params}`,
    { cache: 'no-store' },
  )
  if (!res.ok) throw new Error(`earnings-call/calendar failed: ${res.status}`)
  return res.json()
}

export async function getEarningsCallDetail(
  symbol: string,
  year: number,
  quarter: number,
): Promise<EarningsCallDetail> {
  const params = new URLSearchParams({ year: String(year), quarter: String(quarter) })
  const res = await fetch(
    `${backendUrl()}/api/v1/earnings-call/detail/${encodeURIComponent(symbol)}?${params}`,
    { cache: 'no-store' },
  )
  if (!res.ok) throw new Error(`earnings-call/detail failed: ${res.status}`)
  return res.json()
}
```

- [ ] **Step 7.3: 确认 TypeScript 无报错**

```bash
cd frontend && pnpm build 2>&1 | head -30
```

预期：无 TypeScript 类型错误（可能有其他 lint 警告，非阻断）。

- [ ] **Step 7.4: Commit**

```bash
git add frontend/lib/types.ts frontend/lib/api.ts
git commit -m "feat(earnings-call): add frontend types and API functions"
```

---

## Task 8: 前端 /earnings 页面

**Files:**
- Create: `frontend/app/(pages)/earnings/page.tsx`

- [ ] **Step 8.1: 创建 page.tsx**

```tsx
// frontend/app/(pages)/earnings/page.tsx
'use client'

import { useCallback, useEffect, useState } from 'react'
import { getEarningsCalendar, getEarningsCallDetail } from '@/lib/api'
import type { EarningsCallEvent, EarningsCallDetail } from '@/lib/types'

function today() {
  return new Date()
}

function formatDate(y: number, m: number, d: number): string {
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate()
}

function firstDayOfWeek(year: number, month: number): number {
  // 0=Sun, 1=Mon ... 返回 0-based 周一起始（0=Mon）
  const day = new Date(year, month - 1, 1).getDay()
  return (day + 6) % 7 // 转为周一=0
}

export default function EarningsPage() {
  const now = today()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [calendarData, setCalendarData] = useState<Record<string, EarningsCallEvent[]>>({})
  const [calendarLoading, setCalendarLoading] = useState(false)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [selectedEvent, setSelectedEvent] = useState<EarningsCallEvent | null>(null)
  const [detail, setDetail] = useState<EarningsCallDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)

  const loadCalendar = useCallback(async () => {
    setCalendarLoading(true)
    const start = formatDate(year, month, 1)
    const end = formatDate(year, month, daysInMonth(year, month))
    try {
      const data = await getEarningsCalendar(start, end)
      setCalendarData(data)
    } finally {
      setCalendarLoading(false)
    }
  }, [year, month])

  useEffect(() => { loadCalendar() }, [loadCalendar])

  async function handleEventClick(event: EarningsCallEvent) {
    if (!event.has_transcript) return
    setSelectedEvent(event)
    setDetail(null)
    setDetailError(null)
    setDetailLoading(true)
    try {
      const d = await getEarningsCallDetail(event.symbol, event.year, event.quarter)
      setDetail(d)
    } catch (err) {
      setDetailError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setDetailLoading(false)
    }
  }

  function prevMonth() {
    if (month === 1) { setYear(y => y - 1); setMonth(12) }
    else setMonth(m => m - 1)
  }

  function nextMonth() {
    if (month === 12) { setYear(y => y + 1); setMonth(1) }
    else setMonth(m => m + 1)
  }

  const todayStr = formatDate(now.getFullYear(), now.getMonth() + 1, now.getDate())
  const totalDays = daysInMonth(year, month)
  const firstDay = firstDayOfWeek(year, month)
  const eventsForSelected = selectedDate ? (calendarData[selectedDate] ?? []) : []

  const WEEK_LABELS = ['一', '二', '三', '四', '五', '六', '日']

  return (
    <div className="flex flex-col h-screen" style={{ background: 'rgb(246,248,252)' }}>
      {/* 主体 */}
      <div className="flex flex-1 overflow-hidden">

        {/* 左侧：日历面板 */}
        <div
          className="w-[260px] shrink-0 flex flex-col border-r"
          style={{ background: 'rgb(250,251,253)', borderColor: 'rgba(0,0,0,0.08)' }}
        >
          {/* 月份导航 */}
          <div className="p-4 border-b" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
            <div className="flex items-center justify-between mb-3">
              <button
                onClick={prevMonth}
                className="w-7 h-7 flex items-center justify-center rounded-lg text-sm transition-colors"
                style={{ border: '1px solid rgba(0,0,0,0.1)', background: 'white' }}
              >
                ‹
              </button>
              <span className="text-sm font-semibold" style={{ color: 'rgb(15,23,42)' }}>
                {year}年 {month}月
                {calendarLoading && <span className="ml-2 text-xs animate-pulse" style={{ color: 'rgb(22,119,255)' }}>加载中</span>}
              </span>
              <button
                onClick={nextMonth}
                className="w-7 h-7 flex items-center justify-center rounded-lg text-sm transition-colors"
                style={{ border: '1px solid rgba(0,0,0,0.1)', background: 'white' }}
              >
                ›
              </button>
            </div>

            {/* 星期标题 */}
            <div className="grid grid-cols-7 text-center mb-1">
              {WEEK_LABELS.map(w => (
                <span
                  key={w}
                  className="text-[9px] font-semibold py-1"
                  style={{ color: w === '六' || w === '日' ? 'rgb(248,113,113)' : 'rgb(148,163,184)' }}
                >
                  {w}
                </span>
              ))}
            </div>

            {/* 日期格 */}
            <div className="grid grid-cols-7 gap-y-1">
              {/* 空格占位 */}
              {Array.from({ length: firstDay }).map((_, i) => <div key={`pad-${i}`} />)}

              {Array.from({ length: totalDays }).map((_, i) => {
                const day = i + 1
                const dateStr = formatDate(year, month, day)
                const isToday = dateStr === todayStr
                const isSelected = dateStr === selectedDate
                const hasEvents = !!calendarData[dateStr]?.length

                return (
                  <button
                    key={day}
                    onClick={() => setSelectedDate(dateStr)}
                    className="relative flex items-center justify-center h-7 text-[10px] rounded-full transition-all duration-150"
                    style={{
                      fontWeight: isSelected || hasEvents ? 600 : 400,
                      background: isToday
                        ? 'rgb(22,119,255)'
                        : isSelected
                        ? 'rgba(255,185,0,0.15)'
                        : 'transparent',
                      color: isToday
                        ? 'white'
                        : hasEvents
                        ? 'rgb(15,23,42)'
                        : 'rgb(148,163,184)',
                      border: isSelected && !isToday ? '1px solid rgba(255,185,0,0.4)' : 'none',
                    }}
                  >
                    {day}
                    {hasEvents && !isToday && (
                      <span
                        className="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full"
                        style={{ background: 'rgb(255,185,0)' }}
                      />
                    )}
                  </button>
                )
              })}
            </div>

            {/* 图例 */}
            <div className="flex items-center gap-3 mt-3 text-[9px]" style={{ color: 'rgb(148,163,184)' }}>
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: 'rgb(255,185,0)' }} />
                有会议
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full inline-block" style={{ background: 'rgb(22,119,255)' }} />
                今天
              </span>
            </div>
          </div>

          {/* 当日公司列表 */}
          <div className="flex-1 overflow-y-auto">
            {selectedDate ? (
              <>
                <div
                  className="px-4 py-2 text-[10px] font-semibold uppercase tracking-wider"
                  style={{ color: 'rgb(100,116,139)' }}
                >
                  {selectedDate} · {eventsForSelected.length} 家
                </div>
                {eventsForSelected.length === 0 && (
                  <div className="px-4 py-3 text-[11px]" style={{ color: 'rgb(148,163,184)' }}>
                    当日无纳斯达克100财报会议
                  </div>
                )}
                {eventsForSelected.map(event => {
                  const isChosen = selectedEvent?.symbol === event.symbol
                  return (
                    <button
                      key={event.symbol}
                      onClick={() => handleEventClick(event)}
                      disabled={!event.has_transcript}
                      className="w-full px-4 py-2.5 text-left transition-all duration-150"
                      style={{
                        borderLeft: isChosen ? '2px solid rgb(22,119,255)' : '2px solid transparent',
                        background: isChosen ? 'rgba(22,119,255,0.06)' : 'transparent',
                        borderBottom: '1px solid rgba(0,0,0,0.04)',
                        opacity: event.has_transcript ? 1 : 0.6,
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className="text-[11px] font-semibold"
                          style={{ color: isChosen ? 'rgb(22,119,255)' : 'rgb(51,65,85)' }}
                        >
                          {event.symbol}
                        </span>
                        {event.has_transcript ? (
                          <span
                            className="text-[9px] px-1.5 py-0.5 rounded"
                            style={{ background: 'rgba(0,0,0,0.05)', color: 'rgb(100,116,139)' }}
                          >
                            点击查看
                          </span>
                        ) : (
                          <span
                            className="text-[9px] px-1.5 py-0.5 rounded"
                            style={{ background: 'rgba(148,163,184,0.15)', color: 'rgb(148,163,184)' }}
                          >
                            即将召开
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] mt-0.5" style={{ color: 'rgb(148,163,184)' }}>
                        Q{event.quarter} {event.year}
                      </div>
                    </button>
                  )
                })}
              </>
            ) : (
              <div className="px-4 py-6 text-[11px] text-center" style={{ color: 'rgb(148,163,184)' }}>
                点击左侧日期查看当日会议
              </div>
            )}
          </div>
        </div>

        {/* 右侧：详情面板 */}
        <div className="flex-1 overflow-y-auto p-6">
          {!selectedEvent && (
            <div
              className="flex items-center justify-center h-full text-sm"
              style={{ color: 'rgb(148,163,184)' }}
            >
              从左侧选择日期和公司，查看财报电话会议详情
            </div>
          )}

          {selectedEvent && detailLoading && (
            <div className="flex flex-col items-center justify-center h-64 gap-3">
              <div
                className="w-6 h-6 rounded-full border-2 border-t-transparent animate-spin"
                style={{ borderColor: 'rgb(22,119,255)', borderTopColor: 'transparent' }}
              />
              <p className="text-sm" style={{ color: 'rgb(100,116,139)' }}>
                翻译中，约 30-90 秒...
              </p>
              <p className="text-xs" style={{ color: 'rgb(148,163,184)' }}>
                首次查看需要 AI 翻译全文，之后秒开
              </p>
            </div>
          )}

          {detailError && (
            <div
              className="rounded-xl p-4 text-sm"
              style={{ background: 'rgba(255,80,80,0.06)', border: '1px solid rgba(255,80,80,0.2)', color: 'rgb(220,80,80)' }}
            >
              加载失败：{detailError}
            </div>
          )}

          {detail && !detailLoading && (
            <div className="flex flex-col gap-5 max-w-3xl">
              {/* 标题 */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h1 className="text-xl font-bold" style={{ color: 'rgb(15,23,42)' }}>
                      {detail.company_name}
                    </h1>
                    <span
                      className="text-xs font-semibold px-2 py-0.5 rounded-md"
                      style={{ background: 'rgba(22,119,255,0.1)', color: 'rgb(22,119,255)' }}
                    >
                      {detail.symbol}
                    </span>
                    <span className="text-sm" style={{ color: 'rgb(100,116,139)' }}>
                      Q{detail.quarter} {detail.year}
                    </span>
                  </div>
                  <p className="text-xs" style={{ color: 'rgb(148,163,184)' }}>
                    {detail.date} · 已全文翻译为中文
                  </p>
                </div>
                <span
                  className="text-[10px] px-2 py-1 rounded-md border"
                  style={{ background: 'rgba(0,200,130,0.08)', color: 'rgb(0,160,100)', borderColor: 'rgba(0,200,130,0.3)' }}
                >
                  已翻译
                </span>
              </div>

              {/* 公司简介 */}
              <div
                className="rounded-xl p-5"
                style={{ background: 'white', border: '1px solid rgba(0,0,0,0.08)' }}
              >
                <div
                  className="text-[10px] font-semibold uppercase tracking-wider mb-3"
                  style={{ color: 'rgb(22,119,255)' }}
                >
                  公司简介
                </div>
                <p className="text-sm leading-7" style={{ color: 'rgb(51,65,85)' }}>
                  {detail.description_zh}
                </p>
              </div>

              {/* 主要产品 */}
              <div
                className="rounded-xl p-5"
                style={{ background: 'white', border: '1px solid rgba(0,0,0,0.08)' }}
              >
                <div
                  className="text-[10px] font-semibold uppercase tracking-wider mb-3"
                  style={{ color: 'rgb(22,119,255)' }}
                >
                  主要产品
                </div>
                <div className="flex flex-wrap gap-2">
                  {detail.products_zh.split(/[,，]/).map(p => p.trim()).filter(Boolean).map(product => (
                    <span
                      key={product}
                      className="text-xs px-3 py-1 rounded-full"
                      style={{
                        background: 'rgb(246,248,252)',
                        border: '1px solid rgba(0,0,0,0.08)',
                        color: 'rgb(51,65,85)',
                      }}
                    >
                      {product}
                    </span>
                  ))}
                </div>
              </div>

              {/* AI 摘要 */}
              <div
                className="rounded-xl p-5"
                style={{
                  background: 'rgba(255,185,0,0.04)',
                  border: '1px solid rgba(255,185,0,0.25)',
                }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div
                    className="text-[10px] font-semibold uppercase tracking-wider"
                    style={{ color: 'rgb(180,140,0)' }}
                  >
                    AI 会议摘要
                  </div>
                  <span className="text-[9px]" style={{ color: 'rgb(148,163,184)' }}>
                    由 MiniMax 生成
                  </span>
                </div>
                <p className="text-sm leading-7" style={{ color: 'rgb(51,65,85)' }}>
                  {detail.summary_zh}
                </p>
              </div>

              {/* 分隔线 */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px" style={{ background: 'rgba(0,0,0,0.08)' }} />
                <span className="text-[10px] font-semibold" style={{ color: 'rgb(100,116,139)' }}>
                  完整原文（中文翻译）
                </span>
                <div className="flex-1 h-px" style={{ background: 'rgba(0,0,0,0.08)' }} />
              </div>

              {/* 完整原文 */}
              <div
                className="rounded-xl p-5"
                style={{ background: 'rgb(250,251,253)', border: '1px solid rgba(0,0,0,0.08)' }}
              >
                <pre
                  className="text-sm whitespace-pre-wrap leading-7"
                  style={{ color: 'rgb(51,65,85)', fontFamily: 'inherit' }}
                >
                  {detail.transcript_zh}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 8.2: 在浏览器验证页面渲染**

```bash
cd frontend && pnpm dev
```

访问 `http://localhost:3000/earnings`，确认：
- 页面正常渲染，无 console 报错
- 左侧月历显示当月
- 月份切换按钮正常工作
- 点击有事件的日期，右侧公司列表出现

- [ ] **Step 8.3: Commit**

```bash
git add frontend/app/(pages)/earnings/page.tsx
git commit -m "feat(earnings-call): add /earnings frontend page"
```

---

## Task 9: 导航栏新增入口

**Files:**
- Modify: `frontend/components/layout/AppShell.tsx`

- [ ] **Step 9.1: 在 AppShell.tsx 导航栏中添加「财报日历」链接**

在 `frontend/components/layout/AppShell.tsx` 中，找到现有「信号雷达」的 `<Link>` 之后，添加：

```tsx
<Link
  href="/earnings"
  className="px-3 py-1.5 text-xs rounded-lg transition-all duration-200"
  style={{ color: 'rgba(255,255,255,0.85)' }}
  onMouseEnter={e => {
    (e.currentTarget as HTMLAnchorElement).style.color = 'rgb(255,255,255)'
    ;(e.currentTarget as HTMLAnchorElement).style.background = 'rgba(255,255,255,0.15)'
  }}
  onMouseLeave={e => {
    (e.currentTarget as HTMLAnchorElement).style.color = 'rgba(255,255,255,0.85)'
    ;(e.currentTarget as HTMLAnchorElement).style.background = 'transparent'
  }}
>
  财报日历
</Link>
```

- [ ] **Step 9.2: 验证导航链接在所有页面可见**

```bash
cd frontend && pnpm dev
```

访问 `http://localhost:3000`（研究助手），确认顶栏显示：研究助手 | 信号雷达 | **财报日历**

点击「财报日历」，确认跳转到 `/earnings` 页面。

- [ ] **Step 9.3: 最终全量构建检查**

```bash
cd frontend && pnpm build
```

预期：构建成功，无类型错误。

- [ ] **Step 9.4: Commit**

```bash
git add frontend/components/layout/AppShell.tsx
git commit -m "feat(earnings-call): add navigation link to AppShell"
```

---

## 自检结果

**Spec coverage:**
- ✅ Domain models + protocols (Task 1)
- ✅ FMP loader，过滤 nasdaq100，has_transcript 逻辑 (Task 2)
- ✅ MiniMax 四个处理函数：描述翻译、产品提炼、摘要生成、全文翻译（分段）(Task 3)
- ✅ PG 缓存表 earnings_call_details，upsert (Task 4)
- ✅ Service 编排：缓存命中返回、无 transcript 抛 404、并发翻译 (Task 5)
- ✅ FastAPI router 两个端点 (Task 6)
- ✅ 前端 types + api 函数 (Task 7)
- ✅ 前端页面：月历、公司列表（三种状态）、详情四区块 (Task 8)
- ✅ 导航栏入口 (Task 9)

**已知风险：**
- FMP `/stable/earning-call-transcript` 端点需在真实 API key 下验证路径正确性
- `CompanyProfile.description` 字段存在时才能翻译简介；若为空，`translate_description` 返回空字符串
