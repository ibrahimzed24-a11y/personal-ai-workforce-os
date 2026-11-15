-- =============================================================================
-- Migration: 20261115000003_hybrid_runtime_queue.sql
-- Description: Hybrid Task Queue, Node Registration, Leases & Atomic Dispatch
-- Enables seamless coordination between Vercel web dashboard and local MacBook worker
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. RUNTIME NODES REGISTRY
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS runtime_nodes (
    node_id TEXT PRIMARY KEY,
    node_name TEXT NOT NULL,
    node_type TEXT NOT NULL DEFAULT 'macbook_workstation',
    capabilities JSONB DEFAULT '["browser_automation", "local_shell", "credentials_vault", "python_runtime"]'::jsonb,
    status TEXT NOT NULL DEFAULT 'offline', -- 'online', 'busy', 'offline', 'paused'
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    current_task_id UUID,
    metadata JSONB DEFAULT '{}'::jsonb,
    registered_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runtime_nodes_status ON runtime_nodes(status);
CREATE INDEX IF NOT EXISTS idx_runtime_nodes_heartbeat ON runtime_nodes(last_heartbeat);

-- -----------------------------------------------------------------------------
-- 2. HYBRID TASKS QUEUE
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS hybrid_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    assigned_agent_id TEXT NOT NULL REFERENCES agent_blueprints(id),
    runtime_target TEXT NOT NULL DEFAULT 'any', -- 'local', 'cloud', 'any'
    required_capabilities JSONB DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'waiting_for_local_runtime', 'claimed', 'running', 'completed', 'failed', 'cancelled'
    priority INTEGER DEFAULT 50, -- 1 highest, 100 lowest
    input_payload JSONB DEFAULT '{}'::jsonb,
    output_result JSONB,
    error_message TEXT,
    claimed_by TEXT REFERENCES runtime_nodes(node_id),
    lease_expires_at TIMESTAMPTZ,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hybrid_tasks_status ON hybrid_tasks(status);
CREATE INDEX IF NOT EXISTS idx_hybrid_tasks_target ON hybrid_tasks(runtime_target);
CREATE INDEX IF NOT EXISTS idx_hybrid_tasks_lease ON hybrid_tasks(lease_expires_at);
CREATE INDEX IF NOT EXISTS idx_hybrid_tasks_priority ON hybrid_tasks(priority ASC, created_at ASC);

-- -----------------------------------------------------------------------------
-- 3. ROW LEVEL SECURITY
-- -----------------------------------------------------------------------------

ALTER TABLE runtime_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE hybrid_tasks ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE runtime_nodes FROM anon, public;
REVOKE ALL ON TABLE hybrid_tasks FROM anon, public;

CREATE POLICY "service_role_runtime_nodes" ON runtime_nodes FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_hybrid_tasks" ON hybrid_tasks FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "authenticated_owner_runtime_nodes" ON runtime_nodes FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_hybrid_tasks" ON hybrid_tasks FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);

-- -----------------------------------------------------------------------------
-- 4. ATOMIC QUEUE FUNCTIONS (FOR UPDATE SKIP LOCKED)
-- -----------------------------------------------------------------------------

-- Atomic lease acquisition for local worker
CREATE OR REPLACE FUNCTION claim_hybrid_task(
    p_node_id TEXT,
    p_lease_seconds INT DEFAULT 300
)
RETURNS TABLE (
    id UUID,
    idempotency_key TEXT,
    title TEXT,
    description TEXT,
    assigned_agent_id TEXT,
    runtime_target TEXT,
    input_payload JSONB,
    attempts INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_task_id UUID;
    v_node_capabilities JSONB;
BEGIN
    -- 1. Fetch claiming node capabilities
    SELECT capabilities INTO v_node_capabilities
    FROM runtime_nodes
    WHERE node_id = p_node_id;

    -- 2. Find and lock next eligible task
    SELECT ht.id INTO v_task_id
    FROM hybrid_tasks ht
    WHERE (
        ht.status IN ('pending', 'waiting_for_local_runtime')
        OR (ht.status IN ('claimed', 'running') AND ht.lease_expires_at < NOW())
    )
    AND ht.attempts < ht.max_attempts
    AND (
        ht.runtime_target IN ('local', 'any')
    )
    ORDER BY ht.priority ASC, ht.created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    -- 3. If no task found, return empty
    IF v_task_id IS NULL THEN
        RETURN;
    END IF;

    -- 4. Mark task as claimed with lease expiration
    UPDATE hybrid_tasks
    SET
        status = 'claimed',
        claimed_by = p_node_id,
        lease_expires_at = NOW() + (p_lease_seconds || ' seconds')::interval,
        attempts = hybrid_tasks.attempts + 1,
        started_at = COALESCE(started_at, NOW()),
        updated_at = NOW()
    WHERE hybrid_tasks.id = v_task_id;

    -- 5. Update node state
    UPDATE runtime_nodes
    SET
        status = 'busy',
        current_task_id = v_task_id,
        last_heartbeat = NOW()
    WHERE runtime_nodes.node_id = p_node_id;

    -- 6. Return task details
    RETURN QUERY
    SELECT
        ht.id,
        ht.idempotency_key,
        ht.title,
        ht.description,
        ht.assigned_agent_id,
        ht.runtime_target,
        ht.input_payload,
        ht.attempts
    FROM hybrid_tasks ht
    WHERE ht.id = v_task_id;
END;
$$;

-- Complete task execution
CREATE OR REPLACE FUNCTION complete_hybrid_task(
    p_task_id UUID,
    p_node_id TEXT,
    p_result JSONB
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE hybrid_tasks
    SET
        status = 'completed',
        output_result = p_result,
        completed_at = NOW(),
        lease_expires_at = NULL,
        updated_at = NOW()
    WHERE id = p_task_id AND claimed_by = p_node_id;

    UPDATE runtime_nodes
    SET
        status = 'online',
        current_task_id = NULL,
        last_heartbeat = NOW()
    WHERE node_id = p_node_id;

    RETURN FOUND;
END;
$$;

-- Fail task execution with optional retry
CREATE OR REPLACE FUNCTION fail_hybrid_task(
    p_task_id UUID,
    p_node_id TEXT,
    p_error TEXT,
    p_retry BOOLEAN DEFAULT TRUE
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_attempts INT;
    v_max INT;
BEGIN
    SELECT attempts, max_attempts INTO v_attempts, v_max
    FROM hybrid_tasks
    WHERE id = p_task_id;

    IF p_retry AND (v_attempts < v_max) THEN
        UPDATE hybrid_tasks
        SET
            status = 'waiting_for_local_runtime',
            error_message = p_error,
            claimed_by = NULL,
            lease_expires_at = NULL,
            updated_at = NOW()
        WHERE id = p_task_id;
    ELSE
        UPDATE hybrid_tasks
        SET
            status = 'failed',
            error_message = p_error,
            completed_at = NOW(),
            lease_expires_at = NULL,
            updated_at = NOW()
        WHERE id = p_task_id;
    END IF;

    UPDATE runtime_nodes
    SET
        status = 'online',
        current_task_id = NULL,
        last_heartbeat = NOW()
    WHERE node_id = p_node_id;

    RETURN TRUE;
END;
$$;

-- Node heartbeat
CREATE OR REPLACE FUNCTION heartbeat_runtime_node(
    p_node_id TEXT,
    p_status TEXT DEFAULT 'online',
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    INSERT INTO runtime_nodes (node_id, node_name, status, last_heartbeat, metadata)
    VALUES (p_node_id, p_node_id, p_status, NOW(), p_metadata)
    ON CONFLICT (node_id) DO UPDATE
    SET
        status = EXCLUDED.status,
        last_heartbeat = NOW(),
        metadata = runtime_nodes.metadata || EXCLUDED.metadata;
    RETURN TRUE;
END;
$$;

-- Maintenance: Reclaim orphaned / stale leases when node dies
CREATE OR REPLACE FUNCTION reclaim_stale_tasks()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_count INT;
BEGIN
    WITH reclaimed AS (
        UPDATE hybrid_tasks
        SET
            status = 'waiting_for_local_runtime',
            claimed_by = NULL,
            lease_expires_at = NULL,
            updated_at = NOW()
        WHERE status IN ('claimed', 'running')
        AND lease_expires_at < NOW()
        RETURNING id
    )
    SELECT COUNT(*) INTO v_count FROM reclaimed;
    RETURN v_count;
END;
$$;
