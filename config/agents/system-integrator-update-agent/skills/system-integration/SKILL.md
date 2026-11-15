---
name: system-integration
description: "Discovers, classifies, audits, installs, tests, registers, and maintains newly supplied external capabilities (skills, tools, packages, blueprints, workflows, integrations). Updates OS operational knowledge."
agent_id: system-integrator-update-agent
slash_command: /system-integration
version: 2.0.0
capabilities: ['cap:file_io', 'cap:security_audit', 'cap:code_execute', 'cap:quality_verify']
inputs:
  incoming_dir:
    type: string
    description: "Path to incoming assets"
    required: false
  action:
    type: string
    description: "scan, audit, install, rollback, sync"
    required: true
outputs:
  schema: {"type": "object", "properties": {"discovered_assets": {"type": "array"}, "installed_assets": {"type": "array"}, "synchronized_docs": {"type": "array"}}}
---

# Skill: System Integrator & Update Agent (/system-integration)

## 1. Purpose
The `system-integration` skill operationalizes the core capabilities of the `System Integrator & Update Agent` (`system-integrator-update-agent`). It provides a standardized, repeatable procedure for executing capability lifecycle manager, system auditor, and knowledge synchronizer tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/system-integration`.
- The Coordinator assigns a DAG plan step requiring capability lifecycle manager, system auditor, and knowledge synchronizer.
- An operational objective involves Scanning `incoming/` directory for newly supplied skills, tools, packages, and blueprints, Supervising static security audits to detect privilege escalation, shell injection, or secret leaks.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never execute untrusted incoming binaries without isolated sandbox audit, Never install packages requiring root or sudo without explicit owner authorization).

---

## 4. Step-by-Step Procedure

1. **Scan Source Directory:** Inspect `~/AI-Workforce/incoming/` for newly placed files or bundles.

2. **Task Asset Classifier:** Direct specialist to classify file types and perform static security audits.

3. **Evaluate Security Score:** Reject assets scored `HIGH` or `CRITICAL` risk; require owner review.

4. **Formulate Installation Plan:** Define destination paths and virtual environment requirements.

5. **Task Package Installer:** Direct specialist to copy files, install dependencies, and run verification.

6. **Verify Functional Health:** Run syntax check or automated tests against installed capability.

7. **Execute Rollback on Failure:** If testing fails, clean up all copied files and restore state.

8. **Register in SQLite:** Insert asset record into `installed_assets` table with `ACTIVE` status.

9. **Task Knowledge Synchronizer:** Re-index `SKILLS_INDEX.md` and `AVAILABLE_CAPABILITIES.md`.

10. **Notify Workforce:** Inform Coordinator that newly verified capability is ready for task routing.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:file_io`, `cap:security_audit`, `cap:code_execute`, `cap:quality_verify`
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
    "discovered_assets": {
      "type": "array"
    },
    "installed_assets": {
      "type": "array"
    },
    "synchronized_docs": {
      "type": "array"
    }
  }
}
```
