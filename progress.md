# Project progress

## Completed foundation
- [x] Architecture and free-tier-first choices agreed.
- [x] FastAPI health endpoint and Supabase JWKS bearer-token validation.
- [x] Groq provider interface with no paid fallback.
- [x] Yahoo Finance daily-history adapter and optional Alpha Vantage BSE adapter.
- [x] Configurable market provider router and daily-history API endpoint.
- [x] Next.js frontend with Supabase SSR signup, email confirmation callback, login, and protected dashboard.
- [x] Supabase PostgreSQL initial schema, pgvector extension, and RLS policies.
- [x] Environment template, setup/security/data-source docs, and GitHub Actions workflow.

## Next implementation milestones
- [ ] Run CI and resolve dependency/build issues.
- [ ] Instrument master ingestion, provider reconciliation, market-data cache and persistence.
- [ ] Financial statements and corporate-action normalization.
- [ ] Technical/fundamental analytics.
- [ ] ML dataset builder, walk-forward benchmarking, and MLflow.
- [ ] SHAP global/local/temporal explanations.
- [ ] Portfolio valuation, transactions, risk, and optimisation.
- [ ] Document ingestion, hybrid retrieval, and LangGraph copilot.

## Constraints
Yahoo Finance is unofficial and best-effort. Alpha Vantage adapter currently supports the documented BSE ticker format only; coverage and quotas must be checked. Supabase/Groq free tiers have quotas and free hosts may sleep. No trading or investment recommendations are enabled.