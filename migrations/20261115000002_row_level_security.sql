-- =============================================================================
-- Migration: 20261115000002_row_level_security.sql
-- Description: Strict Row-Level Security (RLS) & Access Policies for Supabase
-- Security Model: Zero public/anonymous access. Access strictly limited to
-- authenticated owner accounts and the backend service_role key.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. ENABLE ROW LEVEL SECURITY ON ALL OPERATIONAL TABLES
-- -----------------------------------------------------------------------------

ALTER TABLE agent_blueprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE specialist_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE execution_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE installed_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE operational_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_routing_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_usage_metrics ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- 2. REVOKE ALL DEFAULT PERMISSIONS FROM PUBLIC AND ANON ROLES
-- -----------------------------------------------------------------------------

REVOKE ALL ON TABLE agent_blueprints FROM anon, public;
REVOKE ALL ON TABLE specialist_definitions FROM anon, public;
REVOKE ALL ON TABLE tasks FROM anon, public;
REVOKE ALL ON TABLE task_plans FROM anon, public;
REVOKE ALL ON TABLE execution_events FROM anon, public;
REVOKE ALL ON TABLE approvals FROM anon, public;
REVOKE ALL ON TABLE verifications FROM anon, public;
REVOKE ALL ON TABLE verification_audits FROM anon, public;
REVOKE ALL ON TABLE system_requirements FROM anon, public;
REVOKE ALL ON TABLE installed_assets FROM anon, public;
REVOKE ALL ON TABLE operational_knowledge FROM anon, public;
REVOKE ALL ON TABLE llm_providers FROM anon, public;
REVOKE ALL ON TABLE llm_models FROM anon, public;
REVOKE ALL ON TABLE llm_routing_rules FROM anon, public;
REVOKE ALL ON TABLE llm_usage_metrics FROM anon, public;

-- -----------------------------------------------------------------------------
-- 3. GRANT PERMISSIONS TO SERVICE_ROLE (LOCAL MAC WORKER & BACKEND API)
-- -----------------------------------------------------------------------------

GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO service_role;

-- -----------------------------------------------------------------------------
-- 4. POLICIES: SERVICE ROLE FULL ACCESS (BYPASS FOR SECURE WORKERS)
-- -----------------------------------------------------------------------------

CREATE POLICY "service_role_agent_blueprints" ON agent_blueprints FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_specialist_definitions" ON specialist_definitions FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_tasks" ON tasks FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_task_plans" ON task_plans FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_execution_events" ON execution_events FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_approvals" ON approvals FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_verifications" ON verifications FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_verification_audits" ON verification_audits FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_system_requirements" ON system_requirements FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_installed_assets" ON installed_assets FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_operational_knowledge" ON operational_knowledge FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_llm_providers" ON llm_providers FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_llm_models" ON llm_models FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_llm_routing_rules" ON llm_routing_rules FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_llm_usage_metrics" ON llm_usage_metrics FOR ALL TO service_role USING (true) WITH CHECK (true);

-- -----------------------------------------------------------------------------
-- 5. POLICIES: AUTHENTICATED OWNER ACCESS (WEB DASHBOARD ON VERCEL)
-- Only verified authenticated users have read/write access to OS data.
-- -----------------------------------------------------------------------------

CREATE POLICY "authenticated_owner_agent_blueprints" ON agent_blueprints FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_specialist_definitions" ON specialist_definitions FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_tasks" ON tasks FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_task_plans" ON task_plans FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_execution_events" ON execution_events FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_approvals" ON approvals FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_verifications" ON verifications FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_verification_audits" ON verification_audits FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_system_requirements" ON system_requirements FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_installed_assets" ON installed_assets FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_operational_knowledge" ON operational_knowledge FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_llm_providers" ON llm_providers FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_llm_models" ON llm_models FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_llm_routing_rules" ON llm_routing_rules FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "authenticated_owner_llm_usage_metrics" ON llm_usage_metrics FOR ALL TO authenticated USING (auth.uid() IS NOT NULL) WITH CHECK (auth.uid() IS NOT NULL);
