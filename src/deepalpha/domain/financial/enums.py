"""financial 领域枚举（domain 层，零外部依赖）"""
from enum import Enum


class StatementPeriod(str, Enum):
    """财务报告期枚举，支持年度、季度和滚动12个月（TTM）。"""

    ANNUAL  = "annual"
    QUARTER = "quarter"
    TTM     = "ttm"
