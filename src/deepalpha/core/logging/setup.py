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
