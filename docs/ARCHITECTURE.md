# Architecture

## Deployment shape
Start with a modular monolith: Next.js frontend, FastAPI API, Supabase PostgreSQL/Auth/pgvector, and provider adapters. Add independent workers when ingestion and ML jobs exist. Never train models inside a serverless HTTP request.

## Trust boundaries
- Browser: Supabase publishable/anon key only; session cookies managed by @supabase/ssr.
- API: verifies Supabase access-token signature through JWKS, issuer, audience, and expiry.
- Database: RLS is the final ownership boundary. Every user-owned row is scoped to auth.uid().
- Secrets: Groq key, provider keys, and database connection strings exist only in backend/deployment secrets.
- LLM: generated text is not a source of financial numbers.

## Data flow
1. Provider adapters fetch and normalize observations.
2. Validation checks identifiers, dates, missing values, duplicates, and OHLC consistency.
3. Stored observations retain provider and retrieval timestamps.
4. Analytics and ML consume versioned, point-in-time-safe data.
5. Copilot tools return deterministic calculations and source metadata before LLM synthesis.

## ML and AI
Future models use forward-return/volatility targets, chronological walk-forward validation, transaction-cost-aware backtests, and reproducible data/feature/model versions. SHAP represents model attribution, not causality. RAG uses metadata filters, PostgreSQL full-text search, pgvector, reranking, and source citations.

## Free-tier constraints
Free services have quotas, rate limits, pauses, and changing terms. Expose freshness and provider failures. Free hosting is suitable for a prototype, not a guaranteed always-on market-data service.
