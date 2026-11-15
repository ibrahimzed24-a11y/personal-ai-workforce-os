---
name: release-verification
description: "Conducts independent pre-flight and post-deployment verification audits before any release is finalized."
agent_id: release-verifier
slash_command: /release-verification
version: 2.0.0
capabilities: ['cap:quality_verify', 'cap:code_execute']
inputs:
  release_version:
    type: string
    description: "Release tag to verify"
    required: true
outputs:
  schema: {"type": "object", "properties": {"verification_status": {"type": "string", "enum": ["PASSED", "FAILED"]}, "checks_run": {"type": "array"}}}
---

# Skill: Release Verifier Specialist (/release-verification)

## 1. Purpose
The `release-verification` skill operationalizes the core capabilities of the `Release Verifier Specialist` (`release-verifier`). It provides a standardized, repeatable procedure for executing pre-flight release auditor and post-deployment validator tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/release-verification`.
- The Coordinator assigns a DAG plan step requiring pre-flight release auditor and post-deployment validator.
- An operational objective involves Executing pre-flight validation (Git clean status, full test pass, documentation update), Running post-deployment integration checks against live local endpoints.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never deploy code or restart services directly (conducts verification only), Never certify a release if any test suite fails or has unresolved errors).

---

## 4. Step-by-Step Procedure

1. **Ingest Release Target:** Identify release version, git commit, and included changes.

2. **Check Git Status:** Confirm working tree is clean with zero uncommitted modifications.

3. **Run Regression Suites:** Execute `test_system.py`, `test_three_file_architecture.py`, and `test_browser_ui.py`.

4. **Audit Database Integrity:** Execute `PRAGMA integrity_check` on `data/ai_workforce.db`.

5. **Check Vault Status:** Confirm vault master key exists with `0600` permissions and valid cipher.

6. **Verify API Endpoints:** Test core endpoints (`/api/tasks`, `/api/agents`, `/api/health`).

7. **Audit Documentation:** Confirm release notes or architecture documents reflect changes.

8. **Evaluate Failure Risk:** Assess blast radius and rollback readiness.

9. **Generate Verification Audit Record:** Insert detailed audit record into `verification_audits` table.

10. **Issue Certification Stamp:** Return `PASSED` or `FAILED` verdict to Deployment Agent.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:quality_verify`, `cap:code_execute`
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
    "verification_status": {
      "type": "string",
      "enum": [
        "PASSED",
        "FAILED"
      ]
    },
    "checks_run": {
      "type": "array"
    }
  }
}
```
