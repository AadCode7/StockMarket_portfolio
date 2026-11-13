# Architecture and implementation status

## Runtime
Next.js App Router + React + Tailwind frontend; FastAPI backend; Supabase PostgreSQL/Auth/pgvector; Groq LLM adapter; Yahoo Finance and optional Alpha Vantage daily data adapters.

## Implemented
- Email/password signup, confirmation, login, SSR session refresh and protected dashboard.
- FastAPI Supabase JWKS token verification.
- Instrument lookup using a small seed universe.
- Daily historical bars with provider fallback, OHLC validation, optional Supabase persistence and a short cache.
- Technical indicators: SMA 20/50/200, RSI 14, MACD, 20-day annualised volatility and lookback drawdown.
- User-owned portfolio CRUD, transaction ledger, weighted-average cost, realised/unrealised P&L, dividends and fees.

## Data flow
1. Frontend searches public instrument master via FastAPI.
2. Stock page requests daily history/technicals.
3. Provider router tries configured free providers in order; invalid/empty data triggers fallback.
4. Backend optionally persists bars using a server-only service-role key. This is the only service-role path.
5. Portfolio API forwards the user's Supabase JWT to PostgREST; RLS restricts access to that user's portfolios and transactions.
6. Portfolio valuation reads latest stored daily closes. If a holding has no stored price, aggregate market value and total P&L are withheld rather than estimated.

## Planned
Authoritative exchange instrument master and ISIN reconciliation, financial statements, corporate-action ingestion, market benchmarks, walk-forward ML benchmarking, MLflow, SHAP, portfolio risk/optimisation, document ingestion, hybrid retrieval and LangGraph agents.

## Important limitations
The starter symbol list is not a complete exchange instrument master. Yahoo Finance is unofficial. The current portfolio ledger uses weighted-average cost, not tax-lot FIFO. The RAG schema exists, but no document ingestion or retrieval workflow is active yet.
