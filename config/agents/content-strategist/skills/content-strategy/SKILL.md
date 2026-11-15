---
name: content-strategy
description: "Authors high-converting landing page copy, technical blog articles, product narratives, and thought-leadership content."
agent_id: content-strategist
slash_command: /content-strategy
version: 2.0.0
capabilities: ['cap:content_author', 'cap:research_gather']
inputs:
  topic:
    type: string
    description: "Subject matter or asset title"
    required: true
  format:
    type: string
    description: "article, landing_page, email_sequence, whitepaper"
    required: true
outputs:
  schema: {"type": "object", "properties": {"content_markdown": {"type": "string"}, "word_count": {"type": "number"}, "key_takeaways": {"type": "array"}}}
---

# Skill: Content Strategist Specialist (/content-strategy)

## 1. Purpose
The `content-strategy` skill operationalizes the core capabilities of the `Content Strategist Specialist` (`content-strategist`). It provides a standardized, repeatable procedure for executing editorial director, copywriter, and narrative architect tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/content-strategy`.
- The Coordinator assigns a DAG plan step requiring editorial director, copywriter, and narrative architect.
- An operational objective involves Writing persuasive, educational, and SEO-optimized long-form content and copy, Developing topic clusters and structured editorial content roadmaps.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never bypass brand voice guidelines or regulatory compliance checks, Never publish unverified or hallucinated product capability claims).

---

## 4. Step-by-Step Procedure

1. **Analyze Brief:** Ingest target topic, format, target persona, and primary keywords.

2. **Conduct Outline Research:** Review high-ranking search results and authoritative domain literature.

3. **Draft Narrative Structure:** Create hook, problem statement, solution framework, and call to action.

4. **Write Hero / Hook Section:** Craft engaging opening designed to capture immediate attention.

5. **Develop Body Sections:** Write detailed, evidence-backed educational or persuasive arguments.

6. **Integrate Visual Cues:** Add markdown tables, callout boxes, and diagram placeholders.

7. **Optimize for SEO:** Weave primary and semantic LSI keywords naturally without keyword stuffing.

8. **Refine Tone & Clarity:** Eliminate passive voice, buzzwords, and vague generalizations.

9. **Check Plagiarism & Originality:** Verify zero duplicate content against source citations.

10. **Deliver Content Draft:** Submit completed markdown asset to Marketing Lead and Brand Compliance.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:content_author`, `cap:research_gather`
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
    "content_markdown": {
      "type": "string"
    },
    "word_count": {
      "type": "number"
    },
    "key_takeaways": {
      "type": "array"
    }
  }
}
```
