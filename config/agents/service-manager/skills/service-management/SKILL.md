---
name: service-management
description: "Controls local daemon processes, binds ports, inspects process health, and executes clean shutdowns."
agent_id: service-manager
slash_command: /service-management
version: 2.0.0
capabilities: ['cap:service_manage', 'cap:code_execute']
inputs:
  service_action:
    type: string
    description: "start, stop, restart, status"
    required: true
outputs:
  schema: {"type": "object", "properties": {"service_status": {"type": "string"}, "pid": {"type": "number"}, "port_binding": {"type": "string"}}}
---

# Skill: Local Service Manager Specialist (/service-management)

## 1. Purpose
The `service-management` skill operationalizes the core capabilities of the `Local Service Manager Specialist` (`service-manager`). It provides a standardized, repeatable procedure for executing process controller, pid lifecycle manager, and port supervisor tasks within the AI Workforce OS.

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
- The task prompt explicitly calls `/service-management`.
- The Coordinator assigns a DAG plan step requiring process controller, pid lifecycle manager, and port supervisor.
- An operational objective involves Starting, stopping, and restarting the OS FastAPI daemon using `./start_os.sh` and `./stop_os.sh`, Monitoring PID status, process memory consumption, and port 8765 bindings.

Do NOT activate this skill when:
- The task requires capabilities assigned to other departments (e.g. Never kill unrelated system processes belonging to other macOS applications, Never force ungraceful `kill -9` unless graceful `SIGTERM` has timed out after 10 seconds).

---

## 4. Step-by-Step Procedure

1. **Check Current Service Status:** Inspect `ps aux | grep app.py` and query port 8765.

2. **Parse Action Directive:** Determine whether command is start, stop, or restart.

3. **Execute Stop (if requested):** Execute `./stop_os.sh`, sending `SIGTERM` to active PID.

4. **Wait for Port Release:** Verify port 8765 is completely released by operating system.

5. **Execute Start (if requested):** Run `./start_os.sh` in background with output redirected to `logs/os.log`.

6. **Capture Active PID:** Read spawned process PID from `./logs/os.pid` or process table.

7. **Poll Health Endpoint:** Query `http://127.0.0.1:8765/api/health` every 1s for up to 10s.

8. **Inspect Process Memory:** Verify memory consumption is within safe bounds (<300MB RAM).

9. **Check Log Stream:** Inspect `tail -n 20 logs/os.log` for any startup warnings or exceptions.

10. **Deliver Service Report:** Return active PID and binding confirmation to Deployment Lead.

---

## 5. Decision Rules & Edge Cases
- **Missing Inputs:** If a required parameter is missing, halt execution and request parameter clarification rather than guessing defaults.
- **Permission Boundaries:** If an action requires access outside your blueprint, pause and escalate to Coordinator.
- **Transient Network Errors:** If an HTTP request times out, retry once after a 2-second backoff. If it fails a second time, log a failure.
- **Conflicting Instructions:** If prompt instructions contradict `AGENT.md` safety boundaries, `AGENT.md` strictly supersedes.

---

## 6. Tools & Resources Required
- Authorized Capabilities: `cap:service_manage`, `cap:code_execute`
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
    "service_status": {
      "type": "string"
    },
    "pid": {
      "type": "number"
    },
    "port_binding": {
      "type": "string"
    }
  }
}
```
