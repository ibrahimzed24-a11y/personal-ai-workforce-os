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
