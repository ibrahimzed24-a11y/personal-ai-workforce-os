---
name: resource-allocation
description: "Maps DAG plan steps to the most capable agent blueprints, checking permissions and tool requirements."
agent_id: resource-allocator
slash_command: /resource-allocation
version: 2.0.0
capabilities: ['cap:plan_decompose']
inputs:
  steps:
    type: array
    description: "List of unassigned plan steps"
    required: true
outputs:
  schema: {"type": "object", "properties": {"assigned_steps": {"type": "array"}}}
---

# Skill: Resource Allocator Specialist (/resource-allocation)

## 1. Purpose
The `resource-allocation` skill operationalizes the core capabilities of the `Resource Allocator Specialist` (`resource-allocator`). It provides a standardized, repeatable procedure for executing agent capability matching and workload balancer tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/resource-allocation`.
- The Coordinator assigns a DAG plan step requiring agent capability matching and workload balancer.
- An operational objective involves Evaluating step requirements against the 32-agent capability catalog, Assigning optimal core agents and specialist subagents to plan steps.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never alter step descriptions or step dependencies, Never grant unapproved security permissions to agents).

---

## 4. Step-by-Step Procedure

1. **Ingest Steps:** Receive decomposed steps from Task Decomposer.

2. **Analyze Skill Requirements:** Identify whether each step needs engineering, browser, research, or audit skills.

3. **Query Blueprint Registry:** Match requirements against `agent_blueprints` and `specialist_definitions`.

4. **Verify Tool Permissions:** Ensure candidate agent possesses required capabilities (`cap:*`).

5. **Check Credential Access:** Verify if the step requires vault credentials and whether agent has policy grant.

6. **Balance Workloads:** Distribute tasks across specialists to avoid overloading a single core agent.

7. **Handle Gaps:** If no agent matches a required capability, flag to System Integrator.

8. **Bind Agents:** Set `assigned_agent` and `specialist_id` on each `PlanStep`.

9. **Verify Assignments:** Confirm all 100% of steps have valid, active agent bindings.

10. **Deliver Mapped Plan:** Return updated steps to Coordinator.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:plan_decompose`
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
    "assigned_steps": {
      "type": "array"
    }
  }
}
```
