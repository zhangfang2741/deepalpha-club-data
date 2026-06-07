# 统一异常日志系统设计文档

**日期**：2026-06-07
**状态**：已批准

---

## 概述

在 `src/deepalpha/core/logging/` 中构建统一日志模块，提供每日滚动文件日志、可配置详细程度、统一异常包装，并将该模块应用于 infrastructure 层的所有 provider 和 cache/db 适配器。

---

## 模块结构

```
src/deepalpha/core/
├── __init__.py
└── logging/
    ├── __init__.py          # 导出 setup_logging, get_logger, log_call
    ├── setup.py             # 初始化 handler：TimedRotatingFileHandler + StreamHandler
    ├── decorators.py        # @log_call 异步装饰器
    └── exceptions.py        # DeepAlphaInfraError 统一异常基类
```

日志文件路径：`src/deepalpha/core/logs/deepalpha_YYYY-MM-DD.log`（目录自动创建，gitignore）

---

## 日志配置

| 参数 | 值 |
|------|-----|
| 滚动策略 | `TimedRotatingFileHandler(when="midnight")` |
| 保留天数 | `backupCount=3` |
| 文件命名 | `deepalpha_YYYY-MM-DD.log`（suffix 格式）|
| 日志格式 | `%(asctime)s [%(levelname)s] %(name)s - %(message)s` |
| Console | 同时输出到 stderr（级别 INFO） |

`setup_logging(level)` 在应用启动时（FastAPI lifespan）调用一次，之后所有模块通过 `get_logger(__name__)` 获取命名 logger。

---

## DeepAlphaInfraError 统一异常

```python
class DeepAlphaInfraError(Exception):
    provider: str       # 来源标识，如 "fmp"、"finnhub"、"cache"、"db"
    method: str         # 方法名，如 "get_income_statement"
    original: Exception # 原始异常实例
```

所有原始异常均被包装为此类型抛出，application 层只需捕获 `DeepAlphaInfraError`。

---

## @log_call 装饰器

应用于 infrastructure 层的异步方法。行为如下：

### 日志内容

| 事件 | INFO 级别 | DEBUG 级别 |
|------|-----------|------------|
| 调用开始 | `provider.method(入参完整，隐藏 apikey)` | 同左 |
| 调用成功 | `返回类型 + 数量（如 "5 x IncomeStatement"）+ 耗时` | 完整返回值 + 耗时 |
| 调用失败 | 异常类型 + 消息 + 耗时 + traceback | 同左 |

### 异常处理

1. 捕获所有异常
2. 以 ERROR 级别记录完整 traceback 到日志文件
3. 将原始异常包装为 `DeepAlphaInfraError(provider, method, original)` 抛出

### 入参脱敏

含 `apikey`、`token`、`password` 的参数值替换为 `"***"` 再记录。

---

## Infrastructure 改造范围

| 文件 | 装饰目标 | provider 标识 |
|------|---------|--------------|
| `providers/base.py` `BaseLoader._get` / `_get_list` / `_to_models` | 3 个方法 | `"base"` |
| `providers/fmp/client.py` `FMPAsyncClient.get` | 1 个方法 | `"fmp"` |
| `providers/finnhub/client.py` `FinnhubClient._get` | 1 个方法 | `"finnhub"` |
| `infrastructure/cache/concept_cache.py` 所有 public 方法 | 4 个方法 | `"cache"` |
| `infrastructure/db/concept_repo.py` 所有 public 方法 | 若干方法 | `"db"` |

fmp loaders（`financial_loader.py` 等）**不改造**，日志已由底层 `BaseLoader` 方法覆盖。

---

## FastAPI 集成

在 `src/deepalpha/interface/web/app.py` lifespan 中调用 `setup_logging()`，确保应用启动时初始化一次：

```python
from deepalpha.core.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()   # 新增
    ...
```

---

## 不在范围内

- 结构化 JSON 日志（structlog）
- 日志远程上报（ELK/Loki）
- fmp loaders 层级的日志（由底层覆盖）
- 新增单元测试（在此 spec 范围外）
