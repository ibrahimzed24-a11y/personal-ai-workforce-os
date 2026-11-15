---
name: visual-inspection
description: "Captures high-resolution full-page screenshots, audits visual UI fidelity, and detects rendering glitches."
agent_id: visual-inspector
slash_command: /visual-inspection
version: 2.0.0
capabilities: ['cap:quality_verify', 'cap:file_io']
inputs:
  screenshot_name:
    type: string
    description: "Base filename for screenshot"
    required: true
  full_page:
    type: boolean
    description: "Capture entire scrollable page"
    required: false
outputs:
  schema: {"type": "object", "properties": {"screenshot_path": {"type": "string"}, "dimensions": {"type": "string"}}}
---

# Skill: Visual Inspector Specialist (/visual-inspection)

## 1. Purpose
The `visual-inspection` skill operationalizes the core capabilities of the `Visual Inspector Specialist` (`visual-inspector`). It provides a standardized, repeatable procedure for executing visual regression tester, screenshot auditor, and layout inspector tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/visual-inspection`.
- The Coordinator assigns a DAG plan step requiring visual regression tester, screenshot auditor, and layout inspector.
- An operational objective involves Capturing full-page and element-specific screenshots in standard PNG format, Inspecting visual layout responsiveness across desktop, tablet, and mobile viewports.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never overwrite baseline visual comparison screenshots without authorization, Never save screenshots containing revealed plain text passwords or private keys).

---

## 4. Step-by-Step Procedure

1. **Ingest Inspection Spec:** Receive page context, target filename, and viewport requirement.

2. **Set Viewport Dimensions:** Configure device emulation if mobile/tablet test is requested.

3. **Wait for Font & CSS Paint:** Ensure web fonts and stylesheets have finished rendering.

4. **Hide Transient Overlays:** Suppress animated cursor or blinking caret elements.

5. **Capture PNG Image:** Call `page.screenshot(path=..., full_page=True)`.

6. **Verify File Creation:** Confirm image file is written to `logs/screenshots/` and size >10KB.

7. **Inspect Visual Geometry:** Verify page does not contain unwanted horizontal scrollbars.

8. **Check Contrast & Text:** Confirm body text is legible and not occluded by fixed headers.

9. **Log Visual Evidence:** Record image path and resolution in execution event metadata.

10. **Deliver Inspection Result:** Hand screenshot artifact path to parent Agent.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:quality_verify`, `cap:file_io`
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
    "screenshot_path": {
      "type": "string"
    },
    "dimensions": {
      "type": "string"
    }
  }
}
```
