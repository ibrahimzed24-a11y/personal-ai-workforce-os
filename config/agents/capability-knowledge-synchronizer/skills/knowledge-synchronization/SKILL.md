---
name: knowledge-synchronization
description: "Maps approved capabilities to authorized agents, updates SKILLS_INDEX.md, AVAILABLE_CAPABILITIES.md, and AGENT_TOOL_ACCESS.json."
agent_id: capability-knowledge-synchronizer
slash_command: /knowledge-synchronization
version: 2.0.0
capabilities: ['cap:file_io', 'cap:reporting_compile']
inputs:
  asset_id:
    type: string
    description: "Installed asset ID to synchronize"
    required: false
outputs:
  schema: {"type": "object", "properties": {"synchronized_files": {"type": "array"}, "skills_indexed_count": {"type": "number"}}}
---

# Skill: Capability & Knowledge Synchronizer Specialist (/knowledge-synchronization)

## 1. Purpose
The `knowledge-synchronization` skill operationalizes the core capabilities of the `Capability & Knowledge Synchronizer Specialist` (`capability-knowledge-synchronizer`). It provides a standardized, repeatable procedure for executing agent capability binding and operational knowledge synchronizer tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/knowledge-synchronization`.
- The Coordinator assigns a DAG plan step requiring agent capability binding and operational knowledge synchronizer.
- An operational objective involves Mapping newly verified tools and skills to authorized agent blueprints, Regenerating `INSTALLED_ASSETS.md` with active asset metadata from SQLite.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never copy asset files or execute installation commands (handled by Package Installer), Never grant tool permissions to agents without blueprint compatibility check).

---

## 4. Step-by-Step Procedure

1. **Query Installed Assets:** Load all active records from `installed_assets` table in SQLite.

2. **Scan Agent Skills:** Traverse all 32 agent directories in `config/agents/*/skills/*/SKILL.md`.

3. **Parse Skill Frontmatter:** Extract `name`, `slash_command`, `version`, and `capabilities`.

4. **Compile SKILLS_INDEX.md:** Generate updated markdown index linking every skill to its agent.

5. **Compile AVAILABLE_CAPABILITIES.md:** Document all active system tools, scripts, and runtime adapters.

6. **Generate AGENT_TOOL_ACCESS.json:** Build JSON map of agent IDs to authorized capabilities.

7. **Audit for Dead Links:** Confirm every referenced file path exists on disk.

8. **Validate JSON Syntax:** Verify `AGENT_TOOL_ACCESS.json` passes strict JSON validation.

9. **Commit Knowledge Updates:** Write updated files to `documentation/knowledge/`.

10. **Broadcast Awareness:** Notify Coordinator that workforce operational knowledge is synchronized.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:file_io`, `cap:reporting_compile`
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
    "synchronized_files": {
      "type": "array"
    },
    "skills_indexed_count": {
      "type": "number"
    }
  }
}
```
