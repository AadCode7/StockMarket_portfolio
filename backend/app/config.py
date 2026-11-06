from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Stock Research Platform"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: str = "http://localhost:3000"
    supabase_jwt_issuer: str = ""
    supabase_jwks_url: str = ""
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    llm_max_tokens: int = Field(default=1200, ge=1, le=4096)
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    market_data_providers: str = "yfinance,alpha_vantage"
    alpha_vantage_api_key: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [v.strip() for v in self.backend_cors_origins.split(",") if v.strip()]

    @property
    def provider_order(self) -> list[str]:
        return [v.strip().lower() for v in self.market_data_providers.split(",") if v.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
