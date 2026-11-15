# AI Workforce OS: Shared Agent Capability Catalog

**Standard:** Portable Agent Capabilities Specification  
**Version:** 2.0.0  
**Maintained By:** System Integrator & Update Agent  
**Last Updated:** 2026-11-15  

---

## 1. Overview & Architectural Principles

The AI Workforce OS adopts a **modular shared capability model**. Instead of redundantly implementing file reading, HTTP requests, research extraction, or database queries inside all 32 agent definitions, core operational capabilities are cataloged as reusable platform primitives with strict, permission-gated access rules.

Every agent maintains:
1. **Its Specialized Skill** (`skills/<job>/SKILL.md`): Domain-specific procedure, decision logic, and domain standards.
2. **Authorized Shared Capabilities**: Cross-cutting tools and procedures invoked to perform operational sub-tasks.

---

## 2. Shared Capability Registry

| Capability ID | Capability Name | Category | Primary Function | Authorized Agents | Risk Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `cap:research_gather` | Deep Research & Source Ingestion | Knowledge & Intelligence | Queries search indexes, scrapes reference URLs, and ingests source data. | `market-seo-geo-researcher`, `competitor-intelligence`, `geo-targeting-analyst`, `content-strategist`, `coordinator` | LOW |
| `cap:source_verify` | Source Verification & Fact Checking | Verification | Validates domain credibility, cross-references citations, and checks timestamp validity. | `market-seo-geo-researcher`, `seo-auditor`, `competitor-intelligence`, `brand-compliance` | LOW |
| `cap:browser_navigate` | Headless Web Navigation | Browser Automation | Controls headless Playwright/Chromium instances, navigates URLs, handles pagination. | `browser-use-agent`, `web-navigator`, `visual-inspector`, `data-extractor` | MEDIUM |
| `cap:data_extract` | Structured Web Data Extraction | Browser & Data | Parses DOM trees, extracts CSS/XPath targets, and normalizes tabular/JSON data. | `browser-use-agent`, `data-extractor`, `seo-auditor`, `competitor-intelligence` | LOW |
| `cap:data_cleanse` | Data Cleaning & Deduplication | Data Processing | Removes duplicates, normalizes casing/UTF-8, filters stop-words, and formats schema. | `data-extractor`, `seo-auditor`, `audit-trail-compiler`, `backend-specialist` | LOW |
| `cap:content_author` | Structured Writing & Drafting | Growth & Content | Generates long-form technical briefs, editorial content, marketing copy, and documentation. | `marketing-agent`, `content-strategist`, `campaign-planner`, `executive-summarizer` | LOW |
| `cap:plan_decompose` | Task Decomposition & DAG Planning | Orchestration | Analyzes objectives and breaks them into ordered execution steps with dependencies. | `coordinator`, `task-decomposer`, `resource-allocator`, `campaign-planner` | LOW |
| `cap:file_io` | Sandboxed File Read / Write | System & Storage | Reads, writes, appends, and diffs files within the local OS workspace. | `software-engineer`, `frontend-specialist`, `backend-specialist`, `system-integrator-update-agent`, `package-runtime-installer` | MEDIUM |
| `cap:code_execute` | Sandboxed Shell & Script Execution | Engineering & Runtime | Executes local tests, linters, builds, and runtime scripts with exit code verification. | `software-engineer`, `qa-test-engineer`, `backend-specialist`, `service-manager`, `release-verifier`, `package-runtime-installer` | HIGH (Approval Gated) |
| `cap:service_manage` | Local Service Lifecycle Control | Infrastructure | Starts, stops, restarts, and monitors local daemons, servers, and background tasks. | `deployment-agent`, `service-manager`, `environment-provisioner` | HIGH (Approval Gated) |
| `cap:reporting_compile` | Executive Report Compilation | Audit & Reporting | Aggregates multi-agent logs, metrics, findings, and generates stakeholder markdown. | `master-reporting-agent`, `executive-summarizer`, `audit-trail-compiler`, `retrospective-analyst` | LOW |
| `cap:quality_verify` | Independent Quality & Artifact Audit | Quality Assurance | Checks file presence, non-empty outputs, schema compliance, and formatting criteria. | `qa-test-engineer`, `release-verifier`, `brand-compliance`, `progress-monitor` | LOW |
| `cap:security_audit` | Secret Scanning & Access Policy Check | Security & Governance | Scans inputs/outputs for credentials, verifies permissions, checks vault access policies. | `asset-classifier-auditor`, `brand-compliance`, `audit-trail-compiler` | HIGH |

---

## 3. Capability Interface Contracts

### Example Contract: `cap:code_execute`
```yaml
capability_id: "cap:code_execute"
description: "Executes a sandboxed shell command or test suite within the local workspace."
inputs:
  command:
    type: string
    description: "The shell command to execute."
    required: true
  working_dir:
    type: string
    description: "Absolute path to workspace directory."
    default: "/Users/ibrahimzid/AI-Workforce"
  timeout_seconds:
    type: integer
    default: 60
outputs:
  exit_code: integer
  stdout: string
  stderr: string
  duration_ms: float
permissions_required:
  - "shell_execution"
  - "workspace_write"
safety_constraints:
  - "Command must not contain destructive root flags (rm -rf /, mkfs)."
  - "Network operations to unapproved endpoints blocked."
```

### Example Contract: `cap:browser_navigate`
```yaml
capability_id: "cap:browser_navigate"
description: "Navigates to a target URL, waits for network idle, and returns rendered snapshot or screenshot."
inputs:
  url:
    type: string
    required: true
  wait_until:
    type: string
    enum: ["load", "domcontentloaded", "networkidle"]
    default: "networkidle"
  capture_screenshot:
    type: boolean
    default: false
outputs:
  status_code: integer
  page_title: string
  final_url: string
  screenshot_path: string (optional)
permissions_required:
  - "browser_automation"
```

---

## 4. Capability Enforcement Protocol

1. **Permission Check:** When an agent attempts to invoke a capability, the runtime checks the agent's blueprint (`config/agents/<id>.yaml` or `AGENT.md`) to verify that the capability is explicitly authorized.
2. **Approval Escalation:** If the capability has a `HIGH` risk level (such as `cap:code_execute` modifying system files, or `cap:service_manage` restarting system processes), the OS pauses execution and generates an `approval_request` in SQLite for owner sign-off.
3. **Execution Traceability:** Every capability call logs an immutable `execution_event` with caller ID, parameters, runtime latency, and exit code.
