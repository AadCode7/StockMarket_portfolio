# StockMarket_portfolio architecture

## Product
NSE/BSE stock research and portfolio intelligence: instrument lookup, daily price history, descriptive technical analysis, transaction-based portfolio tracking, experimental ML benchmarking, explainability and an evidence-grounded research copilot. The product does not execute trades or promise returns.

## Runtime
- Next.js App Router, React, TypeScript and Tailwind CSS.
- FastAPI with typed Pydantic contracts.
- Supabase PostgreSQL, Supabase Auth, pgvector and Row Level Security.
- pandas, NumPy and scikit-learn for deterministic features and baseline ML.
- Groq as the configurable LLM provider; no paid-provider fallback.
- Yahoo Finance via yfinance and optional Alpha Vantage BSE daily-history adapter.
- Vercel frontend and a container-hosted API. Free hosts may sleep.

## Authentication and authorization
Supabase Auth handles registration, confirmation and sessions. Next.js uses SSR cookie sessions and server-side getUser checks. FastAPI validates Supabase JWT signatures, issuer, audience and expiry using JWKS. User portfolio requests forward the user's JWT to PostgREST, where RLS enforces auth.uid() ownership. A server-only service-role key is optionally used for public market-data persistence only; it must never be sent to a browser and must never be used for user portfolio requests.

## Implemented modules
- Instrument lookup against a small seeded NSE/BSE symbol universe.
- Daily OHLCV provider fallback with validation, de-duplication, retrieval timestamps, optional persistence and a short cache.
- SMA 20/50/200, RSI 14, MACD, 20-day annualised volatility and lookback maximum drawdown.
- Portfolio creation, transaction ledger, weighted-average cost basis, realised/unrealised P&L, dividends and fee accounting.
- Multi-model forward-return benchmark with Ridge, Random Forest, Extra Trees and HistGradientBoosting, expanding-window splits, a horizon-sized purge gap and zero-return baseline.
- Authenticated SHAP explainability endpoint for the selected model, returning global mean absolute attributions, latest-observation signed contributions and a recent temporal attribution series.
- Frontend stock search, exchange selection, technical indicator view, recent prices, model benchmark results, portfolio ledger, summary and a Groq structured-data research note.
- Groq copilot endpoint builds its prompt from server-calculated indicators and market bars; no unsupported news/fundamentals or RAG context is implied.

## ML validation rules
The initial task is forward return over 5, 20 or 60 trading observations. Feature rows are chronological; training uses expanding-window TimeSeriesSplit and a purge gap equal to the target horizon. MAE is the primary selection metric, but a candidate is selected only if it beats the zero-return baseline. Metrics include RMSE, directional accuracy and out-of-sample R-squared. This is an experimental benchmark, not a live prediction service. SHAP uses a bounded deterministic background sample and a recent explanation window. It explains model output relative to that background, not causal effects. There is no MLflow registry, calibration, transaction-cost backtest, uncertainty interval or fold/regime attribution-stability analysis.

## Data integrity
1. Keep exchange, provider, trading date and retrieval timestamp with every observation.
2. Preserve unadjusted OHLC and adjusted close separately.
3. Reject invalid OHLC, non-positive prices, negative volume, duplicate dates and out-of-range observations.
4. Use only actual publication dates for future financial-statement features.
5. Prevent look-ahead leakage with chronological walk-forward validation and purged overlapping labels.
6. Treat SHAP as model attribution, not causality.
7. LLMs explain tool outputs; deterministic code calculates financial values.

## Database
The initial migration establishes instruments, price_history, portfolios, portfolio_transactions, research_documents and document_chunks. Migration 0002 adds bse_symbol, corporate_actions, ingestion-run tracking and a small starter instrument universe. pgvector is enabled, but document ingestion/retrieval is not yet implemented.

## Planned next
Authoritative exchange instrument master and ISIN reconciliation; financial statements and corporate-action ingestion; market benchmarks; model persistence and MLflow; fold/regime attribution-stability analysis; portfolio risk and optimisation; document ingestion, hybrid RAG and LangGraph agents.

## Cost controls
Use free-tier APIs only, surface quota/staleness failures and never silently switch to a paid service. Market data is daily and best-effort, not real-time. Persisted market data requires a backend-only Supabase service-role key. Cache by symbol/date/provider and bound provider requests.
