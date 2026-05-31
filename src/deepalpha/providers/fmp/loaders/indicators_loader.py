import datetime
import polars as pl
from deepalpha.loaders.indicators_loader import AbstractTechnicalIndicatorLoader
from deepalpha.loaders.enums import IndicatorType, Interval
from deepalpha.models.indicators import IndicatorRow
from deepalpha.providers.fmp.errors import FMPError

_FMP_INDICATOR_PATHS: dict[IndicatorType, str] = {
    IndicatorType.SMA:      "simple-moving-average",
    IndicatorType.EMA:      "exponential-moving-average",
    IndicatorType.DEMA:     "double-exponential-moving-average",
    IndicatorType.TEMA:     "triple-exponential-moving-average",
    IndicatorType.WMA:      "weighted-moving-average",
    IndicatorType.RSI:      "relative-strength-index",
    IndicatorType.ADX:      "average-directional-index",
    IndicatorType.WILLIAMS: "williams-percent-range",
    IndicatorType.STD_DEV:  "standard-deviation",
}

class FMPTechnicalIndicatorLoader(AbstractTechnicalIndicatorLoader):
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
    ) -> pl.DataFrame:
        path_segment = _FMP_INDICATOR_PATHS.get(indicator)
        if path_segment is None:
            raise FMPError(
                f"FMP Start 不支持指标 {indicator}，支持的指标: "
                + ", ".join(str(k) for k in _FMP_INDICATOR_PATHS.keys())
            )
        params: dict[str, str | int] = {
            "period": period,
            "type": interval.value,
        }
        if start:
            params["from"] = str(start)
        if end:
            params["to"] = str(end)
        records = await self._get_list(f"/stable/{path_segment}/{symbol}", **params)
        return self._to_df(records, IndicatorRow)
