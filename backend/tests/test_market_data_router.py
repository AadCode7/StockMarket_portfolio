from datetime import date, datetime, timezone
import pytest
from app.providers.market_data import MarketDataError, MarketDataProvider, MarketDataRouter, validate_price_bars
from app.schemas import PriceBar

class FailingProvider(MarketDataProvider):
    async def get_daily_history(self, symbol, exchange, start, end):
        raise RuntimeError("provider offline")

class EmptyProvider(MarketDataProvider):
    async def get_daily_history(self, symbol, exchange, start, end):
        return []

class InvalidProvider(MarketDataProvider):
    async def get_daily_history(self, symbol, exchange, start, end):
        return [PriceBar(
            symbol=symbol, exchange=exchange, trading_date=start,
            open=10, high=8, low=9, close=10, volume=100,
            provider="invalid", retrieved_at=datetime.now(timezone.utc),
        )]

class GoodProvider(MarketDataProvider):
    async def get_daily_history(self, symbol, exchange, start, end):
        return [PriceBar(
            symbol=symbol, exchange=exchange, trading_date=start,
            open=10, high=11, low=9, close=10.5, volume=100,
            provider="good", retrieved_at=datetime.now(timezone.utc),
        )]

@pytest.mark.asyncio
async def test_router_reports_all_provider_failures():
    router = MarketDataRouter({"offline": FailingProvider(), "empty": EmptyProvider()}, ["offline", "empty"])
    with pytest.raises(MarketDataError):
        await router.get_daily_history("RELIANCE", "NSE", date(2024, 1, 1), date(2024, 1, 31))

@pytest.mark.asyncio
async def test_router_falls_back_after_invalid_provider_data():
    router = MarketDataRouter({"bad": InvalidProvider(), "good": GoodProvider()}, ["bad", "good"])
    rows = await router.get_daily_history("RELIANCE", "NSE", date(2024, 1, 1), date(2024, 1, 31))
    assert len(rows) == 1
    assert rows[0].provider == "good"
