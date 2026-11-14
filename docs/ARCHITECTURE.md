# Architecture and implementation status

## Runtime
Next.js App Router + React + Tailwind frontend; FastAPI backend; Supabase PostgreSQL/Auth/pgvector; Groq LLM adapter; Yahoo Finance and optional Alpha Vantage daily data adapters; pandas/NumPy/scikit-learn baseline ML.

## Implemented
- Email/password signup, confirmation, login, SSR session refresh and protected dashboard.
- FastAPI Supabase JWKS token verification.
- Instrument lookup using a small seeded NSE/BSE universe.
- Daily historical bars with provider fallback, OHLC validation, optional Supabase persistence, pagination and a short cache.
- SMA 20/50/200, RSI 14, MACD, 20-day annualised volatility and lookback drawdown.
- User-owned portfolio CRUD, transaction ledger, weighted-average cost, realised/unrealised P&L, dividends and fees.
- Authenticated multi-model walk-forward benchmark for 5/20/60 trading-day forward returns, with a zero-return baseline and horizon-sized purge gap.
- Authenticated SHAP endpoint and dashboard for global feature importance, latest-observation contributions and recent temporal attribution.
- Authenticated Groq research-note endpoint built from server-calculated technical indicators and daily OHLCV only. It does not use external news or RAG documents.

## Data flow
1. Frontend searches public instrument master via FastAPI.
2. Stock page requests daily history/technicals.
3. Provider router tries configured free providers in order; invalid/empty data triggers fallback.
4. Backend optionally persists bars using a server-only service-role key. This is the only service-role path.
5. Portfolio API forwards the user's Supabase JWT to PostgREST; RLS restricts access to that user's portfolios and transactions.
6. Portfolio valuation reads latest stored daily closes. If a holding has no stored price, aggregate market value and total P&L are withheld.
7. Model benchmark builds point-in-time daily features and uses expanding-window splits with a purge gap. A candidate is selected only if out-of-sample MAE beats the zero-return baseline.

## Planned
Authoritative exchange instrument master and ISIN reconciliation, financial statements, corporate-action ingestion, market benchmarks, MLflow, attribution-stability analysis, portfolio risk/optimisation, document ingestion, hybrid retrieval and LangGraph agents.

## Important limitations
The starter symbol list is not a complete exchange instrument master. Yahoo Finance is unofficial. The portfolio ledger uses weighted-average cost, not tax-lot FIFO. The benchmark is an experimental baseline, not a production forecast; it has no transaction-cost backtest, model registry, calibration or uncertainty intervals. SHAP values are model attributions, not causal effects, and fold/regime stability is not yet measured. RAG tables exist, but no document ingestion or retrieval workflow is active yet.
