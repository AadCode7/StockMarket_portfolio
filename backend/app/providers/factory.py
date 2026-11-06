from app.config import settings
from app.providers.alpha_vantage_provider import AlphaVantageProvider
from app.providers.market_data import MarketDataRouter
from app.providers.yfinance_provider import YahooFinanceProvider

def build_market_data_router() -> MarketDataRouter:
    return MarketDataRouter(
        providers={"yfinance": YahooFinanceProvider(), "alpha_vantage": AlphaVantageProvider()},
        order=settings.provider_order,
    )
