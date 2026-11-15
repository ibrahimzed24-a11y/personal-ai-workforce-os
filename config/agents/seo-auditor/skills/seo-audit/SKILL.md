---
name: seo-audit
description: "Audits DOM structures, metadata, robots.txt, sitemaps, structured data, Core Web Vitals, and indexability signals."
agent_id: seo-auditor
slash_command: /seo-audit
version: 2.0.0
capabilities: ['cap:data_extract', 'cap:source_verify']
inputs:
  url_or_domain:
    type: string
    description: "Target website URL"
    required: true
outputs:
  schema: {"type": "object", "properties": {"health_score": {"type": "number"}, "critical_issues": {"type": "array"}, "recommendations": {"type": "array"}}}
---

# Skill: Technical SEO Auditor Specialist (/seo-audit)

## 1. Purpose
The `seo-audit` skill operationalizes the core capabilities of the `Technical SEO Auditor Specialist` (`seo-auditor`). It provides a standardized, repeatable procedure for executing on-page, technical seo, and crawlability auditor tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/seo-audit`.
- The Coordinator assigns a DAG plan step requiring on-page, technical seo, and crawlability auditor.
- An operational objective involves Auditing meta titles, descriptions, canonical tags, and header hierarchies (H1-H6), Checking robots.txt directives, XML sitemaps, and HTTP status codes (301, 404, 500).

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never modify server DNS or Apache/Nginx web server configuration files directly, Never purchase backlinks or subscribe to paid indexing services).

---

## 4. Step-by-Step Procedure

1. **URL Validation:** Ingest target URL and confirm HTTP/HTTPS accessibility.

2. **Crawl Inspection:** Check robots.txt and sitemap.xml for indexing blockers.

3. **DOM Metadata Sweep:** Inspect `<title>`, `<meta description>`, and `<link rel='canonical'>` tags.

4. **Heading Hierarchy Audit:** Verify single H1 tag and logical descending H2/H3 structure.

5. **Structured Data Validation:** Parse JSON-LD blocks and validate against Schema.org specifications.

6. **Image & Asset Audit:** Identify unoptimized images missing `alt` attributes or modern WebP/AVIF formats.

7. **Internal Linking Check:** Analyze anchor text distribution and identify broken internal links.

8. **Core Web Vitals Check:** Review simulated LCP, FID, and CLS performance factors.

9. **Compile Defect Matrix:** Categorize issues into Critical, Warning, and Optimization Notice.

10. **Generate Technical Audit Report:** Output deliverable with explicit remediation code snippets.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:data_extract`, `cap:source_verify`
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
    "health_score": {
      "type": "number"
    },
    "critical_issues": {
      "type": "array"
    },
    "recommendations": {
      "type": "array"
    }
  }
}
```
