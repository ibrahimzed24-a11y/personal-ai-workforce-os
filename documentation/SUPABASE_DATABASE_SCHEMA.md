# Personal AI Workforce OS — Supabase Database Schema Specification

**Document Version:** 1.0.0  
**Migration Path:** `migrations/20261115000001_initial_schema.sql` through `20261115000003_hybrid_runtime_queue.sql`  

---

## 1. Schema Classification Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SUPABASE POSTGRESQL SCHEMA                            │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ Core Operational Tables       │ - agent_blueprints                          │
│                               │ - specialist_definitions                    │
│                               │ - tasks                                     │
│                               │ - task_plans                                │
│                               │ - execution_events                          │
│                               │ - approvals                                 │
│                               │ - verifications                             │
│                               │ - verification_audits                       │
│                               │ - system_requirements                       │
│                               │ - installed_assets                          │
│                               │ - operational_knowledge                     │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ Model Management Tables       │ - llm_providers                             │
│                               │ - llm_models                                │
│                               │ - llm_routing_rules                         │
│                               │ - llm_usage_metrics                         │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ Hybrid Runtime Tables         │ - runtime_nodes                             │
│                               │ - hybrid_tasks                              │
└───────────────────────────────┴─────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRICTLY LOCAL SQLITE SCHEMA (MACBOOK ONLY)              │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ Credentials & Secrets Vault   │ - credential_accounts                       │
│ (Zero Cloud Sync)             │ - credential_secrets                        │
│                               │ - credential_versions                       │
│                               │ - credential_access_policies                │
│                               │ - credential_access_sessions                │
│                               │ - credential_registration_requests          │
│                               │ - credential_update_requests                │
│                               │ - credential_audit_logs                     │
└───────────────────────────────┴─────────────────────────────────────────────┘
```

---

## 2. Table Specifications

### 2.1. `runtime_nodes`
Tracks execution nodes (such as the owner's MacBook Pro) capable of running agent workloads.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `node_id` | `TEXT` | `PRIMARY KEY` | Unique node identifier (e.g., `macbook-pro-primary`) |
| `node_name` | `TEXT` | `NOT NULL` | Human-readable node name |
| `node_type` | `TEXT` | `NOT NULL DEFAULT 'macbook_workstation'` | Hardware / environment profile |
| `capabilities` | `JSONB` | `DEFAULT '["browser_automation", "local_shell", "credentials_vault", "python_runtime"]'` | Registered capabilities |
| `status` | `TEXT` | `NOT NULL DEFAULT 'offline'` | Status: `online`, `busy`, `offline`, `paused` |
| `last_heartbeat` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Timestamp of last worker ping |
| `current_task_id` | `UUID` | Nullable | Currently executing task ID |
| `metadata` | `JSONB` | `DEFAULT '{}'` | OS, memory, hardware statistics |
| `registered_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Initial registration timestamp |

### 2.2. `hybrid_tasks`
The central asynchronous task queue between cloud frontends and execution runtimes.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Unique task identifier |
| `idempotency_key` | `TEXT` | `UNIQUE NOT NULL` | Client-provided key preventing duplicate submissions |
| `title` | `TEXT` | `NOT NULL` | Brief summary of the task |
| `description` | `TEXT` | Nullable | Detailed prompt or execution instructions |
| `assigned_agent_id`| `TEXT` | `NOT NULL REFERENCES agent_blueprints(id)` | Targeted agent ID |
| `runtime_target` | `TEXT` | `NOT NULL DEFAULT 'any'` | `'local'`, `'cloud'`, or `'any'` |
| `required_capabilities` | `JSONB` | `DEFAULT '[]'` | Specific tools needed (e.g. `["browser_automation"]`) |
| `status` | `TEXT` | `NOT NULL DEFAULT 'pending'` | `'pending'`, `'waiting_for_local_runtime'`, `'claimed'`, `'running'`, `'completed'`, `'failed'`, `'cancelled'` |
| `priority` | `INTEGER` | `DEFAULT 50` | Priority rank (1 highest, 100 lowest) |
| `input_payload` | `JSONB` | `DEFAULT '{}'` | Task parameters and input context |
| `output_result` | `JSONB` | Nullable | Completed task artifacts, output, or summary |
| `error_message` | `TEXT` | Nullable | Execution error trace if failed |
| `claimed_by` | `TEXT` | `REFERENCES runtime_nodes(node_id)` | Node currently holding the lease |
| `lease_expires_at`| `TIMESTAMPTZ` | Nullable | Lease expiration timestamp |
| `attempts` | `INTEGER` | `DEFAULT 0` | Execution attempt counter |
| `max_attempts` | `INTEGER` | `DEFAULT 3` | Retry ceiling before permanent failure |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Submission timestamp |
| `started_at` | `TIMESTAMPTZ` | Nullable | Execution start timestamp |
| `completed_at` | `TIMESTAMPTZ` | Nullable | Completion timestamp |
| `updated_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Last update timestamp |

### 2.3. `agent_blueprints` & `specialist_definitions`
Catalogs the 32 AI Workforce OS agents (8 Core Agents, 24 Specialists).

- `agent_blueprints`:
  - `id` (`TEXT PRIMARY KEY`): Stable agent ID (e.g. `core-orchestrator`, `core-credentials-access-manager`)
  - `name`, `department`, `role`, `description`, `system_prompt`
  - `capabilities`, `permissions` (`JSONB`)
  - `default_model` (`TEXT DEFAULT 'gemini-2.5-flash'`)
  - `version` (`TEXT DEFAULT '2.0.0'`)
  - `is_active` (`BOOLEAN DEFAULT TRUE`)
- `specialist_definitions`:
  - `id` (`TEXT PRIMARY KEY`): Specialist ID (e.g. `data-engineer`, `system-integrator-specialist`)
  - `blueprint_id` (`TEXT NOT NULL REFERENCES agent_blueprints(id)`)
  - `name`, `specialization`
  - `skills` (`JSONB`)

### 2.4. LLM Management (`llm_providers`, `llm_models`, `llm_routing_rules`, `llm_usage_metrics`)
Configures multi-model AI routing:
- `llm_providers`: ID, provider type (`ollama`, `gemini`, `anthropic`, `openai`, `mock`), base URL, health status.
- `llm_models`: Model name, display name, classification (`frontier`, `standard`, `specialized`, `local`), context window, tool support.
- `llm_routing_rules`: Privacy levels, agent matching, preferred/fallback models.
- `llm_usage_metrics`: Token consumption and latency tracking per task.

---

## 3. Stored Procedures & Atomic Functions

### 3.1. `claim_hybrid_task(p_node_id, p_lease_seconds)`
- Atomically inspects `hybrid_tasks` with `FOR UPDATE SKIP LOCKED`.
- Targets pending tasks or tasks with expired leases matching the runtime target.
- Sets `status = 'claimed'`, `claimed_by = p_node_id`, and `lease_expires_at = NOW() + INTERVAL 'p_lease_seconds SECONDS'`.
- Updates `runtime_nodes` status to `'busy'`.

### 3.2. `complete_hybrid_task(p_task_id, p_node_id, p_result)`
- Marks task as `'completed'`, stores `output_result`, records `completed_at`.
- Sets `runtime_nodes.status = 'online'`.

### 3.3. `fail_hybrid_task(p_task_id, p_node_id, p_error, p_retry)`
- Increments attempts. If `attempts < max_attempts`, re-queues as `'waiting_for_local_runtime'`.
- If max attempts reached, marks `'failed'`.

### 3.4. `heartbeat_runtime_node(p_node_id, p_status, p_metadata)`
- Updates node heartbeat timestamp and status.

### 3.5. `reclaim_stale_tasks()`
- Maintenance cron/trigger that resets orphaned in-flight tasks where `lease_expires_at < NOW()`.
