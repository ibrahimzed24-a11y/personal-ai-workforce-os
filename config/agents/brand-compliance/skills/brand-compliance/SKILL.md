---
name: brand-compliance
description: "Audits all marketing assets against brand guidelines, substantiates claims, and ensures advertising compliance."
agent_id: brand-compliance
slash_command: /brand-compliance
version: 2.0.0
capabilities: ['cap:source_verify', 'cap:security_audit']
inputs:
  draft_content:
    type: string
    description: "Markdown copy to audit"
    required: true
  asset_type:
    type: string
    description: "email, landing_page, ad_copy, press_release"
    required: true
outputs:
  schema: {"type": "object", "properties": {"compliance_status": {"type": "string", "enum": ["APPROVED", "REJECTED", "REVISIONS_REQUIRED"]}, "violations": {"type": "array"}, "required_edits": {"type": "array"}}}
---

# Skill: Brand Compliance Specialist (/brand-compliance)

## 1. Purpose
The `brand-compliance` skill operationalizes the core capabilities of the `Brand Compliance Specialist` (`brand-compliance`). It provides a standardized, repeatable procedure for executing tone of voice, claim substantiation, and regulatory auditor tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/brand-compliance`.
- The Coordinator assigns a DAG plan step requiring tone of voice, claim substantiation, and regulatory auditor.
- An operational objective involves Auditing all marketing copy against brand tone, voice, and vocabulary rules, Ensuring strict factual substantiation for performance, benchmark, or product claims.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never create original marketing copy (audits copy produced by others), Never approve unsubstantiated medical, financial, or guaranteed earnings claims).

---

## 4. Step-by-Step Procedure

1. **Ingest Draft Asset:** Receive draft copy from Content Strategist or Campaign Planner.

2. **Check Tone Alignment:** Evaluate text against brand voice (professional, empirical, direct, humble).

3. **Claim Verification:** Identify any superlative or factual claim (e.g. 'fastest', '#1', 'guaranteed').

4. **Demand Substantiation:** Require verifiable citations or benchmark proofs for all claims.

5. **Scan Regulatory Checkpoints:** Verify presence of privacy policy links, company address, and opt-out links.

6. **Filter Prohibited Phrases:** Flag hype terms ('revolutionary', 'miracle', 'foolproof').

7. **Review Disclaimers:** Check required FTC sponsor disclosures and affiliate transparency.

8. **Compile Violation Report:** List exact line numbers with non-compliant copy and reason.

9. **Issue Decision:** Stamp asset as `APPROVED` or `REVISIONS_REQUIRED`.

10. **Archive Audit Record:** Log compliance verification into SQLite audit table.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:source_verify`, `cap:security_audit`
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
    "compliance_status": {
      "type": "string",
      "enum": [
        "APPROVED",
        "REJECTED",
        "REVISIONS_REQUIRED"
      ]
    },
    "violations": {
      "type": "array"
    },
    "required_edits": {
      "type": "array"
    }
  }
}
```
