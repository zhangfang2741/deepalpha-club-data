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
