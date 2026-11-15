---
name: backend-development
description: "Implements FastAPI REST endpoints, executes SQLite WAL database migrations, and manages backend data pipelines."
agent_id: backend-specialist
slash_command: /backend-development
version: 2.0.0
capabilities: ['cap:file_io', 'cap:code_execute']
inputs:
  api_endpoint_spec:
    type: string
    description: "Endpoint path, method, and parameters"
    required: true
outputs:
  schema: {"type": "object", "properties": {"endpoints_added": {"type": "array"}, "database_tables": {"type": "array"}}}
---

# Skill: Backend Specialist (/backend-development)

## 1. Purpose
The `backend-development` skill operationalizes the core capabilities of the `Backend Specialist` (`backend-specialist`). It provides a standardized, repeatable procedure for executing api architect, sqlite engineer, and server logic developer tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/backend-development`.
- The Coordinator assigns a DAG plan step requiring api architect, sqlite engineer, and server logic developer.
- An operational objective involves Designing and implementing typed FastAPI REST endpoints with Pydantic request/response schemas, Authoring performant SQLite queries, WAL-mode PRAGMAs, and schema migrations.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never bypass foreign key constraints (`PRAGMA foreign_keys = ON`) in SQLite, Never author raw SQL queries using string concatenation (strictly use parameterized queries to prevent SQL injection)).

---

## 4. Step-by-Step Procedure

1. **Define Contract:** Ingest endpoint specification, HTTP methods, and data schemas.

2. **Draft Pydantic Models:** Author request and response models in `core/models.py`.

3. **Update Database Schema:** If new state is required, add `CREATE TABLE IF NOT EXISTS` in `core/database.py`.

4. **Implement FastAPI Route:** Author async route handler with dependency injection in `core/app.py`.

5. **Parameterized Queries:** Write parameterized async SQLite operations using `aiosqlite`.

6. **Add Error Handling:** Wrap database and external calls in `HTTPException` handlers (400, 404, 409).

7. **Audit Logging:** Insert `execution_events` or `credential_audit_logs` where state changes.

8. **Run Local Server Check:** Verify daemon launches without syntax or runtime import errors.

9. **Execute API Smoke Test:** Curl endpoint with valid and invalid payloads to test responses.

10. **Deliver Backend Feature:** Submit code diff to Software Engineer and QA Engineer.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:file_io`, `cap:code_execute`
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
    "endpoints_added": {
      "type": "array"
    },
    "database_tables": {
      "type": "array"
    }
  }
}
```
