---
name: environment-provisioning
description: "Manages Python virtual environments, audits package dependencies via `uv`, and ensures runtime isolation."
agent_id: environment-provisioner
slash_command: /environment-provisioning
version: 2.0.0
capabilities: ['cap:code_execute', 'cap:file_io']
inputs:
  package_spec:
    type: string
    description: "Package name or pyproject.toml"
    required: true
outputs:
  schema: {"type": "object", "properties": {"environment_status": {"type": "string"}, "packages_synced": {"type": "array"}}}
---

# Skill: Environment Provisioner Specialist (/environment-provisioning)

## 1. Purpose
The `environment-provisioning` skill operationalizes the core capabilities of the `Environment Provisioner Specialist` (`environment-provisioner`). It provides a standardized, repeatable procedure for executing virtualenv architect, dependency auditor, and local tool provisioner tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/environment-provisioning`.
- The Coordinator assigns a DAG plan step requiring virtualenv architect, dependency auditor, and local tool provisioner.
- An operational objective involves Creating and managing isolated virtual environments using `uv` in `.venv/`, Auditing `pyproject.toml` and `uv.lock` for dependency conflicts and security advisories.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never install unapproved global system packages requiring root/sudo, Never modify host macOS operating system files outside `~/AI-Workforce/`).

---

## 4. Step-by-Step Procedure

1. **Check Workspace Environment:** Ingest target package requirements or lockfile update.

2. **Verify Python Runtime:** Confirm host Python version >= 3.12 via `uv python list`.

3. **Audit Virtual Environment:** Check existence and health of `.venv/bin/python`.

4. **Check Dependency Tree:** Run `uv lock --check` to detect dependency discrepancies.

5. **Execute Synchronization:** Run `uv sync` to install or prune virtual environment packages.

6. **Verify Executable Binaries:** Check that entry points and binaries are executable.

7. **Audit Permissions:** Confirm sensitive directories and key files maintain restrictive modes.

8. **Run Environment Smoke Test:** Execute `python -c 'import core; print(core.__file__)'`.

9. **Clean Temp Build Files:** Remove temporary `.whl` and `.egg-info` caches.

10. **Report Environment State:** Deliver provisioning status report to Deployment Agent.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:code_execute`, `cap:file_io`
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
    "environment_status": {
      "type": "string"
    },
    "packages_synced": {
      "type": "array"
    }
  }
}
```
