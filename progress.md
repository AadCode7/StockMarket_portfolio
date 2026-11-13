# Project progress

## Implemented foundation
- [x] Architecture and free-tier-first choices agreed.
- [x] Supabase Auth signup, confirmation, login, SSR session and protected dashboard.
- [x] FastAPI JWT verification using Supabase JWKS.
- [x] Groq provider interface with no paid fallback.
- [x] Yahoo Finance and optional Alpha Vantage BSE daily-history adapters.
- [x] Provider fallback and OHLC/date/volume validation.
- [x] Instrument search API and seeded NSE/BSE starter universe.
- [x] Historical price API with optional server-side Supabase persistence, pagination and cache.
- [x] SMA 20/50/200, RSI 14, MACD, annualised 20-day volatility and lookback drawdown.
- [x] Portfolio create/list API, transaction ledger and account-scoped RLS access.
- [x] Weighted-average cost accounting with realised P&L, dividends and fees.
- [x] Portfolio summary with latest stored closing prices and missing-price safeguards.
- [x] Frontend market lookup, exchange selector, indicators, recent daily prices, portfolio creation and transaction entry.
- [x] Multi-model walk-forward benchmark: Ridge, Random Forest, Extra Trees and HistGradientBoosting.
- [x] Zero-return baseline, horizon-sized purge gap, out-of-sample metrics and authenticated benchmark endpoint/UI.
- [x] Groq structured-data research note endpoint and dashboard action, with no fabricated fundamentals/news or RAG claims.
- [x] Unit tests for indicators, portfolio accounting, provider fallback and ML benchmark.
- [x] Setup, security, data-source and architecture documentation updated.

## Current limitations
- The instrument master is a starter list, not a complete exchange feed. ISIN reconciliation is not implemented.
- Market data is daily, unofficial/best-effort via Yahoo Finance; Alpha Vantage BSE coverage must be verified.
- Price persistence/cache requires SUPABASE_SERVICE_ROLE_KEY on the backend only. Without it, live provider results are returned but not stored.
- Portfolio accounting is weighted-average cost, not FIFO tax-lot accounting. Corporate-action adjustment is not yet applied to holdings.
- ML benchmark is an experimental baseline. No model registry, persistence, MLflow, calibration, uncertainty intervals or SHAP yet.
- The Groq copilot summarises supplied price/indicator data only. It does not retrieve documents, news or external sources and is not yet a multi-agent RAG copilot.
- RAG tables exist but document ingestion and retrieval are not active.

## Next milestones
- [ ] Authoritative NSE/BSE instrument master and ISIN reconciliation.
- [ ] Persisted fundamentals, financial statements and corporate-action ingestion.
- [ ] Market benchmark/index data and sector analytics.
- [ ] Feature store, model persistence and MLflow experiment/model registry.
- [ ] SHAP global/local/temporal explanations and model attribution stability.
- [ ] Portfolio return series, volatility, Sharpe, drawdown, VaR/CVaR and optimisation.
- [ ] Document ingestion, hybrid retrieval and LangGraph research copilot.
- [ ] Production rate limiting, audit logging, observability and deployment smoke tests.
