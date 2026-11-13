# Setup

## 1. Create Supabase project
1. Create a Supabase project on the Free plan.
2. Copy the project URL and publishable/anon key.
3. Set SUPABASE_JWT_ISSUER to https://<project-ref>.supabase.co/auth/v1.
4. Set SUPABASE_JWKS_URL to https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json.
5. Run SQL files in order in Supabase SQL Editor: 0001_initial_schema.sql, then 0002_market_and_portfolio_features.sql.
6. In Authentication > URL Configuration, add local and deployed /auth/callback URLs to allowed redirects.
7. Enable email confirmation. Use the email provider available within your Supabase plan.

## 2. Environment variables
Copy root .env.example to backend/.env. Create frontend/.env.local containing only:

    NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
    NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY
    NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

Backend variables:
- SUPABASE_URL and SUPABASE_ANON_KEY: public project configuration used by the API.
- SUPABASE_JWT_ISSUER and SUPABASE_JWKS_URL: signature and claim validation.
- SUPABASE_SERVICE_ROLE_KEY: optional server-only key used to persist/cache public market bars. It bypasses RLS. Keep it only in the backend secret store and never put it in NEXT_PUBLIC_*.
- GROQ_API_KEY: optional; required only when using Groq features.
- ALPHA_VANTAGE_API_KEY: optional secondary provider.
- MARKET_DATA_PROVIDERS: provider order, default yfinance,alpha_vantage.
- MARKET_DATA_CACHE_SECONDS: default 900 seconds.

If the service-role key is omitted, market requests still return data but persistence/cache is disabled. Portfolio operations do not use the service-role key; they forward the signed-in user's JWT and are governed by RLS.

## 3. Backend
Use Python 3.11:

    cd backend
    python -m venv .venv
    # Windows PowerShell: .venv\\Scripts\\Activate.ps1
    # macOS/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Health check: http://localhost:8000/health.

## 4. Frontend
Use Node.js 20 or later:

    cd frontend
    npm install
    npm run dev

Open http://localhost:3000.

## 5. Cloud deployment
- Frontend: deploy frontend/ to Vercel. Set only the three NEXT_PUBLIC_* values above.
- Backend: deploy backend/ using its Dockerfile. Configure Supabase URL/keys, JWT issuer/JWKS, exact frontend CORS origin, market provider order, and optional server-only service-role key.
- Supabase: apply both migrations and add the deployed callback URL.
- Configure all secrets in the cloud provider's secret manager, not in repository files.

Free hosts can sleep or pause, and free-tier APIs have rate limits. No always-on worker or real-time market feed is assumed.
