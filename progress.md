# Project progress

## Implemented foundation
- [x] Architecture and free-tier-first choices agreed.
- [x] Supabase Auth signup, confirmation, login, SSR session and protected dashboard.
- [x] FastAPI JWT verification using Supabase JWKS.
- [x] Groq provider interface with no paid fallback.
- [x] Yahoo Finance and optional Alpha Vantage BSE daily-history adapters.
- [x] Provider fallback and OHLC/date/volume validation.
- [x] Instrument search API and seeded NSE/BSE starter universe.
- [x] Historical price API with optional server-side Supabase persistence and cache.
- [x] SMA 20/50/200, RSI 14, MACD, annualised 20-day volatility and lookback drawdown.
- [x] Portfolio create/list API, transaction ledger and account-scoped RLS access.
- [x] Weighted-average cost accounting with realised P&L, dividends and fees.
- [x] Portfolio summary with latest stored closing prices and missing-price safeguards.
- [x] Frontend market lookup, exchange selector, indicators, recent daily prices, portfolio creation and transaction entry.
- [x] Setup, security, data-source and architecture documentation updated.
- [x] Unit tests for indicators, portfolio accounting and provider fallback.

## Current limitations
- The instrument master is a starter list, not a complete exchange feed. ISIN reconciliation is not implemented.
- Market data is daily, unofficial/best-effort via Yahoo Finance; Alpha Vantage BSE coverage must be verified.
- Price persistence/cache requires SUPABASE_SERVICE_ROLE_KEY on the backend only. Without it, live provider results are returned but not stored.
- Portfolio accounting is weighted-average cost, not FIFO tax-lot accounting. Corporate-action adjustment is not yet applied to holdings.
- RAG tables exist but document ingestion and retrieval are not active.
- ML training, walk-forward model selection, MLflow, SHAP, portfolio risk and optimisation remain planned.

## Next milestones
- [ ] Authoritative NSE/BSE instrument master and ISIN reconciliation.
- [ ] Persisted fundamentals, financial statements and corporate-action ingestion.
- [ ] Market benchmark/index data and sector analytics.
- [ ] Feature store and multiple-model walk-forward evaluation.
- [ ] MLflow model registry, prediction uncertainty and model disagreement.
- [ ] SHAP global/local/temporal explanations.
- [ ] Portfolio return series, volatility, Sharpe, drawdown, VaR/CVaR and optimisation.
- [ ] Document ingestion, hybrid retrieval and LangGraph research copilot.
- [ ] Production rate limiting, audit logging, observability and deployment smoke tests.
