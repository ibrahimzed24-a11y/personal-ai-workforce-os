# Open-Source Foundation Research: Standards, Memory, Execution & LLM Management

**Author:** AI Workforce OS Architecture Team  
**Date:** 2026-11-15  
**Status:** Approved for Implementation  
**Target Environment:** Local macOS Sequoia Workstation (Intel Core i7, 16 GB RAM)

---

## 1. Executive Summary

This research document evaluates proven, maintained, open-source architectures, specifications, and design patterns to guide the foundational upgrade of the AI Workforce OS. Rather than blindly adding heavy third-party dependencies or migrating the existing working codebase to external monolithic frameworks, this research identifies the **exact specifications, design principles, and lightweight implementations** that can be cleanly integrated into our native Python/FastAPI/SQLite runtime.

---

## 2. Agent Skills Standards & Specification

### Evaluated Projects:
- **Agent Skills Specification:** [agentskills.io](https://agentskills.io/) / [agentskills.io/specification](https://agentskills.io/specification)
- **Microsoft Semantic Kernel Skills / Agent Plugins:** [github.com/microsoft/skills](https://github.com/microsoft/skills)
- **Antigravity Skills Standard:** Built-in skill packaging and activation conventions.

### Technical Analysis:
1. **Metadata & Discovery Schema:**
   - Standard Agent Skills require a standardized YAML frontmatter containing:
     - `name`: Lowercase, alphanumeric, kebab-cased identifier.
     - `description`: Explicit statement of what the skill does and *when to activate it* (intent matching).
     - `agent_id`: Owner/primary agent binding.
     - `slash_command`: Direct execution alias (e.g., `/seo-audit`).
     - `version`: Semantic version string (`MAJOR.MINOR.PATCH`).
     - `capabilities`: Explicit list of required platform/tool capabilities.
     - `inputs`: Formally typed parameters with descriptions, requirements, and default values.
     - `outputs`: Schema of the resulting deliverable or return artifact.
2. **Progressive Disclosure:**
   - Skills should not front-load hundreds of kilobytes of reference documentation into the prompt context.
   - Core procedure is kept concise (10 steps) in `SKILL.md`.
   - Detailed references, scripts, templates, and domain-specific checklists reside in modular subdirectories (`references/`, `templates/`, `scripts/`) loaded strictly on-demand.
3. **Execution Safety & Recovery:**
   - Skills must define explicit prerequisite checks, failure modes, error classification, and fallback actions rather than silently failing or hallucinating completion.

### Adoption Decision:
- **Adopt the Agent Skills YAML frontmatter and progressive disclosure folder structure** across all 32 agent skills.
- No heavy external package needed; implement schema validation natively within `core/agent_context.py`.

---

## 3. Agent Identity & Role Engineering

### Evaluated Standards:
- Provider-independent system prompt architectures (Anthropic constitutional patterns, OpenAI system message guidelines, Google system instructions).
- Enterprise RACI (Responsible, Accountable, Consulted, Informed) and organizational role-definition methodologies.

### Technical Analysis:
A robust agent identity requires more than an inspirational persona. It must define sharp operational boundaries:
1. **Mission & Core Competence:** Concise definition of the agent's reason for existing in the workforce.
2. **Explicit Exclusions:** What the agent is strictly prohibited from doing (e.g., a researcher must not write production code; a developer must not execute unapproved deployments).
3. **Authority & Approval Gates:** Clear limits on autonomy. High-risk operations (credential access, system file modification, external network posting) require explicit owner approval.
4. **Input & Deliverable Contracts:** Concrete specifications of required input context and deliverable markdown/JSON schemas.
5. **Delegation & Handoff Protocols:** Clear rules governing when to delegate to specialist subagents vs. escalating to the Coordinator.
6. **Measurable Productivity Indicators:** Objective metrics (execution time, tool success rate, verification pass rate) rather than self-reported success.

### Adoption Decision:
- Restructure all 32 `AGENT.md` files to feature structured sections:
  - Identity & Role Classification
  - Mission & Purpose
  - Scope & Responsibilities
  - Explicit Exclusions & Prohibitions
  - Authority & Human Approval Gates
  - Required Inputs & Deliverable Contracts
  - Tool & Capability Permissions
  - Memory & Context Policy
  - Delegation & Escalation Protocol
  - Objective Productivity Indicators

---

## 4. Multi-Tiered Memory Architecture

### Evaluated Projects:
- **Letta (formerly MemGPT):** [github.com/letta-ai/letta](https://github.com/letta-ai/letta) — Tiered memory (Core memory, Archival memory, Recall memory).
- **LangGraph Persistence:** [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) — Checkpointing, durable state channels, thread-isolated storage.

### Technical Analysis:
Memory failures in autonomous agents arise from conflating temporary scratchpads with durable knowledge, causing context dilution and hallucination. We adopt a strict **Seven-Tier Memory Hierarchy**:

| Tier | Memory Classification | Storage Layer | Lifecycle | Access Control |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Identity & Permanent Instructions | `AGENT.md` | Permanent | Read-only to agent; Owner-editable only. |
| **Tier 2** | Working Memory / Active Task Context | Memory / Task Prompt | Ephemeral (Task) | Scoped strictly to active execution step. |
| **Tier 3** | Durable Feedback Memory | `MEMORY.md` | Persistent | Agent proposes; Guardrails filter; Scoped to agent. |
| **Tier 4** | Project-Specific Knowledge | `projects/<id>/` | Project Lifecycle | Accessible only to agents assigned to project. |
| **Tier 5** | Historical Task & Audit Records | SQLite WAL (`tasks`, `events`) | Immutable | Read-only audit log; System appends. |
| **Tier 6** | Shared Organizational Knowledge | `documentation/knowledge/` | Persistent | Curated by System Integrator & Owner. |
| **Tier 7** | Procedural Memory (Skills) | `skills/*/SKILL.md` | Versioned | Executable procedures; Owner & Integrator managed. |

### Memory Guardrails:
- **Zero-Secret Guarantee:** Scan all memory proposals against entropy and regex patterns (`sk-`, `bearer`, `password`, `key`). Immediately reject candidates containing credentials.
- **Ephemerality Filter:** Reject transient edits, typos, and task-specific corrections. Only preserve durable lessons applicable across future jobs.
- **Fact vs. Assumption Tagging:** Enforce markdown tagging `[FACT: VERIFIED]` vs `[ASSUMPTION: UNVERIFIED]` in memory notes.

---

## 5. Task Execution, Reliability & Productivity

### Evaluated Patterns:
- **LangGraph Checkpointing & State Machines:** Graph execution with state rollback and human-in-the-loop gates.
- **Industrial Quality Assurance & SRE:** Error budgets, rework rates, verification loops.

### Technical Analysis:
The OS must measure actual operational efficiency. Agents should never be evaluated on verbosity or unverified self-assessment.

### Measurable Productivity Indicators:
1. **Task Completion Rate (TCR):** Ratio of tasks successfully completing all steps without unhandled crashes.
2. **Verification Pass Rate (VPR):** Percentage of completed tasks passing independent verification on the first attempt.
3. **Tool-Call Success Rate (TSR):** Ratio of successful tool invocations (`exit_code == 0`) to total tool calls.
4. **Rework Rate (RR):** Frequency of steps rejected by verifiers requiring re-execution.
5. **Execution Latency:** Total wall-clock time from task creation to deliverable synthesis.
6. **Unnecessary Delegation Count:** Instances where a coordinator or core agent delegates trivial tasks that fall within its own remit.

---

## 6. Evaluation & Reliability Foundations

### Evaluated Projects:
- **Inspect (UK AI Safety Institute):** [inspect.aisi.org.uk](https://inspect.aisi.org.uk/) — Framework for large language model evaluations, tool use benchmarks, and agent evaluations.
- **Promptfoo:** [github.com/promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) — CLI and library for evaluating LLM output quality, security, and regression testing.

### Technical Analysis:
Evaluation must be decoupled from agent execution:
- Verification must use independent criteria (file existence on disk, JSON schema validation, non-empty deliverable checks).
- Negative testing must explicitly verify that unauthorized tool executions, prompt injections, and cross-agent memory leaks are blocked with appropriate HTTP status codes (401/403) and log events.

---

## 7. LLM Provider Architecture & Routing

### Evaluated Projects:
- **Ollama:** [docs.ollama.com](https://docs.ollama.com/) — High-efficiency local inference server exposing OpenAI-compatible and native `/api` REST endpoints.
- **LiteLLM:** [github.com/BerriAI/litellm](https://github.com/BerriAI/litellm) / [docs.litellm.ai](https://docs.litellm.ai/) — Lightweight Python SDK and proxy for 100+ LLMs with unified input/output formatting.

### Evaluation of LiteLLM:
- *Pros:* Standardizes API calls across Anthropic, OpenAI, Gemini, Bedrock, and Ollama into OpenAI format.
- *Cons:* Full proxy daemon introduces a heavy always-running background server, additional network hop, and dependency overhead.
- *Decision:* **Adopt LiteLLM's unified parameter naming and adapter design principles** directly into native, lightweight async Python adapters (`core/adapters/`) using `httpx`. Avoid running an external proxy server.

### Provider Integration Architecture:
```
                       +-----------------------------------+
                       |       AI Workforce OS Core        |
                       |  (Orchestrator / Agent Runtime)   |
                       +-----------------+-----------------+
                                         |
                                         v
                       +-----------------------------------+
                       |        Central ModelManager       |
                       | - Registry & Capabilities Catalog |
                       | - Dynamic Task-Based Routing      |
                       | - Privacy & Boundary Enforcement  |
                       | - Fallback & Health-Check Engine  |
                       | - Metrics, Latency & Usage Logs   |
                       +-----------------+-----------------+
                                         |
         +-------------------------------+-------------------------------+
         |                               |                               |
         v                               v                               v
+------------------+           +------------------+            +------------------+
|  Local Adapters  |           |  Cloud Adapters  |            |  Mock / Offline  |
| - Ollama (REST)  |           | - OpenAI API     |            | - Deterministic  |
| - Local Ext.     |           | - Google Gemini  |            |   Local Engine   |
|                  |           | - Anthropic API  |            |   (Safe Fallback)|
+------------------+           +------------------+            +------------------+
```

### Routing & Privacy Rules:
1. **Local-First Boundary:** Tasks flagged with `sensitive` or `local_only` must never be routed to cloud endpoints.
2. **Explicit Fallback:** Cloud fallback from a failed local model is strictly blocked unless an explicit owner fallback policy authorizes it.
3. **Provider-Independent Formatting:** All adapters return a standard dictionary:
   ```python
   {
       "content": str,
       "provider": str,
       "model": str,
       "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
       "latency_ms": float,
       "raw": dict
   }
   ```
