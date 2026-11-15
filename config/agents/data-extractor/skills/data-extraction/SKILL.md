---
name: data-extraction
description: "Parses HTML DOM trees, extracts target text and tabular data, and normalizes into structured JSON."
agent_id: data-extractor
slash_command: /data-extraction
version: 2.0.0
capabilities: ['cap:data_extract', 'cap:data_cleanse']
inputs:
  target_selectors:
    type: object
    description: "CSS selectors for data fields"
    required: true
outputs:
  schema: {"type": "object", "properties": {"records": {"type": "array"}, "record_count": {"type": "number"}}}
---

# Skill: Web Data Extractor Specialist (/data-extraction)

## 1. Purpose
The `data-extraction` skill operationalizes the core capabilities of the `Web Data Extractor Specialist` (`data-extractor`). It provides a standardized, repeatable procedure for executing dom parser, xpath/css query specialist, and data cleaner tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/data-extraction`.
- The Coordinator assigns a DAG plan step requiring dom parser, xpath/css query specialist, and data cleaner.
- An operational objective involves Authoring robust CSS selectors and XPath expressions resilient to minor website redesigns, Extracting tabular, list, and article content from rendered web pages.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never execute browser navigation directly (uses page handle provided by Navigator), Never inject malicious JavaScript into foreign web pages).

---

## 4. Step-by-Step Procedure

1. **Ingest Extraction Rules:** Parse target fields, CSS selectors, and expected types.

2. **Query DOM Elements:** Execute `page.query_selector_all()` against target selectors.

3. **Extract Field Values:** Pull `textContent`, `href`, or custom attributes from nodes.

4. **Handle Missing Elements:** Default absent optional fields to `None` without crashing.

5. **Cleanse Raw Strings:** Strip excessive whitespace, HTML entities (`&amp;`), and newline artifacts.

6. **Deduplicate Records:** Remove identical rows based on unique key identifier.

7. **Cast Data Types:** Convert numbers, dates, and currency strings into standard typed formats.

8. **Validate Extraction Quality:** Check that record count matches expectations (>0 records).

9. **Serialize to JSON:** Format final dataset into clean, indented JSON.

10. **Deliver Dataset:** Submit structured JSON to Browser Use Agent.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:data_extract`, `cap:data_cleanse`
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
    "records": {
      "type": "array"
    },
    "record_count": {
      "type": "number"
    }
  }
}
```
