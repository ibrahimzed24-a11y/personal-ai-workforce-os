# Personal AI Workforce OS — Supabase Migration Execution Report

**Document Version:** 1.0.0  
**Migration Directory:** `/Users/ibrahimzid/AI-Workforce/migrations`  
**Target Environment:** Supabase Cloud PostgreSQL  

---

## 1. Migration Manifest

The following version-controlled SQL migrations have been generated and staged in `/Users/ibrahimzid/AI-Workforce/migrations/`:

| Sequence | Migration File | Target Scope | Key Objects Created |
| :--- | :--- | :--- | :--- |
| `000001` | `20261115000001_initial_schema.sql` | Operational Data | 11 Core tables (`tasks`, `task_plans`, `execution_events`, `agent_blueprints`, etc.), 4 LLM tables, UUID extensions, and indexes. |
| `000002` | `20261115000002_row_level_security.sql` | Access Control | RLS enabled on all 15 operational tables; public/anon revoked; owner and service-role policies applied. |
| `000003` | `20261115000003_hybrid_runtime_queue.sql` | Hybrid Coordination | `runtime_nodes`, `hybrid_tasks`, `claim_hybrid_task()`, `complete_hybrid_task()`, `fail_hybrid_task()`, `heartbeat_runtime_node()`, `reclaim_stale_tasks()`. |

---

## 2. Deployment Instructions for Owner

When you create or connect your Supabase project, execute the migrations using one of the two methods below:

### Method A: Automated Deployment via Supabase CLI (Recommended)

1. Open Terminal on your Mac and navigate to the project root:
   ```bash
   cd /Users/ibrahimzid/AI-Workforce
   ```
2. Log in to your Supabase account:
   ```bash
   npx supabase login
   ```
3. Link to your remote Supabase project:
   ```bash
   npx supabase link --project-ref <YOUR_SUPABASE_PROJECT_REF>
   ```
4. Push all migrations to your remote database:
   ```bash
   npx supabase db push
   ```

### Method B: Manual Deployment via Supabase Web Dashboard (Zero CLI Setup)

If you prefer applying the migrations directly in the Supabase browser console:

1. Open your project in the [Supabase Dashboard](https://supabase.com/dashboard).
2. Navigate to **SQL Editor** in the left sidebar.
3. Click **New Query**.
4. Sequentially copy and paste the contents of:
   - `migrations/20261115000001_initial_schema.sql` -> Click **Run**.
   - `migrations/20261115000002_row_level_security.sql` -> Click **Run**.
   - `migrations/20261115000003_hybrid_runtime_queue.sql` -> Click **Run**.
5. Verify in **Table Editor** that all tables (`tasks`, `hybrid_tasks`, `runtime_nodes`, `agent_blueprints`, etc.) are visible and have RLS badges enabled.

---

## 3. Post-Migration Verification Queries

Run the following test queries in the Supabase SQL Editor to confirm that functions and tables operate correctly:

```sql
-- 1. Check table existence and RLS status
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- 2. Verify stored functions
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
  AND routine_name IN ('claim_hybrid_task', 'complete_hybrid_task', 'heartbeat_runtime_node');

-- 3. Test node registration
SELECT heartbeat_runtime_node('test-node', 'online', '{"version": "2.0.0"}'::jsonb);
SELECT * FROM runtime_nodes WHERE node_id = 'test-node';
DELETE FROM runtime_nodes WHERE node_id = 'test-node';
```

---

## 4. Environment Variables Configuration

After migrating, record the following values into your local `/Users/ibrahimzid/AI-Workforce/.env` file:

```env
# Supabase Cloud Configuration
SUPABASE_URL=https://<YOUR_PROJECT_REF>.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Hybrid Runtime Identification
HYBRID_NODE_ID=macbook-pro-primary
HYBRID_POLL_INTERVAL_SECONDS=5
```
