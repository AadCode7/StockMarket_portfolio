"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

type Instrument = { id: string; company_name: string; nse_symbol: string | null; bse_symbol: string | null; bse_scrip_code: string | null; sector: string | null };
type Portfolio = { id: string; name: string; base_currency: string };
type PriceBar = { trading_date: string; open: number; high: number; low: number; close: number; volume: number };
type Technicals = {
  as_of: string; close: number; sma: Record<string, number | null>; rsi_14: number | null;
  macd: number | null; annualised_volatility_20d: number | null; maximum_drawdown_in_window: number;
  data_provider: string; recent_bars: PriceBar[];
};
type ModelScore = { model: string; mae: number; rmse: number; directional_accuracy: number; out_of_sample_r2: number; out_of_sample_predictions: number };
type BenchmarkResult = { selected_model: string; predicted_forward_return_pct: number; training_observations: number; zero_return_baseline_mae: number; model_scores: ModelScore[]; horizon_trading_days: number; disclaimer: string };
type PortfolioSummary = {
  holdings: Array<{ company_name: string; nse_symbol?: string; quantity: number; average_cost: number; market_value: number | null; unrealized_pnl: number | null }>;
  summary: { market_value: number | null; unrealized_pnl: number | null; realized_pnl: number; total_return_including_dividends: number | null; holdings_count: number };
  calculation_note: string;
};

const API = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const money = (v: number | null | undefined) => v == null ? "Not available" : new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(v);
const fmt = (v: number | null | undefined, digits = 2) => v == null ? "Not available" : v.toFixed(digits);

export default function ResearchWorkspace({ email }: { email: string }) {
  const [token, setToken] = useState("");
  const [query, setQuery] = useState("RELIANCE");
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [selected, setSelected] = useState<Instrument | null>(null);
  const [exchange, setExchange] = useState<"NSE" | "BSE">("NSE");
  const [technicals, setTechnicals] = useState<Technicals | null>(null);
  const [bars, setBars] = useState<PriceBar[]>([]);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [portfolioId, setPortfolioId] = useState("");
  const [portfolioName, setPortfolioName] = useState("My portfolio");
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkResult | null>(null);
  const [horizonDays, setHorizonDays] = useState<5 | 20 | 60>(5);
  const [kind, setKind] = useState<"BUY" | "SELL" | "DIVIDEND" | "FEE">("BUY");
  const [quantity, setQuantity] = useState("1");
  const [price, setPrice] = useState("");
  const [charges, setCharges] = useState("0");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const api = useCallback(async (path: string, init: RequestInit = {}) => {
    const headers = new Headers(init.headers);
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (init.body) headers.set("Content-Type", "application/json");
    const response = await fetch(`${API}/api/v1${path}`, { ...init, headers, cache: "no-store" });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
    return payload;
  }, [token]);

  const searchInstruments = useCallback(async (term: string) => {
    setError("");
    try {
      const response = await fetch(`${API}/api/v1/instruments?q=${encodeURIComponent(term)}&exchange=ALL&limit=30`, { cache: "no-store" });
      const rows = await response.json();
      if (!response.ok) throw new Error(rows.detail || "Instrument search failed");
      setInstruments(rows);
      setSelected(current => current ?? rows[0] ?? null);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not search instruments"); }
  }, []);

  const loadStock = useCallback(async (instrument: Instrument) => {
    setSelected(instrument); setTechnicals(null); setBars([]); setBenchmark(null); setError("");
    const symbol = exchange === "NSE" ? (instrument.nse_symbol || "") : (instrument.bse_symbol || "");
    if (!symbol) { setError(`No ${exchange} provider symbol is mapped for this instrument yet.`); return; }
    try {
      const response = await fetch(`${API}/api/v1/market-data/technicals?symbol=${encodeURIComponent(symbol)}&exchange=${exchange}&lookback_days=500`);
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Market data is unavailable");
      setTechnicals(result);
      setBars((result.recent_bars || []).slice().reverse());
    } catch (err) { setError(err instanceof Error ? err.message : "Could not load stock analysis"); }
  }, [exchange]);

  const loadPortfolios = useCallback(async () => {
    if (!token) return;
    try {
      const rows = await api("/portfolios");
      setPortfolios(rows);
      setPortfolioId(current => current || rows[0]?.id || "");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not load portfolios"); }
  }, [api, token]);

  const loadSummary = useCallback(async () => {
    if (!portfolioId) { setSummary(null); return; }
    try { setSummary(await api(`/portfolios/${portfolioId}/summary`)); }
    catch (err) { setSummary(null); setError(err instanceof Error ? err.message : "Could not load portfolio summary"); }
  }, [api, portfolioId]);

  useEffect(() => {
    let active = true;
    createClient().auth.getSession().then(({ data }) => { if (active) setToken(data.session?.access_token || ""); });
    void searchInstruments("RELIANCE");
    return () => { active = false; };
  }, [searchInstruments]);
  useEffect(() => { if (token) void loadPortfolios(); }, [token, loadPortfolios]);
  useEffect(() => { if (token && portfolioId) void loadSummary(); }, [token, portfolioId, loadSummary]);

  async function runBenchmark() {
    if (!selected) return;
    const symbol = exchange === "NSE" ? (selected.nse_symbol || "") : (selected.bse_symbol || "");
    if (!symbol) { setError(`No ${exchange} symbol is mapped for this instrument.`); return; }
    setBusy(true); setError(""); setNotice(""); setBenchmark(null);
    try {
      const result = await api("/ml/benchmark", {
        method: "POST",
        body: JSON.stringify({ symbol, exchange, horizon_days: horizonDays, lookback_days: 1500 }),
      });
      setBenchmark(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Model benchmark failed");
    } finally { setBusy(false); }
  }

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); await searchInstruments(query);
  }
  async function createPortfolio(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      const created = await api("/portfolios", { method: "POST", body: JSON.stringify({ name: portfolioName, base_currency: "INR" }) });
      const rows = await api("/portfolios"); setPortfolios(rows); setPortfolioId(created.id || rows[0]?.id || "");
      setNotice("Portfolio created.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not create portfolio"); }
    finally { setBusy(false); }
  }
  async function addTransaction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!portfolioId || !selected) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const amount = Number(price), units = kind === "BUY" || kind === "SELL" ? Number(quantity) : 0;
      if (!Number.isFinite(amount) || amount <= 0 || ((kind === "BUY" || kind === "SELL") && (!Number.isFinite(units) || units <= 0))) throw new Error("Enter a positive amount and quantity.");
      await api(`/portfolios/${portfolioId}/transactions`, {
        method: "POST",
        body: JSON.stringify({ instrument_id: selected.id, transaction_type: kind, quantity: units, price: amount, charges: Number(charges || 0), executed_at: new Date().toISOString() }),
      });
      await loadSummary(); setNotice("Transaction saved.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not save transaction"); }
    finally { setBusy(false); }
  }

  return <main className="mx-auto min-h-screen max-w-7xl px-5 py-8 md:px-8">
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-6">
      <div><p className="text-xs font-semibold uppercase tracking-[0.24em] text-blue-400">MarketLens</p><h1 className="mt-2 text-2xl font-semibold">Research workspace</h1><p className="mt-1 text-sm text-slate-400">{email}</p></div>
      <form action="/auth/signout" method="post"><button className="rounded-lg border border-slate-700 px-4 py-2 text-sm">Sign out</button></form>
    </header>
    {(error || notice) && <div role={error ? "alert" : "status"} className={`mt-5 rounded-lg border px-4 py-3 text-sm ${error ? "border-red-900 bg-red-950/30 text-red-300" : "border-emerald-900 bg-emerald-950/30 text-emerald-300"}`}>{error || notice}</div>}

    <div className="mt-8 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 md:p-6">
        <p className="text-sm text-blue-400">01 / Market research</p><h2 className="mt-1 text-xl font-semibold">NSE and BSE instruments</h2>
        <form onSubmit={search} className="mt-5 flex gap-2"><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Company name or symbol" className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-blue-500" /><button className="rounded-lg bg-blue-500 px-4 py-3 text-sm font-semibold text-slate-950">Search</button></form>
        <div className="mt-3 flex flex-wrap gap-2">{instruments.slice(0, 15).map(item => <button key={item.id} onClick={() => void loadStock(item)} className={`rounded-lg border px-3 py-2 text-left text-xs ${selected?.id === item.id ? "border-blue-500 bg-blue-500/10 text-blue-300" : "border-slate-700 text-slate-300"}`}><span className="block font-semibold">{item.nse_symbol || item.bse_scrip_code}</span><span className="mt-1 block max-w-36 truncate text-slate-500">{item.company_name}</span></button>)}</div>
        {selected && <div className="mt-6 border-t border-slate-800 pt-5">
          <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs uppercase tracking-wider text-slate-500">{exchange} · {selected.sector || "Sector not classified"}</p><h3 className="mt-1 text-lg font-semibold">{selected.company_name}</h3><p className="text-sm text-slate-400">{exchange === "NSE" ? selected.nse_symbol : selected.bse_symbol || "Not mapped"}</p></div><div className="flex items-center gap-2"><button type="button" onClick={() => { setExchange("NSE"); setTechnicals(null); setBars([]); }} className={`rounded-md border px-3 py-2 text-xs ${exchange === "NSE" ? "border-blue-500 text-blue-300" : "border-slate-700 text-slate-400"}`}>NSE</button><button type="button" onClick={() => { setExchange("BSE"); setTechnicals(null); setBars([]); }} className={`rounded-md border px-3 py-2 text-xs ${exchange === "BSE" ? "border-blue-500 text-blue-300" : "border-slate-700 text-slate-400"}`}>BSE</button><button type="button" onClick={() => void loadStock(selected!)} className="rounded-md bg-blue-500 px-3 py-2 text-xs font-semibold text-slate-950">Load {exchange}</button>{technicals && <div className="text-right"><p className="text-xs text-slate-500">Latest close · {technicals.as_of}</p><p className="text-2xl font-semibold">{money(technicals.close)}</p></div>}</div></div>
          {technicals ? <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric label="RSI (14)" value={fmt(technicals.rsi_14)} /><Metric label="SMA (20)" value={money(technicals.sma["20"])} /><Metric label="SMA (50)" value={money(technicals.sma["50"])} /><Metric label="SMA (200)" value={money(technicals.sma["200"])} />
            <Metric label="MACD" value={fmt(technicals.macd, 3)} /><Metric label="Annual volatility" value={technicals.annualised_volatility_20d == null ? "Not available" : `${(technicals.annualised_volatility_20d * 100).toFixed(2)}%`} /><Metric label="Window drawdown" value={`${(technicals.maximum_drawdown_in_window * 100).toFixed(2)}%`} /><Metric label="Provider" value={technicals.data_provider} />
          </div> : <p className="mt-5 text-sm text-slate-500">Select an instrument to load daily prices and technical indicators.</p>}
          {bars.length > 0 && <div className="mt-6 overflow-x-auto"><h4 className="mb-3 text-sm font-semibold">Recent daily prices</h4><table className="w-full min-w-[520px] text-left text-xs"><thead className="text-slate-500"><tr><th className="pb-2">Date</th><th className="pb-2 text-right">Open</th><th className="pb-2 text-right">High</th><th className="pb-2 text-right">Low</th><th className="pb-2 text-right">Close</th><th className="pb-2 text-right">Volume</th></tr></thead><tbody>{bars.map(row => <tr key={row.trading_date} className="border-t border-slate-800"><td className="py-2">{row.trading_date}</td><td className="py-2 text-right">{fmt(row.open)}</td><td className="py-2 text-right">{fmt(row.high)}</td><td className="py-2 text-right">{fmt(row.low)}</td><td className="py-2 text-right">{fmt(row.close)}</td><td className="py-2 text-right">{row.volume.toLocaleString("en-IN")}</td></tr>)}</tbody></table></div>}
          <div className="mt-6 border-t border-slate-800 pt-5">
            <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs uppercase tracking-wider text-blue-400">04 / Model lab</p><h4 className="mt-1 text-sm font-semibold">Walk-forward model benchmark</h4><p className="mt-1 text-xs text-slate-500">Ridge, Random Forest, Extra Trees and Gradient Boosting · {horizonDays}-day return</p></div><div className="flex items-center gap-2"><select value={horizonDays} onChange={e => setHorizonDays(Number(e.target.value) as 5 | 20 | 60)} className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-xs"><option value={5}>5 days</option><option value={20}>20 days</option><option value={60}>60 days</option></select><button type="button" disabled={busy || !token} onClick={() => void runBenchmark()} className="rounded-lg border border-blue-500 px-3 py-2 text-xs font-semibold text-blue-300 disabled:opacity-40">{busy ? "Running…" : "Run benchmark"}</button></div></div>
            {benchmark && <div className="mt-4">
              <div className="grid grid-cols-2 gap-3"><Metric label="Selected model" value={benchmark.selected_model} /><Metric label={`Estimated ${benchmark.horizon_trading_days}-day return`} value={`${benchmark.predicted_forward_return_pct.toFixed(3)}%`} /><Metric label="Training observations" value={String(benchmark.training_observations)} /><Metric label="Zero-return baseline MAE" value={benchmark.zero_return_baseline_mae.toFixed(5)} /></div>
              <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[420px] text-left text-xs"><thead className="text-slate-500"><tr><th className="pb-2">Model</th><th className="pb-2 text-right">MAE</th><th className="pb-2 text-right">RMSE</th><th className="pb-2 text-right">Direction</th></tr></thead><tbody>{benchmark.model_scores.map(row => <tr key={row.model} className="border-t border-slate-800"><td className="py-2">{row.model}</td><td className="py-2 text-right">{row.mae.toFixed(5)}</td><td className="py-2 text-right">{row.rmse.toFixed(5)}</td><td className="py-2 text-right">{(row.directional_accuracy * 100).toFixed(1)}%</td></tr>)}</tbody></table></div>
              <p className="mt-3 text-xs leading-5 text-slate-500">{benchmark.disclaimer}</p>
            </div>}
          </div>
          <p className="mt-4 text-xs leading-5 text-slate-500">Daily data is best-effort and may be delayed. Indicators are descriptive, not trading signals.</p>
        </div>}
      </section>

      <div className="space-y-6">
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 md:p-6">
          <p className="text-sm text-blue-400">02 / Portfolio</p><h2 className="mt-1 text-xl font-semibold">Your holdings</h2>
          <div className="mt-4 flex gap-2"><select value={portfolioId} onChange={e => setPortfolioId(e.target.value)} className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"><option value="">Select portfolio</option>{portfolios.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select><button onClick={() => void loadSummary()} disabled={!portfolioId} className="rounded-lg border border-slate-700 px-3 text-xs disabled:opacity-40">Refresh</button></div>
          <form onSubmit={createPortfolio} className="mt-3 flex gap-2"><input value={portfolioName} onChange={e => setPortfolioName(e.target.value)} placeholder="New portfolio name" className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm" /><button disabled={busy} className="rounded-lg bg-slate-200 px-3 py-2 text-xs font-semibold text-slate-950">Create</button></form>
          {summary && <><div className="mt-5 grid grid-cols-2 gap-3"><Metric label="Market value" value={money(summary.summary.market_value)} /><Metric label="Unrealised P&L" value={money(summary.summary.unrealized_pnl)} /><Metric label="Realised P&L" value={money(summary.summary.realized_pnl)} /><Metric label="Total return" value={money(summary.summary.total_return_including_dividends)} /></div><div className="mt-5 space-y-2">{summary.holdings.map(h => <div key={h.nse_symbol || h.company_name} className="flex items-center justify-between gap-3 border-t border-slate-800 pt-3 text-sm"><div className="min-w-0"><p className="truncate font-medium">{h.nse_symbol || h.company_name}</p><p className="text-xs text-slate-500">{h.quantity} units · Avg {money(h.average_cost)}</p></div><div className="text-right"><p>{money(h.market_value)}</p><p className="text-xs text-slate-400">{money(h.unrealized_pnl)}</p></div></div>)}</div><p className="mt-4 text-xs leading-5 text-slate-500">{summary.calculation_note}</p></>}
          {!summary && <p className="mt-5 text-sm text-slate-500">Create a portfolio and record buys, sells, dividends or fees. Your records are scoped to your account.</p>}
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 md:p-6">
          <p className="text-sm text-blue-400">03 / Ledger</p><h2 className="mt-1 text-xl font-semibold">Record a transaction</h2>
          <form onSubmit={addTransaction} className="mt-4 space-y-3">
            <label className="block text-xs text-slate-400">Portfolio<select required value={portfolioId} onChange={e => setPortfolioId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"><option value="">Select portfolio</option>{portfolios.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
            <label className="block text-xs text-slate-400">Selected instrument<input readOnly value={selected ? `${selected.nse_symbol || selected.bse_scrip_code} · ${selected.company_name}` : ""} placeholder="Choose an instrument above" className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100" /></label>
            <label className="block text-xs text-slate-400">Type<select value={kind} onChange={e => setKind(e.target.value as typeof kind)} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"><option value="BUY">Buy</option><option value="SELL">Sell</option><option value="DIVIDEND">Dividend</option><option value="FEE">Fee</option></select></label>
            {(kind === "BUY" || kind === "SELL") && <label className="block text-xs text-slate-400">Quantity<input required type="number" min="0.000001" step="any" value={quantity} onChange={e => setQuantity(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100" /></label>}
            <div className="grid grid-cols-2 gap-3"><label className="block text-xs text-slate-400">{kind === "DIVIDEND" || kind === "FEE" ? "Amount (INR)" : "Price / share (INR)"}<input required type="number" min="0.000001" step="any" value={price} onChange={e => setPrice(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100" /></label><label className="block text-xs text-slate-400">Charges (INR)<input type="number" min="0" step="any" value={charges} onChange={e => setCharges(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100" /></label></div>
            <button disabled={busy || !portfolioId || !selected} className="w-full rounded-lg bg-blue-500 px-4 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{busy ? "Saving…" : "Save transaction"}</button>
          </form>
        </section>
      </div>
    </div>
    <footer className="mt-8 border-t border-slate-800 pt-5 text-xs leading-5 text-slate-500">Market data may be delayed or unavailable. Portfolio calculations use recorded transactions and the latest stored closing prices. Research and record-keeping only, not investment advice.</footer>
  </main>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3"><p className="text-[11px] uppercase tracking-wider text-slate-500">{label}</p><p className="mt-2 break-words text-sm font-semibold text-slate-100">{value}</p></div>;
}
