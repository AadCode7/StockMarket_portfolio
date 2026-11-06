from abc import ABC, abstractmethod
from datetime import date
from app.schemas import PriceBar

class MarketDataError(RuntimeError):
    pass

class MarketDataProvider(ABC):
    @abstractmethod
    async def get_daily_history(self, symbol: str, exchange: str, start: date, end: date) -> list[PriceBar]:
        raise NotImplementedError

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
                if rows:
                    return rows
                failures.append(f"{name}: returned no rows")
            except Exception as exc:
                failures.append(f"{name}: {type(exc).__name__}")
        raise MarketDataError("All configured providers failed: " + "; ".join(failures))
