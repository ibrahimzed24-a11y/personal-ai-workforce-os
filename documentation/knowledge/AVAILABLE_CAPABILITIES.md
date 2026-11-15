# Operational Knowledge: Available Capabilities Catalog

The following capabilities are actively available across the AI Workforce OS:

### audit_sample_skill (`skill`)
- **Path:** `config/skills/audit_sample_skill/SKILL.md`
- **Authorized Agents:** `master-reporting-agent`, `deployment-agent`, `system-integrator-update-agent`, `coordinator`, `software-engineer`
- **Capabilities Added:** `skill:audit_sample_skill`

## Standardized Agent Skills & Slash Commands

- **`/asset-audit`** (`asset-classifier-auditor`): Detects incoming file types, parses manifests (SKILL.md, package.json, pyproject.toml), and scores security risks. (Path: `config/agents/asset-classifier-auditor/skills/asset-audit/SKILL.md`)
- **`/audit-trail`** (`audit-trail-compiler`): Compiles chronological, step-by-step audit timelines from immutable SQLite execution logs. (Path: `config/agents/audit-trail-compiler/skills/audit-trail/SKILL.md`)
- **`/backend-development`** (`backend-specialist`): Implements FastAPI REST endpoints, executes SQLite WAL database migrations, and manages backend data pipelines. (Path: `config/agents/backend-specialist/skills/backend-development/SKILL.md`)
- **`/brand-compliance`** (`brand-compliance`): Audits all marketing assets against brand guidelines, substantiates claims, and ensures advertising compliance. (Path: `config/agents/brand-compliance/skills/brand-compliance/SKILL.md`)
- **`/browser-automation`** (`browser-use-agent`): Operates Playwright and Chromium automation to navigate complex web apps, extract dynamic DOM data, and inspect visual UI states. (Path: `config/agents/browser-use-agent/skills/browser-automation/SKILL.md`)
- **`/campaign-planning`** (`campaign-planner`): Architects multi-touch conversion funnels, maps lifecycle email sequences, and designs A/B test frameworks. (Path: `config/agents/campaign-planner/skills/campaign-planning/SKILL.md`)
- **`/knowledge-synchronization`** (`capability-knowledge-synchronizer`): Maps approved capabilities to authorized agents, updates SKILLS_INDEX.md, AVAILABLE_CAPABILITIES.md, and AGENT_TOOL_ACCESS.json. (Path: `config/agents/capability-knowledge-synchronizer/skills/knowledge-synchronization/SKILL.md`)
- **`/competitor-intelligence`** (`competitor-intelligence`): Conducts competitive benchmarking, analyzes rival content strategies, backlink profiles, and value propositions. (Path: `config/agents/competitor-intelligence/skills/competitor-intelligence/SKILL.md`)
- **`/content-strategy`** (`content-strategist`): Authors high-converting landing page copy, technical blog articles, product narratives, and thought-leadership content. (Path: `config/agents/content-strategist/skills/content-strategy/SKILL.md`)
- **`/coordinator-agent`** (`coordinator`): Decomposes high-level user objectives into directed acyclic graph (DAG) execution plans, assigns tasks to specialized agents, monitors progress, and synthesizes final deliverables. (Path: `config/agents/coordinator/skills/coordinator-agent/SKILL.md`)
- **`/data-extraction`** (`data-extractor`): Parses HTML DOM trees, extracts target text and tabular data, and normalizes into structured JSON. (Path: `config/agents/data-extractor/skills/data-extraction/SKILL.md`)
- **`/deployment-management`** (`deployment-agent`): Manages local services, coordinates application releases, enforces pre-flight verification checks, and executes rollbacks on failure. (Path: `config/agents/deployment-agent/skills/deployment-management/SKILL.md`)
- **`/environment-provisioning`** (`environment-provisioner`): Manages Python virtual environments, audits package dependencies via `uv`, and ensures runtime isolation. (Path: `config/agents/environment-provisioner/skills/environment-provisioning/SKILL.md`)
- **`/executive-summary`** (`executive-summarizer`): Distills dense multi-agent technical data into clear, high-level executive summaries and open decision points. (Path: `config/agents/executive-summarizer/skills/executive-summary/SKILL.md`)
- **`/frontend-development`** (`frontend-specialist`): Builds responsive, accessible, high-performance web user interfaces, dashboards, and client-side interactions. (Path: `config/agents/frontend-specialist/skills/frontend-development/SKILL.md`)
- **`/geo-analysis`** (`geo-targeting-analyst`): Analyzes localized search visibility, hreflang tags, local pack rankings, and regional consumer search intent. (Path: `config/agents/geo-targeting-analyst/skills/geo-analysis/SKILL.md`)
- **`/market-seo-geo-research`** (`market-seo-geo-researcher`): Conducts deep technical SEO audits, geographical search visibility analyses, competitor intelligence sweeps, and market opportunity evaluations. (Path: `config/agents/market-seo-geo-researcher/skills/market-seo-geo-research/SKILL.md`)
- **`/marketing-strategy`** (`marketing-agent`): Formulates integrated multi-channel marketing strategies, leads content production, designs conversion funnels, and enforces brand voice. (Path: `config/agents/marketing-agent/skills/marketing-strategy/SKILL.md`)
- **`/master-reporting`** (`master-reporting-agent`): Compiles executive deliverables, synthesizes cross-departmental findings, audits immutable execution trails, and analyzes operational velocity. (Path: `config/agents/master-reporting-agent/skills/master-reporting/SKILL.md`)
- **`/package-installation`** (`package-runtime-installer`): Executes isolated uv/npm installations, copies assets into destination directories, executes verification tests, and manages rollbacks. (Path: `config/agents/package-runtime-installer/skills/package-installation/SKILL.md`)
- **`/progress-monitoring`** (`progress-monitor`): Monitors live task progression, detects stuck steps, calculates elapsed execution times, and reports SLA metrics. (Path: `config/agents/progress-monitor/skills/progress-monitoring/SKILL.md`)
- **`/qa-testing`** (`qa-test-engineer`): Authors automated pytest and unittest suites, executes edge-case tests, and verifies zero-regression quality. (Path: `config/agents/qa-test-engineer/skills/qa-testing/SKILL.md`)
- **`/release-verification`** (`release-verifier`): Conducts independent pre-flight and post-deployment verification audits before any release is finalized. (Path: `config/agents/release-verifier/skills/release-verification/SKILL.md`)
- **`/resource-allocation`** (`resource-allocator`): Maps DAG plan steps to the most capable agent blueprints, checking permissions and tool requirements. (Path: `config/agents/resource-allocator/skills/resource-allocation/SKILL.md`)
- **`/retrospective-analysis`** (`retrospective-analyst`): Analyzes execution duration, calculates agent rework rates, and provides optimization recommendations. (Path: `config/agents/retrospective-analyst/skills/retrospective-analysis/SKILL.md`)
- **`/seo-audit`** (`seo-auditor`): Audits DOM structures, metadata, robots.txt, sitemaps, structured data, Core Web Vitals, and indexability signals. (Path: `config/agents/seo-auditor/skills/seo-audit/SKILL.md`)
- **`/service-management`** (`service-manager`): Controls local daemon processes, binds ports, inspects process health, and executes clean shutdowns. (Path: `config/agents/service-manager/skills/service-management/SKILL.md`)
- **`/software-engineering`** (`software-engineer`): Designs robust technical architectures, implements clean code across frontend and backend systems, and executes automated test suites. (Path: `config/agents/software-engineer/skills/software-engineering/SKILL.md`)
- **`/system-integration`** (`system-integrator-update-agent`): Discovers, classifies, audits, installs, tests, registers, and maintains newly supplied external capabilities (skills, tools, packages, blueprints, workflows, integrations). Updates OS operational knowledge. (Path: `config/agents/system-integrator-update-agent/skills/system-integration/SKILL.md`)
- **`/task-decomposition`** (`task-decomposer`): Analyzes complex requirements and breaks them into atomic, ordered, and dependency-mapped plan steps. (Path: `config/agents/task-decomposer/skills/task-decomposition/SKILL.md`)
- **`/visual-inspection`** (`visual-inspector`): Captures high-resolution full-page screenshots, audits visual UI fidelity, and detects rendering glitches. (Path: `config/agents/visual-inspector/skills/visual-inspection/SKILL.md`)
- **`/web-navigation`** (`web-navigator`): Handles page navigation, form interactions, cookie consent handling, and multi-step web flows. (Path: `config/agents/web-navigator/skills/web-navigation/SKILL.md`)


