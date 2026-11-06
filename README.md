# Indian Stock Market Research & Portfolio Intelligence

A modular platform for NSE/BSE stock research, explainable machine learning, portfolio analytics, and an evidence-grounded AI research copilot.

## Project status

This repository is being built incrementally. The initial commit establishes the application foundation, authentication boundaries, provider interfaces, database schema, and deployment configuration. Market predictions and investment recommendations are not enabled by this scaffold.

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- Database and authentication: Supabase PostgreSQL, Supabase Auth, pgvector, Row Level Security
- LLM: Groq API through a provider interface; no automatic paid-provider fallback
- Market data: configurable free-source adapters with provenance and fallback controls

## Quick start

1. Copy `.env.example` to `.env` and fill in the required values.
2. Apply `supabase/migrations/0001_initial_schema.sql` to your Supabase project.
3. Install backend dependencies from `backend/requirements.txt` and run `uvicorn app.main:app --reload` from `backend/`.
4. Install frontend dependencies from `frontend/` and run `npm run dev`.

See `docs/SETUP.md`, `docs/ARCHITECTURE.md`, and `docs/DATA_SOURCES.md` before deployment.

## Free-tier expectations

Free plans have quotas, rate limits, inactivity policies, and provider-specific terms. The application must fail clearly when a quota is reached; it must never silently switch to a paid service. Yahoo Finance access through `yfinance` is unofficial and should be treated as best-effort research/prototyping data, not a guaranteed or redistribution-licensed feed.

## Security

Never commit `.env`, Supabase service-role keys, Groq API keys, database passwords, or deployment secrets. The browser may use only the Supabase publishable/anon key. User-owned records are protected by database RLS and backend ownership checks.

## Disclaimer

This project is for research, education, and portfolio analysis. It does not provide guaranteed forecasts, personalised investment advice, or trade execution. Verify data and applicable exchange/provider licences before public or commercial use.
