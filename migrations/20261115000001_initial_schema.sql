-- =============================================================================
-- Migration: 20261115000001_initial_schema.sql
-- Description: Core Operational Schema for Personal AI Workforce OS on Supabase PostgreSQL
-- Security Boundary: Strictly operational metadata only. Secrets, credentials,
-- and website accounts remain exclusively in local SQLite on the MacBook.
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1. AGENT BLUEPRINTS & SPECIALIST DEFINITIONS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS agent_blueprints (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    role TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT,
    capabilities JSONB DEFAULT '[]'::jsonb,
    permissions JSONB DEFAULT '[]'::jsonb,
    default_model TEXT DEFAULT 'gemini-2.5-flash',
    version TEXT DEFAULT '2.0.0',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS specialist_definitions (
    id TEXT PRIMARY KEY,
    blueprint_id TEXT NOT NULL REFERENCES agent_blueprints(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    specialization TEXT NOT NULL,
    skills JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_blueprints_dept ON agent_blueprints(department);
CREATE INDEX IF NOT EXISTS idx_specialist_blueprint_id ON specialist_definitions(blueprint_id);

-- -----------------------------------------------------------------------------
-- 2. OPERATIONAL TASKS, PLANS & EXECUTION EVENTS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    assigned_agent_id TEXT REFERENCES agent_blueprints(id),
    status TEXT NOT NULL DEFAULT 'PENDING',
    priority TEXT NOT NULL DEFAULT 'MEDIUM',
    input_context JSONB DEFAULT '{}'::jsonb,
    output_result JSONB,
    verification_status TEXT DEFAULT 'UNVERIFIED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

CREATE TABLE IF NOT EXISTS task_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    coordinator_id TEXT REFERENCES agent_blueprints(id),
    steps JSONB DEFAULT '[]'::jsonb,
    current_step_index INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'PLANNING',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_plans_task ON task_plans(task_id);

CREATE TABLE IF NOT EXISTS execution_events (
    id BIGSERIAL PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    step_id TEXT,
    agent_id TEXT REFERENCES agent_blueprints(id),
    event_type TEXT NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exec_events_task ON execution_events(task_id);
CREATE INDEX IF NOT EXISTS idx_exec_events_agent ON execution_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_exec_events_timestamp ON execution_events(timestamp DESC);

-- -----------------------------------------------------------------------------
-- 3. APPROVALS & VERIFICATION AUDITS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    step_id TEXT,
    action_type TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'PENDING',
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    responded_at TIMESTAMPTZ,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);

CREATE TABLE IF NOT EXISTS verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    verifier_type TEXT NOT NULL,
    status TEXT NOT NULL,
    checks_run JSONB DEFAULT '[]'::jsonb,
    report_text TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS verification_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    target_component TEXT NOT NULL,
    target_version TEXT NOT NULL,
    profile TEXT NOT NULL,
    status TEXT NOT NULL,
    initiated_by TEXT,
    requirements_evaluated JSONB DEFAULT '[]'::jsonb,
    inspections JSONB DEFAULT '[]'::jsonb,
    tests_executed JSONB DEFAULT '[]'::jsonb,
    security_findings JSONB DEFAULT '[]'::jsonb,
    reliability_findings JSONB DEFAULT '[]'::jsonb,
    evidence_summary TEXT,
    evidence_artifact_path TEXT,
    remediation_plan TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- -----------------------------------------------------------------------------
-- 4. SYSTEM REQUIREMENTS, ASSETS & OPERATIONAL KNOWLEDGE
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS system_requirements (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    specification TEXT NOT NULL,
    change_plan TEXT,
    status TEXT NOT NULL DEFAULT 'PROPOSED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    applied_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS installed_assets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    source_path TEXT,
    install_path TEXT,
    version TEXT,
    status TEXT NOT NULL,
    security_audit JSONB DEFAULT '{}'::jsonb,
    installation_plan JSONB DEFAULT '{}'::jsonb,
    dependencies JSONB DEFAULT '[]'::jsonb,
    target_agents JSONB DEFAULT '[]'::jsonb,
    capabilities_added JSONB DEFAULT '[]'::jsonb,
    test_results JSONB DEFAULT '{}'::jsonb,
    install_log TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    installed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS operational_knowledge (
    key TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 5. LLM PROVIDERS, MODELS, ROUTING RULES & METRICS
-- (Note: Raw API keys are NEVER stored here; api_key_ref points to local vault or env)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS llm_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    base_url TEXT,
    api_key_ref TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    health_status TEXT DEFAULT 'healthy',
    last_health_check TIMESTAMPTZ DEFAULT NOW(),
    config_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS llm_models (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL REFERENCES llm_providers(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    classification TEXT NOT NULL,
    context_window INTEGER NOT NULL DEFAULT 8192,
    supports_tools BOOLEAN DEFAULT TRUE,
    supports_structured_output BOOLEAN DEFAULT TRUE,
    supports_vision BOOLEAN DEFAULT FALSE,
    capabilities JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    latency_p50_ms REAL DEFAULT 0.0,
    success_rate REAL DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS llm_routing_rules (
    id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    task_category TEXT NOT NULL,
    agent_id_match TEXT,
    privacy_level TEXT NOT NULL DEFAULT 'standard',
    preferred_model_id TEXT REFERENCES llm_models(id),
    fallback_model_id TEXT REFERENCES llm_models(id),
    allow_cloud_fallback BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS llm_usage_metrics (
    id BIGSERIAL PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    step_id TEXT,
    agent_id TEXT REFERENCES agent_blueprints(id),
    model_id TEXT REFERENCES llm_models(id),
    provider_id TEXT REFERENCES llm_providers(id),
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    latency_ms REAL DEFAULT 0.0,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_metrics_agent ON llm_usage_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_llm_metrics_model ON llm_usage_metrics(model_id);
CREATE INDEX IF NOT EXISTS idx_llm_metrics_timestamp ON llm_usage_metrics(timestamp DESC);
