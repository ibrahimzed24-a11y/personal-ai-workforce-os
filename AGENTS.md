# Universal AI Developer Instructions: Personal AI Workforce OS

**File Standard:** Runtime-Independent Markdown Instruction Contract  
**Target:** Any capable AI development agent working inside this workspace  
**Repository Root:** `/Users/ibrahimzid/AI-Workforce/`  
**Last Updated:** 2026-11-15  

---

## 1. Project Mission & Core Operating Context

You are operating inside the **Personal AI Workforce OS**, a private, owner-controlled, local multi-agent operating system running on a MacBook Pro workstation. 

### Core Operating Principles:
1. **Evidence-Driven Engineering:** Never report success without reproducible evidence (terminal exit codes, passing assertions, non-empty artifacts).
2. **Preserve Working Work:** Never overwrite, break, or delete working components. Never rebuild from scratch.
3. **No Unprompted Complexity:** Implement the simplest robust solution. Avoid introducing unnecessary external daemons or heavy third-party frameworks.
4. **Local Hardware Respect:** The host workstation is an Intel Core i7 Mac with 16 GB RAM. Avoid running oversized local models or unbounded memory processes.
5. **Universal Portability:** Adhere strictly to universal standards (plain standard Markdown, Python 3.12, FastAPI, SQLite WAL). Never introduce vendor-specific locks (e.g. Claude-specific `.claude/` directories or model-locked conventions).

---

## 2. Repository Structure

```text
/Users/ibrahimzid/AI-Workforce/
├── README.md                           <- Non-technical owner overview & operations guide
├── AGENTS.md                           <- This developer instruction file
├── .gitignore                          <- Git ignore rules for secrets, DB, and caches
├── .env.example                        <- Sanitized configuration template
├── start_os.sh / stop_os.sh            <- Local background process daemons
├── pyproject.toml / uv.lock            <- Python dependencies managed by uv
│
├── core/                               <- Operating System Engine & Runtime
│   ├── app.py                          <- FastAPI HTTP server & REST endpoints
│   ├── orchestrator.py                 <- Multi-step task planner and execution engine
│   ├── agent_context.py                <- 3-file context loader & durable memory guardrails
│   ├── model_manager.py                <- Central provider-independent Model Manager
│   ├── database.py                     <- SQLite WAL connection pool and schema
│   ├── models.py                       <- Pydantic data schemas
│   ├── integrator.py                   <- Capability lifecycle engine (scan, audit, rollback)
│   ├── requirements.py                 <- Change proposal and requirements engine
│   ├── adapters/                       <- Local (Ollama), Cloud (OpenAI/Gemini/Claude), Mock
│   ├── security/                       <- Fernet AES-128 cryptographic vault & credentials
│   ├── ui/                             <- Control center web application (HTML/CSS/JS)
│   ├── verification/                   <- Post-Implementation Verification & Audit engine
│   ├── scripts/                        <- Automation and maintenance scripts
│   └── tests/                          <- Automated test suites
│
├── config/                             <- System Configuration
│   ├── agents/                         <- 32 agent directories (AGENT.md, MEMORY.md, SKILL.md)
│   └── skills/                         <- Dynamically installed external skills
│
├── data/                               <- Persistent State (ai_workforce.db)
├── documentation/                      <- Architectural documentation, policies, and research
├── incoming/                           <- Capability ingestion inbox for System Integrator
├── logs/                               <- Daemon logs (os.log) and final task deliverables
├── projects/                           <- User workspaces & project directories
└── backups/                            <- Automated checkpoints and project ZIP archives
```

---

## 3. Key Architectural Decisions

1. **SQLite in WAL Mode:** Persistent state lives in `data/ai_workforce.db` using Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) and enforced foreign keys (`PRAGMA foreign_keys = ON;`). All state modifications must be executed through parameterized SQL queries via `core/database.py`.
2. **Central Model Manager:** Agents never directly call LLM APIs or hardcode provider URLs. All model requests route through `ModelManager.generate()` in `core/model_manager.py`. Local-only tasks are strictly gated from cloud APIs.
3. **Decoupled Cryptographic Vault:** Master vault key is stored in `~/.ai_workforce_vault.key` outside the project tree with `0600` POSIX permissions. Secrets in the database are encrypted using Fernet (AES-128-CBC + HMAC-SHA256). Plaintext secrets are never committed to Git or logged.
4. **Universal Three-File Agent Standard:** Every agent has its own directory in `config/agents/<id>/` containing `AGENT.md`, `MEMORY.md`, and `skills/<job>/SKILL.md`.

---

## 4. How Agent Definitions & Context Are Loaded

When an agent is invoked:
1. The execution runtime calls `AgentContextLoader.build_runtime_context(agent_id)` from `core/agent_context.py`.
2. `AGENT.md` is loaded for identity, authority, exclusions, and approval gates.
3. `MEMORY.md` is loaded for durable owner feedback.
4. The active skill `skills/<job>/SKILL.md` is parsed and validated (Agent Skills 2.0 YAML frontmatter).
5. The 9-step mandatory startup sequence is generated and prepended to the system prompt.
6. The composite prompt is passed to `ModelManager` for inference.

---

## 5. How Skills Are Registered & Invoked

- Skills live inside `config/agents/<agent-id>/skills/<short-job-name>/SKILL.md`.
- Each skill declares a unique slash command in its YAML frontmatter (e.g. `slash_command: /seo-audit`).
- Slash commands are registered 1:1 without collisions.
- To invoke an agent skill via API: `POST /api/skills/invoke-slash` with `{"command": "/<slash-command>", "user_prompt": "..."}`.
- Shared capabilities (`cap:*`) are cataloged in `documentation/AGENT_CAPABILITY_CATALOG.md` and accessed via runtime adapters.

---

## 6. How Model Providers Are Configured

Model management is handled exclusively by `core/model_manager.py`:
- **Default State:** Offline simulation (`mock-deterministic-v1`).
- **Local Ollama:** Automatically discovered at `http://localhost:11434`.
- **Cloud Providers:** API keys for OpenAI, Gemini, or Anthropic must be saved via `POST /api/models/providers/{provider_id}/credential`. The key is encrypted immediately in the Vault.
- **Privacy Enforcement:** If a request has `privacy_level == "local_only"` or `"sensitive"`, the Model Manager strictly refuses cloud model dispatch. Never attempt to bypass this boundary.

---

## 7. Testing & Verification Requirements

Before submitting any code changes or claiming success, you MUST run all relevant test suites:

```bash
# 1. Architectural standard for all 32 agents
PYTHONPATH=. ~/.local/bin/uv run python core/tests/test_three_file_architecture.py

# 2. End-to-end task orchestration, database, and vault security
PYTHONPATH=. ~/.local/bin/uv run python core/tests/test_system.py

# 3. Independent audit, rollback, and backup verification
PYTHONPATH=. ~/.local/bin/uv run python core/tests/run_audit_verification.py

# 4. Web UI rendering in headless Chromium
PYTHONPATH=. ~/.local/bin/uv run python core/tests/test_browser_ui.py
```

### Passing Standard:
- 100% test pass rate required across all test suites.
- Never weaken, comment out, or bypass assertions to make a test pass.
- All tests must run cleanly with exit code 0.

---

## 8. Security & Privacy Rules

1. **Never Expose Plaintext Credentials:** Do not print API keys, passwords, or session tokens in terminal logs, deliverables, or Git commits.
2. **Keep Secrets Outside Portable Archives:** Never include `~/.ai_workforce_vault.key` or `.env` files in project backups or zip archives.
3. **Foreign Key Integrity:** When inserting events into `execution_events`, verify that `task_id` exists in `tasks` or handle foreign key constraints gracefully.
4. **Never Bypass Approvals:** Actions involving file deletion, financial commitments, external deployment, or unrevealed credential access require explicit owner approval.

---

## 9. Prohibited Actions

- **DO NOT** attempt cloud VPS provisioning (the owner does not own a VPS).
- **DO NOT** deploy private OS code or databases to public cloud hosting (e.g. Vercel, Supabase).
- **DO NOT** install heavy external proxy daemons (e.g. full LiteLLM proxy server).
- **DO NOT** download multi-gigabyte LLM model weights automatically without owner consent.
- **DO NOT** delete or overwrite `data/ai_workforce.db` or backup directories.
- **DO NOT** create public network endpoints.

---

## 10. Required Handover Reporting

When completing any implementation task:
1. Record all modified files with clickable markdown links (`file:///...`).
2. Provide exact commands and verbatim terminal test outputs.
3. Use honest result classifications: `VERIFIED`, `IMPLEMENTED_NOT_VERIFIED`, `PARTIALLY_IMPLEMENTED`, `MOCKED_OR_SIMULATED`, `NOT_IMPLEMENTED`, `BROKEN`, `BLOCKED`.
4. State active Git commit hashes and daemon process status.
