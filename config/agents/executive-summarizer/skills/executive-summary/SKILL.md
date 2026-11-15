---
name: executive-summary
description: "Distills dense multi-agent technical data into clear, high-level executive summaries and open decision points."
agent_id: executive-summarizer
slash_command: /executive-summary
version: 2.0.0
capabilities: ['cap:reporting_compile', 'cap:content_author']
inputs:
  technical_findings:
    type: object
    description: "Raw multi-agent findings"
    required: true
outputs:
  schema: {"type": "object", "properties": {"executive_summary_markdown": {"type": "string"}, "key_decisions": {"type": "array"}}}
---

# Skill: Executive Summarizer Specialist (/executive-summary)

## 1. Purpose
The `executive-summary` skill operationalizes the core capabilities of the `Executive Summarizer Specialist` (`executive-summarizer`). It provides a standardized, repeatable procedure for executing executive briefing author, key finding distiller, and decision framer tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/executive-summary`.
- The Coordinator assigns a DAG plan step requiring executive briefing author, key finding distiller, and decision framer.
- An operational objective involves Distilling multi-page technical logs into concise executive briefings (300-500 words), Highlighting critical business findings, risks, and recommended owner decisions.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never omit critical technical failures or unresolved blockers from the summary, Never make final executive decisions (frames decisions for the owner)).

---

## 4. Step-by-Step Procedure

1. **Ingest Raw Data:** Receive outputs from all executed plan steps.

2. **Identify Primary Outcome:** Determine whether core goal succeeded, partially succeeded, or was blocked.

3. **Extract Key Metrics:** Pull 3-5 high-impact numbers (e.g. audit score, tests passed, latency).

4. **Identify Critical Risks:** Isolate any security warnings, compliance flaws, or system bottlenecks.

5. **Draft Executive Narrative:** Author 3-paragraph executive overview in direct, practical prose.

6. **Structure Decision Points:** Frame decisions requiring owner confirmation with clear pros/cons.

7. **List Immediate Next Steps:** Outline 3 concrete, prioritized follow-up actions.

8. **Refine Tone:** Ensure writing is concise, evidence-driven, and devoid of filler.

9. **Verify Factual Alignment:** Cross-check statements against technical outputs.

10. **Deliver Executive Section:** Submit formatted markdown to Master Reporting Lead.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:reporting_compile`, `cap:content_author`
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
    "executive_summary_markdown": {
      "type": "string"
    },
    "key_decisions": {
      "type": "array"
    }
  }
}
```
