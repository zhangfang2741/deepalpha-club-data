# DeepAlpha 六边形架构重构 + 前端框架设计文档

**日期**：2026-06-01
**状态**：已批准
**范围**：后端架构重组（六边形分层）+ 新增 Agent 层 + 新增 Next.js 前端

---

## 1. 背景与目标

当前 `deepalpha` 包的目录划分为 `models/`、`loaders/`、`providers/`、`pipeline/`，随着概念股池功能落地，`pipeline/concept/` 内同时包含了 DB 层、缓存层、调度任务和 FastAPI 路由，职责边界模糊，业务逻辑与基础设施耦合。

本次重构目标：

1. 引入**六边形架构**（Hexagonal / Ports-Adapters），将代码重组为 `domain / application / infrastructure / interface` 四层，使 domain 核心零外部依赖、各层职责单一。
2. 在 `application/agent/` 新增 **Claude API Agent 层**，支持 search_concept / get_quote / get_financials / generate_report 四类工具，实现自然语言驱动的投研助手。
3. 在仓库根目录新建 `frontend/` 子目录，引入 **Next.js 15 + shadcn/ui + Radix + Tailwind v4 + Vercel AI SDK** 前端框架，提供数据看板与 AI 对话双界面。

---

## 2. 后端目录结构（重组后）

```
src/deepalpha/
├── domain/                    # 领域核心：零外部依赖（仅 stdlib + pydantic）
│   ├── concept/
│   │   ├── models.py          # ConceptEtfMap · ConceptStock · ConceptSummary
│   │   └── protocols.py       # IConceptRepo · IConceptCache
│   ├── market/
│   │   ├── models.py          # Quote · PriceHistory · MarketSnapshot
│   │   └── protocols.py       # IMarketProvider
│   ├── financial/
│   │   ├── models.py          # IncomeStatement · BalanceSheet · CashFlow
│   │   └── protocols.py       # IFinancialProvider
│   ├── analyst/
│   │   ├── models.py          # AnalystRating · PriceTarget · EarningsEstimate
│   │   └── protocols.py       # IAnalystProvider
│   └── company/
│       ├── models.py          # CompanyProfile · Executive · Peer
│       └── protocols.py       # ICompanyProvider
│
├── application/               # 用例层：只依赖 domain protocols
│   ├── services/
│   │   ├── concept_service.py # ConceptService（cache-aside 查询 + 持仓更新）
│   │   ├── market_service.py  # MarketService（报价 · 历史价格 · 技术指标）
│   │   ├── financial_service.py
│   │   └── analyst_service.py
│   └── agent/
│       ├── tools.py           # TOOLS 列表（传给 Claude API）
│       ├── runner.py          # AgentRunner：tool_use 循环 + 流式迭代器
│       └── prompts.py         # 系统提示词
│
├── infrastructure/            # 适配器层：实现 domain protocols
│   ├── providers/
│   │   ├── fmp/               # 平移自 providers/fmp/（零逻辑改动）
│   │   └── finnhub/           # 平移自 providers/finnhub/（零逻辑改动）
│   ├── db/
│   │   └── concept_repo.py    # ConceptRepo 实现 IConceptRepo（平移自 pipeline/concept/db.py）
│   └── cache/
│       └── concept_cache.py   # ConceptCache 实现 IConceptCache（平移自 pipeline/concept/cache.py）
│
└── interface/                 # 驱动适配器：外部进入点
    ├── web/
    │   ├── app.py             # FastAPI 应用入口（lifespan 管理连接池）
    │   ├── deps.py            # 依赖注入：组装 infra → service → agent
    │   └── routers/
    │       ├── concept.py     # GET /concept/list · GET /concept/{name}
    │       ├── market.py      # GET /market/quote/{symbol}
    │       └── agent.py       # POST /agent/stream（SSE）
    └── pipeline/
        └── concept/
            ├── build_concept_map.py   # 月度任务入口（调用 ConceptService）
            └── update_holdings.py     # 日度任务入口（调用 ConceptService）
```

### 迁移对照表

| 现有文件 | 迁移目标 | 改动类型 |
|---|---|---|
| `models/concept.py` | `domain/concept/models.py` | 平移 |
| `models/market.py` | `domain/market/models.py` | 平移 |
| `models/financial.py` | `domain/financial/models.py` | 平移 |
| `models/analyst.py` | `domain/analyst/models.py` | 平移 |
| `models/company.py` | `domain/company/models.py` | 平移 |
| `loaders/hub.py`（Protocol 定义） | `domain/*/protocols.py` | 拆分平移 |
| `loaders/base.py`（BaseLoader） | `infrastructure/providers/base.py` | 平移 |
| `providers/fmp/` | `infrastructure/providers/fmp/` | 平移 |
| `providers/finnhub/` | `infrastructure/providers/finnhub/` | 平移 |
| `pipeline/concept/db.py` | `infrastructure/db/concept_repo.py` | 平移 |
| `pipeline/concept/cache.py` | `infrastructure/cache/concept_cache.py` | 平移 |
| `pipeline/concept/api/router.py` | `interface/web/routers/concept.py` | 平移 |
| `pipeline/concept/tasks/*.py` | `interface/pipeline/concept/*.py` | 重构（瘦身） |
| `pipeline/concept/config.py` | `infrastructure/db/` + `infrastructure/cache/` | 拆分 |
| `pipeline/concept/etfdb_scraper.py` | `infrastructure/providers/etfdb/scraper.py` | 平移 |
| `pipeline/concept/finnhub_loader.py` | `infrastructure/providers/finnhub/etf_loader.py` | 平移 |

---

## 3. domain 层设计

### 原则

- **零外部依赖**：只允许导入 Python stdlib 和 `pydantic`，不导入 httpx / asyncpg / valkey 等。
- **Protocol 而非 ABC**：沿用项目现有风格，使用 `typing.Protocol` + `@runtime_checkable`，infrastructure 无需显式继承。
- **protocols.py 命名**：每个 domain 子包提供 `protocols.py`，定义该领域的仓储/Provider 接口，由 infrastructure 实现。

### concept/protocols.py 示例

```python
from typing import Protocol, runtime_checkable
from datetime import date
from .models import ConceptStock, ConceptEtfMap, ConceptSummary

@runtime_checkable
class IConceptRepo(Protocol):
    async def load_etf_map(self) -> list[ConceptEtfMap]: ...
    async def upsert_etf_map(self, records: list[ConceptEtfMap]) -> None: ...
    async def get_latest_stocks(self, concept: str) -> list[ConceptStock]: ...
    async def upsert_stocks(self, date: date, records: list[ConceptStock]) -> None: ...
    async def get_all_summaries(self) -> list[ConceptSummary]: ...

@runtime_checkable
class IConceptCache(Protocol):
    async def get_concept(self, name: str) -> list[ConceptStock] | None: ...
    async def set_concept(self, name: str, stocks: list[ConceptStock]) -> None: ...
    async def get_list(self) -> list[ConceptSummary] | None: ...
    async def set_list(self, summaries: list[ConceptSummary]) -> None: ...
```

---

## 4. application 层设计

### 4.1 services/

每个 Service 通过构造函数注入 domain protocols（依赖倒置），被 agent tools 和 web routers 共同复用。

```python
class ConceptService:
    def __init__(self, repo: IConceptRepo, cache: IConceptCache) -> None: ...

    async def get_concept(self, name: str) -> list[ConceptStock]:
        # cache-aside：先查 Valkey，未命中查 DB 并回填
        hit = await self.cache.get_concept(name)
        if hit:
            return hit
        rows = await self.repo.get_latest_stocks(name)
        await self.cache.set_concept(name, rows)
        return rows

    async def list_summaries(self) -> list[ConceptSummary]: ...
    async def update_holdings(self, date: date) -> None: ...   # 日度任务调用
    async def rebuild_etf_map(self) -> None: ...               # 月度任务调用
```

### 4.2 agent/tools.py

工具函数字典直接传给 Claude API，对应的调度函数调用 service 层：

| 工具名 | 描述 | 调用 service |
|---|---|---|
| `search_concept` | 查询概念股池成分股列表 | `ConceptService.get_concept()` |
| `get_quote` | 获取股票实时报价 | `MarketService.get_quote()` |
| `get_financials` | 获取财务报表数据 | `FinancialService.get_income()` |
| `generate_report` | 生成结构化投研报告 | 编排多个 service 调用 |

### 4.3 agent/runner.py

实现标准 `tool_use` 循环，返回异步迭代器供 FastAPI SSE 消费：

```python
async def run_agent(messages: list, services: Services) -> AsyncIterator[str]:
    while True:
        async with client.messages.stream(
            model="claude-sonnet-4-6",
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
            # stream 结束后通过 get_final_message() 获取完整响应（含 stop_reason）
            final = await stream.get_final_message()

        if final.stop_reason == "end_turn":
            break
        # 处理 tool_use block → 调用对应 service → 追加 tool_result
        tool_results = await dispatch_tools(final.content, services)
        messages = messages + [{"role": "assistant", "content": final.content}] + tool_results
```

---

## 5. infrastructure 层设计

### 原则

- 每个适配器类声明实现对应的 domain protocol（通过 `isinstance` 断言在测试中验证）。
- 文件大部分是平移，逻辑代码零改动。
- 连接池（asyncpg pool、valkey 连接）在 FastAPI lifespan 中统一创建和销毁。

### 依赖注入（interface/web/deps.py）

```python
# FastAPI lifespan 中组装
pool = await asyncpg.create_pool(dsn)
valkey_client = valkey.asyncio.Valkey(...)

repo = ConceptRepo(pool)          # 实现 IConceptRepo
cache = ConceptCache(valkey_client)  # 实现 IConceptCache
concept_svc = ConceptService(repo, cache)

market_provider = FMPMarketLoader(fmp_client)  # 实现 IMarketProvider
market_svc = MarketService(market_provider)

agent_runner = AgentRunner(concept_svc, market_svc, financial_svc, analyst_svc)
```

---

## 6. interface 层设计

### 6.1 FastAPI 路由

```
GET  /concept/list                        # 所有概念摘要
GET  /concept/{name}?min_etf_count=1      # 概念成分股
GET  /concept/{name}/history              # 历史快照（不走缓存）
GET  /market/quote/{symbol}               # 实时报价
GET  /market/history/{symbol}             # 历史价格
POST /agent/stream                        # Agent SSE 流
```

### 6.2 Agent SSE 路由

```python
@router.post("/agent/stream")
async def agent_stream(
    req: ChatRequest,
    runner: AgentRunner = Depends(get_runner),
):
    return EventSourceResponse(runner.run_agent(req.messages))
```

### 6.3 pipeline 任务（瘦身后）

```python
# interface/pipeline/concept/update_holdings.py
async def main():
    repo, cache = await build_infra()
    svc = ConceptService(repo, cache)
    await svc.update_holdings(date=date.today())
```

---

## 7. 前端架构（frontend/）

### 7.1 技术栈

| 类别 | 选型 |
|---|---|
| 框架 | Next.js 15 App Router + TypeScript |
| UI 组件 | shadcn/ui + Radix UI Primitives |
| 样式 | Tailwind CSS v4 |
| AI 流式 | Vercel AI SDK（`ai` 包）· `useChat` hook |
| 数据图表 | Recharts（shadcn/ui Charts 封装） |
| 数据请求 | SWR + fetch（Next.js 内置缓存） |
| 包管理 | pnpm |

### 7.2 目录结构

```
frontend/
├── app/
│   ├── (dashboard)/
│   │   ├── page.tsx               # 首页：概念总览看板
│   │   └── concept/[name]/
│   │       └── page.tsx           # 概念股详情页
│   ├── (chat)/
│   │   └── page.tsx               # AI 助手对话页
│   ├── api/
│   │   └── chat/
│   │       └── route.ts           # Vercel AI SDK Route Handler
│   ├── layout.tsx                 # 全局布局（顶栏 + 侧边栏）
│   └── globals.css
├── components/
│   ├── ui/                        # shadcn/ui 基础组件
│   ├── concept/
│   │   ├── ConceptCard.tsx
│   │   └── StockTable.tsx
│   ├── charts/
│   │   └── WeightChart.tsx        # ETF 权重分布图
│   └── chat/
│       ├── Message.tsx
│       ├── ToolCallBadge.tsx      # tool_use 渲染组件
│       └── ChatInput.tsx
├── lib/
│   ├── api.ts                     # 后端 API 客户端
│   └── utils.ts                   # cn() 等工具函数
└── hooks/
    ├── use-concept.ts             # SWR 查询概念数据
    └── use-market.ts              # SWR 查询行情数据
```

### 7.3 主界面布局

三栏结构：

```
┌─────────────────────────────────────────────────────────┐
│  DeepAlpha     看板  概念股池  行情         ▶ AI 助手    │  ← 顶栏
├──────────────┬──────────────────────────┬───────────────┤
│              │                          │               │
│  概念分类    │   数据看板               │  AI 助手      │
│              │   · 概念股列表           │  · 消息流     │
│  🤖 AI/ML    │   · ETF 覆盖度           │  · 工具调用   │
│  ⚡ 清洁能源  │   · 权重分布图           │    标签展示   │
│  🧬 生物科技  │   · 成分股表格           │  · 输入框     │
│  ☁️ 云计算   │                          │               │
│  ...50+      │                          │               │
└──────────────┴──────────────────────────┴───────────────┘
```

### 7.4 AI 流式端点（app/api/chat/route.ts）

```typescript
export async function POST(req: Request) {
  const { messages } = await req.json()

  const upstream = await fetch(`${process.env.BACKEND_URL}/agent/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })

  // 将 FastAPI SSE 转为 Vercel AI SDK data stream 格式
  return new StreamingTextResponse(upstream.body!)
}
```

前端对话页使用 `useChat({ api: '/api/chat' })`，`tool_use` 消息渲染为 `ToolCallBadge`，文本消息用 `react-markdown` 渲染。

---

## 8. 数据流总览

```
【AI 对话】
浏览器 useChat
  → Next.js /api/chat (Route Handler)
  → FastAPI POST /agent/stream (SSE)
  → AgentRunner.run_agent()
  → Claude API (stream + tool_use)
  ↔ application/services/* (业务逻辑)
  ↔ infrastructure/* (DB / Cache / 外部 API)
  → 流式文字 → 浏览器

【数据看板】
浏览器 SWR
  → FastAPI GET /concept/* 或 /market/*
  → interface/web/routers
  → application/services
  → infrastructure (cache-aside)
  → JSON → 浏览器

【调度任务】
Cron (SGT 04:30 日度 / 每月 1 日月度)
  → interface/pipeline/concept/update_holdings.py
  → application/services/concept_service.py
  → infrastructure/db + infrastructure/cache
```

---

## 9. 新增依赖

### Python（pyproject.toml）

```toml
"anthropic>=0.40.0",   # Claude API SDK
"sse-starlette>=2.0",  # FastAPI SSE（EventSourceResponse）
```

### Node.js（frontend/package.json）

```json
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "ai": "^4.0.0",
    "swr": "^2.0.0",
    "recharts": "^2.0.0",
    "react-markdown": "^9.0.0"
  }
}
```

shadcn/ui 通过 CLI 初始化，自动安装 Radix UI Primitives 和 Tailwind CSS v4。

---

## 10. 迁移策略

1. **阶段一：domain 层**（平移 + 新增 protocols.py，无逻辑改动）
2. **阶段二：infrastructure 层**（文件平移，import 路径更新）
3. **阶段三：application 层**（新建 services/ 提取业务逻辑 + agent/ 新增）
4. **阶段四：interface 层**（统一 FastAPI 入口，pipeline 任务瘦身）
5. **阶段五：frontend/**（Next.js 脚手架 + shadcn/ui 初始化 + 组件开发）

每个阶段结束后运行现有测试套件确认无回归。
