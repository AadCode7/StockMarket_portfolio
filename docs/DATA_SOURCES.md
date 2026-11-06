# Initial data-source policy

| Source | Intended use | Caveat |
|---|---|---|
| Yahoo Finance via yfinance | Prototype NSE/BSE daily historical bars | Unofficial, best-effort; availability and terms can change. No live-data guarantee or redistribution right is assumed. |
| Alpha Vantage | Optional secondary BSE daily history | Requires a free API key; documented India ticker example uses SYMBOL.BSE. NSE fallback is deliberately disabled until its symbol mapping is verified. Free request limits apply. |
| NSE/BSE disclosures | Exchange-published company filings and information | Market-data feeds and commercial use can require a licence/agreement. Do not scrape private endpoints. |
| Company investor-relations pages | Annual reports and quarterly results | Respect site terms, robots rules, and document copyright. |
| RBI public datasets | Macro context | Preserve publication date and source URL. |

The backend tries providers in MARKET_DATA_PROVIDERS order. Missing credentials or unsupported exchange formats cause a provider to be skipped. If all sources fail, return an explicit unavailable-data error. Never fabricate prices or label daily bars as live quotes.

Before enabling a source, verify symbol format, coverage, adjustment status, trading dates, corporate-action discontinuities, and storage/display/redistribution terms.
