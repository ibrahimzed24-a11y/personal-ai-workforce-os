---
name: progress-monitoring
description: "Monitors live task progression, detects stuck steps, calculates elapsed execution times, and reports SLA metrics."
agent_id: progress-monitor
slash_command: /progress-monitoring
version: 2.0.0
capabilities: ['cap:quality_verify']
inputs:
  task_id:
    type: string
    description: "Task ID to monitor"
    required: true
outputs:
  schema: {"type": "object", "properties": {"progress_percentage": {"type": "number"}, "active_step": {"type": "string"}, "elapsed_seconds": {"type": "number"}}}
---

# Skill: Progress Monitor Specialist (/progress-monitoring)

## 1. Purpose
The `progress-monitoring` skill operationalizes the core capabilities of the `Progress Monitor Specialist` (`progress-monitor`). It provides a standardized, repeatable procedure for executing execution telemetry, timeout tracking, and sla monitor tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/progress-monitoring`.
- The Coordinator assigns a DAG plan step requiring execution telemetry, timeout tracking, and sla monitor.
- An operational objective involves Tracking real-time state changes (`pending` -> `in_progress` -> `completed` / `failed`), Detecting hanging processes or abnormal step execution latencies.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never modify agent code or outputs directly, Never kill host system processes without approval).

---

## 4. Step-by-Step Procedure

1. **Poll Task State:** Ingest current plan status for target `task_id`.

2. **Record Step Start:** Log timestamp when a step shifts to `in_progress`.

3. **Track Heartbeat:** Check step duration against the 120-second timeout budget.

4. **Identify Stalls:** Flag any step inactive for >60s without log output.

5. **Compute Metrics:** Calculate percentage of completed steps vs total plan steps.

6. **Trap Errors:** On step failure, capture stack trace and error payload immediately.

7. **Audit Step Transitions:** Record `step_completed` event with duration in `execution_events`.

8. **Evaluate SLA:** Compare execution time against baseline benchmarks.

9. **Notify Coordinator:** Send status report upon milestone completion or failure.

10. **Archive Metrics:** Commit finalized execution telemetry to SQLite.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:quality_verify`
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
    "progress_percentage": {
      "type": "number"
    },
    "active_step": {
      "type": "string"
    },
    "elapsed_seconds": {
      "type": "number"
    }
  }
}
```
