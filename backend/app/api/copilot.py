from datetime import date, timedelta
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.analytics.technicals import calculate_technicals
from app.api.market_data import fetch_and_store
from app.auth import get_current_user
from app.config import settings
from app.providers.llm import LLMProviderError, get_llm_provider
from app.providers.market_data import MarketDataError
from app.schemas import UserContext

router = APIRouter(prefix="/copilot", tags=["research-copilot"])

class StockSummaryRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._-]+$")
    exchange: Literal["NSE", "BSE"] = "NSE"

@router.post("/stock-summary")
async def create_stock_summary(
    body: StockSummaryRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
):
    del user
    end = date.today()
    try:
        bars = await fetch_and_store(body.symbol, body.exchange, end - timedelta(days=500), end)
        indicators = calculate_technicals(bars)
        recent = [{
            "date": bar.trading_date.isoformat(),
            "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
            "volume": bar.volume,
        } for bar in bars[-10:]]
        context = {
            "symbol": body.symbol.upper(),
            "exchange": body.exchange,
            "data_provider": indicators["data_provider"],
            "retrieved_at": indicators["retrieved_at"],
            "as_of": indicators["as_of"],
            "latest_close_inr": indicators["close"],
            "sma_20_50_200": indicators["sma"],
            "rsi_14": indicators["rsi_14"],
            "macd": indicators["macd"],
            "macd_signal": indicators["macd_signal"],
            "annualised_volatility_20d": indicators["annualised_volatility_20d"],
            "maximum_drawdown_in_500_calendar_day_window": indicators["maximum_drawdown_in_window"],
            "recent_daily_bars": recent,
        }
        prompt = (
            "Write a concise, neutral stock research note using only the supplied structured data. "
            "Explain trend, momentum, volatility and what the data cannot establish. "
            "Do not invent fundamentals, news, valuation ratios, causes, prices, citations or forecasts. "
            "Do not issue buy, sell or hold recommendations. Clearly state that indicators are descriptive "
            "and that the source is best-effort daily market data. If an indicator is null, say it is unavailable.\n\n"
            f"STRUCTURED DATA:\n{context}"
        )
        answer = await get_llm_provider().generate(prompt)
        return {
            "answer": answer,
            "provider": "groq",
            "model": settings.groq_model,
            "symbol": body.symbol.upper(),
            "exchange": body.exchange,
            "data_provider": indicators["data_provider"],
            "data_as_of": indicators["as_of"],
            "retrieved_at": indicators["retrieved_at"],
            "disclaimer": "AI-generated descriptive research, not investment advice. No RAG documents or external news were used.",
        }
    except MarketDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
