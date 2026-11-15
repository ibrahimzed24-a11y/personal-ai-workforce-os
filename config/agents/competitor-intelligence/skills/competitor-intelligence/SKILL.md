---
name: competitor-intelligence
description: "Conducts competitive benchmarking, analyzes rival content strategies, backlink profiles, and value propositions."
agent_id: competitor-intelligence
slash_command: /competitor-intelligence
version: 2.0.0
capabilities: ['cap:research_gather', 'cap:data_extract']
inputs:
  competitors:
    type: array
    description: "List of competitor domains or names"
    required: true
  industry_vertical:
    type: string
    description: "Target industry sector"
    required: true
outputs:
  schema: {"type": "object", "properties": {"competitor_matrix": {"type": "array"}, "content_gaps": {"type": "array"}}}
---

# Skill: Competitor Intelligence Analyst Specialist (/competitor-intelligence)

## 1. Purpose
The `competitor-intelligence` skill operationalizes the core capabilities of the `Competitor Intelligence Analyst Specialist` (`competitor-intelligence`). It provides a standardized, repeatable procedure for executing competitive benchmarking and market share intelligence analyst tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/competitor-intelligence`.
- The Coordinator assigns a DAG plan step requiring competitive benchmarking and market share intelligence analyst.
- An operational objective involves Auditing competitor content velocity, topic clusters, and editorial publishing frequencies, Benchmarking competitor organic search footprint and keyword market share.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never engage in industrial espionage, unauthorized computer intrusion, or NDA violations, Never attempt to scrape non-public, authenticated competitor dashboards).

---

## 4. Step-by-Step Procedure

1. **Identify Competitor Cohort:** Select 3-5 primary and secondary competitors in target vertical.

2. **Map Organic Footprint:** Estimate competitor search visibility and shared keyword overlaps.

3. **Analyze Content Strategy:** Review top-performing blog posts, whitepapers, and landing pages.

4. **Inspect Funnels & Pricing:** Document pricing structures, freemium tiers, and CTA mechanics.

5. **Identify Keyword & Content Gaps:** Pinpoint high-value search queries where competitors lack coverage.

6. **Evaluate Unique Selling Propositions:** Contrast competitor positioning statements.

7. **Examine Backlink Authority:** Review domain authority tiers and press mentions.

8. **Perform SWOT Analysis:** Summarize Strengths, Weaknesses, Opportunities, and Threats.

9. **Formulate Counter-Strategies:** Define positioning angles to outmaneuver rival offerings.

10. **Deliver Intelligence Brief:** Package insights into executive comparison matrix.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:research_gather`, `cap:data_extract`
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
    "competitor_matrix": {
      "type": "array"
    },
    "content_gaps": {
      "type": "array"
    }
  }
}
```
