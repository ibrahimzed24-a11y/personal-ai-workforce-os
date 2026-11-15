# Open-Source Asset Adoption Register

**Registry Maintained By:** AI Workforce OS — System Integrator & Update Agent  
**Last Updated:** 2026-11-15  
**Policy:** Principles-First & Minimal-Dependencies Standard

---

## 1. Asset Adoption Inventory

| Asset Name | Official Source / Repository | License | Adoption Level | Responsible Component | Installed Status | Description & Justification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Agent Skills Specification** | `https://agentskills.io/` | Apache 2.0 / Open Spec | Full Specification Format | `core/agent_context.py`, all `SKILL.md` files | Integrated (Schema Enforced) | Standardized metadata frontmatter (`name`, `description`, `capabilities`, `inputs`, `outputs`), progressive disclosure folder structure (`references/`, `templates/`, `scripts/`). |
| **Letta / MemGPT Memory Patterns** | `https://github.com/letta-ai/letta` | Apache 2.0 | Architectural Design Pattern | `core/agent_context.py`, all `MEMORY.md` files | Integrated (Native Pattern) | Tiered memory hierarchy (Core, Working, Archival). Memory guardrails against secrets and transient noise. Adopted without installing the Letta server package. |
| **LangGraph Checkpointing & Persistence** | `https://docs.langchain.com/oss/python/langgraph/` | MIT | Design Pattern | `core/orchestrator.py`, `core/database.py` | Integrated (Native SQLite WAL) | State persistence, step-level checkpointing, retry budget, independent verifier gates. Preserves existing SQLite schema without external graph dependencies. |
| **Ollama REST API Specification** | `https://docs.ollama.com/` | MIT | API Protocol Specification | `core/adapters/ollama_adapter.py` | Integrated (Adapter Built) | Native async HTTP integration with Ollama endpoints (`/api/tags`, `/api/chat`, `/api/generate`) for local inference on macOS. No heavy SDK required. |
| **LiteLLM Unified Model Interface** | `https://github.com/BerriAI/litellm` | MIT | Design Pattern | `core/model_manager.py`, `core/adapters/cloud_adapters.py` | Integrated (Native Adapters) | Unified parameter mapping, model capability tagging, and standard dictionary response format. Implemented natively in async Python using `httpx` without the LiteLLM proxy daemon. |
| **UK AISI Inspect Evaluation Standards** | `https://inspect.aisi.org.uk/` | MIT | Evaluation Methodology | `core/tests/test_agent_functional_verification.py` | Integrated (Test Suite) | Independent verification criteria, verifiable artifact checking, and negative security testing protocols. |

---

## 2. Detailed Asset Adoption Records

### A. Agent Skills Specification
- **Source:** Agent Skills Community (`https://agentskills.io/specification`)
- **Version/Standard:** 2025/2026 Open Specification Draft
- **License:** Apache 2.0
- **Changes Made:** Native Python parser implemented in `core/agent_context.py` using `pyyaml` (already installed in OS virtualenv). Adapted schema to include `agent_id` and `slash_command` bindings.
- **Future Considerations:** Monitor upstream specification changes for standardized tool-use schema declarations.

### B. Letta / MemGPT Tiered Memory Principles
- **Source:** Letta AI (`https://github.com/letta-ai/letta`)
- **Version Reference:** v0.4.x architectural papers and documentation
- **License:** Apache 2.0
- **Changes Made:** Implemented 7-tier separation (Identity, Working, Durable, Project, History, Org, Procedural). Enforced strict secret regex/entropy filtering and fact/assumption tagging natively in `core/agent_context.py`.
- **Future Considerations:** Evaluate vector similarity search integration (e.g. `sqlite-vss`) when memory scales beyond 1,000 entries per agent.

### C. LiteLLM Unified Model Pattern
- **Source:** BerriAI LiteLLM (`https://github.com/BerriAI/litellm`)
- **Version Reference:** Design patterns from LiteLLM v1.30+
- **License:** MIT
- **Changes Made:** Built zero-dependency async client classes (`OpenAIAdapter`, `GeminiAdapter`, `AnthropicAdapter`, `OllamaAdapter`) standardizing requests to `/v1/chat/completions` or provider-native endpoints, returning a normalized `ModelResponse` dict.
- **Future Considerations:** Add streaming response support when real-time UI token rendering is introduced.

### D. Ollama Local Inference Protocol
- **Source:** Ollama (`https://docs.ollama.com/`)
- **License:** MIT
- **Changes Made:** Lightweight async HTTP client querying `http://localhost:11434` for model discovery (`/api/tags`) and generation (`/api/chat`). Detects availability and measures first-token latency.
- **Future Considerations:** Support Ollama custom modelfiles and quantization parameters (e.g., Q4_K_M for 16 GB Mac memory bounds).

---

## 3. Dependency Impact & Security Audit

- **Third-Party Packages Added:** **0** (Zero external Python packages added; utilizes existing virtual environment dependencies `httpx`, `fastapi`, `pydantic`, `pyyaml`, `aiosqlite`, `cryptography`).
- **Binary Daemons Added:** **0** (No background proxy servers installed).
- **Security Posture:** All network calls are strictly outbound, explicit, and gated by the central `ModelManager` and `CredentialsVault`.
