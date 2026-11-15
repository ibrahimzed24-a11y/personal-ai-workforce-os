---
name: coordinator-agent
description: "Decomposes high-level user objectives into directed acyclic graph (DAG) execution plans, assigns tasks to specialized agents, monitors progress, and synthesizes final deliverables."
agent_id: coordinator
slash_command: /coordinator-agent
version: 2.0.0
capabilities: ['cap:plan_decompose', 'cap:reporting_compile', 'cap:research_gather']
inputs:
  goal:
    type: string
    description: "High-level objective or prompt from owner"
    required: true
  priority:
    type: string
    description: "low, medium, high, critical"
    required: false
  privacy_level:
    type: string
    description: "local_only, standard, sensitive"
    required: false
outputs:
  schema: {"type": "object", "properties": {"plan_id": {"type": "string"}, "steps": {"type": "array"}, "deliverable_path": {"type": "string"}}}
---

# Skill: Coordinator Agent (/coordinator-agent)

## 1. Purpose
The `coordinator-agent` skill operationalizes the core capabilities of the `Coordinator Agent` (`coordinator`). It provides a standardized, repeatable procedure for executing master task planner and workforce coordinator tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/coordinator-agent`.
- The Coordinator assigns a DAG plan step requiring master task planner and workforce coordinator.
- An operational objective involves Decomposing complex user goals into multi-step DAG execution plans with explicit prerequisites, Selecting optimal core agent blueprints and specialists based on task requirements and capability match.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never author production application source code directly (delegate to Software Engineer), Never execute direct Playwright browser navigation or DOM scraping (delegate to Browser Use Agent)).

---

## 4. Step-by-Step Procedure

1. **Ingest Objective:** Parse the user objective, constraints, privacy classification, and deadline.

2. **Decompose Workflow:** Invoke Task Decomposer to formulate an atomic, dependency-mapped DAG execution plan.

3. **Evaluate Resource Allocation:** Check specialist capabilities and agent workloads via Resource Allocator.

4. **Identify Approval Gates:** Flag any steps involving credential revelation, external deployment, or code modification.

5. **Persist Execution Plan:** Save structured plan to SQLite `task_plans` with approved status.

6. **Dispatch Step 1:** Invoke the designated agent with injected three-file runtime context.

7. **Monitor Progression:** Track step status transitions and record execution events in audit log.

8. **Handle Retries or Fallbacks:** If a step fails, trigger retry budget or route to fallback specialist.

9. **Trigger Independent Verification:** Call Verification Adapter to validate all step deliverables.

10. **Synthesize Final Report:** Compile consolidated markdown deliverable in `logs/deliverable_<task_id>.md`.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:plan_decompose`, `cap:reporting_compile`, `cap:research_gather`
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
    "plan_id": {
      "type": "string"
    },
    "steps": {
      "type": "array"
    },
    "deliverable_path": {
      "type": "string"
    }
  }
}
```
