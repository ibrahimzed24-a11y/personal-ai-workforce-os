-- 7. Add dynamic LLM provider, model, and endpoint configuration per project
alter table public.projects 
  add column if not exists llm_provider text not null default 'gemini',
  add column if not exists llm_model text not null default 'gemini-2.5-flash',
  add column if not exists llm_api_key text default null,
  add column if not exists llm_endpoint text default null,
  add column if not exists llm_settings jsonb not null default '{"temperature": 0.7, "max_tokens": 4096}'::jsonb;
