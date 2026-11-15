---
name: deployment-management
description: "Manages local services, coordinates application releases, enforces pre-flight verification checks, and executes rollbacks on failure."
agent_id: deployment-agent
slash_command: /deployment-management
version: 2.0.0
capabilities: ['cap:service_manage', 'cap:code_execute', 'cap:quality_verify']
inputs:
  release_version:
    type: string
    description: "Target release tag"
    required: true
  action:
    type: string
    description: "deploy, restart, rollback, status"
    required: true
outputs:
  schema: {"type": "object", "properties": {"deployment_status": {"type": "string"}, "active_pid": {"type": "number"}, "health_report": {"type": "object"}}}
---

# Skill: Deployment Agent (/deployment-management)

## 1. Purpose
The `deployment-management` skill operationalizes the core capabilities of the `Deployment Agent` (`deployment-agent`). It provides a standardized, repeatable procedure for executing release manager, local environment supervisor, and deployment director tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/deployment-management`.
- The Coordinator assigns a DAG plan step requiring release manager, local environment supervisor, and deployment director.
- An operational objective involves Supervising local OS background processes, daemons, and system health checks, Managing application release pipelines from staging checks to active deployment.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never attempt cloud VPS provisioning or deploy private OS code to public Vercel/Supabase, Never terminate running services without confirming port availability and process identity).

---

## 4. Step-by-Step Procedure

1. **Ingest Deployment Directive:** Parse target version, affected components, and rollback target.

2. **Execute Pre-Flight Audit:** Instruct Release Verifier to validate test suites and Git clean state.

3. **Backup Current State:** Create dated backup of SQLite database and configuration files.

4. **Prepare Environment:** Task Environment Provisioner with checking Python venv and dependencies.

5. **Execute Service Staging:** Stage new code artifacts in workspace.

6. **Restart Services:** Direct Service Manager to execute clean restart via `./stop_os.sh` and `./start_os.sh`.

7. **Verify Live Health:** Poll `/api/health` and verify HTTP 200 within 10 seconds.

8. **Execute Post-Deployment Checks:** Run automated smoke tests against live local endpoints.

9. **Handle Failures / Rollback:** If any smoke test fails, immediately restore backup and rollback.

10. **Issue Release Summary:** Compile deployment report with active PID and git commit hash.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:service_manage`, `cap:code_execute`, `cap:quality_verify`
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
    "deployment_status": {
      "type": "string"
    },
    "active_pid": {
      "type": "number"
    },
    "health_report": {
      "type": "object"
    }
  }
}
```
