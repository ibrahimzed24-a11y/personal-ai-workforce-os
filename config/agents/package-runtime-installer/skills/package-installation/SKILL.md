---
name: package-installation
description: "Executes isolated uv/npm installations, copies assets into destination directories, executes verification tests, and manages rollbacks."
agent_id: package-runtime-installer
slash_command: /package-installation
version: 2.0.0
capabilities: ['cap:file_io', 'cap:code_execute']
inputs:
  installation_plan:
    type: object
    description: "Source and destination paths"
    required: true
outputs:
  schema: {"type": "object", "properties": {"installed_path": {"type": "string"}, "installation_status": {"type": "string", "enum": ["ACTIVE", "FAILED", "ROLLED_BACK"]}}}
---

# Skill: Package & Runtime Installer Specialist (/package-installation)

## 1. Purpose
The `package-installation` skill operationalizes the core capabilities of the `Package & Runtime Installer Specialist` (`package-runtime-installer`). It provides a standardized, repeatable procedure for executing isolated installation, virtual environment, and rollback specialist tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/package-installation`.
- The Coordinator assigns a DAG plan step requiring isolated installation, virtual environment, and rollback specialist.
- An operational objective involves Creating isolated `uv` virtual environments in target tool directories, Copying approved skills, tools, and configurations into `config/` and `shared-tools/`.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never install unapproved packages globally outside the designated virtualenv, Never leave orphaned half-installed files or broken state upon failure).

---

## 4. Step-by-Step Procedure

1. **Ingest Installation Plan:** Verify source path in `incoming/` and destination path in workspace.

2. **Record Pre-Install State:** Create snapshot list of files prior to copying for rollback tracking.

3. **Copy Asset Files:** Copy asset files safely to target directory (`config/skills/...` or `shared-tools/...`).

4. **Set Permissions:** Apply `0755` permissions to executable scripts and `0644` to markdown/yaml files.

5. **Provision Virtualenv (if tool):** If Python tool, run `uv venv` in tool subdirectory.

6. **Install Tool Dependencies:** Run `uv pip install -r requirements.txt` inside tool venv.

7. **Execute Verification Test:** Run quick smoke test (e.g. `python -m py_compile` or tool help flag).

8. **Trigger Rollback on Failure:** If smoke test fails, delete all copied files and mark state `ROLLED_BACK`.

9. **Clean Up Incoming:** Archive or remove original payload from `incoming/` upon verified success.

10. **Deliver Install Verdict:** Report active installation path to System Integrator Lead.

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
    "installed_path": {
      "type": "string"
    },
    "installation_status": {
      "type": "string",
      "enum": [
        "ACTIVE",
        "FAILED",
        "ROLLED_BACK"
      ]
    }
  }
}
```
