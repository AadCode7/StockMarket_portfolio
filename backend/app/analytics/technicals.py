from __future__ import annotations

from collections.abc import Sequence
import math
import pandas as pd
from app.schemas import PriceBar

def calculate_technicals(bars: Sequence[PriceBar]) -> dict:
    """Calculate reproducible indicators from chronological daily close prices."""
    ordered = sorted(bars, key=lambda item: item.trading_date)
    if not ordered:
        raise ValueError("At least one price bar is required")
    frame = pd.DataFrame({
        "date": [item.trading_date.isoformat() for item in ordered],
        "close": [item.adjusted_close if item.adjusted_close is not None else item.close for item in ordered],
        "volume": [item.volume for item in ordered],
    }).drop_duplicates("date").sort_values("date")
    close = frame["close"].astype(float)
    returns = close.pct_change()
    sma = {str(window): _last_or_none(close.rolling(window).mean()) for window in (20, 50, 200)}
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    delta = close.diff()
    gains = delta.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    losses = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    relative_strength = gains / losses.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + relative_strength))
    rsi = rsi.mask((losses == 0) & (gains > 0), 100.0)
    rsi = rsi.mask((gains == 0) & (losses > 0), 0.0)
    rsi = rsi.mask((gains == 0) & (losses == 0), 50.0)
    volatility = float(returns.tail(20).std(ddof=1) * math.sqrt(252)) if len(returns.dropna()) >= 20 else None
    drawdown = close / close.cummax() - 1
    latest = ordered[-1]
    return {
        "symbol": latest.symbol, "exchange": latest.exchange,
        "as_of": latest.trading_date.isoformat(), "observations": int(len(frame)),
        "close": float(close.iloc[-1]), "sma": sma,
        "rsi_14": _last_or_none(rsi), "macd": _last_or_none(macd),
        "macd_signal": _last_or_none(signal), "macd_histogram": _last_or_none(macd - signal),
        "annualised_volatility_20d": volatility,
        "maximum_drawdown_in_window": float(drawdown.min()),
        "data_provider": latest.provider, "retrieved_at": latest.retrieved_at.isoformat(),
        "note": "Indicators use adjusted close when supplied; otherwise unadjusted close. They are descriptive, not trading signals.",
    }

def _last_or_none(series: pd.Series) -> float | None:
    if series.empty or pd.isna(series.iloc[-1]):
        return None
    return float(series.iloc[-1])
