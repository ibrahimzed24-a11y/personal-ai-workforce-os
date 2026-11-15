import aiosqlite
import json
import logging
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List, Optional

logger = logging.getLogger("ai_workforce_os.database")

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "ai_workforce.db"

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Core Agent Blueprints & Specialists
CREATE TABLE IF NOT EXISTS agent_blueprints (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    role TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT,
    capabilities TEXT NOT NULL, -- JSON array
    permissions TEXT NOT NULL,   -- JSON object
    default_model TEXT NOT NULL, -- JSON object
    version TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS specialist_definitions (
    id TEXT PRIMARY KEY,
    blueprint_id TEXT NOT NULL,
    name TEXT NOT NULL,
    specialization TEXT NOT NULL,
    skills TEXT NOT NULL, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(blueprint_id) REFERENCES agent_blueprints(id) ON DELETE CASCADE
);

-- Core Tasks & Execution Plans
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    assigned_agent_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, planning, in_progress, awaiting_approval, verifying, completed, failed
    priority TEXT NOT NULL DEFAULT 'medium', -- low, medium, high, urgent
    input_context TEXT,  -- JSON object
    output_result TEXT,  -- JSON object
    verification_status TEXT DEFAULT 'unverified', -- unverified, passed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_plans (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL UNIQUE,
    coordinator_id TEXT NOT NULL,
    steps TEXT NOT NULL, -- JSON array of PlanStep
    current_step_index INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft', -- draft, approved, executing, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS execution_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    step_id TEXT,
    agent_id TEXT,
    event_type TEXT NOT NULL, -- task_created, plan_created, step_started, tool_call, tool_result, approval_requested, verification, completed, error
    payload TEXT NOT NULL,    -- JSON object
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_id TEXT,
    action_type TEXT NOT NULL,
    details TEXT NOT NULL, -- JSON object
    status TEXT NOT NULL DEFAULT 'pending', -- pending, approved, rejected
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS verifications (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    verifier_type TEXT NOT NULL,
    status TEXT NOT NULL, -- passed, failed
    checks_run TEXT NOT NULL, -- JSON array of checks
    report_text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS system_requirements (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL, -- agent, specialist, model, tool, workflow, permission
    title TEXT NOT NULL,
    specification TEXT NOT NULL, -- JSON or text
    change_plan TEXT,           -- JSON array of proposed operations
    status TEXT NOT NULL DEFAULT 'draft', -- draft, proposed, approved, applied
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP
);

-- System Integrator & Installed Assets
CREATE TABLE IF NOT EXISTS installed_assets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- skill, tool, agent, model, workflow, integration, documentation, configuration, unknown
    source_path TEXT NOT NULL,
    install_path TEXT,
    version TEXT DEFAULT '1.0.0',
    status TEXT NOT NULL DEFAULT 'DISCOVERED', -- DISCOVERED, AUDITED, PLANNED, APPROVED, INSTALLING, TESTING, ACTIVE, REJECTED, BLOCKED, FAILED, DISABLED, ROLLED_BACK
    security_audit TEXT,      -- JSON object
    installation_plan TEXT,   -- JSON object
    dependencies TEXT,        -- JSON array
    target_agents TEXT,       -- JSON array
    capabilities_added TEXT,  -- JSON array
    test_results TEXT,        -- JSON object
    install_log TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    installed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operational_knowledge (
    key TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Centralized Credentials & Access Management
CREATE TABLE IF NOT EXISTS credential_accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    login_url TEXT NOT NULL,
    username_or_email TEXT NOT NULL,
    category TEXT NOT NULL, -- ai_tools, research_seo, marketing, social_media, hosting_domains, development, cloud_infra, analytics, communication, business_apps, personal, other
    project_id TEXT DEFAULT 'global',
    owner_id TEXT DEFAULT 'owner',
    status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, LOCKED, EXPIRED, REQUIRES_VERIFICATION
    auth_method TEXT NOT NULL DEFAULT 'PASSWORD', -- PASSWORD, OAUTH, API_KEY, SESSION_COOKIE
    mfa_status TEXT NOT NULL DEFAULT 'DISABLED', -- DISABLED, TOTP, SMS, EMAIL, SECURITY_KEY
    mfa_metadata TEXT, -- JSON object
    notes TEXT,
    recovery_instructions TEXT,
    health_status TEXT NOT NULL DEFAULT 'HEALTHY', -- HEALTHY, WARNING, EXPIRED, MISSING_CREDENTIALS
    last_successful_login TIMESTAMP,
    last_failed_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS credential_secrets (
    account_id TEXT PRIMARY KEY,
    encrypted_password TEXT NOT NULL,     -- Fernet authenticated ciphertext
    encrypted_api_key TEXT,               -- Fernet authenticated ciphertext
    encrypted_session_data TEXT,          -- Fernet authenticated JSON ciphertext
    version INTEGER NOT NULL DEFAULT 1,
    last_rotated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES credential_accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS credential_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    encrypted_password TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES credential_accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS credential_access_policies (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    permission_level TEXT NOT NULL, -- discover, authenticate, use, manage, administer
    project_id TEXT DEFAULT 'global',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES credential_accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS credential_access_sessions (
    session_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    project_id TEXT DEFAULT 'global',
    status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, EXPIRED, REVOKED
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES credential_accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS credential_registration_requests (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    service_name TEXT NOT NULL,
    website_url TEXT NOT NULL,
    category TEXT NOT NULL,
    reason TEXT NOT NULL,
    proposed_username_or_email TEXT NOT NULL,
    is_paid INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED, COMPLETED
    approval_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS credential_update_requests (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    update_type TEXT NOT NULL, -- password_rotation, mfa_update, username_change
    reason TEXT NOT NULL,
    new_encrypted_secret TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, APPROVED, VERIFYING, APPLIED, REJECTED, ROLLED_BACK
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES credential_accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS credential_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT,
    actor_type TEXT NOT NULL, -- agent, owner, system
    actor_id TEXT NOT NULL,
    task_id TEXT,
    action TEXT NOT NULL, -- DISCOVER, REQUEST_ACCESS, GRANT_ACCESS, AUTHENTICATE, AUTH_SUCCESS, AUTH_FAILED, REVEAL_PASSWORD, ROTATE_PASSWORD, REGISTER_REQUEST, REGISTER_APPROVED, REVOKE_SESSION
    status TEXT NOT NULL, -- SUCCESS, DENIED, FAILED, PENDING_APPROVAL
    details TEXT,         -- JSON object (never contains plaintext secrets!)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Post-Implementation Verification & Evidence Audit System
CREATE TABLE IF NOT EXISTS verification_audits (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    target_component TEXT NOT NULL,
    target_version TEXT,
    profile TEXT NOT NULL, -- lightweight, standard, comprehensive, security_audit
    status TEXT NOT NULL,  -- VERIFIED, IMPLEMENTED_NOT_VERIFIED, PARTIALLY_IMPLEMENTED, MOCKED_OR_SIMULATED, NOT_IMPLEMENTED, BROKEN, BLOCKED
    initiated_by TEXT NOT NULL, -- coordinator, verifier, system_integrator, deployment_agent, user
    requirements_evaluated TEXT NOT NULL, -- JSON array
    inspections TEXT NOT NULL,            -- JSON array
    tests_executed TEXT NOT NULL,         -- JSON array
    security_findings TEXT NOT NULL,      -- JSON array
    reliability_findings TEXT NOT NULL,   -- JSON array
    evidence_summary TEXT NOT NULL,
    evidence_artifact_path TEXT,
    remediation_plan TEXT,                -- JSON object or text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- LLM Provider & Model Management
CREATE TABLE IF NOT EXISTS llm_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider_type TEXT NOT NULL, -- local_ollama, cloud_openai, cloud_gemini, cloud_anthropic, openai_compatible, mock
    base_url TEXT NOT NULL,
    api_key_ref TEXT,            -- Vault account ID reference if secured
    is_active INTEGER NOT NULL DEFAULT 1,
    health_status TEXT NOT NULL DEFAULT 'unknown', -- healthy, unreachable, unauthenticated, error, unknown
    last_health_check TIMESTAMP,
    config_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS llm_models (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    classification TEXT NOT NULL, -- local, cloud, mock
    context_window INTEGER DEFAULT 8192,
    supports_tools INTEGER NOT NULL DEFAULT 1,
    supports_structured_output INTEGER NOT NULL DEFAULT 1,
    supports_vision INTEGER NOT NULL DEFAULT 0,
    capabilities TEXT NOT NULL DEFAULT '[]', -- JSON array of tags: coding, reasoning, fast, general
    is_active INTEGER NOT NULL DEFAULT 1,
    is_default INTEGER NOT NULL DEFAULT 0,
    latency_p50_ms REAL DEFAULT 0.0,
    success_rate REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(provider_id) REFERENCES llm_providers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS llm_routing_rules (
    id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    task_category TEXT NOT NULL DEFAULT '*', -- code, research, marketing, coordination, general, sensitive
    agent_id_match TEXT NOT NULL DEFAULT '*',
    privacy_level TEXT NOT NULL DEFAULT 'standard', -- local_only, standard, cloud_allowed
    preferred_model_id TEXT NOT NULL,
    fallback_model_id TEXT,
    allow_cloud_fallback INTEGER NOT NULL DEFAULT 0,
    priority INTEGER NOT NULL DEFAULT 10,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(preferred_model_id) REFERENCES llm_models(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS llm_usage_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    step_id TEXT,
    agent_id TEXT,
    model_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    latency_ms REAL DEFAULT 0.0,
    success INTEGER NOT NULL DEFAULT 1,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_events_task_id ON execution_events(task_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_installed_assets_status ON installed_assets(status);
CREATE INDEX IF NOT EXISTS idx_credential_accounts_cat ON credential_accounts(category);
CREATE INDEX IF NOT EXISTS idx_credential_access_agent ON credential_access_policies(agent_id);
CREATE INDEX IF NOT EXISTS idx_credential_audit_acc ON credential_audit_logs(account_id);
CREATE INDEX IF NOT EXISTS idx_credential_audit_actor ON credential_audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_verification_audits_status ON verification_audits(status);
CREATE INDEX IF NOT EXISTS idx_verification_audits_target ON verification_audits(target_component);
CREATE INDEX IF NOT EXISTS idx_verification_audits_profile ON verification_audits(profile);
CREATE INDEX IF NOT EXISTS idx_llm_models_provider ON llm_models(provider_id);
CREATE INDEX IF NOT EXISTS idx_llm_models_active ON llm_models(is_active);
CREATE INDEX IF NOT EXISTS idx_llm_routing_task ON llm_routing_rules(task_category);
CREATE INDEX IF NOT EXISTS idx_llm_metrics_task ON llm_usage_metrics(task_id);
CREATE INDEX IF NOT EXISTS idx_llm_metrics_model ON llm_usage_metrics(model_id);
"""

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode = WAL;")
    await db.execute("PRAGMA foreign_keys = ON;")
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    logger.info(f"Database initialized successfully at {DB_PATH}")
