# AI Workforce OS: Model Routing & Privacy Policy

**Policy Version:** 2.0.0  
**Enforced By:** `core/model_manager.py` (Central Model Manager)  
**Status:** Active & System-Enforced  
**Last Updated:** 2026-11-15  

---

## 1. Principles of Model Routing

The AI Workforce OS operates under a **governed, multi-model routing model**. No agent is hardcoded to a single LLM provider, vendor, or token price tier. Instead, every task execution request is evaluated against objective routing criteria before model dispatch:

1. **Privacy & Boundary Integrity:** Sensitive local data must never leave the workstation.
2. **Task-Capability Matching:** Models are matched to tasks based on empirical capabilities (e.g. coding benchmarks, context length, tool calling).
3. **Resilience with Zero Silent Leakage:** Fallbacks are supported to prevent system halts, but cloud fallback from local-only tasks is strictly prohibited without owner authorization.
4. **Economic & Resource Efficiency:** Routine and repetitive tasks prefer lightweight local models; high-complexity tasks utilize frontier models.

---

## 2. Privacy Classification Levels

Every task created in the OS is assigned a **Privacy Level**:

| Privacy Level | Definition | Permitted Model Classification | Prohibited Actions |
| :--- | :--- | :--- | :--- |
| `local_only` | Data contains local file paths, personal credentials, private system configs, or offline notes. | **Local Only** (`local_ollama`, `mock`) | **STRICTLY FORBIDDEN:** Outbound network transmission to any cloud API endpoint. |
| `sensitive` | Internal project architectures, proprietary business plans, or unreleased draft content. | **Local Preferred** (`local_ollama`); Cloud requires explicit opt-in policy. | Silent automatic fallback to cloud. |
| `standard` | General technical research, code refactoring, SEO analysis, or public data processing. | **Local or Cloud** (`local_ollama`, `cloud_openai`, `cloud_gemini`, `cloud_anthropic`, `mock`) | None. Optimal routing based on capability and latency. |
| `cloud_allowed` | Large-scale external queries, heavy web scraping analysis, or multi-megabyte context processing. | **Frontier Cloud** (`cloud_gemini`, `cloud_anthropic`, `cloud_openai`) | None. |

---

## 3. Departmental & Functional Routing Rules

| Rule ID | Department / Task Category | Agent Match | Preferred Model | Fallback Model | Cloud Fallback Allowed | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `rule_sensitive_local` | Security, Credentials, Vault | `*` | `ollama-llama32` | `mock-default` | **NO (0)** | 100 (Highest) |
| `rule_coding_complex` | Software Engineering & QA | `software-engineer`, `backend-specialist` | `claude-35-sonnet` | `ollama-qwen25` | YES (1) | 80 |
| `rule_research_market` | Market, SEO & GEO Research | `market-seo-geo-researcher`, `seo-auditor` | `gemini-15-flash` | `mock-default` | YES (1) | 70 |
| `rule_browser_extract` | Browser Automation & Scraping | `browser-use-agent`, `data-extractor` | `openai-gpt4o-mini` | `ollama-llama32` | YES (1) | 60 |
| `rule_master_report` | Master Executive Reporting | `master-reporting-agent`, `executive-summarizer`| `gemini-15-pro` | `mock-default` | YES (1) | 50 |
| `rule_default_system` | General Workflow & Execution | `*` | System Default Model | `mock-default` | NO (0) | 10 (Baseline) |

---

## 4. Independent Verifier Isolation Rule

To guarantee rigorous quality control:
- When a task execution step produces code or an architectural deliverable using Model $A$, the **independent verification step** must, whenever feasible, be conducted by a separate verification adapter or an alternate model from a different family (e.g. Generation by Claude, Verification by Gemini or local deterministic verifier).
- An agent or model is never permitted to unilaterally approve its own output without verifiable execution artifacts (exit code 0, non-empty deliverable file, valid test assertions).

---

## 5. Non-Negotiable Boundary Enforcement Code

The following enforcement logic is embedded in `core/model_manager.py`:

```python
# Boundary Enforcement Check
if request.privacy_level in ("local_only", "sensitive") and model_data["classification"] == "cloud":
    raise PermissionError(
        f"Privacy Violation: Task requires '{request.privacy_level}' execution, "
        f"but target model '{model_data['id']}' is a CLOUD model. "
        "Outbound request blocked by Central Model Manager."
    )
```

If an active local model becomes unreachable during a `local_only` task, the OS **will never** silently send the prompt to OpenAI or Google. It will either route to an offline deterministic mock or pause execution and report an error to the owner.
