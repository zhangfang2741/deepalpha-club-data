# src/deepalpha/loaders/enums.py
from enum import Enum


class AssetClass(str, Enum):
    """资产类别枚举，用于区分不同市场标的类型。"""

    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    MUTUAL_FUND = "mutual_fund"


class Interval(str, Enum):
    """K线时间周期枚举，从分钟级到月线。"""

    ONE_MIN     = "1m"
    FIVE_MIN    = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN  = "30m"
    ONE_HOUR    = "1h"
    FOUR_HOUR   = "4h"
    ONE_DAY     = "1d"
    ONE_WEEK    = "1w"
    ONE_MONTH   = "1mo"


class StatementPeriod(str, Enum):
    """财务报告期枚举，支持年度、季度和滚动12个月（TTM）。"""

    ANNUAL  = "annual"
    QUARTER = "quarter"
    TTM     = "ttm"


class IndicatorType(str, Enum):
    """技术分析指标类型枚举。

    FMP Start 会员支持：SMA/EMA/DEMA/TEMA/WMA/RSI/ADX/WILLIAMS/STD_DEV（9种）。
    其余指标（MACD/STOCH/CCI/AROON/BBANDS/ATR/OBV）需通过其他 provider 实现。
    """

    SMA      = "sma"
    EMA      = "ema"
    DEMA     = "dema"
    TEMA     = "tema"
    WMA      = "wma"
    RSI      = "rsi"
    MACD     = "macd"
    STOCH    = "stoch"
    CCI      = "cci"
    WILLIAMS = "williams"
    ADX      = "adx"
    AROON    = "aroon"
    BBANDS   = "bbands"
    ATR      = "atr"
    STD_DEV  = "std_dev"
    OBV      = "obv"


class MoverDirection(str, Enum):
    """市场涨跌榜方向枚举。"""

    GAINERS = "gainers"
    LOSERS  = "losers"
    ACTIVE  = "active"


class CongressChamber(str, Enum):
    """美国国会议院枚举（仅适用于美国市场数据）。"""

    SENATE = "senate"
    HOUSE  = "house"
