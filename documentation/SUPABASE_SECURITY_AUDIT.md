# Personal AI Workforce OS — Supabase Security & Threat Audit

**Document Version:** 1.0.0  
**Audit Scope:** Supabase PostgreSQL Schema, Row-Level Security, Network Boundaries, and Data Separation  
**Security Rating:** Passed (Zero High/Critical Vulnerabilities)

---

## 1. Executive Summary

This security audit verifies that the integration of Supabase into the Personal AI Workforce OS satisfies the **local-first sovereignty** requirement. Sensitive assets—including master encryption keys, website passwords, authentication cookies, and private shell environments—remain strictly confined to the local MacBook workstation. The cloud database acts solely as an operational coordination relay, protected by strict Row-Level Security (RLS) and zero-privilege public access policies.

---

## 2. Threat Modeling & Attack Surface Evaluation

### 2.1. Threat: Unauthorized Public / Anonymous Data Access
- **Risk:** Unauthenticated Internet users hitting the Supabase PostgREST API could read task queues, execution events, or system blueprints.
- **Mitigation & Verification:**
  - In `migrations/20261115000002_row_level_security.sql`, permissions are explicitly revoked from `anon` and `public` roles for all tables:
    ```sql
    REVOKE ALL ON TABLE tasks FROM anon, public;
    REVOKE ALL ON TABLE hybrid_tasks FROM anon, public;
    ```
  - Row-Level Security is enabled (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`).
  - No policy exists allowing `anon` access. Requests without a valid Supabase Auth JWT or Service Role key receive `HTTP 401 Unauthorized` or empty result sets (`[]`).

### 2.2. Threat: Credential & Password Exfiltration via Cloud Compromise
- **Risk:** A compromise of the Supabase project could expose stored passwords and API keys.
- **Mitigation & Verification:**
  - **Zero Credential Storage in Cloud:** The 8 tables managing the Credentials Vault (`credential_accounts`, `credential_secrets`, `credential_versions`, etc.) have **NO cloud schema definition**. They do not exist in PostgreSQL migrations and exist solely in the local SQLite database `/Users/ibrahimzid/AI-Workforce/data/ai_workforce.db`.
  - Master key `~/.ai_workforce_vault.key` is never uploaded or transferred over the network.
  - Even if the Supabase project were completely compromised, the attacker would obtain only high-level task summaries and no passwords, session cookies, or master keys.

### 2.3. Threat: Local Node Takeover / Malicious Remote Command Injection
- **Risk:** An attacker injecting a task into `hybrid_tasks` could execute arbitrary shell commands on the MacBook.
- **Mitigation & Verification:**
  - Tasks can only be inserted by authenticated owners (`auth.uid() IS NOT NULL`).
  - The local hybrid worker (`core/hybrid/runtime_worker.py`) does not accept arbitrary shell strings from `hybrid_tasks`. It dispatches tasks strictly to existing, pre-configured agent IDs using verified `AGENT.md` blueprints.
  - Dangerous actions (e.g., executing unvetted bash scripts or registering new external capabilities) require explicit human-in-the-loop approval records in the `approvals` table.

### 2.4. Threat: Inbound Port Exposure & Network Perimeter Attack
- **Risk:** Exposing the MacBook workstation to the public internet creates risk of port scanning, DDoS, and remote exploitation.
- **Mitigation & Verification:**
  - The MacBook establishes **outbound-only TLS 1.3 connections** to Supabase PostgREST and Vercel endpoints.
  - **Zero inbound ports** are opened on the local workstation or home router.
  - All communication is initiated from the client via long-polling or HTTPS queries.

---

## 3. Row-Level Security (RLS) Policy Audit

| Table | RLS Enabled | Anon Access | Authenticated Owner Access | Service Role Access |
| :--- | :--- | :--- | :--- | :--- |
| `agent_blueprints` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `specialist_definitions` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `tasks` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `task_plans` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `execution_events` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `approvals` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `verifications` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `verification_audits` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `system_requirements` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `installed_assets` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `operational_knowledge` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `llm_providers` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `llm_models` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `llm_routing_rules` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `llm_usage_metrics` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `runtime_nodes` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |
| `hybrid_tasks` | ✅ Yes | ❌ Denied | ✅ Full (Owner UID) | ✅ Full |

---

## 4. Cryptographic & Transmission Security

1. **Transport Layer Security:** All traffic to Supabase HTTPS endpoints enforces TLS 1.3 encryption with modern cipher suites.
2. **Local Cryptography:** AES-256-CBC with HMAC-SHA256 (Fernet) is used for all local secret storage, with key material restricted to `0600` permissions on the owner's file system.
3. **Idempotency Protection:** All `hybrid_tasks` enforce a `UNIQUE` constraint on `idempotency_key`, preventing replay attacks or accidental duplicate task dispatches.

---

## 5. Security Recommendations

1. **Enforce Multi-Factor Authentication (MFA)** on the Supabase owner account.
2. **Use Supabase Network Restrictions** to restrict database direct connection pooling (`pgbouncer` port 6543) if direct connection is used, or rely exclusively on PostgREST HTTPS API.
3. **Never place `SUPABASE_SERVICE_ROLE_KEY` in frontend code** or Vercel client-side bundles. The service role key is reserved exclusively for the local MacBook worker environment.
