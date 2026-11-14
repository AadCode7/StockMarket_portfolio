from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.auth import get_current_user
from app.providers.market_data import MarketDataError
from app.api.market_data import fetch_and_store
from app.ml.benchmark import benchmark_forward_returns, explain_forward_returns
from app.schemas import UserContext

router = APIRouter(prefix="/ml", tags=["machine-learning"])

class BenchmarkRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._-]+$")
    exchange: Literal["NSE", "BSE"] = "NSE"
    horizon_days: Literal[5, 20, 60] = 5
    lookback_days: int = Field(default=1500, ge=365, le=3650)

class ExplainRequest(BenchmarkRequest):
    model: Literal["ridge", "random_forest", "extra_trees", "hist_gradient_boosting"]

@router.post("/benchmark")
async def run_model_benchmark(
    body: BenchmarkRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
):
    del user  # Authentication is required to protect provider quota and training resources.
    from datetime import date, timedelta
    try:
        end = date.today()
        bars = await fetch_and_store(body.symbol, body.exchange, end - timedelta(days=body.lookback_days), end)
        return benchmark_forward_returns(bars, horizon_days=body.horizon_days)
    except MarketDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/explain")
async def explain_model(
    body: ExplainRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
):
    del user  # Authentication bounds provider quota and CPU-intensive explainability.
    from datetime import date, timedelta
    try:
        end = date.today()
        bars = await fetch_and_store(body.symbol, body.exchange, end - timedelta(days=body.lookback_days), end)
        return explain_forward_returns(bars, horizon_days=body.horizon_days, model_name=body.model)
    except MarketDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
