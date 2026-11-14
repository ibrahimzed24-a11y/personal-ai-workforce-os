import asyncio
import os
import shutil
from pathlib import Path


from core.database import init_db, get_db_connection
from core.orchestrator import Orchestrator
from core.models import TaskCreate
from core.integrator import SystemIntegratorEngine
from core.security.manager import CredentialsManager
from core.security.vault import VaultProvider

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

async def run_full_suite():
    print("=" * 60)
    print("🚀 AI WORKFORCE OS COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 60)

    # 1. Database Init
    print("\n[TEST 1] Initializing SQLite database...")
    await init_db()
    async with get_db_connection() as db:
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as c:
            tables = [row["name"] for row in await c.fetchall()]
    print(f"✓ SQLite WAL database verified with {len(tables)} tables: {', '.join(tables[:6])}...")
    assert "tasks" in tables
    assert "agent_blueprints" in tables
    assert "installed_assets" in tables
    assert "credential_accounts" in tables
    assert "credential_secrets" in tables

    # 2. Agent Blueprints
    print("\n[TEST 2] Synchronizing and verifying agent blueprints...")
    orch = Orchestrator()
    await orch.sync_blueprints_from_disk()
    blueprints = await orch.get_all_blueprints()
    print(f"✓ {len(blueprints)} agent blueprints registered:")
    for bp in blueprints:
        print(f"  • {bp['name']} ({bp['department']}) - {len(bp['specialists'])} specialists")
    assert len(blueprints) >= 8, f"Expected at least 8 agents, found {len(blueprints)}"
    agent_ids = [b["id"] for b in blueprints]
    assert "coordinator" in agent_ids
    assert "market-seo-geo-researcher" in agent_ids
    assert "software-engineer" in agent_ids
    assert "browser-use-agent" in agent_ids
    assert "system-integrator-update-agent" in agent_ids

    # 3. Task Orchestration Vertical Slice
    print("\n[TEST 3] Running vertical slice task orchestration...")
    task_in = TaskCreate(
        title="Comprehensive Autonomous Market & Architecture Audit",
        description="Analyze target keywords for AI workforce, design modular architecture, and formulate executive synthesis.",
        priority="high"
    )
    task = await orch.create_task(task_in)
    print(f"✓ Created task: {task['id']} (Status: {task['status']})")
    assert task["status"] == "pending"

    # Run orchestration
    completed_task = await orch.run_task(task["id"])
    print(f"✓ Orchestrated task to completion: Status = {completed_task['status']}")
    print(f"✓ Verification Status = {completed_task['verification_status']}")
    assert completed_task["status"] == "completed"
    assert completed_task["verification_status"] == "passed"
    assert completed_task["plan"] is not None
    assert len(completed_task["plan"]["steps"]) == 3
    print(f"✓ Deliverable file created at: {completed_task['output_result']['artifact_path']}")
    assert Path(completed_task["output_result"]["artifact_path"]).exists()

    # Verify execution events recorded
    events = await orch.get_task_events(task["id"])
    print(f"✓ {len(events)} execution events recorded in immutable audit log.")
    assert len(events) >= 8

    # 4. System Integrator & Update Agent Lifecycle
    print("\n[TEST 4] Testing System Integrator capability lifecycle...")
    integrator = SystemIntegratorEngine()
    
    # Stage a sample skill in incoming/skills/sample_seo_skill/
    sample_skill_dir = WORKSPACE_ROOT / "incoming" / "skills" / "sample_seo_audit"
    sample_skill_dir.mkdir(parents=True, exist_ok=True)
    with open(sample_skill_dir / "SKILL.md", "w") as f:
        f.write("""---
name: Regional SEO Auditor
description: Audits localized search engine rankings and geo-targeted keywords.
version: 1.2.0
---
# Regional SEO Auditor Skill
Detailed instructions for auditing regional SERPs and localized search volume.
""")

    # Scan incoming
    discovered = await integrator.scan_incoming()
    print(f"✓ Discovered and audited {len(discovered)} incoming assets.")
    skill_asset = next((a for a in discovered if "sample_seo_audit" in a["name"]), None)
    assert skill_asset is not None
    print(f"✓ Classified: {skill_asset['name']} as category '{skill_asset['category']}' with Risk: {skill_asset['security_audit']['risk_level']}")
    assert skill_asset["category"] == "skill"
    assert "market-seo-geo-researcher" in skill_asset["target_agents"]

    # Approve & Install
    await integrator.approve_asset(skill_asset["id"])
    installed_skill = await integrator.install_asset(skill_asset["id"])
    print(f"✓ Installed skill to: {installed_skill['installation_plan']['target_path']} (Status: {installed_skill['status']})")
    assert installed_skill["status"] == "ACTIVE"
    assert Path(WORKSPACE_ROOT / installed_skill["installation_plan"]["target_path"]).exists()

    # Verify Operational Knowledge updated
    skills_index_path = WORKSPACE_ROOT / "documentation" / "knowledge" / "SKILLS_INDEX.md"
    assert skills_index_path.exists()
    with open(skills_index_path, "r") as f:
        skills_text = f.read()
    assert "sample_seo_audit" in skills_text
    print("✓ Operational knowledge (SKILLS_INDEX.md) synchronized successfully.")

    # Test Rollback
    rolled_back = await integrator.rollback_asset(skill_asset["id"])
    print(f"✓ Rollback executed: Status = {rolled_back['status']}")
    assert rolled_back["status"] == "ROLLED_BACK"
    assert not Path(WORKSPACE_ROOT / installed_skill["installation_plan"]["target_path"]).exists()
    print("✓ Clean rollback verified: target files safely removed.")

    # 5. Security & Credentials Vault Lifecycle
    print("\n[TEST 5] Testing Security & Credentials Vault...")
    creds = CredentialsManager()
    
    # Create account with encrypted password
    acc = await creds.create_account(
        name="Semrush SEO Intelligence",
        url="https://www.semrush.com",
        login_url="https://www.semrush.com/login",
        username_or_email="analyst@ai-workforce.local",
        category="research_seo",
        password="SuperSecretPassword123!",
        assigned_agents=["market-seo-geo-researcher", "browser-use-agent"]
    )
    print(f"✓ Account registered in vault: {acc['id']} - {acc['name']}")
    assert acc["has_password"] is True

    # Confirm ciphertext is encrypted in database
    async with get_db_connection() as db:
        async with db.execute("SELECT encrypted_password FROM credential_secrets WHERE account_id = ?", (acc["id"],)) as c:
            secret_row = await c.fetchone()
            ciphertext = secret_row["encrypted_password"]
            print(f"✓ Ciphertext at rest: {ciphertext[:35]}... (Plaintext NEVER stored in DB)")
            assert "SuperSecretPassword123!" not in ciphertext

    # Agent scope filtering: authorized agent vs unauthorized agent
    authorized_list = await creds.list_accounts(agent_id="market-seo-geo-researcher")
    unauthorized_list = await creds.list_accounts(agent_id="deployment-agent")
    print(f"✓ Scoped Discovery: Authorized agent sees {len(authorized_list)} accounts; Unauthorized agent sees {len(unauthorized_list)} accounts.")
    assert len(authorized_list) >= 1
    assert len(unauthorized_list) == 0

    # Negative test: unauthorized agent direct access attempt
    try:
        await creds.get_account_detail(acc["id"], agent_id="deployment-agent")
        assert False, "Should have thrown PermissionError"
    except PermissionError:
        print("✓ Negative Security Test Passed: Unauthorized agent access blocked.")

    # Owner password reveal with master key
    vault = VaultProvider()
    with open(vault.key_path, "r") as f:
        master_key = f.read().strip()
    revealed = await creds.reveal_password(acc["id"], master_key)
    print(f"✓ Owner Re-Auth: Password decrypted and verified: '{revealed['password']}'")
    assert revealed["password"] == "SuperSecretPassword123!"

    # Negative test: invalid master key
    try:
        await creds.reveal_password(acc["id"], "wrong_invalid_key_value")
        assert False, "Should have thrown PermissionError"
    except PermissionError:
        print("✓ Negative Security Test Passed: Invalid master key rejected.")

    # Credential Broker access grant
    session = await creds.request_credential_access(
        account_id=acc["id"],
        agent_id="browser-use-agent",
        task_id=task["id"]
    )
    print(f"✓ Credential Broker issued temporary session: {session['session_id']} (Expires: {session['expires_at']})")
    assert session["session_id"].startswith("sess_")

    # Password rotation with version preservation
    rotated = await creds.update_credentials(acc["id"], "NewRotatedPassword456!", changed_by="owner", reason="Security rotation")
    print(f"✓ Credential rotated to Version {rotated['new_version']} (Old version preserved in history)")
    assert rotated["new_version"] == 2

    # Agent Account Registration Request
    reg_req = await creds.request_account_registration(
        agent_id="software-engineer",
        task_id=task["id"],
        service_name="Docker Hub Registry",
        website_url="https://hub.docker.com",
        category="development",
        reason="Required for pulling container base images",
        proposed_username="dev-agent@ai-workforce.local",
        is_paid=False
    )
    print(f"✓ Agent registration request submitted: {reg_req['id']} (Requires Owner Approval)")
    assert reg_req["status"] == "PENDING"

    # Owner approves registration
    approved_reg = await creds.approve_registration(reg_req["id"], "APPROVED", notes="Approved for official base images")
    print(f"✓ Registration request approved by owner: Status = {approved_reg['status']}")
    assert approved_reg["status"] == "APPROVED"

    # Security Health & Posture
    health = await creds.get_credential_health_report()
    print(f"✓ Vault Health Report: Total Accounts={health['total_accounts']}, Vault={health['vault_status']}")
    assert health["total_accounts"] >= 1

    # Security Audit Logs
    audit_logs = await creds.get_audit_logs(limit=10)
    print(f"✓ Audit Trail: Verified {len(audit_logs)} security events logged.")
    assert len(audit_logs) >= 5

    print("\n" + "=" * 60)
    print("🎉 ALL 5 TEST SUITES PASSED FLAWLESSLY WITH ZERO FAILURES!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_full_suite())
