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
