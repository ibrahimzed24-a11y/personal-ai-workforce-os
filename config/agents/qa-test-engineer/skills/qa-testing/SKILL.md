---
name: qa-testing
description: "Authors automated pytest and unittest suites, executes edge-case tests, and verifies zero-regression quality."
agent_id: qa-test-engineer
slash_command: /qa-testing
version: 2.0.0
capabilities: ['cap:code_execute', 'cap:file_io', 'cap:quality_verify']
inputs:
  test_target:
    type: string
    description: "Component or feature to test"
    required: true
outputs:
  schema: {"type": "object", "properties": {"test_suite_path": {"type": "string"}, "tests_passed": {"type": "number"}, "tests_failed": {"type": "number"}, "pass_rate": {"type": "number"}}}
---

# Skill: QA Test Engineer Specialist (/qa-testing)

## 1. Purpose
The `qa-testing` skill operationalizes the core capabilities of the `QA Test Engineer Specialist` (`qa-test-engineer`). It provides a standardized, repeatable procedure for executing test automation engineer, edge-case investigator, and defect auditor tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/qa-testing`.
- The Coordinator assigns a DAG plan step requiring test automation engineer, edge-case investigator, and defect auditor.
- An operational objective involves Authoring automated test scripts covering unit, integration, and end-to-end user flows, Designing negative security tests (e.g. invalid auth, path traversal, SQL injection, secret leaks).

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never comment out or weaken failing assertions to force a test pass, Never use real production passwords or live API tokens in test scripts).

---

## 4. Step-by-Step Procedure

1. **Identify Test Scope:** Ingest target component and map happy path, edge cases, and failure modes.

2. **Draft Test File:** Create or extend test script under `core/tests/`.

3. **Author Setup & Teardown:** Use isolated temporary databases or test workspaces.

4. **Write Positive Tests:** Verify expected functionality with valid inputs.

5. **Write Negative Tests:** Test invalid credentials, malformed JSON, missing files, and boundary values.

6. **Execute Test Suite:** Run tests via `PYTHONPATH=. ~/.local/bin/uv run python <test_file.py>`.

7. **Inspect Output & Assertions:** Verify all assertions pass and check execution duration.

8. **Check Clean Teardown:** Ensure test artifacts and temp databases are removed after execution.

9. **Calculate Pass Rate:** Verify 100% of test suites succeed without warnings or errors.

10. **Issue QA Certification:** Produce comprehensive test report with evidence logs.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:code_execute`, `cap:file_io`, `cap:quality_verify`
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
    "test_suite_path": {
      "type": "string"
    },
    "tests_passed": {
      "type": "number"
    },
    "tests_failed": {
      "type": "number"
    },
    "pass_rate": {
      "type": "number"
    }
  }
}
```
