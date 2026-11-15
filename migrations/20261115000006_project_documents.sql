-- 6. Project Core Documents / Files (PDF, CSV, XLSX) for Agent Harness Context
create table if not exists public.project_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  project_id uuid references public.projects(id) on delete cascade not null,
  file_name text not null,
  file_type text not null, -- 'pdf', 'csv', 'xlsx', 'json', 'txt'
  file_size integer not null default 0,
  row_count integer default null,
  page_count integer default null,
  columns jsonb default '[]'::jsonb,
  sample_rows jsonb default '[]'::jsonb,
  extracted_text text not null default '',
  file_data_base64 text default null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.project_documents enable row level security;

drop policy if exists "Users manage own project documents" on public.project_documents;
create policy "Users manage own project documents"
  on public.project_documents for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
