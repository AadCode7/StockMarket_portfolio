import asyncio
import math
from datetime import date, datetime, timezone
import yfinance as yf
from app.schemas import PriceBar
from app.providers.market_data import MarketDataProvider

class YahooFinanceProvider(MarketDataProvider):
    async def get_daily_history(self, symbol: str, exchange: str, start: date, end: date) -> list[PriceBar]:
        ticker = symbol.upper()
        suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
        if not ticker.endswith((".NS", ".BO")):
            ticker += suffix
        frame = await asyncio.to_thread(
            lambda: yf.Ticker(ticker).history(
                start=start.isoformat(), end=end.isoformat(), interval="1d",
                auto_adjust=False, actions=False,
            )
        )
        if frame.empty:
            return []
        retrieved = datetime.now(timezone.utc)
        rows = []
        for timestamp, row in frame.iterrows():
            adjusted = row.get("Adj Close")
            adjusted_value = None
            if adjusted is not None and math.isfinite(float(adjusted)) and float(adjusted) > 0:
                adjusted_value = float(adjusted)
            rows.append(PriceBar(
                symbol=symbol.upper(), exchange=exchange.upper(), trading_date=timestamp.date(),
                open=float(row["Open"]), high=float(row["High"]), low=float(row["Low"]),
                close=float(row["Close"]), adjusted_close=adjusted_value,
                volume=int(row["Volume"]), provider="yfinance", retrieved_at=retrieved,
                is_delayed=True,
            ))
        return rows
