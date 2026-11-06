# Setup

## Supabase
1. Create a Supabase Free project.
2. Copy project URL and publishable/anon key into .env.
3. Set SUPABASE_JWT_ISSUER to https://<project-ref>.supabase.co/auth/v1.
4. Set SUPABASE_JWKS_URL to https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json.
5. Run supabase/migrations/0001_initial_schema.sql in the SQL editor.
6. In Authentication > URL Configuration, add http://localhost:3000/auth/callback and the deployed frontend callback URL to allowed redirects.
7. Enable email confirmation. Configure SMTP within the plan's current limits.

## Backend
Use Python 3.11:
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Health: http://localhost:8000/health.

## Frontend
Use Node.js 20 or later:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:3000.

## Groq
Create a key in the Groq console and set GROQ_API_KEY. Verify the selected model and your account's current free-tier limits. The code does not fall back to paid providers.

## Cloud deployment
- Frontend: deploy frontend/ to Vercel. Set NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_BASE_URL.
- API: deploy backend/ as a Docker web service. Set Supabase issuer/JWKS, CORS, Groq, and market provider environment variables in the host dashboard.
- Supabase: Free plan; projects can pause after inactivity and have storage/egress limits.
- CORS must contain the exact deployed frontend origin.
- Never put a service-role key in a NEXT_PUBLIC_ variable.
- Free hosts may sleep and may not support always-on workers or persistent disk.
