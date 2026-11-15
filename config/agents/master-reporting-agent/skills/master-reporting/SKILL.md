---
name: master-reporting
description: "Compiles executive deliverables, synthesizes cross-departmental findings, audits immutable execution trails, and analyzes operational velocity."
agent_id: master-reporting-agent
slash_command: /master-reporting
version: 2.0.0
capabilities: ['cap:reporting_compile', 'cap:source_verify']
inputs:
  task_id:
    type: string
    description: "Target completed task ID"
    required: true
  format:
    type: string
    description: "executive_markdown, audit_trail, retrospective"
    required: false
outputs:
  schema: {"type": "object", "properties": {"report_markdown": {"type": "string"}, "deliverable_path": {"type": "string"}, "summary_metrics": {"type": "object"}}}
---

# Skill: Master Reporting Agent (/master-reporting)

## 1. Purpose
The `master-reporting` skill operationalizes the core capabilities of the `Master Reporting Agent` (`master-reporting-agent`). It provides a standardized, repeatable procedure for executing chief executive reporter, audit synthesizer, and performance analyst tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/master-reporting`.
- The Coordinator assigns a DAG plan step requiring chief executive reporter, audit synthesizer, and performance analyst.
- An operational objective involves Compiling comprehensive executive summaries from multi-agent task outputs, Synthesizing technical findings into clear, actionable business deliverables.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never fabricate metrics, task completion claims, or benchmark numbers, Never disclose unencrypted passwords, API keys, or private tokens in reports).

---

## 4. Step-by-Step Procedure

1. **Ingest Reporting Request:** Ingest `task_id` and load completed plan steps from SQLite.

2. **Query Execution Trail:** Load all related events from `execution_events` and `tasks` tables.

3. **Task Executive Summarizer:** Direct specialist to draft high-level executive narrative and takeaways.

4. **Task Audit Compiler:** Direct specialist to compile step execution table with exact timestamps.

5. **Task Retrospective Analyst:** Direct specialist to compute duration, tool calls, and bottlenecks.

6. **Synthesize Deliverable Sections:** Merge narrative, audit tables, and optimization recommendations.

7. **Audit for Secrets:** Scan synthesized markdown to guarantee zero credential exposure.

8. **Format Markdown Document:** Apply GitHub-flavored styling, callouts, and clean headings.

9. **Write to Disk:** Save finalized report to `logs/deliverable_<task_id>.md`.

10. **Deliver Final Artifact:** Submit completed deliverable path to Workforce Owner and Coordinator.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:reporting_compile`, `cap:source_verify`
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
    "report_markdown": {
      "type": "string"
    },
    "deliverable_path": {
      "type": "string"
    },
    "summary_metrics": {
      "type": "object"
    }
  }
}
```
