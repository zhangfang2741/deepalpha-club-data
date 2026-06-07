# Core Logging System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `src/deepalpha/core/logging/` 构建统一日志模块（structlog JSON 文件 + 彩色 Console），提供 `AppLogger` 公共类和 `@log_call` 装饰器，并将其应用于 infrastructure 层的所有 provider、cache、db 适配器。

**Architecture:** `core/logging/` 作为零依赖的基础模块，`exceptions.py` 定义统一异常，`setup.py` 初始化 structlog + stdlib handler，`logger.py` 提供 `AppLogger` 公共类，`decorators.py` 提供 `@log_call` 装饰器。Infrastructure 层各文件只需 import 并应用装饰器，无需修改业务逻辑。

**Tech Stack:** Python 3.11+, structlog, stdlib `logging.handlers.TimedRotatingFileHandler`, FastAPI lifespan

---

## 文件清单

| 操作 | 路径 |
|------|------|
| Create | `src/deepalpha/core/__init__.py` |
| Create | `src/deepalpha/core/logging/__init__.py` |
| Create | `src/deepalpha/core/logging/exceptions.py` |
| Create | `src/deepalpha/core/logging/setup.py` |
| Create | `src/deepalpha/core/logging/logger.py` |
| Create | `src/deepalpha/core/logging/decorators.py` |
| Modify | `pyproject.toml` — 新增 structlog 依赖 |
| Modify | `src/deepalpha/infrastructure/providers/base.py` |
| Modify | `src/deepalpha/infrastructure/providers/fmp/client.py` |
| Modify | `src/deepalpha/infrastructure/providers/finnhub/client.py` |
| Modify | `src/deepalpha/infrastructure/cache/concept_cache.py` |
| Modify | `src/deepalpha/infrastructure/db/concept_repo.py` |
| Modify | `src/deepalpha/interface/web/deps.py` |

---

### Task 1: 添加 structlog 依赖

**Files:**
- Modify: `pyproject.toml:6-27`

- [ ] **Step 1: 在 pyproject.toml dependencies 列表中添加 structlog**

  在 `"sse-starlette>=2.0",` 一行后添加：

  ```toml
      "structlog>=24.0.0",
  ```

- [ ] **Step 2: 安装依赖**

  ```bash
  uv sync
  ```

  Expected：输出包含 `structlog` 安装成功，无错误。

- [ ] **Step 3: 验证可 import**

  ```bash
  uv run python -c "import structlog; print(structlog.__version__)"
  ```

  Expected：打印版本号，如 `24.x.x`。

- [ ] **Step 4: Commit**

  ```bash
  git add pyproject.toml uv.lock
  git commit -m "feat(core): add structlog dependency"
  ```

---

### Task 2: 创建 core 包和统一异常类

**Files:**
- Create: `src/deepalpha/core/__init__.py`
- Create: `src/deepalpha/core/logging/__init__.py`（空占位，Task 6 填充）
- Create: `src/deepalpha/core/logging/exceptions.py`

- [ ] **Step 1: 创建 core 包 __init__.py**

  创建 `src/deepalpha/core/__init__.py`，内容为空文件（仅包标识）：

  ```python
  ```

- [ ] **Step 2: 创建 logging 包空 __init__.py**

  创建 `src/deepalpha/core/logging/__init__.py`，内容为空（Task 6 填充）：

  ```python
  ```

- [ ] **Step 3: 创建 exceptions.py**

  创建 `src/deepalpha/core/logging/exceptions.py`：

  ```python
  """Infrastructure 层统一异常，所有 provider/cache/db 异常均包装为此类型。"""


  class DeepAlphaInfraError(Exception):
      """Infrastructure 层统一异常基类。

      所有原始异常（FMPError、httpx.HTTPError、asyncpg 等）均被 @log_call
      捕获后包装为此类型抛出，application 层只需捕获 DeepAlphaInfraError。

      Attributes:
          provider: 来源标识，如 "fmp"、"finnhub"、"cache"、"db"
          method: 方法名，如 "get_income_statement"
          original: 原始异常实例
      """

      def __init__(self, provider: str, method: str, original: Exception) -> None:
          self.provider = provider
          self.method = method
          self.original = original
          super().__init__(
              f"[{provider}.{method}] {type(original).__name__}: {original}"
          )
  ```

- [ ] **Step 4: 验证 import**

  ```bash
  uv run python -c "from deepalpha.core.logging.exceptions import DeepAlphaInfraError; print('OK')"
  ```

  Expected：`OK`

- [ ] **Step 5: Commit**

  ```bash
  git add src/deepalpha/core/
  git commit -m "feat(core/logging): add DeepAlphaInfraError unified exception"
  ```

---

### Task 3: 创建 setup.py（structlog 初始化）

**Files:**
- Create: `src/deepalpha/core/logging/setup.py`

- [ ] **Step 1: 创建 setup.py**

  创建 `src/deepalpha/core/logging/setup.py`：

  ```python
  """structlog + stdlib logging 初始化。

  调用 setup_logging() 一次后，全局日志生效：
  - 文件：~/logs/deepalpha-club-data/deepalpha.log（每天滚动，保留 3 天，JSON 格式）
  - Console：stderr，INFO 级别，彩色可读格式
  """

  import logging
  import logging.handlers
  from pathlib import Path

  import structlog


  def setup_logging(level: str = "INFO") -> None:
      """初始化 structlog + stdlib logging。

      在 FastAPI lifespan 启动时调用一次。重复调用幂等（不重复添加 handler）。

      Args:
          level: 日志级别字符串，如 "INFO"、"DEBUG"。默认 "INFO"。
      """
      log_level = getattr(logging, level.upper(), logging.INFO)
      root_logger = logging.getLogger()

      # 幂等：已初始化则跳过
      if root_logger.handlers:
          return

      root_logger.setLevel(log_level)

      # 日志目录自动创建
      log_dir = Path.home() / "logs" / "deepalpha-club-data"
      log_dir.mkdir(parents=True, exist_ok=True)

      # 文件 handler：每天滚动，保留 3 天
      file_handler = logging.handlers.TimedRotatingFileHandler(
          filename=str(log_dir / "deepalpha.log"),
          when="midnight",
          backupCount=3,
          encoding="utf-8",
      )
      file_handler.suffix = "_%Y-%m-%d"
      file_handler.setLevel(logging.DEBUG)

      # Console handler
      console_handler = logging.StreamHandler()
      console_handler.setLevel(logging.INFO)

      # structlog 共享 processors（在进入 stdlib 之前执行）
      shared_processors: list[structlog.types.Processor] = [
          structlog.contextvars.merge_contextvars,
          structlog.stdlib.add_logger_name,
          structlog.stdlib.add_log_level,
          structlog.stdlib.PositionalArgumentsFormatter(),
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.StackInfoRenderer(),
          structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
      ]

      # 文件 formatter：JSON
      json_formatter = structlog.stdlib.ProcessorFormatter(
          processors=[
              structlog.stdlib.ProcessorFormatter.remove_processors_meta,
              structlog.processors.format_exc_info,
              structlog.processors.JSONRenderer(),
          ],
      )

      # Console formatter：彩色可读
      console_formatter = structlog.stdlib.ProcessorFormatter(
          processors=[
              structlog.stdlib.ProcessorFormatter.remove_processors_meta,
              structlog.processors.format_exc_info,
              structlog.dev.ConsoleRenderer(),
          ],
      )

      file_handler.setFormatter(json_formatter)
      console_handler.setFormatter(console_formatter)

      root_logger.addHandler(file_handler)
      root_logger.addHandler(console_handler)

      # structlog 全局配置
      structlog.configure(
          processors=shared_processors,
          wrapper_class=structlog.stdlib.BoundLogger,
          context_class=dict,
          logger_factory=structlog.stdlib.LoggerFactory(),
          cache_logger_on_first_use=True,
      )
  ```

- [ ] **Step 2: 验证 setup_logging 可调用**

  ```bash
  uv run python -c "
  from deepalpha.core.logging.setup import setup_logging
  setup_logging('DEBUG')
  import structlog
  log = structlog.get_logger('test')
  log.info('setup_logging OK', check=True)
  print('PASS')
  "
  ```

  Expected：控制台看到彩色日志行，打印 `PASS`，`~/logs/deepalpha-club-data/deepalpha.log` 文件存在。

- [ ] **Step 3: Commit**

  ```bash
  git add src/deepalpha/core/logging/setup.py
  git commit -m "feat(core/logging): add setup_logging with structlog JSON + console handlers"
  ```

---

### Task 4: 创建 AppLogger 公共日志类

**Files:**
- Create: `src/deepalpha/core/logging/logger.py`

- [ ] **Step 1: 创建 logger.py**

  创建 `src/deepalpha/core/logging/logger.py`：

  ```python
  """公共日志类，任意模块可直接实例化使用。

  用法：
      logger = AppLogger(__name__)
      logger.info("查询完成", symbol="AAPL", count=5)
      logger.error("请求失败", exc_info=True, provider="fmp")

      # 绑定固定字段（适合在类 __init__ 中使用）
      logger = AppLogger(__name__).bind(provider="fmp")
      logger.debug("原始响应", status_code=200)
  """

  from typing import Any

  import structlog


  class AppLogger:
      """structlog BoundLogger 的薄封装，提供标准日志方法和字段绑定。

      Args:
          name: logger 名称，通常传入 __name__
      """

      def __init__(self, name: str) -> None:
          self._log: Any = structlog.get_logger(name)

      def debug(self, event: str, **kw: Any) -> None:
          """DEBUG 级别日志，完整记录所有结构化字段。"""
          self._log.debug(event, **kw)

      def info(self, event: str, **kw: Any) -> None:
          """INFO 级别日志。"""
          self._log.info(event, **kw)

      def warning(self, event: str, **kw: Any) -> None:
          """WARNING 级别日志。"""
          self._log.warning(event, **kw)

      def error(self, event: str, **kw: Any) -> None:
          """ERROR 级别日志。传入 exc_info=True 可附加当前异常 traceback。"""
          self._log.error(event, **kw)

      def bind(self, **kw: Any) -> "AppLogger":
          """返回绑定了固定上下文字段的新 AppLogger 实例。

          原实例不受影响。适合在类 __init__ 中绑定 provider 等固定字段：

              self._log = AppLogger(__name__).bind(provider="fmp")
          """
          bound = AppLogger.__new__(AppLogger)
          bound._log = self._log.bind(**kw)
          return bound


  def get_logger(name: str) -> AppLogger:
      """工厂函数，等价于 AppLogger(name)。

      Args:
          name: logger 名称，通常传入 __name__

      Returns:
          AppLogger 实例
      """
      return AppLogger(name)
  ```

- [ ] **Step 2: 验证 AppLogger 可用**

  ```bash
  uv run python -c "
  from deepalpha.core.logging.setup import setup_logging
  from deepalpha.core.logging.logger import AppLogger, get_logger
  setup_logging()
  log = AppLogger('test.module')
  log.info('AppLogger OK', key='value')
  log2 = log.bind(provider='fmp')
  log2.debug('bound logger', symbol='AAPL')
  log3 = get_logger('test.factory')
  log3.warning('factory OK')
  print('PASS')
  "
  ```

  Expected：控制台打印 3 条日志（只有 INFO/WARNING 可见），打印 `PASS`。

- [ ] **Step 3: Commit**

  ```bash
  git add src/deepalpha/core/logging/logger.py
  git commit -m "feat(core/logging): add AppLogger public logger class"
  ```

---

### Task 5: 创建 @log_call 装饰器

**Files:**
- Create: `src/deepalpha/core/logging/decorators.py`

- [ ] **Step 1: 创建 decorators.py**

  创建 `src/deepalpha/core/logging/decorators.py`：

  ```python
  """@log_call 装饰器：自动记录 infrastructure 层方法的入参、出参、耗时和异常。

  用法：
      @log_call("fmp")
      async def get(self, path: str, **params: Any) -> Any:
          ...
  """

  import functools
  import inspect
  import logging
  import time
  from collections.abc import Callable
  from typing import Any

  from deepalpha.core.logging.exceptions import DeepAlphaInfraError
  from deepalpha.core.logging.logger import AppLogger

  # 需要脱敏的参数名（小写匹配）
  _SENSITIVE_KEYS = {"apikey", "api_key", "token", "password", "secret"}


  def _sanitize(params: dict[str, Any]) -> dict[str, Any]:
      """将敏感字段值替换为 '***'。"""
      return {k: "***" if k.lower() in _SENSITIVE_KEYS else v for k, v in params.items()}


  def _summarize(result: Any) -> str:
      """返回结果摘要（用于 INFO 级别）。"""
      if isinstance(result, list):
          if result:
              return f"{len(result)} x {type(result[0]).__name__}"
          return "[] (empty)"
      if result is None:
          return "None"
      return type(result).__name__


  def _extract_call_args(func: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
      """从 args/kwargs 中提取命名参数（排除 self/cls），并脱敏。"""
      try:
          sig = inspect.signature(func)
          bound = sig.bind(*args, **kwargs)
          bound.apply_defaults()
          call_args = {k: v for k, v in bound.arguments.items() if k not in ("self", "cls")}
      except TypeError:
          call_args = dict(kwargs)
      return _sanitize(call_args)


  def log_call(provider: str) -> Callable:
      """装饰器工厂，为 infrastructure 方法添加结构化日志和统一异常包装。

      Args:
          provider: 来源标识，如 "fmp"、"finnhub"、"cache"、"db"、"base"

      Returns:
          装饰器，支持 async 和 sync 函数
      """

      def decorator(func: Callable) -> Callable:
          logger = AppLogger(f"deepalpha.{provider}").bind(provider=provider)
          method = func.__name__

          if inspect.iscoroutinefunction(func):
              @functools.wraps(func)
              async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                  call_args = _extract_call_args(func, args, kwargs)
                  logger.info(f"调用 {method}", method=method, **call_args)
                  start = time.perf_counter()
                  try:
                      result = await func(*args, **kwargs)
                      elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                      if logging.getLogger().isEnabledFor(logging.DEBUG):
                          logger.debug(
                              f"{method} 完成",
                              method=method,
                              result=repr(result),
                              elapsed_ms=elapsed_ms,
                          )
                      else:
                          logger.info(
                              f"{method} 完成",
                              method=method,
                              result_summary=_summarize(result),
                              elapsed_ms=elapsed_ms,
                          )
                      return result
                  except DeepAlphaInfraError:
                      # 已包装过，直接重抛，不重复包装
                      raise
                  except Exception as exc:
                      elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                      logger.error(
                          f"{method} 异常",
                          method=method,
                          exc_type=type(exc).__name__,
                          exc_msg=str(exc),
                          elapsed_ms=elapsed_ms,
                          exc_info=True,
                      )
                      raise DeepAlphaInfraError(provider, method, exc) from exc

              return async_wrapper

          else:
              @functools.wraps(func)
              def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                  call_args = _extract_call_args(func, args, kwargs)
                  logger.info(f"调用 {method}", method=method, **call_args)
                  start = time.perf_counter()
                  try:
                      result = func(*args, **kwargs)
                      elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                      if logging.getLogger().isEnabledFor(logging.DEBUG):
                          logger.debug(
                              f"{method} 完成",
                              method=method,
                              result=repr(result),
                              elapsed_ms=elapsed_ms,
                          )
                      else:
                          logger.info(
                              f"{method} 完成",
                              method=method,
                              result_summary=_summarize(result),
                              elapsed_ms=elapsed_ms,
                          )
                      return result
                  except DeepAlphaInfraError:
                      raise
                  except Exception as exc:
                      elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                      logger.error(
                          f"{method} 异常",
                          method=method,
                          exc_type=type(exc).__name__,
                          exc_msg=str(exc),
                          elapsed_ms=elapsed_ms,
                          exc_info=True,
                      )
                      raise DeepAlphaInfraError(provider, method, exc) from exc

              return sync_wrapper

      return decorator
  ```

- [ ] **Step 2: 验证装饰器可用（sync 和 async 均测试）**

  ```bash
  uv run python -c "
  import asyncio
  from deepalpha.core.logging.setup import setup_logging
  from deepalpha.core.logging.decorators import log_call
  from deepalpha.core.logging.exceptions import DeepAlphaInfraError

  setup_logging()

  @log_call('test')
  def sync_func(x: int, password: str = 'secret') -> list[int]:
      return [x, x + 1]

  @log_call('test')
  async def async_func(symbol: str, apikey: str = 'abc123') -> dict:
      return {'symbol': symbol}

  @log_call('test')
  async def error_func() -> None:
      raise ValueError('boom')

  # sync
  result = sync_func(42, password='should_be_hidden')
  assert result == [42, 43], result

  # async success
  result2 = asyncio.run(async_func('AAPL', apikey='should_be_hidden'))
  assert result2 == {'symbol': 'AAPL'}

  # async error -> DeepAlphaInfraError
  try:
      asyncio.run(error_func())
      assert False, 'should raise'
  except DeepAlphaInfraError as e:
      assert e.provider == 'test'
      assert e.method == 'error_func'
      assert isinstance(e.original, ValueError)

  print('PASS')
  "
  ```

  Expected：控制台打印日志（apikey/password 显示 `***`），最终打印 `PASS`。

- [ ] **Step 3: Commit**

  ```bash
  git add src/deepalpha/core/logging/decorators.py
  git commit -m "feat(core/logging): add @log_call decorator with sanitization and exception wrapping"
  ```

---

### Task 6: 完成 __init__.py 导出

**Files:**
- Modify: `src/deepalpha/core/logging/__init__.py`

- [ ] **Step 1: 填充 __init__.py**

  将 `src/deepalpha/core/logging/__init__.py` 改为：

  ```python
  """DeepAlpha 统一日志模块。

  快速上手：
      from deepalpha.core.logging import setup_logging, AppLogger, get_logger, log_call

      # 应用启动时调用一次
      setup_logging()

      # 任意模块手动记日志
      logger = AppLogger(__name__)
      logger.info("事件描述", key="value")

      # infrastructure 方法自动日志 + 异常包装
      @log_call("fmp")
      async def my_method(self, symbol: str) -> list:
          ...
  """

  from deepalpha.core.logging.decorators import log_call
  from deepalpha.core.logging.exceptions import DeepAlphaInfraError
  from deepalpha.core.logging.logger import AppLogger, get_logger
  from deepalpha.core.logging.setup import setup_logging

  __all__ = [
      "setup_logging",
      "AppLogger",
      "get_logger",
      "log_call",
      "DeepAlphaInfraError",
  ]
  ```

- [ ] **Step 2: 验证顶层 import**

  ```bash
  uv run python -c "
  from deepalpha.core.logging import setup_logging, AppLogger, get_logger, log_call, DeepAlphaInfraError
  print('all exports OK')
  "
  ```

  Expected：`all exports OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/deepalpha/core/logging/__init__.py
  git commit -m "feat(core/logging): wire up __init__.py exports"
  ```

---

### Task 7: 改造 BaseLoader（providers/base.py）

**Files:**
- Modify: `src/deepalpha/infrastructure/providers/base.py`

- [ ] **Step 1: 为 _get、_get_list、_to_models 添加 @log_call**

  在文件顶部导入区添加：

  ```python
  from deepalpha.core.logging import log_call
  ```

  在 `_get` 方法上方添加装饰器：

  ```python
  @log_call("base")
  async def _get(self, endpoint: str, **params: Any) -> dict[str, Any]:
  ```

  在 `_get_list` 方法上方添加装饰器：

  ```python
  @log_call("base")
  async def _get_list(self, endpoint: str, **params: Any) -> list[dict[str, Any]]:
  ```

  在 `_to_models` 方法上方添加装饰器：

  ```python
  @log_call("base")
  def _to_models(
      self, records: list[dict[str, Any]], model: type[M]
  ) -> list[M]:
  ```

- [ ] **Step 2: 验证 import 正常**

  ```bash
  uv run python -c "from deepalpha.infrastructure.providers.base import BaseLoader; print('OK')"
  ```

  Expected：`OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/deepalpha/infrastructure/providers/base.py
  git commit -m "feat(infra/base): add @log_call to BaseLoader._get, _get_list, _to_models"
  ```

---

### Task 8: 改造 FMPAsyncClient（providers/fmp/client.py）

**Files:**
- Modify: `src/deepalpha/infrastructure/providers/fmp/client.py`

- [ ] **Step 1: 为 get 方法添加 @log_call**

  在文件顶部导入区添加：

  ```python
  from deepalpha.core.logging import log_call
  ```

  在 `get` 方法上方添加装饰器：

  ```python
  @log_call("fmp")
  async def get(self, path: str, **params: Any) -> Any:
  ```

- [ ] **Step 2: 验证 import 正常**

  ```bash
  uv run python -c "from deepalpha.infrastructure.providers.fmp.client import FMPAsyncClient; print('OK')"
  ```

  Expected：`OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/deepalpha/infrastructure/providers/fmp/client.py
  git commit -m "feat(infra/fmp): add @log_call to FMPAsyncClient.get"
  ```

---

### Task 9: 改造 FinnhubClient（providers/finnhub/client.py）

**Files:**
- Modify: `src/deepalpha/infrastructure/providers/finnhub/client.py`

- [ ] **Step 1: 为 _get 方法添加 @log_call**

  在文件顶部导入区添加：

  ```python
  from deepalpha.core.logging import log_call
  ```

  在 `_get` 方法上方添加装饰器：

  ```python
  @log_call("finnhub")
  async def _get(self, path: str, **params: Any) -> Any:
  ```

- [ ] **Step 2: 验证 import 正常**

  ```bash
  uv run python -c "from deepalpha.infrastructure.providers.finnhub.client import FinnhubClient; print('OK')"
  ```

  Expected：`OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/deepalpha/infrastructure/providers/finnhub/client.py
  git commit -m "feat(infra/finnhub): add @log_call to FinnhubClient._get"
  ```

---

### Task 10: 改造 ConceptCache（cache/concept_cache.py）

**Files:**
- Modify: `src/deepalpha/infrastructure/cache/concept_cache.py`

- [ ] **Step 1: 为所有 public 方法添加 @log_call**

  在文件顶部导入区添加：

  ```python
  from deepalpha.core.logging import log_call
  ```

  为以下 4 个方法各加装饰器（紧贴 `async def` 上方）：

  ```python
  @log_call("cache")
  async def get_concept(self, name: str) -> list[ConceptStock] | None:
  ```

  ```python
  @log_call("cache")
  async def set_concept(self, name: str, stocks: list[ConceptStock]) -> None:
  ```

  ```python
  @log_call("cache")
  async def get_list(self) -> list[ConceptSummary] | None:
  ```

  ```python
  @log_call("cache")
  async def set_list(self, summaries: list[ConceptSummary]) -> None:
  ```

- [ ] **Step 2: 验证 import 正常**

  ```bash
  uv run python -c "from deepalpha.infrastructure.cache.concept_cache import ConceptCache; print('OK')"
  ```

  Expected：`OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/deepalpha/infrastructure/cache/concept_cache.py
  git commit -m "feat(infra/cache): add @log_call to ConceptCache public methods"
  ```

---

### Task 11: 改造 ConceptRepo（db/concept_repo.py）

**Files:**
- Modify: `src/deepalpha/infrastructure/db/concept_repo.py`

- [ ] **Step 1: 为所有 public async 方法添加 @log_call**

  在文件顶部导入区添加：

  ```python
  from deepalpha.core.logging import log_call
  ```

  为以下 7 个 public 方法各加装饰器（`initialize` 为内部启动方法，不装饰）：

  ```python
  @log_call("db")
  async def replace_etf_map(self, records: list[ConceptEtfMap]) -> None:
  ```

  ```python
  @log_call("db")
  async def upsert_etf_map(self, records: list[ConceptEtfMap]) -> None:
  ```

  ```python
  @log_call("db")
  async def load_etf_map(self) -> list[ConceptEtfMap]:
  ```

  ```python
  @log_call("db")
  async def get_etfs_by_concept(self, concept: str) -> list[ConceptEtfMap]:
  ```

  ```python
  @log_call("db")
  async def upsert_stocks(self, date: datetime.date, records: list[ConceptStock]) -> None:
  ```

  ```python
  @log_call("db")
  async def get_latest_stocks(self, concept: str) -> list[ConceptStock]:
  ```

  ```python
  @log_call("db")
  async def get_all_summaries(self) -> list[ConceptSummary]:
  ```

  ```python
  @log_call("db")
  async def get_stocks_history(
      self, concept: str, start: datetime.date, end: datetime.date
  ) -> list[ConceptStock]:
  ```

- [ ] **Step 2: 验证 import 正常**

  ```bash
  uv run python -c "from deepalpha.infrastructure.db.concept_repo import ConceptRepo; print('OK')"
  ```

  Expected：`OK`

- [ ] **Step 3: Commit**

  ```bash
  git add src/deepalpha/infrastructure/db/concept_repo.py
  git commit -m "feat(infra/db): add @log_call to ConceptRepo public methods"
  ```

---

### Task 12: FastAPI lifespan 集成

**Files:**
- Modify: `src/deepalpha/interface/web/deps.py:1-12`

- [ ] **Step 1: 在 lifespan 最开始调用 setup_logging()**

  在 `deps.py` 的 import 区添加：

  ```python
  from deepalpha.core.logging import setup_logging
  ```

  在 `lifespan` 函数体第一行添加（`cfg = get_config()` 之前）：

  ```python
  setup_logging()
  ```

  修改后 lifespan 函数头部为：

  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI) -> AsyncIterator[None]:
      global _services, _pool, _cache
      setup_logging()
      cfg = get_config()
      ...
  ```

- [ ] **Step 2: 验证应用启动无错误**

  ```bash
  uv run python -c "
  from deepalpha.interface.web.deps import lifespan
  print('lifespan import OK')
  "
  ```

  Expected：`lifespan import OK`

- [ ] **Step 3: 运行现有单元测试确认无回归**

  ```bash
  uv run pytest tests/unit/ -x -q
  ```

  Expected：所有测试通过，无 FAILED。

- [ ] **Step 4: Commit**

  ```bash
  git add src/deepalpha/interface/web/deps.py
  git commit -m "feat(web): call setup_logging() at FastAPI lifespan startup"
  ```

---

## 完成标准

- `~/logs/deepalpha-club-data/deepalpha.log` 在应用启动后自动创建
- 每次 FMP/Finnhub 请求、Cache 读写、DB 操作均有 INFO 日志（含 provider、method、耗时）
- DEBUG 级别下日志包含完整入参和返回值
- apikey/token/password 字段在日志中显示为 `***`
- 任何异常均以 ERROR 级别记录完整 traceback，并包装为 `DeepAlphaInfraError` 抛出
- `from deepalpha.core.logging import AppLogger` 在任意模块可用
