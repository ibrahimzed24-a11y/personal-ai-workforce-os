---
name: marketing-strategy
description: "Formulates integrated multi-channel marketing strategies, leads content production, designs conversion funnels, and enforces brand voice."
agent_id: marketing-agent
slash_command: /marketing-strategy
version: 2.0.0
capabilities: ['cap:content_author', 'cap:research_gather', 'cap:reporting_compile']
inputs:
  campaign_objective:
    type: string
    description: "Core goal of the marketing effort"
    required: true
  target_audience:
    type: string
    description: "Audience persona or market segment"
    required: true
outputs:
  schema: {"type": "object", "properties": {"strategy_brief": {"type": "string"}, "funnel_map": {"type": "object"}, "content_plan": {"type": "array"}}}
---

# Skill: Marketing Agent (/marketing-strategy)

## 1. Purpose
The `marketing-strategy` skill operationalizes the core capabilities of the `Marketing Agent` (`marketing-agent`). It provides a standardized, repeatable procedure for executing chief marketing strategist, brand architect, and growth director tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/marketing-strategy`.
- The Coordinator assigns a DAG plan step requiring chief marketing strategist, brand architect, and growth director.
- An operational objective involves Architecting high-converting marketing strategies across content, email, and organic channels, Supervising content production, editorial calendars, and brand positioning narratives.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never execute live ad spend or bind credit cards without owner approval, Never publish unreviewed content to public production blogs or social accounts autonomously).

---

## 4. Step-by-Step Procedure

1. **Ingest Growth Goals:** Parse target conversion metrics, customer personas, and product offerings.

2. **Conduct Audience Research:** Ingest market insights from Market & SEO Researcher.

3. **Formulate Core Narrative:** Establish campaign hook, value proposition, and messaging pillars.

4. **Direct Funnel Design:** Instruct Campaign Planner to model multi-stage conversion funnel.

5. **Commission Content Assets:** Task Content Strategist with creating copy for landing pages and emails.

6. **Review Brand Compliance:** Submit all generated copy to Brand Compliance for rigorous review.

7. **Audit Conversion Points:** Ensure clear calls-to-action (CTAs) and frictionless sign-up flows.

8. **Define Attribution Metrics:** Set key performance indicators (KPIs, CTR, conversion rates).

9. **Package Campaign Strategy:** Consolidate funnel diagrams, copy briefs, and delivery timeline.

10. **Submit for Approval:** Deliver complete strategy package to Workforce Owner.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:content_author`, `cap:research_gather`, `cap:reporting_compile`
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
    "strategy_brief": {
      "type": "string"
    },
    "funnel_map": {
      "type": "object"
    },
    "content_plan": {
      "type": "array"
    }
  }
}
```
