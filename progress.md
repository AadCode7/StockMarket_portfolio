# Project progress

## Foundation scaffold
- [x] Product architecture and free-tier-first constraint agreed.
- [x] Initial repository commit on main.
- [x] Environment template and secret-safe ignore rules.
- [x] FastAPI app, health endpoint, and Supabase JWKS token verification.
- [x] Groq provider interface with no paid fallback.
- [x] Yahoo Finance and optional Alpha Vantage daily-history adapters.
- [x] Next.js shell, Supabase SSR client, login, signup, email callback, protected dashboard.
- [x] Initial PostgreSQL schema with RLS.
- [x] Setup, architecture, data-source, and security documentation.

## Next
- [ ] Instrument master ingestion and provider reconciliation.
- [ ] Market-data API endpoints, caching, and persistence.
- [ ] Financial statements and corporate-action normalization.
- [ ] Technical/fundamental analytics.
- [ ] ML dataset builder, walk-forward benchmarking, and MLflow.
- [ ] SHAP global/local/temporal explanations.
- [ ] Portfolio valuation, transactions, risk, and optimisation.
- [ ] Document ingestion, hybrid retrieval, and LangGraph copilot.
- [ ] CI and deployment workflows.

## Constraints
Yahoo Finance is unofficial; Alpha Vantage India coverage is not guaranteed. Supabase/Groq free tiers have quotas and free hosts may sleep. No trading or investment recommendations are enabled.
