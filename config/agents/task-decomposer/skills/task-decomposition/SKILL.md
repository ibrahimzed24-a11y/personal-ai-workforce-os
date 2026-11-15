---
name: task-decomposition
description: "Analyzes complex requirements and breaks them into atomic, ordered, and dependency-mapped plan steps."
agent_id: task-decomposer
slash_command: /task-decomposition
version: 2.0.0
capabilities: ['cap:plan_decompose']
inputs:
  task_title:
    type: string
    description: "Title of the parent task"
    required: true
  description:
    type: string
    description: "Detailed task description"
    required: true
outputs:
  schema: {"type": "object", "properties": {"steps": {"type": "array"}}}
---

# Skill: Task Decomposer Specialist (/task-decomposition)

## 1. Purpose
The `task-decomposition` skill operationalizes the core capabilities of the `Task Decomposer Specialist` (`task-decomposer`). It provides a standardized, repeatable procedure for executing task decomposition and dependency dag architect tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/task-decomposition`.
- The Coordinator assigns a DAG plan step requiring task decomposition and dependency dag architect.
- An operational objective involves Breaking down complex objectives into atomic execution steps with clear boundaries, Establishing prerequisite mapping and data flow contracts between steps.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never assign agents directly (owned by Resource Allocator), Never execute implementation steps directly).

---

## 4. Step-by-Step Procedure

1. **Parse Scope:** Extract deliverables and technical boundaries from task prompt.

2. **Identify Milestones:** Divide the task into logical phases (e.g. Research -> Build -> Verify -> Report).

3. **Atomize Actions:** Break each phase into discrete actions achievable by a single specialist.

4. **Define Inputs/Outputs:** Establish exact parameters each step needs and produces.

5. **Map Dependencies:** Assign `prerequisites` list to enforce sequential or parallel execution.

6. **Identify Critical Path:** Calculate the execution path with the longest sequential dependency chain.

7. **Check Failure Modes:** Define timeout and error handling parameters per step.

8. **Review Redundancies:** Merge duplicate research or file-read operations.

9. **Validate DAG Structure:** Ensure zero circular references (`step_A -> step_B -> step_A`).

10. **Output Step Specification:** Deliver standardized JSON list of `PlanStep` objects.

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
    "steps": {
      "type": "array"
    }
  }
}
```
