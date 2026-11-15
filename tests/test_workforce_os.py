from fastapi.testclient import TestClient
from api.index import app as cloud_app, encrypt_secret, get_cipher
from core.hybrid.runtime_worker import app as worker_app

cloud_client = TestClient(cloud_app)
worker_client = TestClient(worker_app)


def test_health_and_vault_encryption():
    res = cloud_client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    token = encrypt_secret("my_hostinger_password_123")
    assert token != "my_hostinger_password_123"
    decrypted = get_cipher().decrypt(token.encode("utf-8")).decode("utf-8")
    assert decrypted == "my_hostinger_password_123"


def test_unauthenticated_endpoints_blocked():
    assert cloud_client.get("/api/projects").status_code == 401
    assert cloud_client.post("/api/chat", json={"project_id": "123", "message": "hi"}).status_code == 401


def test_local_worker_cors():
    res = worker_client.get(
        "/health",
        headers={"Origin": "https://personal-ai-workforce-os-pi.vercel.app"},
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://personal-ai-workforce-os-pi.vercel.app"
