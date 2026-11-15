# Personal AI Workforce OS — Supabase Architecture Blueprint

**Document Version:** 1.0.0  
**Status:** Approved & Implemented  
**Classification:** Private Architecture Specification  

---

## 1. Architectural Overview & Design Philosophy

The Personal AI Workforce OS utilizes a **hybrid sovereign architecture**. This architecture combines the benefits of cloud-hosted access (anywhere web dashboard, persistent relational database, serverless APIs) with the uncompromising security and capability of a local physical workstation (MacBook Pro):

- **Supabase Cloud (PostgreSQL & Auth):** Serves as the central operational state store, audit repository, and decoupled asynchronous job queue.
- **MacBook Pro (Local Runtime):** Serves as the sovereign execution engine, running autonomous agents, browser automation, filesystem access, local CLI tools, and hosting the AES-256 encrypted credentials vault.
- **Vercel (Serverless Dashboard):** Hosts the owner web interface and lightweight operational APIs without holding private secrets or browser automation sessions.

```
       ┌────────────────────────────────────────────────────────┐
       │                   OWNER / WEB BROWSER                  │
       └───────────────────────────┬────────────────────────────┘
                                   │ (HTTPS / Supabase Auth)
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             VERCEL SERVERLESS DASHBOARD                │
       │    - UI, Agent Inspector, Task Submissions             │
       └───────────────────────────┬────────────────────────────┘
                                   │ (PostgREST / JWT)
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             SUPABASE CLOUD POSTGRESQL                  │
       │  - Task Queue (hybrid_tasks)                           │
       │  - Node Registry (runtime_nodes)                       │
       │  - Operational Metadata (plans, events, blueprints)    │
       │  - Row-Level Security (RLS) Owner Enforcement          │
       └───────────────────────────▲────────────────────────────┘
                                   │
                                   │ OUTBOUND-ONLY SECURE POLLING (HTTPS)
                                   │ (No open ports, behind NAT/Firewall)
                                   │
       ┌───────────────────────────┴────────────────────────────┐
       │              MACBOOK PRO LOCAL RUNTIME                 │
       │                                                        │
       │  ┌─────────────────────────┐  ┌─────────────────────┐  │
       │  │  Local Hybrid Worker    │  │ Credentials Vault   │  │
       │  │  - Lease acquisition   │  │ - AES-256 Fernet    │  │
       │  │  - Idempotency checks   │  │ - Website Logins    │  │
       │  │  - Heartbeat dispatcher │  │ - Local SQLite Only │  │
       │  └────────────┬────────────┘  └──────────┬──────────┘  │
       │               │                          │             │
       │               ▼                          ▼             │
       │  ┌──────────────────────────────────────────────────┐  │
       │  │         32 Autonomous Agents & Runtimes          │  │
       │  │  - Browser Automation (Playwright/Puppeteer)     │  │
       │  │  - Local Shell & Workspace Execution             │  │
       │  │  - Model Routing (Ollama / Local / Cloud APIs)   │  │
       │  └──────────────────────────────────────────────────┘  │
       └────────────────────────────────────────────────────────┘
```

---

## 2. Strict Cloud vs. Local Data Separation

To ensure absolute privacy and security, the system enforces a strict data separation boundary:

| Domain | Cloud Supabase PostgreSQL | Local MacBook Workstation |
| :--- | :--- | :--- |
| **Credentials & Passwords** | ❌ **FORBIDDEN** (Zero account secrets stored) | ✅ **STRICTLY LOCAL** (Encrypted in `ai_workforce.db` with master key `~/.ai_workforce_vault.key`) |
| **Website Logins & Sessions** | ❌ **FORBIDDEN** | ✅ **STRICTLY LOCAL** (Local Playwright browser cookies and profiles) |
| **Agent Blueprints & Metadata** | ✅ Synchronized catalog of 32 agents | ✅ Read from `config/agents/**/AGENT.md` |
| **Operational Tasks & Queue** | ✅ Public task queue with idempotency keys | ✅ Polled and claimed by local worker |
| **Task Execution & Shell** | ❌ Cloud does not execute shell scripts | ✅ Executed locally in sandboxed subprocesses |
| **Audit Logs & Metrics** | ✅ Operational event logs and token metrics | ✅ Local `logs/os.log` and SQLite audit tables |
| **Network Exposure** | Outbound HTTPS endpoint via Supabase API | **Zero open inbound ports** (Operates entirely behind home/mobile NAT) |

---

## 3. Asynchronous Hybrid Task Queue Lifecycle

1. **Submission:**
   - Owner submits a task from Vercel UI or API.
   - A row is inserted into `hybrid_tasks` with a unique `idempotency_key`, `runtime_target = 'local'`, and `status = 'pending'`.
2. **Polling & Atomic Lease:**
   - The local MacBook worker (`core/hybrid/runtime_worker.py`) polls Supabase using the stored procedure `claim_hybrid_task`.
   - PostgreSQL locks the record with `FOR UPDATE SKIP LOCKED`, preventing duplicate leases.
   - The task status transitions to `'claimed'` and `lease_expires_at` is set (default 300 seconds).
3. **Local Execution:**
   - The Mac worker loads the designated agent's `AGENT.md`, `SKILL.md`, and `MEMORY.md`.
   - If website interaction or credential access is required, the agent requests the local Credentials Vault via local IPC.
   - The agent executes tools (browser automation, shell, code editing).
   - If the task takes longer than 300 seconds, the worker extends the lease via periodic heartbeats.
4. **Completion & Result Synchronization:**
   - On completion, the worker invokes `complete_hybrid_task(task_id, node_id, result)`.
   - The task status transitions to `'completed'`.
   - The Vercel web dashboard immediately reflects the updated state and results.
5. **Offline & Recovery Handling:**
   - If the MacBook is asleep, offline, or disconnected:
     - Tasks remain safely in status `'pending'` or transition to `'waiting_for_local_runtime'`.
     - When the MacBook reconnects, the worker automatically resumes polling and processes queued tasks.
     - If the MacBook crashes during execution, the maintenance procedure `reclaim_stale_tasks()` detects the expired lease and resets the task for retry up to `max_attempts`.

---

## 4. Security & Access Model

- **Zero-Trust Anonymous Access:** All default Postgres permissions are revoked from `anon` and `public`.
- **Row-Level Security (RLS):** Every operational table enforces RLS.
- **Service Role Secret Key:** The local Mac worker uses the `SUPABASE_SERVICE_ROLE_KEY` over TLS to claim tasks and update execution status.
- **Client Anon/Authenticated Key:** The Vercel dashboard uses the public `SUPABASE_ANON_KEY` combined with Supabase Auth JWT tokens (`auth.uid()`) to allow only the authenticated owner to inspect tasks and trigger workflows.
