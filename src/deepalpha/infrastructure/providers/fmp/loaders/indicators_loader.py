import datetime
from typing import Any

from deepalpha.domain.market.enums import IndicatorType, Interval
from deepalpha.infrastructure.providers.base import BaseLoader
from deepalpha.domain.market.models import IndicatorRow
from deepalpha.infrastructure.providers.fmp.errors import FMPError

_FMP_INDICATOR_PATHS: dict[IndicatorType, str] = {
    IndicatorType.SMA:      "sma",
    IndicatorType.EMA:      "ema",
    IndicatorType.DEMA:     "dema",
    IndicatorType.TEMA:     "tema",
    IndicatorType.WMA:      "wma",
    IndicatorType.RSI:      "rsi",
    IndicatorType.ADX:      "adx",
    IndicatorType.WILLIAMS: "williams",
    IndicatorType.STD_DEV:  "standardDeviation",
}

_FMP_INDICATOR_FIELD: dict[IndicatorType, str] = {
    IndicatorType.SMA:      "sma",
    IndicatorType.EMA:      "ema",
    IndicatorType.DEMA:     "dema",
    IndicatorType.TEMA:     "tema",
    IndicatorType.WMA:      "wma",
    IndicatorType.RSI:      "rsi",
    IndicatorType.ADX:      "adx",
    IndicatorType.WILLIAMS: "williams",
    IndicatorType.STD_DEV:  "standardDeviation",
}

_FMP_TIMEFRAME: dict[Interval, str] = {
    Interval.ONE_MIN:     "1min",
    Interval.FIVE_MIN:    "5min",
    Interval.FIFTEEN_MIN: "15min",
    Interval.THIRTY_MIN:  "30min",
    Interval.ONE_HOUR:    "1hour",
    Interval.FOUR_HOUR:   "4hour",
    Interval.ONE_DAY:     "1day",
}


class FMPTechnicalIndicatorLoader(BaseLoader):
    """FMP Start 会员技术指标加载器。

    支持的指标（9 种）：SMA, EMA, DEMA, TEMA, WMA, RSI, ADX, WILLIAMS, STD_DEV。
    不支持的指标（需 Alpha Vantage 等 provider）：MACD, STOCH, CCI, AROON, BBANDS, ATR, OBV。
    调用不支持的指标会抛出 FMPError。
    """

    async def get_indicator(
        self,
        symbol: str,
        indicator: IndicatorType,
        period: int,
        interval: Interval = Interval.ONE_DAY,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> list[IndicatorRow]:
        path_segment = _FMP_INDICATOR_PATHS.get(indicator)
        if path_segment is None:
            raise FMPError(
                f"FMP Start 不支持指标 {indicator}，支持的指标: "
                + ", ".join(str(k) for k in _FMP_INDICATOR_PATHS.keys())
            )
        timeframe = _FMP_TIMEFRAME.get(interval, "1day")
        params: dict[str, Any] = {
            "symbol": symbol,
            "periodLength": period,
            "timeframe": timeframe,
        }
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)
        records = await self._get_list(f"/stable/technical-indicators/{path_segment}", **params)
        field_name = _FMP_INDICATOR_FIELD.get(indicator, indicator.value)
        for r in records:
            if field_name in r and "value" not in r:
                r["value"] = r[field_name]
        return self._to_models(records, IndicatorRow)
