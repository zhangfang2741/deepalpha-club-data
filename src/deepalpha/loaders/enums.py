# src/deepalpha/loaders/enums.py
from enum import StrEnum

class AssetClass(StrEnum):
    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    MUTUAL_FUND = "mutual_fund"

class Interval(StrEnum):
    ONE_MIN     = "1m"
    FIVE_MIN    = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN  = "30m"
    ONE_HOUR    = "1h"
    FOUR_HOUR   = "4h"
    ONE_DAY     = "1d"
    ONE_WEEK    = "1w"
    ONE_MONTH   = "1mo"

class StatementPeriod(StrEnum):
    ANNUAL  = "annual"
    QUARTER = "quarter"
    TTM     = "ttm"

class IndicatorType(StrEnum):
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

class MoverDirection(StrEnum):
    GAINERS = "gainers"
    LOSERS  = "losers"
    ACTIVE  = "active"

class CongressChamber(StrEnum):
    SENATE = "senate"
    HOUSE  = "house"
