from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, field_validator
from app.auth import get_current_user
from app.portfolio.accounting import PortfolioAccountingError, aggregate_transactions
from app.schemas import UserContext
from app.services.supabase_rest import SupabaseRestClient, SupabaseRestError

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    base_currency: Literal["INR"] = "INR"

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Portfolio name cannot be blank")
        return value

class TransactionCreate(BaseModel):
    instrument_id: str
    transaction_type: Literal["BUY", "SELL", "DIVIDEND", "FEE"]
    quantity: float = Field(default=0, ge=0)
    price: float = Field(default=0, ge=0)
    charges: float = Field(default=0, ge=0)
    executed_at: datetime
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("executed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("executed_at must include a timezone")
        return value

def _client(authorization: str) -> SupabaseRestClient:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Bearer token required")
    return SupabaseRestClient(access_token=token)

def _handle_error(exc: SupabaseRestError):
    message = str(exc)
    status = 403 if "403" in message or "401" in message else 503
    raise HTTPException(status_code=status, detail="Database request failed. Check ownership, RLS policies, and Supabase configuration.") from exc

@router.get("")
async def list_portfolios(
    user: Annotated[UserContext, Depends(get_current_user)],
    authorization: Annotated[str, Header()],
):
    try:
        return await _client(authorization).select("portfolios", {
            "select": "id,name,base_currency,created_at,updated_at",
            "user_id": f"eq.{user.id}", "order": "created_at.desc",
        })
    except SupabaseRestError as exc:
        _handle_error(exc)

@router.post("", status_code=201)
async def create_portfolio(
    body: PortfolioCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    authorization: Annotated[str, Header()],
):
    try:
        rows = await _client(authorization).insert("portfolios", {
            "user_id": user.id, "name": body.name, "base_currency": body.base_currency,
        })
        return rows[0] if rows else {"created": True}
    except SupabaseRestError as exc:
        _handle_error(exc)

async def _owned_portfolio(client: SupabaseRestClient, portfolio_id: str, user_id: str):
    rows = await client.select("portfolios", {
        "select": "id,name,base_currency", "id": f"eq.{portfolio_id}",
        "user_id": f"eq.{user_id}", "limit": "1",
    })
    if not rows:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return rows[0]

@router.post("/{portfolio_id}/transactions", status_code=201)
async def add_transaction(
    portfolio_id: str,
    body: TransactionCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    authorization: Annotated[str, Header()],
):
    if body.transaction_type in ("BUY", "SELL") and (body.quantity <= 0 or body.price <= 0):
        raise HTTPException(status_code=422, detail="BUY and SELL require positive quantity and price")
    if body.transaction_type in ("DIVIDEND", "FEE") and (body.quantity != 0 or body.price <= 0):
        raise HTTPException(status_code=422, detail="DIVIDEND and FEE require zero quantity and a positive amount in price")
    client = _client(authorization)
    try:
        await _owned_portfolio(client, portfolio_id, user.id)
        instrument = await client.select("instruments", {
            "select": "id", "id": f"eq.{body.instrument_id}", "limit": "1",
        })
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        rows = await client.insert("portfolio_transactions", {
            "portfolio_id": portfolio_id, "user_id": user.id,
            **body.model_dump(mode="json"),
        })
        return rows[0] if rows else {"created": True}
    except SupabaseRestError as exc:
        _handle_error(exc)

@router.get("/{portfolio_id}/transactions")
async def list_transactions(
    portfolio_id: str,
    user: Annotated[UserContext, Depends(get_current_user)],
    authorization: Annotated[str, Header()],
):
    client = _client(authorization)
    try:
        await _owned_portfolio(client, portfolio_id, user.id)
        return await client.select("portfolio_transactions", {
            "select": "id,instrument_id,transaction_type,quantity,price,charges,executed_at,notes",
            "portfolio_id": f"eq.{portfolio_id}", "order": "executed_at.asc",
        })
    except SupabaseRestError as exc:
        _handle_error(exc)

@router.get("/{portfolio_id}/summary")
async def portfolio_summary(
    portfolio_id: str,
    user: Annotated[UserContext, Depends(get_current_user)],
    authorization: Annotated[str, Header()],
):
    client = _client(authorization)
    try:
        portfolio = await _owned_portfolio(client, portfolio_id, user.id)
        transactions = await client.select("portfolio_transactions", {
            "select": "instrument_id,transaction_type,quantity,price,charges,executed_at",
            "portfolio_id": f"eq.{portfolio_id}", "order": "executed_at.asc",
        })
        states = aggregate_transactions(transactions)
        holdings = []
        market_value = cost_basis = realized = dividends = fees = 0.0
        missing_prices = 0
        for instrument_id, state in states.items():
            quantity = float(state["quantity"])
            cost = float(state["cost"])
            realized += float(state["realized_pnl"])
            dividends += float(state["dividends"])
            fees += float(state["fees"])
            if quantity <= 0:
                cost_basis += cost
                continue
            instruments = await client.select("instruments", {
                "select": "id,company_name,nse_symbol,bse_symbol,bse_scrip_code",
                "id": f"eq.{instrument_id}", "limit": "1",
            })
            instrument = instruments[0] if instruments else {"id": instrument_id, "company_name": "Unknown instrument"}
            prices = await client.select("price_history", {
                "select": "trading_date,close,provider", "instrument_id": f"eq.{instrument_id}",
                "order": "trading_date.desc", "limit": "1",
            })
            latest = prices[0] if prices else None
            current_price = float(latest["close"]) if latest else None
            value = quantity * current_price if current_price is not None else None
            unrealized = value - cost if value is not None else None
            cost_basis += cost
            if value is None:
                missing_prices += 1
            else:
                market_value += value
            holdings.append({
                **instrument, "quantity": round(quantity, 6),
                "average_cost": round(cost / quantity, 4),
                "market_price": current_price,
                "market_value": round(value, 2) if value is not None else None,
                "unrealized_pnl": round(unrealized, 2) if unrealized is not None else None,
                "price_as_of": latest["trading_date"] if latest else None,
                "price_provider": latest["provider"] if latest else None,
            })
        prices_complete = missing_prices == 0
        unrealized_total = market_value - cost_basis if prices_complete else None
        total_return = unrealized_total + realized + dividends - fees if unrealized_total is not None else None
        return {
            "portfolio": portfolio, "holdings": holdings,
            "summary": {
                "market_value": round(market_value, 2) if prices_complete else None,
                "remaining_cost_basis": round(cost_basis, 2),
                "unrealized_pnl": round(unrealized_total, 2) if unrealized_total is not None else None,
                "realized_pnl": round(realized, 2),
                "dividends_net_of_recorded_charges": round(dividends, 2),
                "fees": round(fees, 2),
                "total_return_including_dividends": round(total_return, 2) if total_return is not None else None,
                "prices_available": len(holdings) - missing_prices,
                "holdings_count": len(holdings),
            },
            "calculation_note": "Weighted-average cost basis with decimal arithmetic. DIVIDEND and FEE amount is entered in the price field. Buy charges enter cost basis; sell charges reduce realised P&L. Missing prices are never estimated.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except PortfolioAccountingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SupabaseRestError as exc:
        _handle_error(exc)
