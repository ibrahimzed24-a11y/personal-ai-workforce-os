import os
import sys
import uuid
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.adapters.supabase_adapter import SupabaseAdapter
from core.hybrid.runtime_worker import HybridRuntimeWorker
from api.index import app
from fastapi.testclient import TestClient

class TestHybridRuntime(unittest.TestCase):
    """
    Test suite for Supabase Adapter, Hybrid Runtime Worker, and Vercel Serverless API.
    """

    def setUp(self):
        self.client = TestClient(app)

    def test_01_supabase_adapter_offline_mode(self):
        """Verify SupabaseAdapter handles unconfigured/offline state safely."""
        adapter = SupabaseAdapter(supabase_url="", service_role_key="")
        self.assertFalse(adapter.is_configured())

        # Test heartbeat in offline mode
        res = asyncio.run(adapter.heartbeat_node("test-node"))
        self.assertFalse(res["success"])
        self.assertTrue(res.get("offline"))

        # Test claim task in offline mode
        res = asyncio.run(adapter.claim_hybrid_task("test-node"))
        self.assertFalse(res["success"])
        self.assertTrue(res.get("offline"))

    def test_02_supabase_adapter_mocked_calls(self):
        """Verify SupabaseAdapter RPC serialization and headers."""
        adapter = SupabaseAdapter(
            supabase_url="https://xyzcompany.supabase.co",
            service_role_key="test-service-key"
        )
        self.assertTrue(adapter.is_configured())
        headers = adapter._get_headers(prefer="return=representation")
        self.assertEqual(headers["apikey"], "test-service-key")
        self.assertEqual(headers["Authorization"], "Bearer test-service-key")
        self.assertEqual(headers["Prefer"], "return=representation")

    @patch("httpx.AsyncClient.post")
    def test_03_claim_and_complete_task_flow(self, mock_post):
        """Verify atomic task lease claiming and completion reporting."""
        mock_task = [{
            "id": "11111111-2222-3333-4444-555555555555",
            "idempotency_key": "test-key-001",
            "title": "Automated SEO Audit",
            "description": "Perform comprehensive SEO evaluation",
            "assigned_agent_id": "seo-auditor",
            "runtime_target": "local",
            "input_payload": {"url": "https://example.com"},
            "attempts": 1
        }]

        mock_post.return_value = MagicMock(
            is_success=True,
            status_code=200,
            json=MagicMock(return_value=mock_task)
        )

        adapter = SupabaseAdapter(
            supabase_url="https://xyzcompany.supabase.co",
            service_role_key="test-key"
        )

        claim_res = asyncio.run(adapter.claim_hybrid_task("macbook-primary"))
        self.assertTrue(claim_res["success"])
        self.assertEqual(claim_res["task"]["idempotency_key"], "test-key-001")

        # Mock complete task call
        mock_post.return_value = MagicMock(
            is_success=True,
            status_code=200,
            json=MagicMock(return_value=True)
        )
        complete_res = asyncio.run(adapter.complete_hybrid_task(
            task_id="11111111-2222-3333-4444-555555555555",
            node_id="macbook-primary",
            result={"status": "passed"}
        ))
        self.assertTrue(complete_res["success"])

    def test_04_hybrid_worker_telemetry_and_idempotency(self):
        """Verify worker telemetry collection and local duplicate prevention."""
        worker = HybridRuntimeWorker(node_id="test-macbook")
        telemetry = worker.get_telemetry()
        self.assertEqual(telemetry["node_id"], "test-macbook")
        self.assertIn("browser_automation", telemetry["capabilities"])
        self.assertIn("credentials_vault", telemetry["capabilities"])

        # Simulate duplicate task execution
        mock_task = {
            "id": "22222222-3333-4444-5555-666666666666",
            "idempotency_key": "unique-idempotent-key-42",
            "title": "Duplicate Check Task",
            "assigned_agent_id": "coordinator"
        }

        # Add to processed set
        worker._processed_idempotency_keys.add("unique-idempotent-key-42")
        result = asyncio.run(worker.process_task(mock_task))
        self.assertEqual(result.get("note"), "idempotent_replay")

    def test_05_vercel_serverless_api_health(self):
        """Verify Vercel serverless FastAPI /api/health endpoint."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["runtime"], "vercel-serverless")

    def test_06_vercel_serverless_api_agents(self):
        """Verify Vercel serverless /api/agents returns the registered agent catalog."""
        res = self.client.get("/api/agents")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 8)
        agent_ids = [a.get("id") or a.get("agent_id") for a in data]
        self.assertIn("coordinator", agent_ids)
        self.assertIn("software-engineer", agent_ids)

    def test_07_vercel_serverless_api_nodes(self):
        """Verify Vercel serverless /api/nodes endpoint."""
        res = self.client.get("/api/nodes")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("nodes", data)

    def test_08_vercel_serverless_ui_index(self):
        """Verify root endpoint / returns 200 and loads HTML dashboard."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers.get("content-type", ""))

if __name__ == "__main__":
    unittest.main()
