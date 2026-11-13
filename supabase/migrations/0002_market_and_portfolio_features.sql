-- Market data, instrument lookup, and portfolio workspace.
-- Run after 0001_initial_schema.sql.

alter table public.instruments add column if not exists bse_symbol text;
create index if not exists idx_instruments_name on public.instruments (company_name);
create index if not exists idx_instruments_nse_symbol on public.instruments (nse_symbol);
create index if not exists idx_instruments_bse_symbol on public.instruments (bse_symbol);
create index if not exists idx_instruments_bse_code on public.instruments (bse_scrip_code);

create table if not exists public.market_data_ingestion_runs (
  id uuid primary key default gen_random_uuid(),
  instrument_id uuid references public.instruments(id) on delete set null,
  exchange text not null check (exchange in ('NSE', 'BSE')),
  provider text not null,
  requested_start date not null,
  requested_end date not null,
  rows_received integer not null default 0 check (rows_received >= 0),
  rows_persisted integer not null default 0 check (rows_persisted >= 0),
  status text not null check (status in ('success', 'partial', 'failed')),
  error_message text,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  check (requested_start <= requested_end)
);
alter table public.market_data_ingestion_runs enable row level security;
revoke all on public.market_data_ingestion_runs from anon, authenticated;

create table if not exists public.corporate_actions (
  id uuid primary key default gen_random_uuid(),
  instrument_id uuid not null references public.instruments(id) on delete cascade,
  action_type text not null check (action_type in ('DIVIDEND', 'SPLIT', 'BONUS', 'RIGHTS', 'OTHER')),
  ex_date date not null,
  record_date date,
  payment_date date,
  ratio_numerator numeric(18,6),
  ratio_denominator numeric(18,6),
  cash_amount numeric(18,6),
  currency text not null default 'INR',
  source_url text,
  provider text not null,
  retrieved_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
create index if not exists idx_corporate_actions_instrument_date
  on public.corporate_actions(instrument_id, ex_date desc);
alter table public.corporate_actions enable row level security;
drop policy if exists "Corporate actions are publicly readable" on public.corporate_actions;
create policy "Corporate actions are publicly readable"
  on public.corporate_actions for select to anon, authenticated using (true);
grant select on public.corporate_actions to anon, authenticated;

-- Seed a starter universe. ISINs remain null until loaded from an authoritative exchange master.
insert into public.instruments (company_name, nse_symbol, bse_symbol, bse_scrip_code, sector, currency)
values
  ('Reliance Industries Limited', 'RELIANCE', 'RELIANCE', '500325', 'Energy', 'INR'),
  ('Tata Consultancy Services Limited', 'TCS', 'TCS', '532540', 'Information Technology', 'INR'),
  ('Infosys Limited', 'INFY', 'INFY', '500209', 'Information Technology', 'INR'),
  ('HDFC Bank Limited', 'HDFCBANK', 'HDFCBANK', '500180', 'Financial Services', 'INR'),
  ('ICICI Bank Limited', 'ICICIBANK', 'ICICIBANK', '532174', 'Financial Services', 'INR'),
  ('State Bank of India', 'SBIN', 'SBIN', '500112', 'Financial Services', 'INR'),
  ('ITC Limited', 'ITC', 'ITC', '500875', 'FMCG', 'INR'),
  ('Larsen & Toubro Limited', 'LT', 'LT', '500510', 'Industrials', 'INR'),
  ('Bharti Airtel Limited', 'BHARTIARTL', 'BHARTIARTL', '532454', 'Telecommunication', 'INR'),
  ('Tata Motors Limited', 'TATAMOTORS', 'TATAMOTORS', '500570', 'Automobile', 'INR'),
  ('Hindustan Unilever Limited', 'HINDUNILVR', 'HINDUNILVR', '500696', 'FMCG', 'INR'),
  ('Axis Bank Limited', 'AXISBANK', 'AXISBANK', '532215', 'Financial Services', 'INR'),
  ('Kotak Mahindra Bank Limited', 'KOTAKBANK', 'KOTAKBANK', '500247', 'Financial Services', 'INR'),
  ('Wipro Limited', 'WIPRO', 'WIPRO', '507685', 'Information Technology', 'INR'),
  ('Maruti Suzuki India Limited', 'MARUTI', 'MARUTI', '532500', 'Automobile', 'INR')
on conflict do nothing;

create index if not exists idx_portfolio_transactions_instrument
  on public.portfolio_transactions(portfolio_id, instrument_id, executed_at);
