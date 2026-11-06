from datetime import date, datetime, timezone
import httpx
from app.config import settings
from app.providers.market_data import MarketDataError, MarketDataProvider
from app.schemas import PriceBar

class AlphaVantageProvider(MarketDataProvider):
    async def get_daily_history(self, symbol: str, exchange: str, start: date, end: date) -> list[PriceBar]:
        if not settings.alpha_vantage_api_key:
            raise MarketDataError("ALPHA_VANTAGE_API_KEY is not configured")
        params = {
            "function": "TIME_SERIES_DAILY", "symbol": symbol.upper(),
            "outputsize": "full", "apikey": settings.alpha_vantage_api_key,
        }
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.get("https://www.alphavantage.co/query", params=params)
            response.raise_for_status()
            payload = response.json()
        series = payload.get("Time Series (Daily)")
        if not series:
            reason = payload.get("Note") or payload.get("Information") or payload.get("Error Message")
            raise MarketDataError(f"Alpha Vantage returned no daily series: {reason or 'unknown response'}")
        retrieved = datetime.now(timezone.utc)
        rows = []
        for day, values in series.items():
            trading_day = date.fromisoformat(day)
            if start <= trading_day <= end:
                rows.append(PriceBar(
                    symbol=symbol.upper(), exchange=exchange.upper(), trading_date=trading_day,
                    open=float(values["1. open"]), high=float(values["2. high"]),
                    low=float(values["3. low"]), close=float(values["4. close"]),
                    volume=int(values["5. volume"]), provider="alpha_vantage",
                    retrieved_at=retrieved, is_delayed=True,
                ))
        return sorted(rows, key=lambda item: item.trading_date)
