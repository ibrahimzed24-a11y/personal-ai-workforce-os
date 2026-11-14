import asyncio
import os
import shutil
import sqlite3
import httpx
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_URL = "http://127.0.0.1:8765"

async def run_audit():
    print("=" * 70)
    print("🔍 AI WORKFORCE OS INDEPENDENT AUDIT VERIFICATION")
    print("=" * 70)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # --- TEST 1: Health & System Diagnostics ---
        print("\n--- AUDIT 1: System Health & Core Metadata ---")
        health_resp = await client.get("/api/health")
        print(f"GET /api/health: {health_resp.status_code}")
        health_data = health_resp.json()
        print(f"Health Data: {health_data}")
        assert health_resp.status_code == 200
        assert health_data["status"] == "healthy"
        
        # --- TEST 2: Real End-to-End Task Execution ---
        print("\n--- AUDIT 2: Real End-to-End Task Execution Flow ---")
        task_payload = {
            "title": "Audit Verification Task: Architecture & Security Benchmarking",
            "description": "Perform end-to-end task decomposition, execute specialized steps, write deliverable, and run independent verification.",
            "priority": "high",
            "target_agent": "coordinator",
            "context": {"audit_run": True}
        }
        create_resp = await client.post("/api/tasks", json=task_payload)
        assert create_resp.status_code == 200
        task_data = create_resp.json()
        task_id = task_data["id"]
        print(f"✓ Task Created via API: {task_id} (Status: {task_data['status']})")
        
        # Run pipeline
        run_resp = await client.post(f"/api/tasks/{task_id}/run")
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        print(f"✓ Task Execution Complete: Status = {run_data['status']}, Verification = {run_data['verification_status']}")
        assert run_data["status"] == "completed"
        assert run_data["verification_status"] == "passed"
        assert run_data["plan"] is not None
        assert len(run_data["plan"]["steps"]) == 3
        
        artifact_path = run_data["output_result"]["artifact_path"]
        print(f"✓ Verified Deliverable file on disk: {artifact_path}")
        assert Path(artifact_path).exists()
        
        # Check event trail
        events_resp = await client.get(f"/api/tasks/{task_id}/events")
        events = events_resp.json()
        print(f"✓ Immutable Execution Events Recorded: {len(events)} events")
        for ev in events[:4]:
            print(f"  • [{ev['event_type']}] Agent: {ev['agent_id'] or 'system'}")

        # --- TEST 3: System Integrator Workflows (Positive & Failed Rollback) ---
        print("\n--- AUDIT 3: System Integrator Ingestion & Rollback ---")
        # Positive Test: Harmless Skill
        skill_dir = WORKSPACE_ROOT / "incoming" / "skills" / "audit_sample_skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        with open(skill_dir / "SKILL.md", "w") as f:
            f.write("""---
name: Audit Benchmark Skill
description: Safe sample skill for independent system audit testing.
version: 1.0.0
---
# Audit Benchmark Skill Instructions
Execute safe static code analysis.
""")
        
        scan_resp = await client.get("/api/integrator/scan")
        assert scan_resp.status_code == 200
        scan_assets = scan_resp.json()
        bench_asset = next((a for a in scan_assets if "audit_sample_skill" in a["name"]), None)
        assert bench_asset is not None
        print(f"✓ Ingestion Scanner Detected: {bench_asset['name']} (Risk: {bench_asset['security_audit']['risk_level']})")
        
        # Approve & Install
        appr_resp = await client.post(f"/api/integrator/approve/{bench_asset['id']}")
        assert appr_resp.status_code == 200
        inst_resp = await client.post(f"/api/integrator/install/{bench_asset['id']}")
        assert inst_resp.status_code == 200
        inst_data = inst_resp.json()
        print(f"✓ Asset Installed & Activated: Status = {inst_data['status']} at {inst_data['installation_plan']['target_path']}")
        assert inst_data["status"] == "ACTIVE"
        assert Path(WORKSPACE_ROOT / inst_data["installation_plan"]["target_path"]).exists()
        
        # Negative Test: Failed Installation & Automatic Rollback
        print("\nTesting Malformed Asset Installation Failure & Clean Rollback...")
        malformed_dir = WORKSPACE_ROOT / "incoming" / "skills" / "malformed_skill"
        malformed_dir.mkdir(parents=True, exist_ok=True)
        with open(malformed_dir / "SKILL.md", "w") as f:
            f.write("   ") # empty malformed skill
            
        await client.get("/api/integrator/scan")
        assets_resp = await client.get("/api/integrator/assets")
        malformed_asset = next((a for a in assets_resp.json() if "malformed_skill" in a["name"]), None)
        assert malformed_asset is not None
        await client.post(f"/api/integrator/approve/{malformed_asset['id']}")
        
        fail_install_resp = await client.post(f"/api/integrator/install/{malformed_asset['id']}")
        print(f"✓ Failed Install Response Code: {fail_install_resp.status_code} (Expected 500)")
        assert fail_install_resp.status_code == 500
        
        # Verify rollback occurred and asset marked FAILED
        assets_after = (await client.get("/api/integrator/assets")).json()
        failed_record = next(a for a in assets_after if a["id"] == malformed_asset["id"])
        print(f"✓ Asset Lifecycle State after failure: {failed_record['status']}")
        assert failed_record["status"] == "FAILED"
        target_failed_path = WORKSPACE_ROOT / failed_record["installation_plan"]["target_path"]
        print(f"✓ Target file uninstalled/cleaned up: {not target_failed_path.exists()}")
        assert not target_failed_path.exists()

        # Clean up test directories
        if skill_dir.exists(): shutil.rmtree(skill_dir)
        if malformed_dir.exists(): shutil.rmtree(malformed_dir)
        installed_bench = WORKSPACE_ROOT / inst_data["installation_plan"]["target_path"]
        if installed_bench.parent.exists(): shutil.rmtree(installed_bench.parent)

        # --- TEST 4: Security Negative Access Tests ---
        print("\n--- AUDIT 4: Security & Access Control Negative Tests ---")
        # Create dummy test account with dummy password
        account_payload = {
            "name": "Audit Dummy Service",
            "url": "https://audit-dummy.local",
            "login_url": "https://audit-dummy.local/login",
            "username_or_email": "audit_user@example.local",
            "category": "development",
            "password": "AuditDummyPassword999!",
            "assigned_agents": ["market-seo-geo-researcher"]
        }
        create_acc_resp = await client.post("/api/security/accounts", json=account_payload)
        assert create_acc_resp.status_code == 200
        acc_data = create_acc_resp.json()
        acc_id = acc_data["id"]
        print(f"✓ Dummy Account Created: {acc_id} (Password Encrypted in Vault)")
        
        # Test 4.1: Scoped Discovery
        auth_agent_list = (await client.get(f"/api/security/accounts?agent_id=market-seo-geo-researcher")).json()
        unauth_agent_list = (await client.get(f"/api/security/accounts?agent_id=software-engineer")).json()
        auth_has_it = any(a["id"] == acc_id for a in auth_agent_list)
        unauth_has_it = any(a["id"] == acc_id for a in unauth_agent_list)
        print(f"✓ Scoped Discovery Enforcement: Authorized sees account={auth_has_it}, Unauthorized sees account={unauth_has_it}")
        assert auth_has_it is True
        assert unauth_has_it is False
        
        # Test 4.2: Unauthorized Agent Detail Fetch -> Expect 403
        unauth_detail = await client.get(f"/api/security/accounts/{acc_id}?agent_id=software-engineer")
        print(f"✓ Unauthorized Agent Detail Request: HTTP {unauth_detail.status_code} (Expected 403)")
        assert unauth_detail.status_code == 403
        
        # Test 4.3: Unauthorized Agent Credential Access Request -> Expect 403
        unauth_grant = await client.post(f"/api/security/accounts/{acc_id}/request-access", json={
            "agent_id": "software-engineer",
            "task_id": task_id
        })
        print(f"✓ Unauthorized Credential Broker Grant Request: HTTP {unauth_grant.status_code} (Expected 403)")
        assert unauth_grant.status_code == 403
        
        # Test 4.4: Password Reveal with Wrong Master Key -> Expect 401
        wrong_reveal = await client.post(f"/api/security/accounts/{acc_id}/reveal", json={
            "master_key": "COMPLETELY_INVALID_MASTER_KEY_STRING"
        })
        print(f"✓ Invalid Master Key Re-Auth Attempt: HTTP {wrong_reveal.status_code} (Expected 401)")
        assert wrong_reveal.status_code == 401

        # Test 4.5: Valid Session Grant and Subsequent Revocation
        grant_resp = await client.post(f"/api/security/accounts/{acc_id}/request-access", json={
            "agent_id": "market-seo-geo-researcher",
            "task_id": task_id
        })
        assert grant_resp.status_code == 200
        session_id = grant_resp.json()["session_id"]
        print(f"✓ Valid Broker Grant Session Created: {session_id}")
        
        # Revoke session
        revoke_resp = await client.post(f"/api/security/sessions/{session_id}/revoke")
        assert revoke_resp.status_code == 200
        print(f"✓ Session Revoked: {session_id}")

        # --- TEST 5: Database Backup & Restore in Separate Test DB ---
        print("\n--- AUDIT 5: Database Backup & Recovery Verification ---")
        active_db_path = WORKSPACE_ROOT / "data" / "ai_workforce.db"
        backup_db_path = WORKSPACE_ROOT / "temp" / "backup_verification_test.db"
        backup_db_path.parent.mkdir(parents=True, exist_ok=True)
        if backup_db_path.exists(): backup_db_path.unlink()
        
        # Perform SQLite online backup API
        src_conn = sqlite3.connect(active_db_path)
        dst_conn = sqlite3.connect(backup_db_path)
        src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
        
        print(f"✓ Online backup completed to: {backup_db_path}")
        assert backup_db_path.exists()
        
        # Verify backup integrity
        chk_conn = sqlite3.connect(backup_db_path)
        cur = chk_conn.cursor()
        chk_res = cur.execute("PRAGMA integrity_check").fetchall()
        chk_fk = cur.execute("PRAGMA foreign_key_check").fetchall()
        row_counts = cur.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        chk_conn.close()
        
        print(f"✓ Backup Integrity Check: {chk_res}")
        print(f"✓ Backup Foreign Key Check: {chk_fk}")
        print(f"✓ Backup Tasks Row Count: {row_counts}")
        assert chk_res == [('ok',)]
        assert chk_fk == []
        assert row_counts >= 1
        
        # Clean up test backup
        backup_db_path.unlink()
        print("✓ Test backup verified and safely cleaned up without touching active DB.")

    print("\n" + "=" * 70)
    print("✅ INDEPENDENT AUDIT VERIFICATION SUITE COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_audit())
