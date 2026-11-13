# Security

- Supabase Auth handles signup, email confirmation, and sessions.
- Next.js uses @supabase/ssr and server-side auth.getUser() checks.
- FastAPI validates Supabase JWT signatures and the issuer, audience and expiry claims using the configured JWKS endpoint.
- Portfolio API calls forward the signed-in user's bearer token to PostgREST. Database RLS remains the authorization boundary.
- Public instruments and daily market bars are read-only to anon/authenticated roles.
- The optional SUPABASE_SERVICE_ROLE_KEY is used only by the backend market-data cache/ingestion path. It bypasses RLS and must never be sent to a browser, returned in an API response, or committed to Git.
- Never use a service-role client for a user's portfolio read or write.
- Never log bearer tokens, passwords, or provider API keys.
- Before public launch, add rate limiting, audit logging, security headers, abuse controls and a review of account recovery and email-delivery settings.
