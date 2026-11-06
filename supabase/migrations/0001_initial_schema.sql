create extension if not exists pgcrypto;
create extension if not exists vector with schema extensions;

create table if not exists public.instruments (
  id uuid primary key default gen_random_uuid(),
  company_name text not null,
  isin text unique,
  nse_symbol text unique,
  bse_scrip_code text unique,
  sector text,
  industry text,
  currency text not null default 'INR',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint instruments_has_identifier check (isin is not null or nse_symbol is not null or bse_scrip_code is not null)
);

create table if not exists public.price_history (
  id bigint generated always as identity primary key,
  instrument_id uuid not null references public.instruments(id) on delete cascade,
  exchange text not null check (exchange in ('NSE', 'BSE')),
  trading_date date not null,
  open numeric(18,4) not null,
  high numeric(18,4) not null,
  low numeric(18,4) not null,
  close numeric(18,4) not null,
  adjusted_close numeric(18,4),
  volume bigint not null default 0,
  provider text not null,
  retrieved_at timestamptz not null default now(),
  is_adjusted boolean not null default false,
  unique (instrument_id, exchange, trading_date, provider),
  check (high >= low),
  check (volume >= 0)
);
create index if not exists idx_price_history_instrument_date
  on public.price_history(instrument_id, trading_date desc);

create table if not exists public.portfolios (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 100),
  base_currency text not null default 'INR',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_portfolios_user on public.portfolios(user_id);

create table if not exists public.portfolio_transactions (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references public.portfolios(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  instrument_id uuid not null references public.instruments(id),
  transaction_type text not null check (transaction_type in ('BUY','SELL','DIVIDEND','FEE')),
  quantity numeric(20,6) not null default 0,
  price numeric(20,6) not null default 0,
  charges numeric(20,6) not null default 0,
  executed_at timestamptz not null,
  notes text,
  created_at timestamptz not null default now(),
  check (quantity >= 0 and price >= 0 and charges >= 0)
);
create index if not exists idx_portfolio_transactions_owner
  on public.portfolio_transactions(user_id, portfolio_id, executed_at desc);

create table if not exists public.research_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  instrument_id uuid references public.instruments(id) on delete set null,
  title text not null,
  source_url text,
  source_name text,
  document_type text,
  published_at timestamptz,
  ingested_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.research_documents(id) on delete cascade,
  user_id uuid references auth.users(id) on delete cascade,
  chunk_index integer not null,
  content text not null,
  embedding extensions.vector(384),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(document_id, chunk_index)
);
create index if not exists idx_document_chunks_embedding
  on public.document_chunks using ivfflat (embedding extensions.vector_cosine_ops) with (lists = 100);

alter table public.instruments enable row level security;
alter table public.price_history enable row level security;
create policy "Instruments are readable" on public.instruments
  for select to anon, authenticated using (true);
create policy "Price history is readable" on public.price_history
  for select to anon, authenticated using (true);

alter table public.portfolios enable row level security;
create policy "Users manage their portfolios" on public.portfolios
  for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table public.portfolio_transactions enable row level security;
create policy "Users manage their own transactions" on public.portfolio_transactions
  for all to authenticated
  using (auth.uid() = user_id and exists (
    select 1 from public.portfolios p where p.id = portfolio_id and p.user_id = auth.uid()
  ))
  with check (auth.uid() = user_id and exists (
    select 1 from public.portfolios p where p.id = portfolio_id and p.user_id = auth.uid()
  ));

alter table public.research_documents enable row level security;
create policy "Users read public or owned research documents" on public.research_documents
  for select to authenticated using (user_id is null or user_id = auth.uid());
create policy "Users manage owned research documents" on public.research_documents
  for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

alter table public.document_chunks enable row level security;
create policy "Users read public or owned chunks" on public.document_chunks
  for select to authenticated using (user_id is null or user_id = auth.uid());
create policy "Users manage owned chunks" on public.document_chunks
  for all to authenticated
  using (user_id = auth.uid() and exists (
    select 1 from public.research_documents d where d.id = document_id and d.user_id = auth.uid()
  ))
  with check (user_id = auth.uid() and exists (
    select 1 from public.research_documents d where d.id = document_id and d.user_id = auth.uid()
  ));

grant select on public.instruments, public.price_history to anon, authenticated;
grant select, insert, update, delete on public.portfolios, public.portfolio_transactions to authenticated;
grant select, insert, update, delete on public.research_documents, public.document_chunks to authenticated;
