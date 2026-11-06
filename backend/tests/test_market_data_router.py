from datetime import date
import pytest
from app.providers.market_data import MarketDataError, MarketDataProvider, MarketDataRouter

class FailingProvider(MarketDataProvider):
    async def get_daily_history(self, symbol, exchange, start, end):
        raise RuntimeError("provider offline")

class EmptyProvider(MarketDataProvider):
    async def get_daily_history(self, symbol, exchange, start, end):
        return []

@pytest.mark.asyncio
async def test_router_reports_all_provider_failures():
    router = MarketDataRouter({"offline": FailingProvider(), "empty": EmptyProvider()}, ["offline", "empty"])
    with pytest.raises(MarketDataError):
        await router.get_daily_history("RELIANCE", "NSE", date(2024, 1, 1), date(2024, 1, 31))
