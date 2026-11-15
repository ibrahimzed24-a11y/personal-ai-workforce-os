-- Personal AI Workforce OS v3.2: Live Connected Chat, Pipeline Handovers & Project-Isolated Reporting

-- 1. Project Slug support
alter table public.projects 
  add column if not exists slug text;

update public.projects 
  set slug = lower(regexp_replace(trim(name), '[^a-zA-Z0-9]+', '-', 'g'))
  where slug is null or slug = '';

create index if not exists idx_projects_slug on public.projects(slug);

-- 2. Enhanced Chat Messages (Direct agent chat, slash-command attribution, telemetry, embedded artifact cards)
alter table public.project_messages
  add column if not exists recipient_agent text default null,
  add column if not exists command text default null,
  add column if not exists command_args jsonb default '{}'::jsonb,
  add column if not exists token_count integer default 0,
  add column if not exists latency_ms integer default 0,
  add column if not exists artifacts jsonb default '[]'::jsonb,
  add column if not exists stage_status text default null;

create index if not exists idx_project_messages_recipient on public.project_messages(recipient_agent);

-- 3. Pipeline Runs Ledger & Synthesis
alter table public.pipeline_runs
  add column if not exists project_slug text,
  add column if not exists task_id uuid default gen_random_uuid(),
  add column if not exists completed_ledger jsonb default '[]'::jsonb,
  add column if not exists pending_ledger jsonb default '[]'::jsonb,
  add column if not exists master_report_url text default null,
  add column if not exists exported_files jsonb default '[]'::jsonb;

-- 4. Pipeline Handovers (Stage-to-stage agent handoff payloads & 5-stage loop logs)
create table if not exists public.pipeline_handovers (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null,
  project_id uuid references public.projects(id) on delete cascade not null,
  project_slug text not null,
  step_number integer not null default 1,
  from_agent_id text not null,
  to_agent_id text not null,
  execution_status text not null default 'VERIFIED_COMPLETE',
  completed_actions jsonb not null default '[]'::jsonb,
  pending_items jsonb not null default '[]'::jsonb,
  exported_artifacts jsonb not null default '[]'::jsonb,
  handover_payload jsonb not null default '{}'::jsonb,
  context_for_next_agent text not null default '',
  latency_ms integer not null default 0,
  created_at timestamptz not null default now()
);

create index if not exists idx_pipeline_handovers_task on public.pipeline_handovers(task_id);
create index if not exists idx_pipeline_handovers_proj on public.pipeline_handovers(project_id);

alter table public.pipeline_handovers enable row level security;

drop policy if exists "Users manage own handovers" on public.pipeline_handovers;
create policy "Users manage own handovers"
  on public.pipeline_handovers for all
  using (
    exists (
      select 1 from public.projects p
      where p.id = pipeline_handovers.project_id
      and p.user_id = auth.uid()
    )
  );

-- 5. Project Reports & Multi-Format Exports Registry
create table if not exists public.project_reports (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade not null,
  project_slug text not null,
  task_id uuid not null,
  agent_id text not null,
  pipeline_step integer not null default 1,
  title text not null,
  file_format text not null, -- 'pdf', 'docx', 'xlsx', 'csv', 'md', 'svg', 'zip', 'json'
  file_size integer not null default 0,
  local_path text not null,
  storage_url text default null,
  verification_status text not null default 'VERIFIED',
  metadata jsonb not null default '{}'::jsonb,
  content_preview text default null,
  created_at timestamptz not null default now()
);

create index if not exists idx_project_reports_task on public.project_reports(task_id);
create index if not exists idx_project_reports_proj on public.project_reports(project_id);
create index if not exists idx_project_reports_format on public.project_reports(file_format);

alter table public.project_reports enable row level security;

drop policy if exists "Users manage own project reports" on public.project_reports;
create policy "Users manage own project reports"
  on public.project_reports for all
  using (
    exists (
      select 1 from public.projects p
      where p.id = project_reports.project_id
      and p.user_id = auth.uid()
    )
  );

-- 6. Enable Realtime Publications
do $$
begin
  alter publication supabase_realtime add table public.project_messages;
exception when others then null;
end $$;

do $$
begin
  alter publication supabase_realtime add table public.pipeline_runs;
exception when others then null;
end $$;

do $$
begin
  alter publication supabase_realtime add table public.pipeline_handovers;
exception when others then null;
end $$;

do $$
begin
  alter publication supabase_realtime add table public.project_reports;
exception when others then null;
end $$;
