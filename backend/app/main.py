from typing import Annotated
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.market_data import router as market_data_router
from app.auth import get_current_user
from app.config import settings
from app.schemas import UserContext

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(market_data_router, prefix=settings.api_v1_prefix)

@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "stock-market-api"}

@app.get(f"{settings.api_v1_prefix}/me", tags=["auth"])
async def me(user: Annotated[UserContext, Depends(get_current_user)]) -> UserContext:
    return user
