# Indian Stock Market Research & Portfolio Intelligence

MarketLens is an NSE/BSE research and portfolio workspace. It is being implemented in independently testable stages, with free-tier providers as the default.

## Working functionality in this release
- Supabase Auth signup, email confirmation, login, session handling and protected dashboard.
- Public instrument search against a starter NSE/BSE instrument master.
- Daily historical OHLCV retrieval through provider adapters with validation and fallback.
- Optional server-side persistence and a 15-minute cache in Supabase PostgreSQL.
- SMA 20/50/200, RSI 14, MACD, 20-day annualised volatility and lookback maximum drawdown.
- Private portfolios, transaction ledger, weighted-average cost accounting, realised/unrealised P&L, dividend and fee tracking.
- Supabase RLS and JWT-scoped PostgREST access for user-owned portfolio records.

## Stack
- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python 3.11
- Database/auth: Supabase PostgreSQL, Supabase Auth, pgvector, Row Level Security
- LLM: Groq API through a configurable provider interface; no automatic paid fallback
- Market data: Yahoo Finance via yfinance; optional Alpha Vantage adapter

## Setup
1. Copy .env.example to backend/.env. Put only NEXT_PUBLIC_* variables in frontend/.env.local.
2. Apply migrations 0001_initial_schema.sql, then 0002_market_and_portfolio_features.sql in the Supabase SQL Editor.
3. Configure Supabase URL, anon key, JWT issuer and JWKS URL.
4. Configure SUPABASE_SERVICE_ROLE_KEY in the backend hosting environment only if you want the backend to persist/cache public market data. Never expose it to Next.js or commit it.
5. Install backend dependencies and run uvicorn app.main:app --reload from backend/.
6. Run npm install && npm run dev from frontend/.

Full instructions: docs/SETUP.md.

## API endpoints
- GET /api/v1/instruments?q=RELIANCE&exchange=ALL
- GET /api/v1/market-data/history?symbol=RELIANCE&exchange=NSE&start=2024-01-01&end=2024-12-31
- GET /api/v1/market-data/technicals?symbol=RELIANCE&exchange=NSE&lookback_days=500
- GET/POST /api/v1/portfolios (Supabase bearer token required)
- GET/POST /api/v1/portfolios/{portfolio_id}/transactions (bearer token required)
- GET /api/v1/portfolios/{portfolio_id}/summary (bearer token required)

## Market-data and accounting caveats
Yahoo Finance access through yfinance is unofficial and best-effort. It is not a guaranteed live feed or an assumed redistribution licence. Alpha Vantage coverage and free quotas must be checked for each exchange symbol. Daily prices are not live quotes.

The starter instrument universe is deliberately small. ISINs are not fabricated; load an authoritative exchange instrument master before relying on full instrument identity. Price persistence requires the server-only Supabase service-role key. Without it, market endpoints can still return provider data, but the API will not cache it in PostgreSQL.

Portfolio accounting uses weighted-average cost. Buy charges enter cost basis, sell charges reduce realised P&L, dividends are entered as an amount in the transaction price field, and fees are entered as an amount in the same field. A total valuation is withheld if any open holding lacks a stored closing price. Taxes and statutory costs are only included if entered by the user.

## Still planned
Model benchmarking and walk-forward validation, MLflow, SHAP, portfolio risk/optimisation, financial statement ingestion, corporate-action ingestion, document ingestion, hybrid RAG and LangGraph agents are not yet implemented. pgvector is enabled in the database schema, but the RAG pipeline is not yet active.

## Security
The browser uses only the Supabase publishable/anon key. The service-role key is backend-only and bypasses RLS; it is used only for public market-data persistence. Portfolio reads and writes use the user's bearer JWT, and database RLS scopes rows to auth.uid(). Never commit API keys or passwords.

## Disclaimer
For research, education and record-keeping. No guaranteed forecasts, personalised investment advice or trade execution.
