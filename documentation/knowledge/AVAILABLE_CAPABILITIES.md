# Operational Knowledge: Available Capabilities Catalog

The following capabilities are actively available across the AI Workforce OS:

### audit_sample_skill (`skill`)
- **Path:** `config/skills/audit_sample_skill/SKILL.md`
- **Authorized Agents:** `coordinator`
- **Capabilities Added:** `skill:audit_sample_skill`

## Standardized Agent Skills & Slash Commands

- **`/asset-audit`** (`asset-classifier-auditor`): Detects incoming file types, parses manifests (SKILL.md, package.json, pyproject.toml), and scores security risks. (Path: `config/agents/asset-classifier-auditor/skills/asset-audit/SKILL.md`)
- **`/audit-trail`** (`audit-trail-compiler`): Extracts chronological execution events, serializes immutable audit logs, and validates compliance with OS policies. (Path: `config/agents/audit-trail-compiler/skills/audit-trail/SKILL.md`)
- **`/backend-development`** (`backend-specialist`): Designs robust RESTful APIs, implements SQLite WAL database schemas, and manages asynchronous server workflows. (Path: `config/agents/backend-specialist/skills/backend-development/SKILL.md`)
- **`/brand-compliance`** (`brand-compliance`): Enforces brand style guidelines, audits promotional claims, and ensures regulatory and privacy compliance. (Path: `config/agents/brand-compliance/skills/brand-compliance/SKILL.md`)
- **`/browser-automation`** (`browser-use-agent`): Operates headless and GUI browsers via Playwright, executes automated web navigation, extracts structured data, and audits UI state. (Path: `config/agents/browser-use-agent/skills/browser-automation/SKILL.md`)
- **`/campaign-planning`** (`campaign-planner`): Architects multi-touch conversion funnels, maps lifecycle email sequences, and designs A/B test frameworks. (Path: `config/agents/campaign-planner/skills/campaign-planning/SKILL.md`)
- **`/knowledge-synchronization`** (`capability-knowledge-synchronizer`): Maps approved capabilities to authorized agents, updates SKILLS_INDEX.md, AVAILABLE_CAPABILITIES.md, and AGENT_TOOL_ACCESS.json. (Path: `config/agents/capability-knowledge-synchronizer/skills/knowledge-synchronization/SKILL.md`)
- **`/competitor-intelligence`** (`competitor-intelligence`): Constructs competitive feature matrices, analyzes pricing models, benchmarks positioning, and identifies market gaps. (Path: `config/agents/competitor-intelligence/skills/competitor-intelligence/SKILL.md`)
- **`/content-strategy`** (`content-strategist`): Plans editorial calendars, crafts thought leadership narratives, writes high-converting copy, and optimizes headlines. (Path: `config/agents/content-strategist/skills/content-strategy/SKILL.md`)
- **`/coordinator-agent`** (`coordinator`): Decomposes high-level objectives into actionable execution plans, assigns tasks to specialized agents, monitors progress, and synthesizes final deliverables. (Path: `config/agents/coordinator/skills/coordinator-agent/SKILL.md`)
- **`/data-extraction`** (`data-extractor`): Parses HTML DOM trees, extracts complex tabular data, normalizes text schemas, and exports structured JSON/CSV files. (Path: `config/agents/data-extractor/skills/data-extraction/SKILL.md`)
- **`/deployment-management`** (`deployment-agent`): Manages system runtime environments, process supervision, daemon lifecycles, and validates release deployments. (Path: `config/agents/deployment-agent/skills/deployment-management/SKILL.md`)
- **`/environment-provisioning`** (`environment-provisioner`): Validates system dependencies, audits PATH configurations, verifies package managers, and scaffolds runtime directories. (Path: `config/agents/environment-provisioner/skills/environment-provisioning/SKILL.md`)
- **`/executive-summary`** (`executive-summarizer`): Distills dense technical logs into clear executive briefs, formats KPIs, and packages high-value deliverable markdown. (Path: `config/agents/executive-summarizer/skills/executive-summary/SKILL.md`)
- **`/frontend-development`** (`frontend-specialist`): Builds responsive Web/PWA interfaces, implements accessible DOM structures, and optimizes frontend rendering performance. (Path: `config/agents/frontend-specialist/skills/frontend-development/SKILL.md`)
- **`/geo-analysis`** (`geo-targeting-analyst`): Analyzes localized search trends, regional demand distribution, language intent, and geo-targeted market signals. (Path: `config/agents/geo-targeting-analyst/skills/geo-analysis/SKILL.md`)
- **`/market-seo-geo-research`** (`market-seo-geo-researcher`): Conducts deep market intelligence, keyword discovery, regional SEO trend analysis, and competitor capability benchmarks. (Path: `config/agents/market-seo-geo-researcher/skills/market-seo-geo-research/SKILL.md`)
- **`/marketing-strategy`** (`marketing-agent`): Creates persuasive marketing copy, designs multi-channel promotional funnels, and ensures strict compliance with brand guidelines. (Path: `config/agents/marketing-agent/skills/marketing-strategy/SKILL.md`)
- **`/master-reporting`** (`master-reporting-agent`): Synthesizes multi-agent task outputs, maintains immutable audit trails, creates executive summaries, and provides process improvement retrospectives. (Path: `config/agents/master-reporting-agent/skills/master-reporting/SKILL.md`)
- **`/package-installation`** (`package-runtime-installer`): Executes isolated uv/npm installations, copies assets into destination directories, executes verification tests, and manages rollbacks. (Path: `config/agents/package-runtime-installer/skills/package-installation/SKILL.md`)
- **`/progress-monitoring`** (`progress-monitor`): Tracks step execution in real time, manages timeouts, detects bottlenecks, and routes approval requests. (Path: `config/agents/progress-monitor/skills/progress-monitoring/SKILL.md`)
- **`/qa-testing`** (`qa-test-engineer`): Designs unit, integration, and end-to-end test suites, prevents software regressions, and enforces testing standards. (Path: `config/agents/qa-test-engineer/skills/qa-testing/SKILL.md`)
- **`/release-verification`** (`release-verifier`): Executes automated smoke tests, probes HTTP health endpoints, validates release criteria, and triggers rollbacks upon failure. (Path: `config/agents/release-verifier/skills/release-verification/SKILL.md`)
- **`/resource-allocation`** (`resource-allocator`): Selects optimal agent blueprints, models, and runtime tool bindings for decomposed plan steps. (Path: `config/agents/resource-allocator/skills/resource-allocation/SKILL.md`)
- **`/retrospective-analysis`** (`retrospective-analyst`): Analyzes execution timelines, identifies process bottlenecks, calculates agent velocity, and formulates optimization recommendations. (Path: `config/agents/retrospective-analyst/skills/retrospective-analysis/SKILL.md`)
- **`/seo-audit`** (`seo-auditor`): Audits search crawlability, keyword density, semantic metadata, search engine crawlability, and on-page optimization. (Path: `config/agents/seo-auditor/skills/seo-audit/SKILL.md`)
- **`/service-management`** (`service-manager`): Manages background daemon lifecycles, monitors PID files, executes graceful shutdowns, and inspects port bindings. (Path: `config/agents/service-manager/skills/service-management/SKILL.md`)
- **`/software-engineering`** (`software-engineer`): Designs robust technical architectures, implements clean code across frontend and backend systems, and executes automated test suites. (Path: `config/agents/software-engineer/skills/software-engineering/SKILL.md`)
- **`/system-integration`** (`system-integrator-update-agent`): Discovers, classifies, audits, installs, tests, registers, and maintains newly supplied external capabilities (skills, tools, packages, blueprints, workflows, integrations). Updates OS operational knowledge and agent tool awareness. (Path: `config/agents/system-integrator-update-agent/skills/system-integration/SKILL.md`)
- **`/task-decomposition`** (`task-decomposer`): Analyzes complex requirements and breaks them into atomic, ordered, and dependency-mapped plan steps. (Path: `config/agents/task-decomposer/skills/task-decomposition/SKILL.md`)
- **`/visual-inspection`** (`visual-inspector`): Captures viewport and full-page screenshots, verifies layout integrity, and detects visual rendering defects. (Path: `config/agents/visual-inspector/skills/visual-inspection/SKILL.md`)
- **`/web-navigation`** (`web-navigator`): Navigates multi-step web workflows, handles dynamic element waits, fills forms, and manages authenticated browser contexts. (Path: `config/agents/web-navigator/skills/web-navigation/SKILL.md`)


