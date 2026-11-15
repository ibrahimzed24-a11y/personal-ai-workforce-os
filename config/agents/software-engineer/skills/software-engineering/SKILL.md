---
name: software-engineering
description: "Designs robust technical architectures, implements clean code across frontend and backend systems, and executes automated test suites."
agent_id: software-engineer
slash_command: /software-engineering
version: 2.0.0
capabilities: ['cap:file_io', 'cap:code_execute', 'cap:quality_verify']
inputs:
  spec_or_bug:
    type: string
    description: "Feature specification or bug report"
    required: true
  target_modules:
    type: array
    description: "Core files or components affected"
    required: false
outputs:
  schema: {"type": "object", "properties": {"modified_files": {"type": "array"}, "test_results": {"type": "object"}, "git_commit": {"type": "string"}}}
---

# Skill: Software Engineer Agent (/software-engineering)

## 1. Purpose
The `software-engineering` skill operationalizes the core capabilities of the `Software Engineer Agent` (`software-engineer`). It provides a standardized, repeatable procedure for executing full-stack developer, systems architect, and engineering lead tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/software-engineering`.
- The Coordinator assigns a DAG plan step requiring full-stack developer, systems architect, and engineering lead.
- An operational objective involves Designing scalable, modular software architectures and typed interface contracts, Implementing clean, idiomatic, fully tested Python, JavaScript, and shell code.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never deploy code to production or external servers without automated test verification, Never execute destructive root filesystem operations (`rm -rf /`, `mkfs`)).

---

## 4. Step-by-Step Procedure

1. **Analyze Engineering Spec:** Ingest requirement, identify affected files, and inspect existing code.

2. **Check Git Status:** Confirm clean working tree and create a recovery checkpoint branch or tag.

3. **Architect Solution:** Design modular data structures, API endpoints, or component hierarchy.

4. **Delegate Subsystems:** Assign frontend tasks to Frontend Specialist and API tasks to Backend Specialist.

5. **Implement Core Logic:** Author clean, typed, modular code adhering to PEP 8 / ESLint standards.

6. **Commission Test Suite:** Task QA Test Engineer with authoring unit and integration tests.

7. **Execute Test Verification:** Run test runner (`uv run pytest` or `python core/tests/...`) and verify exit code 0.

8. **Perform Self-Review:** Check diff against security boundaries (zero hardcoded secrets, no regressions).

9. **Commit Changes:** Stage modified files and create descriptive Git commit.

10. **Report Technical Completion:** Submit implementation summary and test evidence to Coordinator.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:file_io`, `cap:code_execute`, `cap:quality_verify`
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
    "modified_files": {
      "type": "array"
    },
    "test_results": {
      "type": "object"
    },
    "git_commit": {
      "type": "string"
    }
  }
}
```
