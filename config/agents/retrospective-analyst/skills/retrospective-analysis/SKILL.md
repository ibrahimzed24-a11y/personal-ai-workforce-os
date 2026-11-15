---
name: retrospective-analysis
description: "Analyzes execution duration, calculates agent rework rates, and provides optimization recommendations."
agent_id: retrospective-analyst
slash_command: /retrospective-analysis
version: 2.0.0
capabilities: ['cap:reporting_compile', 'cap:quality_verify']
inputs:
  task_id:
    type: string
    description: "Task ID to analyze"
    required: true
outputs:
  schema: {"type": "object", "properties": {"total_duration_seconds": {"type": "number"}, "bottlenecks_identified": {"type": "array"}, "recommendations": {"type": "array"}}}
---

# Skill: Retrospective Analyst Specialist (/retrospective-analysis)

## 1. Purpose
The `retrospective-analysis` skill operationalizes the core capabilities of the `Retrospective Analyst Specialist` (`retrospective-analyst`). It provides a standardized, repeatable procedure for executing post-mortem investigator, velocity analyst, and bottleneck optimizer tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/retrospective-analysis`.
- The Coordinator assigns a DAG plan step requiring post-mortem investigator, velocity analyst, and bottleneck optimizer.
- An operational objective involves Calculating step duration, total execution latency, and agent response times, Investigating root causes for step failures, retries, and error conditions.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never blame individual agents subjectively (focus on objective architecture and prompts), Never alter system parameters without testing).

---

## 4. Step-by-Step Procedure

1. **Ingest Event Timestamps:** Calculate start, milestone, and end timestamps from task audit log.

2. **Calculate Step Latencies:** Measure elapsed time per plan step in seconds and milliseconds.

3. **Identify Bottlenecks:** Isolate steps that consumed >40% of total execution duration.

4. **Analyze Failure Root Causes:** If retries occurred, determine why (e.g. timeout, selector change).

5. **Compute Productivity Indicators:** Calculate Task Completion Rate (TCR) and Tool Success Rate (TSR).

6. **Compare Against Baselines:** Compare execution duration against historical task averages.

7. **Identify Unnecessary Steps:** Flag any redundant data fetch or file read operations.

8. **Formulate Optimization Actions:** Propose specific prompt, tool, or caching improvements.

9. **Draft Retrospective Report:** Package findings into structured post-mortem section.

10. **Deliver Performance Section:** Hand analysis to Master Reporting Lead.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:reporting_compile`, `cap:quality_verify`
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
    "total_duration_seconds": {
      "type": "number"
    },
    "bottlenecks_identified": {
      "type": "array"
    },
    "recommendations": {
      "type": "array"
    }
  }
}
```
