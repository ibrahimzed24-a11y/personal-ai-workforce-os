---
name: geo-analysis
description: "Analyzes localized search visibility, hreflang tags, local pack rankings, and regional consumer search intent."
agent_id: geo-targeting-analyst
slash_command: /geo-analysis
version: 2.0.0
capabilities: ['cap:research_gather', 'cap:source_verify']
inputs:
  brand_or_domain:
    type: string
    description: "Brand or domain to analyze"
    required: true
  regions:
    type: array
    description: "Target regions/cities"
    required: true
outputs:
  schema: {"type": "object", "properties": {"regional_visibility": {"type": "object"}, "hreflang_status": {"type": "string"}}}
---

# Skill: GEO Targeting Analyst Specialist (/geo-analysis)

## 1. Purpose
The `geo-analysis` skill operationalizes the core capabilities of the `GEO Targeting Analyst Specialist` (`geo-targeting-analyst`). It provides a standardized, repeatable procedure for executing regional search visibility and local serp analyst tasks within the AI Workforce OS.

---

## 2. Read First & Prerequisites
Before executing this skill, you must inspect and load:
1. `AGENT.md`: Primary identity, permissions, and operating boundaries.
2. `MEMORY.md`: Accumulated durable owner feedback and operational lessons.
3. Relevant Project Context: Task specification and input context.
4. Relevant Knowledge Sources: `~/AI-Workforce/documentation/knowledge/`
5. Approved Examples: Prior verified deliverables in `~/AI-Workforce/logs/`
6. Supporting Skills: Relevant runtime adapters and verification tools.

---

## 3. When to Use (Intent Matching)
Activate this skill when:
- The task prompt explicitly calls `/geo-analysis`.
- The Coordinator assigns a DAG plan step requiring regional search visibility and local serp analyst.
- An operational objective involves Auditing `hreflang` internationalization tags and language-region targeting configurations, Analyzing localized SERP features (Google Map Pack, local directories, local citations).

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never spoof GPS or IP locations using unapproved proxy tunnels, Never post fake regional reviews or local citations).

---

## 4. Step-by-Step Procedure

1. **Define Geo Targets:** Ingest target countries, provinces, or metropolitan areas.

2. **Audit Hreflang Tags:** Parse HTML headers for bilateral `hreflang` reciprocity (`en-US`, `en-GB`, etc.).

3. **Inspect Local Signals:** Evaluate NAP (Name, Address, Phone) consistency across public footers.

4. **Analyze Local Intent:** Extract search volumes for localized keyword modifiers.

5. **Examine Map Pack Visibility:** Assess local business schema markup and directory citations.

6. **Benchmark Local Competitors:** Identify dominant regional players ranking in target zones.

7. **Identify Language Nuances:** Flag dialect, currency, or cultural terminology mismatches.

8. **Score Regional Penetration:** Calculate relative visibility score per target region.

9. **Formulate Localization Strategy:** Outline steps for regional landing page optimization.

10. **Deliver Geo-Targeting Brief:** Present structured regional matrix to parent Researcher.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:research_gather`, `cap:source_verify`
- Reference Materials: Located in `references/` and `documentation/knowledge/`
- Output Destination: `logs/deliverable_<task_id>.md`

---

## 7. Quality Standards
A high-quality result from this skill must satisfy:
- **Accuracy:** All statements, data points, and code implementations are strictly verified against real sources or tests.
- **Completeness:** Every requirement specified in the task prompt or plan step is addressed without omission.
- **Evidence:** Concrete evidence (exit codes, test outputs, file paths, DOM selectors) is provided for all claimed results.
- **Output Format:** Output is formatted in clean GitHub-flavored Markdown or valid JSON matching the system schema.
- **Validation:** All intermediate and final checks pass with zero unhandled exceptions.

---

## 8. Failure Handling
- On critical failure: Capture full error trace, revert any partial file writes, log the failure event to SQLite `execution_events`, and report the blocker state to Coordinator.
- If a dependency is missing, request installation via System Integrator rather than aborting silently.

---

## 9. Final Deliverable
The final deliverable from this skill must be rendered in GitHub-flavored Markdown and stored at:
`~/AI-Workforce/logs/deliverable_<task_id>.md`
Schema:
```json
{
  "type": "object",
  "properties": {
    "regional_visibility": {
      "type": "object"
    },
    "hreflang_status": {
      "type": "string"
    }
  }
}
```
