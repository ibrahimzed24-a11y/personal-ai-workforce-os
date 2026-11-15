# Personal AI Workforce OS — Infrastructure Operations Standard Operating Procedure (SOP)

**Document Version:** 1.0.0  
**Effective Date:** 2026-11-15  
**Audience:** System Owner & Operations  

---

## 1. System Architecture Quick Reference

| Component | Host / Runtime | Responsibility | Network Binding |
| :--- | :--- | :--- | :--- |
| **Local OS Daemon** | MacBook Pro (`127.0.0.1:8765`) | Local orchestrator, local UI, agent execution | Localhost only |
| **Hybrid Runtime Worker** | MacBook Pro (Python service) | Polls Supabase outbound, claims tasks, runs tools | Outbound HTTPS only |
| **Cloud PostgreSQL & Auth** | Supabase Cloud | Task queue, operational metadata, RLS | Inbound TLS 1.3 via PostgREST |
| **Cloud Web Dashboard** | Vercel Serverless | Mobile/remote dashboard, task submissions | Public HTTPS with RLS |
| **Credentials Vault** | MacBook Pro (`data/ai_workforce.db`) | AES-256 encrypted passwords & website logins | Local filesystem only (`0600`) |

---

## 2. Daily Operations & Routine Management

### 2.1. Starting the Local Services

To run the local OS daemon and the hybrid worker concurrently:

```bash
cd /Users/ibrahimzid/AI-Workforce

# 1. Start the local OS Daemon (Background)
nohup /Users/ibrahimzid/.local/bin/uv run uvicorn core.app:app --host 127.0.0.1 --port 8765 > logs/os.log 2>&1 &

# 2. Start the Hybrid Runtime Worker
nohup /Users/ibrahimzid/AI-Workforce/.venv/bin/python core/hybrid/runtime_worker.py --interval 5.0 > logs/hybrid_worker.log 2>&1 &
```

### 2.2. Checking Operational Status

```bash
# Check running processes
ps aux | grep -E "uvicorn|runtime_worker"

# Verify local daemon health
curl -s http://127.0.0.1:8765/api/agents | head -n 20

# Inspect worker logs
tail -f /Users/ibrahimzid/AI-Workforce/logs/hybrid_worker.log
```

### 2.3. Stopping Services

```bash
# Gracefully terminate daemon and worker
pkill -f "uvicorn core.app:app"
pkill -f "runtime_worker.py"
```

---

## 3. Credentials & Vault Management

### 3.1. Adding Website Logins
Website logins must **never** be entered into cloud settings or unencrypted files. Always register them through the local API or credentials manager:
```bash
# Example: Adding via local python script / credentials manager
/Users/ibrahimzid/AI-Workforce/.venv/bin/python -c "
import asyncio
from core.security.manager import CredentialsManager
creds = CredentialsManager()
asyncio.run(creds.create_account(
    name='GitHub Production',
    url='https://github.com',
    username='my_user',
    password='my_secure_password',
    category='development'
))
"
```

### 3.2. Vault Backup SOP
The vault encryption key is located at `~/.ai_workforce_vault.key`.
- Keep an offline physical backup (e.g., encrypted USB or 1Password) of this key.
- Never commit `~/.ai_workforce_vault.key` or `data/ai_workforce.db` to Git.

---

## 4. Cloud Task & Hybrid Queue Maintenance

### 4.1. Monitoring Queue Health
In the Supabase SQL Editor:
```sql
-- Check count of tasks by status
SELECT status, count(*) 
FROM hybrid_tasks 
GROUP BY status;

-- Check active execution nodes
SELECT node_id, status, last_heartbeat 
FROM runtime_nodes;
```

### 4.2. Handling Stale Leases (Node Crash or Sleep)
If the MacBook was closed during task execution, run the maintenance function in Supabase SQL Editor:
```sql
SELECT reclaim_stale_tasks();
```
This automatically resets tasks whose leases expired back to `waiting_for_local_runtime`.

---

## 5. Offline & Traveling Workstation Scenarios

When operating with the MacBook offline or traveling:
1. **Cloud Queue Buffering:** Tasks submitted through Vercel remain queued safely in Supabase.
2. **Local Autonomous Execution:** The local OS at `http://127.0.0.1:8765` functions 100% offline using local Ollama models and cached agent blueprints.
3. **Re-connection:** Once internet is restored, the hybrid worker automatically re-establishes its outbound connection and drains queued tasks.

---

## 6. Disaster Recovery & Rollback

### 6.1. Restoring from Consolidated Project Backup
If files are corrupted or accidentally deleted:
```bash
cd /Users/ibrahimzid/AI-Workforce
unzip -o backups/Personal-AI-Workforce-OS-Project.zip
```

### 6.2. Re-applying Database Migrations
If Supabase database state needs to be re-initialized:
```bash
cd /Users/ibrahimzid/AI-Workforce
npx supabase db push
```
