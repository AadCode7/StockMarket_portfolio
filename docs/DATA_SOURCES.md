# Data-source policy

| Source | Use | Limitations |
|---|---|---|
| Yahoo Finance via yfinance | Best-effort NSE/BSE daily OHLCV history | Unofficial endpoint wrapper; availability, accuracy, terms and coverage can change. Not a live feed or assumed redistribution licence. |
| Alpha Vantage | Optional BSE daily history fallback | Requires a free API key; free request limits apply; exchange symbol coverage must be checked. |
| NSE/BSE instrument data and disclosures | Authoritative instrument mapping and company filings | Confirm permitted access, storage and redistribution rights. |
| Company investor-relations pages | Annual reports and quarterly results | Respect terms and document copyright. |
| RBI public datasets | Macro context in a later phase | Preserve publication date and source URL. |

## Data integrity
- Every stored bar includes exchange, provider, retrieval timestamp, and trading date.
- Raw OHLC and adjusted close are kept separately.
- Provider results are checked for valid OHLC values, non-negative volume, requested date range and duplicate trading dates.
- Provider fallback is sequential and configuration-driven. An empty or invalid response is a failure, not a zero-price observation.
- Cached bars are used only when their retrieval timestamp is within the configured cache window and the requested date range appears covered.
- If providers fail, previously stored bars may be returned with their original provider and retrieval timestamps.
- Do not describe daily bars as live quotes.

## Free-tier policy
A free API key is not a grant of exchange redistribution rights. Check provider terms before publishing, sharing or commercialising market data. Never scrape undocumented endpoints or bypass rate limits.
