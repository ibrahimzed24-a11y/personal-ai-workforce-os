---
name: browser-automation
description: "Operates Playwright and Chromium automation to navigate complex web apps, extract dynamic DOM data, and inspect visual UI states."
agent_id: browser-use-agent
slash_command: /browser-automation
version: 2.0.0
capabilities: ['cap:browser_navigate', 'cap:data_extract', 'cap:source_verify']
inputs:
  url:
    type: string
    description: "Target web page URL"
    required: true
  action:
    type: string
    description: "navigate, extract, inspect, screenshot"
    required: true
outputs:
  schema: {"type": "object", "properties": {"final_url": {"type": "string"}, "extracted_data": {"type": "object"}, "screenshot_path": {"type": "string"}}}
---

# Skill: Browser Use Agent (/browser-automation)

## 1. Purpose
The `browser-automation` skill operationalizes the core capabilities of the `Browser Use Agent` (`browser-use-agent`). It provides a standardized, repeatable procedure for executing headless browser automation director and web intelligence lead tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/browser-automation`.
- The Coordinator assigns a DAG plan step requiring headless browser automation director and web intelligence lead.
- An operational objective involves Supervising headless Chromium automation workflows, authentication, and session handling, Extracting structured datasets from JavaScript-rendered single-page applications (SPAs).

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never attempt to solve or bypass CAPTCHAs, bot challenges, or Cloudflare Turnstile gates, Never perform bulk scripted spam, unauthorized account creation, or platform manipulation).

---

## 4. Step-by-Step Procedure

1. **Validate Target URL:** Ingest URL, verify domain legality, and check robots.txt constraints.

2. **Check Authentication:** Determine if target requires login; request temporary session from Vault if needed.

3. **Launch Browser Context:** Initialize headless Chromium instance with isolated storage state.

4. **Navigate to Target:** Direct Web Navigator to load page and wait for `networkidle` state.

5. **Execute Interaction:** Handle cookie banners, modal dismissals, or necessary pagination clicks.

6. **Extract Data:** Task Data Extractor with querying selectors and normalizing extracted text.

7. **Capture Visual State:** Instruct Visual Inspector to capture full-page screenshot.

8. **Clean Up Session:** Close browser context immediately to release Mac RAM and CPU resources.

9. **Validate Data Integrity:** Verify extracted records against expected schema.

10. **Deliver Browser Report:** Submit structured dataset and screenshot path to Coordinator.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:browser_navigate`, `cap:data_extract`, `cap:source_verify`
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
    "final_url": {
      "type": "string"
    },
    "extracted_data": {
      "type": "object"
    },
    "screenshot_path": {
      "type": "string"
    }
  }
}
```
