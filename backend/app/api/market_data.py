from datetime import date, datetime, timedelta, timezone
import logging
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from app.analytics.technicals import calculate_technicals
from app.config import settings
from app.providers.factory import build_market_data_router
from app.providers.market_data import MarketDataError
from app.schemas import PriceBar
from app.services.supabase_rest import SupabaseRestClient, SupabaseRestError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market-data", tags=["market-data"])

async def _cached_rows(symbol: str, exchange: str, start: date, end: date):
    admin = SupabaseRestClient(service_role=True)
    key = "nse_symbol" if exchange == "NSE" else "bse_symbol"
    instruments = await admin.select("instruments", {"select": "id", key: f"eq.{symbol.upper()}", "limit": "1"})
    if not instruments:
        return None, None
    instrument_id = instruments[0]["id"]
    rows = await admin.select_all("price_history", {
        "select": "trading_date,open,high,low,close,adjusted_close,volume,provider,retrieved_at",
        "instrument_id": f"eq.{instrument_id}", "exchange": f"eq.{exchange}",
        "trading_date": f"gte.{start.isoformat()}",
        "and": f"(trading_date.lte.{end.isoformat()})",
        "order": "trading_date.asc", "limit": "5000",
    })
    return instrument_id, rows

def _to_bars(rows: list[dict], symbol: str, exchange: str) -> list[PriceBar]:
    bars = []
    for row in rows:
        retrieved = datetime.fromisoformat(row["retrieved_at"].replace("Z", "+00:00"))
        bars.append(PriceBar(
            symbol=symbol.upper(), exchange=exchange, trading_date=date.fromisoformat(row["trading_date"]),
            open=float(row["open"]), high=float(row["high"]), low=float(row["low"]),
            close=float(row["close"]), adjusted_close=float(row["adjusted_close"]) if row.get("adjusted_close") is not None else None,
            volume=int(row["volume"]), provider=row["provider"], retrieved_at=retrieved,
        ))
    return bars

async def fetch_and_store(symbol: str, exchange: str, start: date, end: date):
    admin = None
    instrument_id = None
    cached = []
    try:
        admin = SupabaseRestClient(service_role=True)
        instrument_id, cached_rows = await _cached_rows(symbol, exchange, start, end)
        cached = _to_bars(cached_rows or [], symbol, exchange)
        if cached and settings.market_data_cache_seconds > 0:
            newest_fetch = max(bar.retrieved_at for bar in cached)
            coverage_ok = cached[0].trading_date <= start + timedelta(days=7) and cached[-1].trading_date >= end - timedelta(days=7)
            cache_fresh = (datetime.now(timezone.utc) - newest_fetch).total_seconds() <= settings.market_data_cache_seconds
            if coverage_ok and cache_fresh:
                return cached
    except SupabaseRestError as exc:
        if "SUPABASE_SERVICE_ROLE_KEY is not configured" not in str(exc):
            logger.warning("Market data cache unavailable: %s", exc)
        admin = None

    try:
        bars = await build_market_data_router().get_daily_history(symbol, exchange, start, end)
    except MarketDataError:
        if cached:
            logger.warning("All live providers failed; returning previously stored daily bars for %s", symbol)
            return cached
        raise

    if admin and instrument_id and bars:
        payload = [{
            "instrument_id": instrument_id, "exchange": exchange,
            "trading_date": bar.trading_date.isoformat(), "open": bar.open,
            "high": bar.high, "low": bar.low, "close": bar.close,
            "adjusted_close": bar.adjusted_close, "volume": bar.volume,
            "provider": bar.provider, "retrieved_at": bar.retrieved_at.isoformat(),
            "is_adjusted": False,
        } for bar in bars]
        try:
            await admin.upsert("price_history", payload, "instrument_id,exchange,trading_date,provider")
        except SupabaseRestError as exc:
            logger.warning("Market data persistence unavailable: %s", exc)
    return bars

@router.get("/history")
async def get_daily_history(
    symbol: str = Query(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._-]+$"),
    exchange: Literal["NSE", "BSE"] = "NSE",
    start: date = Query(),
    end: date = Query(),
):
    if start > end:
        raise HTTPException(status_code=422, detail="start must be on or before end")
    if (end - start).days > 3650:
        raise HTTPException(status_code=422, detail="Date range cannot exceed 10 years")
    try:
        return await _fetch_and_store(symbol, exchange, start, end)
    except MarketDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@router.get("/technicals")
async def get_technical_indicators(
    symbol: str = Query(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._-]+$"),
    exchange: Literal["NSE", "BSE"] = "NSE",
    lookback_days: int = Query(default=500, ge=30, le=3650),
):
    end = date.today()
    start = end - timedelta(days=lookback_days)
    try:
        bars = await _fetch_and_store(symbol, exchange, start, end)
        result = calculate_technicals(bars)
        result["recent_bars"] = [bar.model_dump(mode="json") for bar in bars[-10:]]
        return result
    except MarketDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
