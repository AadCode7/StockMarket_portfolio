import re
from fastapi import APIRouter, HTTPException, Query
from app.services.supabase_rest import SupabaseRestClient, SupabaseRestError

router = APIRouter(prefix="/instruments", tags=["instruments"])

@router.get("")
async def search_instruments(
    q: str = Query(default="", max_length=80),
    exchange: str = Query(default="NSE", pattern="^(NSE|BSE|ALL)$"),
    limit: int = Query(default=25, ge=1, le=100),
):
    try:
        client = SupabaseRestClient()
        params = {
            "select": "id,company_name,isin,nse_symbol,bse_symbol,bse_scrip_code,sector,industry,currency",
            "is_active": "eq.true", "limit": str(limit), "order": "company_name.asc",
        }
        term = re.sub(r"[^A-Za-z0-9 .&_-]", "", q.strip())
        if term:
            params["or"] = f"(company_name.ilike.*{term}*,nse_symbol.ilike.*{term}*,bse_symbol.ilike.*{term}*,bse_scrip_code.ilike.*{term}*)"
        if exchange == "NSE":
            params["nse_symbol"] = "not.is.null"
        elif exchange == "BSE":
            params["bse_symbol"] = "not.is.null"
        return await client.select("instruments", params)
    except SupabaseRestError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@router.get("/{symbol}")
async def get_instrument(symbol: str):
    normalized = re.sub(r"[^A-Za-z0-9._-]", "", symbol.upper())
    if not normalized:
        raise HTTPException(status_code=422, detail="A valid exchange symbol or BSE code is required")
    try:
        rows = await SupabaseRestClient().select("instruments", {
            "select": "id,company_name,isin,nse_symbol,bse_symbol,bse_scrip_code,sector,industry,currency",
            "or": f"(nse_symbol.eq.{normalized},bse_symbol.eq.{normalized},bse_scrip_code.eq.{normalized})",
            "limit": "1",
        })
        if not rows:
            raise HTTPException(status_code=404, detail="Instrument not found")
        return rows[0]
    except SupabaseRestError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
