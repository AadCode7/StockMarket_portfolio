from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field

class UserContext(BaseModel):
    id: str
    email: str | None = None

class PriceBar(BaseModel):
    symbol: str
    exchange: Literal["NSE", "BSE"]
    trading_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    provider: str
    retrieved_at: datetime
    currency: str = "INR"
    adjusted_close: float | None = None
    is_delayed: bool = True

class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)

class ChatResponse(BaseModel):
    answer: str
    provider: str
    model: str
    disclaimer: str = "Research assistance only. Verify financial information independently."
