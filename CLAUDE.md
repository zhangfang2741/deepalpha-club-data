# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

DeepAlpha 是一个美股金融数据平台，包含：
- Python 后端（FastAPI + 六边形架构）
- Next.js 前端（AI 对话 + 数据可视化）
- LangGraph ReAct Agent（MiniMax-Text-01 模型，通过 OpenAI-compatible API）

## 常用命令

### 后端

```bash
# 启动开发服务器
uv run fastapi dev src/deepalpha/interface/web/app.py

# 运行单元测试
uv run pytest tests/unit/

# 运行单个测试文件
uv run pytest tests/unit/providers/fmp/loaders/test_financial.py -v

# 集成测试（需要真实 API Key）
uv run pytest -m integration

# Lint 检查
uv run ruff check .

# 类型检查
uv run mypy src/
```

### 前端

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建
pnpm build
```

## 架构

### 后端分层（六边形架构）

```
src/deepalpha/
├── domain/          # 领域层：Pydantic 模型 + Protocol 接口（纯定义，无副作用）
├── application/     # 应用层：services（编排领域逻辑）+ agent（LangGraph ReAct）
├── infrastructure/  # 基础设施层：FMP/Finnhub/yfinance providers, PostgreSQL, Valkey
└── interface/       # 接口层：FastAPI web routers + pipeline 脚本
```

**依赖方向**：`interface → application → domain`；`infrastructure` 实现 `domain` 中的 Protocol。

### 关键设计模式

- **`BaseLoader`** ([src/deepalpha/infrastructure/providers/base.py](src/deepalpha/infrastructure/providers/base.py))：所有 FMP/Finnhub loader 的基类，提供 `_get()`, `_get_list()`, `_to_models()` 方法。空字符串在 `_to_models()` 中自动转为 `None`（FMP 的惯例）。
- **Domain Protocol**：每个 domain 子模块有 `protocols.py` 定义抽象接口，infrastructure 实现这些 Protocol，application 依赖 Protocol 而非具体类。
- **依赖注入**：所有 services 在 FastAPI lifespan 中组装，见 [src/deepalpha/interface/web/deps.py](src/deepalpha/interface/web/deps.py)。
- **Agent 工具**：`build_tools(services)` 在 [src/deepalpha/application/agent/tools.py](src/deepalpha/application/agent/tools.py) 中用 `@lc_tool` 创建 LangChain 工具，工具通过闭包注入 `services`。

### 数据提供商

| 提供商 | 用途 | 环境变量 |
|-------|------|---------|
| FMP (Financial Modeling Prep) | 行情、财务报表、分析师、新闻等主要数据源 | `FMP_API_KEY` |
| Finnhub | ETF 持仓数据（概念股池构建） | `FINNHUB_API_KEY` |
| yfinance | 概念股 scraping | — |

### 外部服务

- **PostgreSQL**（Neon）：概念股池数据持久化
- **Valkey**（Upstash，Redis 兼容）：概念股缓存，默认 TTL 2 天
- **MiniMax**：AI Agent 模型（`MINIMAX_API_KEY`）

### 前端架构

- Next.js App Router，`app/(dashboard)/` 为主界面路由组
- `app/api/chat/route.ts`：AI 对话 API 路由，调用后端 SSE 流
- Vercel AI SDK (`@ai-sdk/openai`) + `useChat` hook
- shadcn/ui 组件 + Tailwind CSS v4 + Recharts 图表

## 环境配置

复制 `.env.example` 为 `.env` 并填写所有必填项。`FMPConfig` 使用 `FMP_` 前缀读取环境变量（如 `FMP_API_KEY`），其余配置直接读取（如 `POSTGRES_HOST`）。

## 测试约定

- 集成测试使用 `@pytest.mark.integration` 标记，默认不运行，需显式 `-m integration`
- 单元测试通过 `pytest-httpx` mock HTTP 请求，不依赖真实 API
- `asyncio_mode = "auto"` 已在 `pyproject.toml` 配置，异步测试无需额外装饰器

## 代码规范

- Python 3.11+，mypy strict 模式，ruff line-length 100
- 所有新 domain 模型使用 Pydantic v2，字段使用中文 `title`
- loader 类继承 `BaseLoader`，实现对应 domain Protocol
- Agent 工具 docstring 为中文，供 LLM 理解工具用途
