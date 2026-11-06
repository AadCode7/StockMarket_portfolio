# StockMarket_portfolio architecture

NSE/BSE stock research and portfolio intelligence platform. Next.js App Router is the frontend; FastAPI is the API; Supabase provides PostgreSQL, Auth, RLS, and pgvector; Groq is the configurable LLM provider. Market data adapters retain source and retrieval timestamps.

## Security
Supabase Auth handles signup, confirmation, and sessions. Next.js uses SSR session checks. FastAPI validates Supabase bearer JWTs using JWKS, issuer, audience, and expiry. RLS scopes user-owned rows to auth.uid(). Service-role keys must never reach the browser.

## Data integrity
Store raw and adjusted prices separately. Preserve provider, exchange, currency, and retrieval timestamps. Use actual filing/publication dates for financial features. Prevent look-ahead leakage with chronological walk-forward validation. SHAP describes model attribution, not causality. LLMs explain deterministic tool outputs and must not invent financial values.

## Planned modules
backend/app/api, core, contracts, db, data/providers, data/ingestion, analytics, features, ml, ml/explainability, portfolio, ai/agents, ai/tools, ai/rag, services, tasks. frontend/app, components, and lib. supabase/migrations. docs, research, and scripts. These modules will be added as implemented; no empty placeholder packages are created.

## Cost controls
Use free-tier providers only, expose quotas and staleness, and never silently fall back to paid APIs. Free hosting may sleep and is not a guaranteed always-on service.