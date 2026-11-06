from datetime import date
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from app.providers.factory import build_market_data_router
from app.providers.market_data import MarketDataError

router = APIRouter(prefix="/market-data", tags=["market-data"])

@router.get("/history")
async def get_daily_history(
    symbol: str = Query(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._-]+$"),
    exchange: Literal["NSE", "BSE"] = "NSE",
    start: date = Query(),
    end: date = Query(),
):
    if start > end:
        raise HTTPException(status_code=422, detail="start must be on or before end")
    try:
        return await build_market_data_router().get_daily_history(symbol, exchange, start, end)
    except MarketDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
