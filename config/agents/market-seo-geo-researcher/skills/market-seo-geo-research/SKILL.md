---
name: market-seo-geo-research
description: "Conducts deep technical SEO audits, geographical search visibility analyses, competitor intelligence sweeps, and market opportunity evaluations."
agent_id: market-seo-geo-researcher
slash_command: /market-seo-geo-research
version: 2.0.0
capabilities: ['cap:research_gather', 'cap:source_verify', 'cap:data_extract', 'cap:reporting_compile']
inputs:
  domain_or_topic:
    type: string
    description: "Target domain or market keyword"
    required: true
  regions:
    type: array
    description: "Target geo regions (e.g. US, EU)"
    required: false
outputs:
  schema: {"type": "object", "properties": {"seo_findings": {"type": "object"}, "geo_insights": {"type": "object"}, "competitor_analysis": {"type": "object"}}}
---

# Skill: Market, SEO & GEO Researcher Agent (/market-seo-geo-research)

## 1. Purpose
The `market-seo-geo-research` skill operationalizes the core capabilities of the `Market, SEO & GEO Researcher Agent` (`market-seo-geo-researcher`). It provides a standardized, repeatable procedure for executing search intelligence, competitive benchmarking, and regional market strategist tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/market-seo-geo-research`.
- The Coordinator assigns a DAG plan step requiring search intelligence, competitive benchmarking, and regional market strategist.
- An operational objective involves Synthesizing technical SEO audits, site architecture reviews, and keyword opportunity clusters, Analyzing geographical search visibility, local pack rankings, and regional intent patterns.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never execute black-hat SEO, automated spam generation, or link farm schemes, Never deploy code changes to production servers directly).

---

## 4. Step-by-Step Procedure

1. **Define Research Scope:** Identify target domains, search verticals, and geographical boundaries.

2. **Activate Technical SEO Sweep:** Instruct SEO Auditor to inspect crawlability, indexing, and Core Web Vitals.

3. **Activate GEO Analysis:** Instruct GEO Targeting Analyst to evaluate regional SERP rankings and local pack signals.

4. **Activate Competitor Benchmarking:** Instruct Competitor Intelligence to audit top ranking competitors.

5. **Aggregate Search Metrics:** Ingest keyword volume, search intent distribution, and ranking volatility.

6. **Synthesize Findings:** Correlate technical deficiencies with ranking drops or market opportunities.

7. **Formulate Optimization Roadmap:** Prioritize recommendations by impact (Quick Wins vs Strategic).

8. **Validate Evidence:** Verify all citation URLs and data timestamps are current and accurate.

9. **Format Markdown Report:** Structure comprehensive report with executive summary and actionable tables.

10. **Deliver Strategic Brief:** Submit verified report to Coordinator and Marketing Agent.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:research_gather`, `cap:source_verify`, `cap:data_extract`, `cap:reporting_compile`
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
    "seo_findings": {
      "type": "object"
    },
    "geo_insights": {
      "type": "object"
    },
    "competitor_analysis": {
      "type": "object"
    }
  }
}
```
