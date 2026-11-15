---
name: web-navigation
description: "Handles page navigation, form interactions, cookie consent handling, and multi-step web flows."
agent_id: web-navigator
slash_command: /web-navigation
version: 2.0.0
capabilities: ['cap:browser_navigate']
inputs:
  url:
    type: string
    description: "URL to navigate"
    required: true
  interaction_steps:
    type: array
    description: "Clicks, scrolls, input fills"
    required: false
outputs:
  schema: {"type": "object", "properties": {"navigation_success": {"type": "boolean"}, "status_code": {"type": "number"}}}
---

# Skill: Web Navigator Specialist (/web-navigation)

## 1. Purpose
The `web-navigation` skill operationalizes the core capabilities of the `Web Navigator Specialist` (`web-navigator`). It provides a standardized, repeatable procedure for executing playwright controller, session handler, and flow navigator tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/web-navigation`.
- The Coordinator assigns a DAG plan step requiring playwright controller, session handler, and flow navigator.
- An operational objective involves Executing complex Playwright navigation sequences across multi-page web applications, Handling modal popups, cookie consent banners, and dynamic lazy-loading triggers.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never bypass anti-bot challenges or proof-of-work gates, Never submit payment or checkout forms autonomously).

---

## 4. Step-by-Step Procedure

1. **Ingest Navigation Route:** Parse target URL and interaction instructions.

2. **Initialize Playwright Page:** Set viewport to standard 1280x800 resolution.

3. **Navigate with Timeout:** Call `page.goto()` with a 30-second timeout limit.

4. **Handle Consent Dialogs:** Locate common cookie banners ('Accept', 'Agree') and click safely.

5. **Execute Interactions:** Execute specified clicks, typing, or dropdown selections sequentially.

6. **Trigger Lazy Loading:** Scroll viewport down smoothly to trigger dynamic content loading.

7. **Wait for Network Idle:** Ensure all AJAX and WebSocket network requests complete.

8. **Trap Errors:** Handle navigation aborts, HTTP 403, and HTTP 500 errors gracefully.

9. **Confirm Final URL:** Record final navigated URL (checking for unexpected redirects).

10. **Signal Ready:** Notify Data Extractor that DOM is stable for parsing.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:browser_navigate`
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
    "navigation_success": {
      "type": "boolean"
    },
    "status_code": {
      "type": "number"
    }
  }
}
```
