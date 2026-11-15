import json
import logging
import sqlite3
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, List, Optional

try:
    import aiosqlite
    HAS_AIOSQLITE = True
except ImportError:
    aiosqlite = None
    HAS_AIOSQLITE = False

logger = logging.getLogger("ai_workforce_os.database")

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "ai_workforce.db"
_SCHEMA_ENSURED = False


class _FallbackAsyncCursor:
    """Async-compatible cursor wrapper around stdlib sqlite3.Cursor when aiosqlite is unavailable."""
    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def lastrowid(self) -> Optional[int]:
        return self._cursor.lastrowid

    async def fetchone(self):
        return self._cursor.fetchone()

    async def fetchall(self):
        return self._cursor.fetchall()

    async def close(self):
        self._cursor.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._cursor.close()


class _FallbackExecuteContext:
    """Supports both `await db.execute(...)` and `async with db.execute(...) as cursor:`."""
    def __init__(self, conn: sqlite3.Connection, sql: str, parameters: Any = ()):
        self._conn = conn
        self._sql = sql
        self._parameters = parameters
        self._cursor: Optional[_FallbackAsyncCursor] = None

    def _run(self) -> _FallbackAsyncCursor:
        if self._cursor is None:
            raw_cur = self._conn.execute(self._sql, self._parameters)
            self._cursor = _FallbackAsyncCursor(raw_cur)
        return self._cursor

    def __await__(self):
        async def _coro():
            return self._run()
        return _coro().__await__()

    async def __aenter__(self) -> _FallbackAsyncCursor:
        return self._run()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._cursor is not None:
            await self._cursor.close()


class _FallbackAsyncConnection:
    """Drop-in async wrapper around stdlib sqlite3.Connection matching aiosqlite.Connection."""
    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    @property
    def row_factory(self):
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, factory):
        self._conn.row_factory = factory

    def execute(self, sql: str, parameters: Any = ()) -> _FallbackExecuteContext:
        return _FallbackExecuteContext(self._conn, sql, parameters)

    async def executescript(self, sql_script: str):
        self._conn.executescript(sql_script)

    async def commit(self):
        self._conn.commit()

    async def rollback(self):
        self._conn.rollback()

    async def close(self):
        self._conn.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._conn.close()


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
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- 5-Stage Agent Execution Loop Traces (Run Policy -> Think -> Act -> Observe -> Deterministic Code Check)
CREATE TABLE IF NOT EXISTS agent_loop_traces (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    step_id TEXT,
    agent_id TEXT NOT NULL,
    specialist_id TEXT,
    skill_command TEXT NOT NULL,
    status TEXT NOT NULL,
    iterations_run INTEGER NOT NULL DEFAULT 1,
    policy_check TEXT NOT NULL,
    think_traces TEXT NOT NULL,
    act_records TEXT NOT NULL,
    observations TEXT NOT NULL,
    deterministic_check TEXT NOT NULL,
    final_output TEXT,
    duration_ms REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_id TEXT,
    action_type TEXT NOT NULL,
    details TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS verifications (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    verifier_type TEXT NOT NULL,
    status TEXT NOT NULL,
    checks_run TEXT NOT NULL,
    report_text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS system_requirements (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    specification TEXT NOT NULL,
    change_plan TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP
);

-- System Integrator & Installed Assets
CREATE TABLE IF NOT EXISTS installed_assets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    source_path TEXT NOT NULL,
    install_path TEXT,
    version TEXT DEFAULT '1.0.0',
    status TEXT NOT NULL DEFAULT 'DISCOVERED',
    security_audit TEXT,
    installation_plan TEXT,
    dependencies TEXT,
    target_agents TEXT,
    capabilities_added TEXT,
    test_results TEXT,
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
    category TEXT NOT NULL,
    project_id TEXT DEFAULT 'global',
    owner_id TEXT DEFAULT 'owner',
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    auth_method TEXT NOT NULL DEFAULT 'PASSWORD',
    mfa_status TEXT NOT NULL DEFAULT 'DISABLED',
    mfa_metadata TEXT,
    notes TEXT,
    recovery_instructions TEXT,
    health_status TEXT NOT NULL DEFAULT 'HEALTHY',
    last_successful_login TIMESTAMP,
    last_failed_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS credential_secrets (
    account_id TEXT PRIMARY KEY,
    encrypted_password TEXT NOT NULL,
    encrypted_api_key TEXT,
    encrypted_session_data TEXT,
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
    permission_level TEXT NOT NULL,
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
    status TEXT NOT NULL DEFAULT 'ACTIVE',
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
    status TEXT NOT NULL DEFAULT 'PENDING',
    approval_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS credential_update_requests (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    update_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    new_encrypted_secret TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES credential_accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS credential_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT,
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    task_id TEXT,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Post-Implementation Verification & Evidence Audit System
CREATE TABLE IF NOT EXISTS verification_audits (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    target_component TEXT NOT NULL,
    target_version TEXT,
    profile TEXT NOT NULL,
    status TEXT NOT NULL,
    initiated_by TEXT NOT NULL,
    requirements_evaluated TEXT NOT NULL,
    inspections TEXT NOT NULL,
    tests_executed TEXT NOT NULL,
    security_findings TEXT NOT NULL,
    reliability_findings TEXT NOT NULL,
    evidence_summary TEXT NOT NULL,
    evidence_artifact_path TEXT,
    remediation_plan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- LLM Provider & Model Management
CREATE TABLE IF NOT EXISTS llm_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    base_url TEXT NOT NULL,
    api_key_ref TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    health_status TEXT NOT NULL DEFAULT 'unknown',
    last_health_check TIMESTAMP,
    config_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS llm_models (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    classification TEXT NOT NULL,
    context_window INTEGER DEFAULT 8192,
    supports_tools INTEGER NOT NULL DEFAULT 1,
    supports_structured_output INTEGER NOT NULL DEFAULT 1,
    supports_vision INTEGER NOT NULL DEFAULT 0,
    capabilities TEXT NOT NULL DEFAULT '[]',
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
    task_category TEXT NOT NULL DEFAULT '*',
    agent_id_match TEXT NOT NULL DEFAULT '*',
    privacy_level TEXT NOT NULL DEFAULT 'standard',
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
CREATE INDEX IF NOT EXISTS idx_loop_traces_task_id ON agent_loop_traces(task_id);
CREATE INDEX IF NOT EXISTS idx_loop_traces_agent_id ON agent_loop_traces(agent_id);
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


@asynccontextmanager
async def get_db_connection():
    global _SCHEMA_ENSURED
    DB_DIR.mkdir(parents=True, exist_ok=True)
    if HAS_AIOSQLITE:
        db = await aiosqlite.connect(DB_PATH)
        db.row_factory = aiosqlite.Row
    else:
        db = _FallbackAsyncConnection(DB_PATH)
    await db.execute("PRAGMA journal_mode = WAL;")
    await db.execute("PRAGMA foreign_keys = ON;")
    if not _SCHEMA_ENSURED:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
        _SCHEMA_ENSURED = True
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    global _SCHEMA_ENSURED
    DB_DIR.mkdir(parents=True, exist_ok=True)
    async with get_db_connection() as db:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    _SCHEMA_ENSURED = True
    logger.info(f"Database initialized successfully at {DB_PATH}")
