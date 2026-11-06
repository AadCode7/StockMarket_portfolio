# Security

- Supabase Auth handles signup, email confirmation, sessions, and password reset.
- Next.js uses the Supabase SSR package and server-side getUser() checks.
- FastAPI validates access tokens using Supabase JWKS, issuer, audience, and expiry.
- Row Level Security scopes user-owned records to auth.uid().
- Browser code may use only the Supabase publishable/anon key.
- Service-role keys bypass RLS and must never reach a browser or Git.
- Enforce ownership in API code as well as RLS.
- Never log tokens, passwords, or provider keys.
- Add rate limiting, audit logs, CSRF review, and security headers before public launch.
