---
name: campaign-planning
description: "Architects multi-touch conversion funnels, maps lifecycle email sequences, and designs A/B test frameworks."
agent_id: campaign-planner
slash_command: /campaign-planning
version: 2.0.0
capabilities: ['cap:plan_decompose', 'cap:content_author']
inputs:
  campaign_goal:
    type: string
    description: "Lead gen, product launch, webinar, retention"
    required: true
  target_kpi:
    type: string
    description: "Target conversion rate or CAC"
    required: false
outputs:
  schema: {"type": "object", "properties": {"funnel_stages": {"type": "array"}, "email_sequence": {"type": "array"}, "ab_test_plan": {"type": "object"}}}
---

# Skill: Campaign Planner Specialist (/campaign-planning)

## 1. Purpose
The `campaign-planning` skill operationalizes the core capabilities of the `Campaign Planner Specialist` (`campaign-planner`). It provides a standardized, repeatable procedure for executing funnel architect, lifecycle marketing, and a/b test specialist tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/campaign-planning`.
- The Coordinator assigns a DAG plan step requiring funnel architect, lifecycle marketing, and a/b test specialist.
- An operational objective involves Mapping customer conversion journeys from initial awareness to retention and referral, Designing automated email nurture sequences, behavioral triggers, and branching logic.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never connect live payment gateways or process customer billing autonomously, Never allocate media ad budgets without explicit owner approval).

---

## 4. Step-by-Step Procedure

1. **Define Campaign Objective:** Ingest conversion targets (e.g. 500 newsletter signups, 50 demo bookings).

2. **Map Funnel Stages:** Diagram TOFU (Awareness), MOFU (Consideration), and BOFU (Decision) touchpoints.

3. **Design Lead Magnet:** Specify high-value asset required to incentivize conversion.

4. **Architect Email Sequence:** Draft trigger logic for 5-part onboarding nurture flow.

5. **Formulate A/B Tests:** Define split test variations (Headline A vs B, Button Color, Social Proof).

6. **Specify Tracking Parameters:** Define UTM naming taxonomy (`utm_source`, `utm_medium`, `utm_campaign`).

7. **Model Unit Economics:** Project conversion rates and estimated customer acquisition costs.

8. **Review Friction Points:** Remove unnecessary form fields and navigation dead-ends.

9. **Integrate Compliance:** Ensure CAN-SPAM and GDPR unsubscribe requirements are satisfied.

10. **Deliver Funnel Blueprint:** Submit completed lifecycle specification to Marketing Lead.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:plan_decompose`, `cap:content_author`
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
    "funnel_stages": {
      "type": "array"
    },
    "email_sequence": {
      "type": "array"
    },
    "ab_test_plan": {
      "type": "object"
    }
  }
}
```
