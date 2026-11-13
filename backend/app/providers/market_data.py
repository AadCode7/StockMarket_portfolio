from abc import ABC, abstractmethod
from datetime import date
import math
from app.schemas import PriceBar

class MarketDataError(RuntimeError):
    pass

class MarketDataProvider(ABC):
    @abstractmethod
    async def get_daily_history(self, symbol: str, exchange: str, start: date, end: date) -> list[PriceBar]:
        raise NotImplementedError

def validate_price_bars(rows: list[PriceBar], symbol: str, exchange: str, start: date, end: date) -> list[PriceBar]:
    if not rows:
        raise MarketDataError("Provider returned no rows")
    by_date: dict[date, PriceBar] = {}
    for bar in rows:
        if bar.exchange != exchange:
            raise MarketDataError("Provider returned a bar for the wrong exchange")
        if not start <= bar.trading_date <= end:
            raise MarketDataError("Provider returned data outside the requested date range")
        prices = (bar.open, bar.high, bar.low, bar.close)
        if not all(math.isfinite(value) and value > 0 for value in prices):
            raise MarketDataError("Provider returned a non-finite or non-positive OHLC value")
        if bar.high < max(bar.open, bar.close, bar.low) or bar.low > min(bar.open, bar.close, bar.high):
            raise MarketDataError("Provider returned inconsistent OHLC values")
        if bar.volume < 0:
            raise MarketDataError("Provider returned negative volume")
        by_date[bar.trading_date] = bar
    return [by_date[day] for day in sorted(by_date)]

class MarketDataRouter:
    def __init__(self, providers: dict[str, MarketDataProvider], order: list[str]) -> None:
        self.providers = providers
        self.order = order

    async def get_daily_history(self, symbol: str, exchange: str, start: date, end: date) -> list[PriceBar]:
        failures: list[str] = []
        for name in self.order:
            provider = self.providers.get(name)
            if provider is None:
                failures.append(f"{name}: not configured")
                continue
            try:
                rows = await provider.get_daily_history(symbol, exchange, start, end)
                return validate_price_bars(rows, symbol, exchange, start, end)
            except Exception as exc:
                failures.append(f"{name}: {type(exc).__name__}")
        raise MarketDataError("All configured providers failed: " + "; ".join(failures))
