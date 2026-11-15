---
name: audit-trail
description: "Compiles chronological, step-by-step audit timelines from immutable SQLite execution logs."
agent_id: audit-trail-compiler
slash_command: /audit-trail
version: 2.0.0
capabilities: ['cap:reporting_compile', 'cap:security_audit']
inputs:
  task_id:
    type: string
    description: "Task ID to audit"
    required: true
outputs:
  schema: {"type": "object", "properties": {"audit_timeline": {"type": "array"}, "event_count": {"type": "number"}}}
---

# Skill: Audit Trail Compiler Specialist (/audit-trail)

## 1. Purpose
The `audit-trail` skill operationalizes the core capabilities of the `Audit Trail Compiler Specialist` (`audit-trail-compiler`). It provides a standardized, repeatable procedure for executing execution event correlator, timeline compiler, and evidence logger tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/audit-trail`.
- The Coordinator assigns a DAG plan step requiring execution event correlator, timeline compiler, and evidence logger.
- An operational objective involves Querying and structuring `execution_events` into human-readable chronological timelines, Correlating task steps with assigned agents, specialists, exit codes, and timestamps.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never alter or delete execution records in the database, Never expose raw decrypted passwords or master keys in the audit table).

---

## 4. Step-by-Step Procedure

1. **Ingest Task Context:** Receive target `task_id`.

2. **Query Event Store:** Fetch all rows from `execution_events` matching `task_id` ordered by timestamp.

3. **Parse Event Payloads:** Decode JSON event payloads safely.

4. **Format Chronological Table:** Build Markdown table with columns: Time, Step, Agent, Event, Details.

5. **Redact Sensitive Strings:** Ensure no inadvertent secret strings exist in payload text.

6. **Correlate Tool Invocations:** Document all tool calls (`cap:*`, shell, filesystem, browser).

7. **Highlight State Changes:** Mark failures in bold or warning callouts.

8. **Summarize Event Counts:** Calculate total events recorded for the task.

9. **Verify Integrity:** Confirm first event is `task_created` and final event is `deliverable_created`.

10. **Deliver Audit Section:** Hand completed timeline table to Master Reporting Agent.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:reporting_compile`, `cap:security_audit`
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
    "audit_timeline": {
      "type": "array"
    },
    "event_count": {
      "type": "number"
    }
  }
}
```
