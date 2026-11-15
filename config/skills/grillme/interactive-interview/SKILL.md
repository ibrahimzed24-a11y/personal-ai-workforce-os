---
name: grillme-adaptive-clarification
description: Adaptive Clarification & Alignment Interview Skill. Mandates that agents question the admin with a sequence of domain-tailored, high-leverage alignment questions to resolve critical variables, steer the admin to optimal architecture and workflow logic, and maximize task accuracy before executing destructive or high-stakes actions.
version: "1.0.0"
author: "AntiGravity & Sovereign Workforce OS Core"
slash_command: "/grillme"
department_affinity: [
  "Operations & Orchestration",
  "Research & Market Strategy",
  "Growth & Communications",
  "Engineering & Technology",
  "Automation & Data Acquisition",
  "Infrastructure & Operations",
  "Executive & Audit",
  "System Architecture & Integration"
]
tools_required: ["interactive_chat", "core_data_harness", "vault_inspector", "pipeline_orchestrator"]
verification_gate: "Explicit admin alignment on workflow sequence and operational parameters"
---

# GrillMe: Adaptive Clarification & Alignment Interview Protocol

## 1. Core Mandate
Autonomous agents must **never** make blind assumptions regarding critical operational variables (such as target audience filters, email dispatch volumes, tone of voice, API safety thresholds, database schema migrations, or scheduled delivery timezones).

Before executing high-stakes directives, the assigned Agent (or Lead Coordinator) must actively **interview ("grill") the admin** with a sequence of structured, role-tailored questions designed to:
1. **Uncover Ambiguities:** Surface missing constraints, trade-offs, and critical parameters.
2. **Ground in Context:** Anchor questions directly in the project's active core data files (e.g., CSV lead lists, PDF playbooks) and connected tools (e.g., Hostinger SMTP, Google Search Console).
3. **Steer Toward the Optimal Workflow:** Proactively propose the best architectural logic, stage sequence, and safety verification gates.
4. **Provide Recommended Answers:** Present actionable, high-probability recommendations labeled `(Recommended)` alongside distinct alternatives, allowing one-click or rapid conversational approval.

---

## 2. Departmental Inquiry Vectors

Every specialist agent questions the admin through its specialized domain lens:

### Operations & Orchestration (`coordinator`, `task-decomposer`, `resource-allocator`, `progress-monitor`)
- **Focus:** Pipeline stage handoffs, task decomposition dependencies, execution SLA, and rollback criteria.
- **Optimal Workflow Guidance:** Enforces dependency-ordered stages: Ingest ➔ Scrutinize ➔ Act ➔ Observe ➔ Code/Verify ➔ Executive Package.

### Research & Market Strategy (`market-seo-geo-researcher`, `competitor-intelligence`, `geo-targeting-analyst`, `seo-auditor`)
- **Focus:** Target demographic boundaries, regional nuances (e.g. Canadian provinces EST vs PST), clinic size/specialty, competitor benchmarks.
- **Optimal Workflow Guidance:** Deep data extraction ➔ Intent scoring ➔ Geo-targeted segmentation.

### Growth & Communications (`marketing-agent`, `content-strategist`, `campaign-planner`, `brand-compliance`)
- **Focus:** Value proposition angles (ROI vs patient acquisition vs tech innovation), tone, dynamic merge field mapping, CAN-SPAM / CASL compliance.
- **Optimal Workflow Guidance:** Personalized hook formulation ➔ Preview generation ➔ Verification review.

### Operations & Outreach (`email-operator`, `service-manager`)
- **Focus:** Sender address (`sales@health.valioz.com`), live SMTP ports, test dispatch to admin (`ibrahim.zed24@gmail.com`), sending cadence, and spam-trigger prevention.
- **Optimal Workflow Guidance:** Admin test verification ➔ Staggered release (4-minute throttling) ➔ Delivery audit.

### Engineering & Technology (`software-engineer`, `backend-specialist`, `frontend-specialist`, `qa-test-engineer`)
- **Focus:** Architectural patterns, backwards compatibility, test coverage requirements, local vs cloud execution, failure recovery.
- **Optimal Workflow Guidance:** Contract specification ➔ Test-driven implementation ➔ Automated regression suite ➔ Production release.

### Automation & Data Acquisition (`browser-use-agent`, `web-navigator`, `data-extractor`, `visual-inspector`)
- **Focus:** Target URLs, DOM selectors, authentication gates, headless browser viewport resolution, rate limits.
- **Optimal Workflow Guidance:** Headless Chrome launch ➔ Authenticated navigation ➔ DOM extraction ➔ Visual verification screenshot.

### Executive & Audit (`master-reporting-agent`, `executive-summarizer`, `audit-trail-compiler`, `retrospective-analyst`)
- **Focus:** Deliverable formats (Consolidated PDF, Word Brief DOCX, Markdown Ledger), stakeholder metric summaries, immutable telemetry.
- **Optimal Workflow Guidance:** Multi-stage synthesis ➔ Multi-format export generation ➔ Consolidated Task Deliverables Package.

### System Architecture & Integration (`system-integrator-update-agent`, `capability-knowledge-synchronizer`, `release-verifier`, `asset-classifier-auditor`)
- **Focus:** Schema migration safety, POSIX file permissions, cryptographic encryption ciphers, dependency locking.
- **Optimal Workflow Guidance:** Sandbox verification ➔ Vault encryption check ➔ Atomic commit.

---

## 3. Protocol Execution Loop

```
[Admin Directive Received]
         │
         ▼
[GrillMe Assessment]
 ├─ Analyze Directive & Identify Implicit Assumptions
 ├─ Inspect Core Data Harness (Files, CSV Columns, Record Counts)
 ├─ Inspect Credential Vault & Connected Tools
 └─ Formulate Optimal Architecture & Workflow Proposal
         │
         ▼
[Emit Interactive Alignment Brief to Admin]
 ├─ Propose Best Workflow & Logic Sequence
 ├─ Present 2–4 Domain-Tailored Questions with (Recommended) Defaults
 └─ Offer One-Click "[⚡ Proceed with Recommended Workflow]" Option
         │
         ▼
[Admin Alignment Received (Conversation or Click)]
         │
         ▼
[Deterministic Multi-Agent Execution Dispatched]
```

---

## 4. Usage Commands
- `/grillme`: Triggers an alignment interview for the current project directive.
- `/grill @agent <topic>`: Directs a specific specialist agent to grill the admin regarding a domain-specific design decision or task.
