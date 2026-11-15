---
name: frontend-development
description: "Builds responsive, accessible, high-performance web user interfaces, dashboards, and client-side interactions."
agent_id: frontend-specialist
slash_command: /frontend-development
version: 2.0.0
capabilities: ['cap:file_io', 'cap:code_execute']
inputs:
  ui_component_spec:
    type: string
    description: "UI layout or dashboard requirement"
    required: true
outputs:
  schema: {"type": "object", "properties": {"html_css_js_files": {"type": "array"}, "ui_verification_status": {"type": "string"}}}
---

# Skill: Frontend Specialist (/frontend-development)

## 1. Purpose
The `frontend-development` skill operationalizes the core capabilities of the `Frontend Specialist` (`frontend-specialist`). It provides a standardized, repeatable procedure for executing modern web ui developer, dom specialist, and css architect tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/frontend-development`.
- The Coordinator assigns a DAG plan step requiring modern web ui developer, dom specialist, and css architect.
- An operational objective involves Authoring semantic, accessible HTML5 structures and responsive CSS layouts, Implementing lightweight, modern vanilla JavaScript / Web Components for UI interactivity.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never modify backend SQLite database tables or migration scripts directly, Never introduce heavy multi-megabyte frontend frameworks without owner authorization).

---

## 4. Step-by-Step Procedure

1. **Review UI Spec:** Ingest component mockup, layout requirements, and user interaction states.

2. **Inspect Existing UI Assets:** Review `core/ui/index.html`, `style.css`, and `app.js`.

3. **Draft Semantic HTML:** Author clean HTML structure using accessible ARIA landmarks.

4. **Style Responsive Layout:** Implement mobile-first CSS grid/flexbox with CSS custom properties.

5. **Implement Client Logic:** Author modular JavaScript event listeners and async fetch calls.

6. **Add UI Feedback:** Ensure loading spinners, success toasts, and error alerts are rendered.

7. **Check Accessibility:** Validate keyboard tab navigation and color contrast ratios (WCAG AA).

8. **Test Headless Rendering:** Execute Playwright headless browser test to verify DOM presence.

9. **Refactor Code:** Remove redundant CSS rules and format JavaScript cleanly.

10. **Deliver UI Component:** Submit modified frontend files to Software Engineer Lead.

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
    "html_css_js_files": {
      "type": "array"
    },
    "ui_verification_status": {
      "type": "string"
    }
  }
}
```
