# src/deepalpha/providers/fmp/errors.py

class FMPError(Exception):
    """FMP 客户端异常基类"""

class FMPAuthError(FMPError):
    """401 — API Key 无效或过期"""

class FMPRateLimitError(FMPError):
    """429 — 超出速率限制"""

class FMPNotFoundError(FMPError):
    """404 或空响应 — 标的不存在"""

class FMPServerError(FMPError):
    """5xx — FMP 服务端错误"""
