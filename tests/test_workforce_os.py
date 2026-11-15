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
