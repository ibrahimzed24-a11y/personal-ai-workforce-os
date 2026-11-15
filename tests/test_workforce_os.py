import io
import csv
import openpyxl
from fastapi.testclient import TestClient
from api.index import app as cloud_app, encrypt_secret, get_cipher, parse_project_file
from core.hybrid.runtime_worker import app as worker_app

cloud_client = TestClient(cloud_app)
worker_client = TestClient(worker_app)


def test_health_and_vault_encryption():
    res = cloud_client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "pdf" in data["harness_formats"]
    assert "csv" in data["harness_formats"]
    assert "xlsx" in data["harness_formats"]

    token = encrypt_secret("my_hostinger_password_123")
    assert token != "my_hostinger_password_123"
    decrypted = get_cipher().decrypt(token.encode("utf-8")).decode("utf-8")
    assert decrypted == "my_hostinger_password_123"


def test_unauthenticated_endpoints_blocked():
    assert cloud_client.get("/api/projects").status_code == 401
    assert cloud_client.post("/api/chat", json={"project_id": "123", "message": "hi"}).status_code == 401
    assert cloud_client.get("/api/projects/123/documents").status_code == 401
    assert cloud_client.post("/api/projects/123/documents", json={"file_name": "test.csv", "content_base64": "YQ=="}).status_code == 401


def test_local_worker_cors():
    res = worker_client.get(
        "/health",
        headers={"Origin": "https://personal-ai-workforce-os-pi.vercel.app"},
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://personal-ai-workforce-os-pi.vercel.app"


def test_csv_and_xlsx_harness_parsing():
    # 1. Test CSV Parsing
    raw_csv = b"Clinic Name,City,Email,Phone,Contact Person\nDowntown Dental,Toronto,info@downtowndental.ca,416-555-0101,Dr. Smith\n"
    csv_parsed = parse_project_file("Canadian Dental Clinics Leads.csv", raw_csv)
    assert csv_parsed["file_type"] == "csv"
    assert csv_parsed["row_count"] == 1
    assert "Clinic Name" in csv_parsed["columns"]
    assert "Dr. Smith" in csv_parsed["extracted_text"]

    # 2. Test XLSX Parsing
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Prospects"
    ws.append(["Company", "Decision Maker", "Work Email", "MRR"])
    ws.append(["Valioz Health", "Ibrahim", "sales@health.valioz.com", "$12,000"])
    bio = io.BytesIO()
    wb.save(bio)
    xlsx_parsed = parse_project_file("Valioz_Prospects.xlsx", bio.getvalue())
    assert xlsx_parsed["file_type"] == "xlsx"
    assert xlsx_parsed["row_count"] == 1
    assert "Decision Maker" in xlsx_parsed["columns"]
    assert "Valioz Health" in xlsx_parsed["extracted_text"]


def test_llm_providers_catalog():
    res = cloud_client.get("/api/models/providers")
    assert res.status_code == 200
    providers = res.json().get("providers", [])
    provider_ids = [p["id"] for p in providers]
    assert "antigravity" in provider_ids
    assert "gemini" in provider_ids
    assert "openai" in provider_ids
    assert "anthropic" in provider_ids
    assert "groq" in provider_ids
    assert "deepseek" in provider_ids
    assert "openrouter" in provider_ids
    assert "ollama" in provider_ids

    # Also verify local worker has provider parity
    local_res = worker_client.get("/api/models/providers")
    assert local_res.status_code == 200
    local_ids = [p["id"] for p in local_res.json().get("providers", [])]
    assert "antigravity" in local_ids
    assert "gemini" in local_ids
    assert "ollama" in local_ids


def test_llm_test_endpoint():
    # Diagnostic test call returns structured status (ok or error) with latency
    res = cloud_client.post(
        "/api/models/test",
        json={"provider": "gemini", "model": "gemini-2.5-flash", "api_key": "fake_test_key"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "gemini"
    assert data["model"] == "gemini-2.5-flash"
    assert "status" in data


def test_project_llm_configuration_and_sanitization():
    from api.index import sanitize_project_for_client
    raw_project = {
        "id": "test_proj_123",
        "name": "Valioz Sales Outreach",
        "runtime_mode": "cloud_api",
        "llm_provider": "claude",
        "llm_model": "claude-3-7-sonnet-20250219",
        "llm_api_key": encrypt_secret("sk-ant-test-secret-key-12345"),
        "llm_endpoint": None,
    }
    sanitized = sanitize_project_for_client(raw_project)
    assert sanitized["has_api_key"] is True
    assert sanitized["llm_api_key"] == "••••••••"
    assert sanitized["llm_provider"] == "claude"
    assert sanitized["llm_model"] == "claude-3-7-sonnet-20250219"


def test_multi_format_exporter_and_guardrails():
    from pathlib import Path
    from core.exporter import (
        MultiFormatExporter,
        generate_and_save_stage_report,
        resolve_scoped_path,
        ProjectPathViolationError
    )

    # 1. Path Guardrail
    try:
        resolve_scoped_path("valioz-health", "../../etc/shadow")
        assert False, "Should raise ProjectPathViolationError"
    except ProjectPathViolationError:
        pass

    # 2. Multi-Format Deliverable Generation
    slug = "valioz-health"
    task_id = "test-task-suite-01"

    pdf_res = generate_and_save_stage_report(
        project_slug=slug,
        task_id=task_id,
        agent_id="coordinator",
        step_index=1,
        title="Stage 1 Verification",
        sections={"Summary": "Scope validated.", "Records": 5},
        file_format="pdf"
    )
    assert pdf_res["file_size"] > 0
    assert Path(pdf_res["local_path"]).exists()

    docx_res = generate_and_save_stage_report(
        project_slug=slug,
        task_id=task_id,
        agent_id="browser-researcher",
        step_index=2,
        title="Stage 2 Dossier",
        sections={"Intelligence": ["Lead A", "Lead B"]},
        file_format="docx"
    )
    assert docx_res["file_size"] > 0
    assert Path(docx_res["local_path"]).exists()

    xlsx_res = generate_and_save_stage_report(
        project_slug=slug,
        task_id=task_id,
        agent_id="data-extractor",
        step_index=3,
        title="Stage 3 Data",
        sections={},
        file_format="xlsx",
        tabular_data=[["Lead", "Score"], ["Alpha", 98]]
    )
    assert xlsx_res["file_size"] > 0
    assert Path(xlsx_res["local_path"]).exists()


def test_slash_command_router_and_add_agent():
    import asyncio
    from core.orchestrator import PipelineHandoverOrchestrator
    from api.index import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

    orchestrator = PipelineHandoverOrchestrator(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    dummy_project = {
        "id": "ec48c7ae-185b-4ec9-bf2c-183024b740f4",
        "name": "valioz health sales",
        "slug": "valioz-health-sales",
        "assigned_agents": ["coordinator", "browser-researcher"]
    }
    dummy_user = {"id": "3ff7069c-7720-43de-92ca-892170124f62", "email": "ibrahim.zed24@gmail.com"}

    async def _run():
        res = await orchestrator.handle_slash_command(
            raw_message="/direct coordinator Focus on high-intent Canadian leads",
            project=dummy_project,
            user=dummy_user,
            token=SUPABASE_SERVICE_ROLE_KEY,
            documents=[],
            tools=[]
        )
        assert res is not None
        assert res["role"] == "coordinator"
        assert "Steering Directive Acknowledged" in res["content"]

    asyncio.run(_run())


def test_32_agents_and_8_departments_architecture():
    from core.agent_context import AgentContextLoader
    loader = AgentContextLoader()
    agents = loader.list_all_agents()
    assert len(agents) == 32, f"Expected 32 agents, found {len(agents)}"

    valid_count = 0
    for a in agents:
        v = loader.validate_agent_architecture(a["agent_id"])
        if v.get("valid"):
            valid_count += 1
    assert valid_count == 32, f"Expected all 32 agents to be valid, got {valid_count}"

    # Verify API endpoint returns real agents
    res = cloud_client.get("/api/agents")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 32
    assert len(data["departments"]) == 8


def test_permanent_framework_skills_and_events():
    from core.agent_context import AgentContextLoader
    loader = AgentContextLoader()
    skills = loader.discover_permanent_skills()
    assert len(skills) >= 15
    categories = set(s["category"] for s in skills)
    assert "deepseek" in categories
    assert "superpowers" in categories
    assert "ecc" in categories
    assert "addyosmani" in categories
    assert "browser-use" in categories

    # Test API endpoint
    res = cloud_client.get("/api/skills")
    assert res.status_code == 200
    assert res.json()["count"] >= 15

    # Test events endpoint returns 200
    ev_res = cloud_client.get("/api/events")
    assert ev_res.status_code == 200
    assert "events" in ev_res.json()


def test_connectors_catalog_and_test():
    res = cloud_client.get("/api/connectors")
    assert res.status_code == 200
    data = res.json()
    assert "connectors" in data
    ids = [c["id"] for c in data["connectors"]]
    assert "antigravity-cli" in ids
    assert "browser-use" in ids
    assert "google-search-console" in ids
    assert "gmail" in ids
    assert "google-calendar" in ids

    # Test connector probe
    t_res = cloud_client.post("/api/connectors/antigravity-cli/test")
    assert t_res.status_code == 200
    assert t_res.json()["connector_id"] == "antigravity-cli"


def test_serverless_read_only_resilience():
    from core.exporter import get_project_root, generate_and_save_stage_report
    # Ensure get_project_root returns a valid directory that can be created
    p = get_project_root("serverless-resilience-check")
    assert p.exists()

    # Generate report and ensure it completes with VERIFIED status
    rep = generate_and_save_stage_report(
        project_slug="serverless-resilience-check",
        task_id="task-err30-guard",
        agent_id="coordinator",
        step_index=1,
        title="Serverless Safe Report",
        sections={"Test": "Passed"},
        file_format="pdf"
    )
    assert rep["verification_status"] == "VERIFIED"
    assert rep["file_size"] > 0


def test_download_auth_query_parameter_and_squad_selection():
    import os
    # 1. Unauthenticated download fails with 401
    assert cloud_client.get("/api/projects/123/reports/rep-1/download").status_code == 401

    # 2. Invalid token fails with 401
    assert cloud_client.get("/api/projects/123/reports/rep-1/download?token=bad_token").status_code == 401

    # 3. Agents catalog returns 32 sovereign agents with valid ids
    agents_res = cloud_client.get("/api/agents")
    assert agents_res.status_code == 200
    agents_data = agents_res.json()
    assert agents_data["count"] == 32
    agent_ids = [a.get("id") or a.get("agent_id") for a in agents_data["agents"]]
    assert "coordinator" in agent_ids
    assert "market-seo-geo-researcher" in agent_ids
    assert "software-engineer" in agent_ids
    assert "browser-use-agent" in agent_ids
    assert "master-reporting-agent" in agent_ids


def test_grillme_skill_and_engine_alignment():
    from core.grillme import GrillMeEngine
    engine = GrillMeEngine()

    dummy_docs = [{"file_name": "Canadian Dental Clinics Leads.csv", "row_count": 50}]
    dummy_tools = [{"tool_name": "Hostinger SMTP", "login_url": "smtp.hostinger.com:465"}]
    dummy_project = {
        "id": "ec48c7ae-185b-4ec9-bf2c-183024b740f4",
        "name": "valioz health sales",
        "slug": "valioz-health-sales"
    }

    # 1. Sales & Outreach Vector
    interview = engine.generate_alignment_interview(
        directive="Review records and start drafting emails for Canadian dental clinics",
        agent_id=None,
        project=dummy_project,
        documents=dummy_docs,
        tools=dummy_tools
    )
    assert interview["status"] == "ready"
    assert interview["agent_id"] == "coordinator"
    assert "Sales Squad" in interview["agent_name"]
    assert len(interview["proposed_workflow"]["stages"]) == 4
    assert len(interview["questions"]) >= 3
    assert any("Toronto" in q["recommended_option"] for q in interview["questions"])
    assert "⚡ Proceed with Recommended Workflow" in interview["formatted_markdown"]

    # 2. Software Engineering Vector
    code_interview = engine.generate_alignment_interview(
        directive="Refactor database schema and add pytest coverage",
        agent_id="software-engineer",
        project=dummy_project,
        documents=[],
        tools=[]
    )
    assert code_interview["agent_id"] == "software-engineer"
    assert "Engineering" in code_interview["department"]
    assert any("Modular Resilient Micro-Service" in q["recommended_option"] for q in code_interview["questions"])


def test_grillme_slash_command_and_permanent_skill():
    import asyncio
    from core.agent_context import AgentContextLoader
    from core.orchestrator import PipelineHandoverOrchestrator
    from api.index import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

    # 1. Permanent skill discovery
    loader = AgentContextLoader()
    skills = loader.discover_permanent_skills()
    grillme_skill = next((s for s in skills if s["slash_command"] == "/grillme"), None)
    assert grillme_skill is not None
    assert grillme_skill["name"] == "grillme-adaptive-clarification"
    assert len(grillme_skill["department_affinity"]) == 8

    # 2. Slash command routing
    orchestrator = PipelineHandoverOrchestrator(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    dummy_project = {
        "id": "ec48c7ae-185b-4ec9-bf2c-183024b740f4",
        "name": "valioz health sales",
        "slug": "valioz-health-sales"
    }
    dummy_user = {"id": "3ff7069c-7720-43de-92ca-892170124f62", "email": "ibrahim.zed24@gmail.com"}

    async def _run():
        res = await orchestrator.handle_slash_command(
            raw_message="/grillme @browser-use-agent Extract Canadian clinic records",
            project=dummy_project,
            user=dummy_user,
            token=SUPABASE_SERVICE_ROLE_KEY,
            documents=[],
            tools=[]
        )
        assert res is not None
        assert res["role"] == "agent"
        assert res["grillme"]["is_grillme"] is True
        assert len(res["grillme"]["questions"]) >= 2

    asyncio.run(_run())


def test_audit_integrity_and_security_remediation():
    import pytest
    from api.index import decrypt_secret, call_llm
    from core.orchestrator import PipelineHandoverOrchestrator

    # 1. Fail-closed vault decryption (F-04)
    # Invalid or tampered ciphertext must return empty string, never the raw ciphertext
    bad_cipher = "gAAAAABfakeCipherTampered12345"
    assert decrypt_secret(bad_cipher) == ""
    assert decrypt_secret("") == ""

    # 2. Honest error when worker is offline (F-01, F-06)
    # Calling offline antigravity provider without local worker must raise RuntimeError, never synthetic success string
    import asyncio
    async def _test_offline_llm():
        with pytest.raises(RuntimeError) as exc_info:
            await call_llm(
                provider="antigravity",
                model="nonexistent-model",
                system_prompt="Test",
                user_prompt="Hello",
                endpoint="http://127.0.0.1:9999",
                timeout=1.0
            )
        assert "offline" in str(exc_info.value).lower()

    asyncio.run(_test_offline_llm())




