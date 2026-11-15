-- Personal AI Workforce OS v3.0: Project Isolation, Credential Vault, Pipeline Handoffs & Bilingual Chat

create extension if not exists "pgcrypto";

-- 1. Projects (Each project is an isolated workspace)
create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  name text not null,
  goal text not null default '',
  runtime_mode text not null default 'antigravity' check (runtime_mode in ('antigravity', 'local_llm', 'cloud_api')),
  assigned_agents jsonb not null default '["coordinator", "browser-researcher", "operations-writer"]'::jsonb,
  status text not null default 'active' check (status in ('active', 'paused', 'archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 2. Encrypted Credential Vault & Permitted Tools per Project
create table if not exists public.credential_vault (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  project_id uuid references public.projects(id) on delete cascade not null,
  tool_name text not null,
  login_url text not null,
  username_identifier text not null,
  encrypted_secret text not null,
  allowed_actions jsonb not null default '["read", "browse", "draft"]'::jsonb,
  is_enabled boolean not null default true,
  created_at timestamptz not null default now()
);

-- 3. Project Chat Messages (English & Egyptian Arabic operator commands)
create table if not exists public.project_messages (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  project_id uuid references public.projects(id) on delete cascade not null,
  sender_role text not null check (sender_role in ('operator', 'coordinator', 'agent', 'system')),
  sender_name text not null default 'Operator',
  content text not null,
  language text not null default 'en',
  created_at timestamptz not null default now()
);

-- 4. Sequential Pipeline Runs & Admin Reports
create table if not exists public.pipeline_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  project_id uuid references public.projects(id) on delete cascade not null,
  directive text not null,
  runtime_used text not null default 'antigravity',
  status text not null default 'completed' check (status in ('running', 'completed', 'failed')),
  handoff_steps jsonb not null default '[]'::jsonb,
  admin_report text not null default '',
  latency_ms integer not null default 0,
  created_at timestamptz not null default now()
);

-- 5. Strict Row-Level Security (RLS)
alter table public.projects enable row level security;
alter table public.credential_vault enable row level security;
alter table public.project_messages enable row level security;
alter table public.pipeline_runs enable row level security;

drop policy if exists "Users manage own projects" on public.projects;
create policy "Users manage own projects"
  on public.projects for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "Users manage own vault" on public.credential_vault;
create policy "Users manage own vault"
  on public.credential_vault for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "Users manage own messages" on public.project_messages;
create policy "Users manage own messages"
  on public.project_messages for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "Users manage own runs" on public.pipeline_runs;
create policy "Users manage own runs"
  on public.pipeline_runs for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
