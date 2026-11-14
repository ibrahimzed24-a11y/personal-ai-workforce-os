---
name: Post-Implementation Verification & Evidence Audit
id: post-implementation-verification
category: quality_assurance / system_integrity
version: 1.0.0
description: Standardized, evidence-driven mechanism for independently verifying implementations, changes, installations, integrations, agent executions, system updates, and operational workflows.
author: AI Workforce OS Core Architecture Team
tags:
  - verification
  - quality_assurance
  - evidence_audit
  - security_audit
  - testing
target_agents:
  - coordinator
  - master-reporting-agent
  - system-integrator-update-agent
  - deployment-agent
  - software-engineer
---

# Post-Implementation Verification & Evidence Audit Core Skill

## 1. Objective & Purpose
The **Post-Implementation Verification & Evidence Audit** skill provides the AI Workforce OS with an independent, repeatable, evidence-driven framework to verify that code changes, agent blueprints, external capabilities, and deployment workflows are actually functional, properly permissioned, and backed by verifiable test executions.

> [!IMPORTANT]
> **Core Principle:** The AI Workforce OS must be able to prove what it has built with reproducible evidence, not merely describe what it believes it has built. The existence of a file, class, function, or route must never be confused with a functioning implementation.

---

## 2. Standardized Verification Profiles

The skill dynamically scales verification depth according to risk and scope:

| Profile | Target Changes | Included Checks | Evidence Requirements |
| :--- | :--- | :--- | :--- |
| **`lightweight`** | Documentation, minor configs, isolated prompt updates. | AST parsing, markdown lint, path resolution, credential leak scan. | Clean syntax, zero secret leaks, verified paths. |
| **`standard`** | New skills, tools, agent changes, ordinary features, workflows. | Lightweight + mock/placeholder detection, automated test execution, basic runtime permission probing. | Real test execution exit code 0, no unapproved mocks, zero hardcoded secrets. |
| **`comprehensive`** | Core architecture changes, DB migrations, runtimes, release builds. | Standard + deep test suites, SQLite WAL persistence, state restart recovery, negative security probing. | Full test suite logs, database integrity proof, deliverable file checksums. |
| **`security_audit`** | Vault changes, auth/authz, permissions, sensitive data, network boundaries. | Comprehensive + vault key permissions (`0600`), negative authorization access rejection, token lifecycle assertion. | 100% negative test assertions passed, zero unencrypted secrets at rest or in git. |

---

## 3. Authoritative Implementation Statuses

Every evaluated requirement and overall audit is classified into one of the following authoritative states:

- **`VERIFIED`**: Implemented and supported by sufficient successful evidence (real passing tests, exit code 0, verified artifacts).
- **`IMPLEMENTED_NOT_VERIFIED`**: Source code exists on disk, but no automated test executed or evidence is unavailable.
- **`PARTIALLY_IMPLEMENTED`**: Only some required functionality exists, or partial test assertions passed.
- **`MOCKED_OR_SIMULATED`**: Functionality relies on mocks, placeholders, stubs, or hardcoded simulated return values.
- **`NOT_IMPLEMENTED`**: Required capability or component does not exist.
- **`BROKEN`**: Implementation exists, but executing its test or functional probe raises an error, exception, or non-zero exit code.
- **`BLOCKED`**: Verification cannot proceed because of a documented dependency, permission restriction, or network blockage.

### Security Severity Classification:
- **`CRITICAL`**: Remote execution risk, arbitrary command execution without sandbox, leaking plaintext secrets, hardcoded production keys.
- **`HIGH`**: Broken authorization, privilege escalation, bypass of approval gates, directory traversal escaping workspace.
- **`MEDIUM`**: Overly permissive file permissions (e.g. non-0600 vault keys), missing rate limits, unencrypted sensitive caches.
- **`LOW`**: Missing header annotations, informational security warnings.
- **`INFORMATIONAL`**: Security best practice suggestions.

---

## 4. Evidence Schema & Artifact Storage

Every audit run produces:
1. **Durable Database Record:** Stored in the SQLite WAL table `verification_audits`.
2. **Detailed JSON Evidence File:** Saved to `~/AI-Workforce/logs/evidence/audit_<id>.json`.
3. **Traceability:** Bound to the specific Git commit SHA (`target_version`) and executing agent.

```json
{
  "id": "audit_8fa31b2c",
  "task_id": "task_1a2b3c4d",
  "target_component": "skill:post-implementation-verification",
  "target_version": "a3780c11d42e5cbe995b135b8859fd45179a0705",
  "profile": "standard",
  "status": "VERIFIED",
  "initiated_by": "system-integrator-update-agent",
  "requirements_evaluated": [
    {
      "requirement_id": "req_functional",
      "title": "Functional Implementation",
      "status": "VERIFIED",
      "evidence_ref": "Passed 8 automated test assertions with exit code 0."
    }
  ],
  "tests_executed": [
    {
      "command": "~/.local/bin/uv run python core/tests/test_verification_skill.py",
      "exit_code": 0,
      "status": "passed",
      "duration_sec": 1.42,
      "stdout_preview": "✓ All test scenarios verified..."
    }
  ],
  "security_findings": [],
  "evidence_summary": "### Post-Implementation Verification Report...",
  "evidence_artifact_path": "/Users/ibrahimzid/AI-Workforce/logs/evidence/audit_8fa31b2c.json",
  "created_at": "2026-11-15T00:27:00Z",
  "completed_at": "2026-11-15T00:27:02Z"
}
```

---

## 5. OS Integration & Agent Invocations

### A. Coordinator Agent
- Plans tasks and mandates verification steps for code, skills, or deployment changes.
- Selects the verification profile based on task risk.
- Prevents tasks from reaching `completed` status if verification is failed or blocked.

### B. Independent Verifier
- Executes independent evaluation without conflict of interest.
- Inspects concrete evidence (commands, exit codes, output logs) rather than relying on agent self-reporting.
- Challenges unverified claims and downgrades unverified implementations to `IMPLEMENTED_NOT_VERIFIED`.

### C. Master Reporting Agent
- Synthesizes verification audit metrics into executive deliverables.
- Embeds clickable links to evidence artifacts.
- Highlights open remediation items and security findings.

### D. System Integrator & Update Agent
- Automatically invokes `post-implementation-verification` immediately following any incoming asset installation (skills, tools, packages, blueprints).
- The asset is marked `ACTIVE` only after verification achieves `VERIFIED`.

### E. Deployment Agent
- Requires `comprehensive` verification before promoting releases or verifying service daemons.
- Retains existing approval requirements for production configuration or rollbacks.

---

## 6. Loop Prevention Policy
To avoid infinite execution cascades:
- The verification engine maintains an in-memory execution lock (`_active_audits`).
- Verification reports, evidence artifacts, and audit database updates do **not** trigger new audits.
- Audits initiated with target components matching `audit_*` are rejected by the recursion guard.

---

## 7. Manual Invocation Instructions

### Via REST API:
```bash
curl -X POST http://127.0.0.1:8765/api/verification/audit \
  -H "Content-Type: application/json" \
  -d '{
    "target_component": "core/security",
    "profile": "security_audit",
    "initiated_by": "owner"
  }'
```

### Via Python Engine:
```python
import asyncio
from core.verification import PostImplementationVerificationEngine, VerificationProfile

async def verify():
    engine = PostImplementationVerificationEngine()
    result = await engine.run_audit(
        target_component="skill:post-implementation-verification",
        profile=VerificationProfile.STANDARD,
        initiated_by="coordinator"
    )
    print("Verification Result:", result["status"])

asyncio.run(verify())
```
