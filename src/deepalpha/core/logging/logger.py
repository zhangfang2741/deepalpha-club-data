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
