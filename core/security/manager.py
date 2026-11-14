import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiosqlite

from core.database import get_db_connection
from core.security.vault import VaultProvider

logger = logging.getLogger("ai_workforce_os.security.manager")

class CredentialsManager:
    def __init__(self):
        self.vault = VaultProvider()

    async def create_account(
        self,
        name: str,
        url: str,
        login_url: str,
        username_or_email: str,
        category: str,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        project_id: str = "global",
        mfa_status: str = "DISABLED",
        notes: str = "",
        assigned_agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Creates an account record and securely encrypts secret values in the vault."""
        account_id = f"acc_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        async with get_db_connection() as db:
            # 1. Insert metadata
            await db.execute("""
                INSERT INTO credential_accounts (
                    id, name, url, login_url, username_or_email, category,
                    project_id, owner_id, status, auth_method, mfa_status,
                    notes, health_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'owner', 'ACTIVE', 'PASSWORD', ?, ?, 'HEALTHY', ?, ?)
            """, (account_id, name, url, login_url, username_or_email, category, project_id, mfa_status, notes, now, now))
            
            # 2. Encrypt & insert secrets
            enc_password = self.vault.encrypt(password) if password else ""
            enc_api_key = self.vault.encrypt(api_key) if api_key else ""
            
            await db.execute("""
                INSERT INTO credential_secrets (account_id, encrypted_password, encrypted_api_key, version, last_rotated_at)
                VALUES (?, ?, ?, 1, ?)
            """, (account_id, enc_password, enc_api_key, now))
            
            # 3. Store initial version in history
            if enc_password:
                await db.execute("""
                    INSERT INTO credential_versions (account_id, version, encrypted_password, changed_by, reason, created_at)
                    VALUES (?, 1, ?, 'owner', 'Initial credential provisioning', ?)
                """, (account_id, enc_password, now))
                
            # 4. Bind access policies for assigned agents
            if assigned_agents:
                for agent_id in assigned_agents:
                    policy_id = f"pol_{uuid.uuid4().hex[:8]}"
                    await db.execute("""
                        INSERT INTO credential_access_policies (id, account_id, agent_id, permission_level, project_id)
                        VALUES (?, ?, ?, 'use', ?)
                    """, (policy_id, account_id, agent_id, project_id))
                    
            # 5. Record audit log
            await self._log_audit(
                db, account_id=account_id, actor_type="owner", actor_id="owner",
                action="CREATE_ACCOUNT", status="SUCCESS",
                details={"name": name, "category": category, "assigned_agents": assigned_agents or []}
            )
            
            await db.commit()

        return await self.get_account_detail(account_id)

    async def list_accounts(
        self,
        agent_id: Optional[str] = None,
        category: Optional[str] = None,
        project_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lists accounts. If requested by an agent, enforces strict scope filtering:
        only accounts where the agent holds 'discover', 'authenticate', or 'use' permissions are visible.
        Never exposes plaintext passwords or secrets!
        """
        query = "SELECT a.* FROM credential_accounts a WHERE 1=1"
        params = []
        
        if agent_id:
            query += """ AND a.id IN (
                SELECT account_id FROM credential_access_policies 
                WHERE agent_id = ? AND is_active = 1
            )"""
            params.append(agent_id)
            
        if category:
            query += " AND a.category = ?"
            params.append(category)
            
        if project_id:
            query += " AND (a.project_id = ? OR a.project_id = 'global')"
            params.append(project_id)
            
        if search:
            query += " AND (a.name LIKE ? OR a.url LIKE ? OR a.username_or_email LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])
            
        query += " ORDER BY a.updated_at DESC"
        
        async with get_db_connection() as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                accounts = []
                for row in rows:
                    acc = dict(row)
                    # Check if secret exists without exposing it
                    async with db.execute("SELECT 1 FROM credential_secrets WHERE account_id = ? AND encrypted_password != ''", (acc["id"],)) as s_cursor:
                        acc["has_password"] = bool(await s_cursor.fetchone())
                    # Fetch authorized agents
                    async with db.execute("SELECT agent_id, permission_level FROM credential_access_policies WHERE account_id = ? AND is_active = 1", (acc["id"],)) as p_cursor:
                        acc["authorized_agents"] = [dict(pr) for pr in await p_cursor.fetchall()]
                    accounts.append(acc)
                return accounts

    async def get_account_detail(self, account_id: str, agent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM credential_accounts WHERE id = ?", (account_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                acc = dict(row)
                
            # If agent requested, verify permission
            if agent_id:
                async with db.execute("""
                    SELECT permission_level FROM credential_access_policies 
                    WHERE account_id = ? AND agent_id = ? AND is_active = 1
                """, (account_id, agent_id)) as pol_cursor:
                    if not await pol_cursor.fetchone():
                        await self._log_audit(
                            db, account_id=account_id, actor_type="agent", actor_id=agent_id,
                            action="DISCOVER", status="DENIED", details={"reason": "No policy grant"}
                        )
                        await db.commit()
                        raise PermissionError(f"Agent {agent_id} is not authorized to access account {account_id}")
                        
            # Fetch policies
            async with db.execute("SELECT agent_id, permission_level FROM credential_access_policies WHERE account_id = ? AND is_active = 1", (account_id,)) as p_cursor:
                acc["authorized_agents"] = [dict(pr) for pr in await p_cursor.fetchall()]
                
            # Fetch secret metadata
            async with db.execute("SELECT version, last_rotated_at FROM credential_secrets WHERE account_id = ?", (account_id,)) as s_cursor:
                s_row = await s_cursor.fetchone()
                acc["secret_metadata"] = dict(s_row) if s_row else {"version": 0, "last_rotated_at": None}
                acc["has_password"] = bool(s_row)
                
            # Fetch recent access history
            async with db.execute("""
                SELECT actor_id, action, status, timestamp 
                FROM credential_audit_logs 
                WHERE account_id = ? ORDER BY id DESC LIMIT 10
            """, (account_id,)) as a_cursor:
                acc["recent_activity"] = [dict(ar) for ar in await a_cursor.fetchall()]
                
            return acc

    async def reveal_password(self, account_id: str, master_key: str) -> Dict[str, Any]:
        """Owner re-authentication required to decrypt and view plaintext password."""
        async with get_db_connection() as db:
            if not self.vault.verify_master_auth(master_key):
                await self._log_audit(
                    db, account_id=account_id, actor_type="owner", actor_id="owner",
                    action="REVEAL_PASSWORD", status="DENIED", details={"reason": "Invalid master key authentication"}
                )
                await db.commit()
                raise PermissionError("Master key authentication failed")
                
            async with db.execute("SELECT encrypted_password FROM credential_secrets WHERE account_id = ?", (account_id,)) as cursor:
                row = await cursor.fetchone()
                if not row or not row["encrypted_password"]:
                    raise ValueError("No stored password for this account")
                ciphertext = row["encrypted_password"]
                
            plaintext = self.vault.decrypt(ciphertext)
            await self._log_audit(
                db, account_id=account_id, actor_type="owner", actor_id="owner",
                action="REVEAL_PASSWORD", status="SUCCESS", details={"account_id": account_id}
            )
            await db.commit()
            return {"account_id": account_id, "password": plaintext}

    async def request_credential_access(
        self,
        account_id: str,
        agent_id: str,
        task_id: str,
        project_id: str = "global"
    ) -> Dict[str, Any]:
        """
        The Credential Broker access grant endpoint.
        Validates agent permission, creates a 15-minute temporary session,
        and provides controlled authentication parameters.
        """
        async with get_db_connection() as db:
            # 1. Check policy grant
            async with db.execute("""
                SELECT permission_level FROM credential_access_policies 
                WHERE account_id = ? AND agent_id = ? AND is_active = 1
            """, (account_id, agent_id)) as cursor:
                pol = await cursor.fetchone()
                if not pol:
                    await self._log_audit(
                        db, account_id=account_id, actor_type="agent", actor_id=agent_id,
                        task_id=task_id, action="REQUEST_ACCESS", status="DENIED",
                        details={"reason": "Agent not in access grant policy"}
                    )
                    await db.commit()
                    raise PermissionError(f"Access denied: Agent '{agent_id}' has no access grant for account '{account_id}'")
                    
            # 2. Check account status
            async with db.execute("SELECT * FROM credential_accounts WHERE id = ?", (account_id,)) as cursor:
                acc = await cursor.fetchone()
                if not acc or acc["status"] != "ACTIVE":
                    raise ValueError(f"Account is not in ACTIVE state (current: {acc['status'] if acc else 'None'})")
                    
            # 3. Create active session with 15-minute TTL
            session_id = f"sess_{uuid.uuid4().hex[:12]}"
            expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
            now = datetime.utcnow().isoformat()
            
            await db.execute("""
                INSERT INTO credential_access_sessions (session_id, account_id, agent_id, task_id, project_id, status, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
            """, (session_id, account_id, agent_id, task_id, project_id, expires_at, now))
            
            await self._log_audit(
                db, account_id=account_id, actor_type="agent", actor_id=agent_id,
                task_id=task_id, action="GRANT_ACCESS", status="SUCCESS",
                details={"session_id": session_id, "expires_at": expires_at}
            )
            await db.commit()
            
            return {
                "session_id": session_id,
                "account_id": account_id,
                "service_name": acc["name"],
                "login_url": acc["login_url"],
                "username_or_email": acc["username_or_email"],
                "expires_at": expires_at
            }

    async def broker_browser_login(
        self,
        session_id: str,
        page_handle: Any
    ) -> Dict[str, Any]:
        """
        Injects credentials directly into the Playwright page session in memory.
        Passwords are NEVER logged to disk, console, or task output.
        """
        async with get_db_connection() as db:
            # 1. Validate session
            async with db.execute("""
                SELECT s.*, a.login_url, a.username_or_email, sec.encrypted_password
                FROM credential_access_sessions s
                JOIN credential_accounts a ON s.account_id = a.id
                JOIN credential_secrets sec ON a.id = sec.account_id
                WHERE s.session_id = ? AND s.status = 'ACTIVE'
            """, (session_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    raise PermissionError("Invalid or expired credential session")
                session = dict(row)
                
            # Check expiry
            if datetime.fromisoformat(session["expires_at"]) < datetime.utcnow():
                await db.execute("UPDATE credential_access_sessions SET status = 'EXPIRED' WHERE session_id = ?", (session_id,))
                await db.commit()
                raise PermissionError("Credential access session has expired")
                
            # Decrypt password strictly in memory for injection
            plaintext_password = self.vault.decrypt(session["encrypted_password"])
            username = session["username_or_email"]
            account_id = session["account_id"]
            agent_id = session["agent_id"]
            task_id = session["task_id"]

            try:
                # Direct in-memory DOM injection via Playwright
                # Fill username
                user_selectors = ['input[type="email"]', 'input[type="text"]', 'input[name*="user"]', 'input[name*="email"]', 'input[id*="user"]', 'input[id*="email"]']
                filled_user = False
                for sel in user_selectors:
                    if await page_handle.query_selector(sel):
                        await page_handle.fill(sel, username)
                        filled_user = True
                        break
                        
                # Fill password
                pass_selectors = ['input[type="password"]', 'input[name*="pass"]', 'input[id*="pass"]']
                filled_pass = False
                for sel in pass_selectors:
                    if await page_handle.query_selector(sel):
                        await page_handle.fill(sel, plaintext_password)
                        filled_pass = True
                        break

                auth_success = filled_user and filled_pass
                now = datetime.utcnow().isoformat()
                
                if auth_success:
                    await db.execute("UPDATE credential_accounts SET last_successful_login = ? WHERE id = ?", (now, account_id))
                    await self._log_audit(
                        db, account_id=account_id, actor_type="agent", actor_id=agent_id,
                        task_id=task_id, action="AUTH_SUCCESS", status="SUCCESS",
                        details={"message": "In-memory credential injection executed successfully"}
                    )
                else:
                    await db.execute("UPDATE credential_accounts SET last_failed_login = ? WHERE id = ?", (now, account_id))
                    await self._log_audit(
                        db, account_id=account_id, actor_type="agent", actor_id=agent_id,
                        task_id=task_id, action="AUTH_FAILED", status="FAILED",
                        details={"message": "Could not locate matching authentication inputs on page"}
                    )
                    
                await db.commit()
                
                # Securely clean up plaintext variable from local scope
                del plaintext_password
                
                return {
                    "status": "success" if auth_success else "partial",
                    "account_id": account_id,
                    "injected_user": filled_user,
                    "injected_pass": filled_pass
                }

            except Exception as e:
                await self._log_audit(
                    db, account_id=account_id, actor_type="agent", actor_id=agent_id,
                    task_id=task_id, action="AUTH_FAILED", status="FAILED",
                    details={"error": str(e)}
                )
                await db.commit()
                raise

    async def update_credentials(
        self,
        account_id: str,
        new_password: str,
        changed_by: str,
        reason: str = "Routine rotation"
    ) -> Dict[str, Any]:
        """Secure credential update preserving previous version for rollback protection."""
        now = datetime.utcnow().isoformat()
        enc_new_password = self.vault.encrypt(new_password)
        
        async with get_db_connection() as db:
            async with db.execute("SELECT version, encrypted_password FROM credential_secrets WHERE account_id = ?", (account_id,)) as cursor:
                sec_row = await cursor.fetchone()
                if not sec_row:
                    raise ValueError(f"No secret record found for account {account_id}")
                old_version = sec_row["version"]
                old_enc_password = sec_row["encrypted_password"]
                
            # 1. Archive old version into credential_versions
            await db.execute("""
                INSERT INTO credential_versions (account_id, version, encrypted_password, changed_by, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (account_id, old_version, old_enc_password, changed_by, reason, now))
            
            # 2. Update to new version
            new_version = old_version + 1
            await db.execute("""
                UPDATE credential_secrets 
                SET encrypted_password = ?, version = ?, last_rotated_at = ?
                WHERE account_id = ?
            """, (enc_new_password, new_version, now, account_id))
            
            await db.execute("UPDATE credential_accounts SET updated_at = ? WHERE id = ?", (now, account_id))
            
            await self._log_audit(
                db, account_id=account_id, actor_type="agent" if changed_by != "owner" else "owner",
                actor_id=changed_by, action="ROTATE_PASSWORD", status="SUCCESS",
                details={"new_version": new_version, "reason": reason}
            )
            await db.commit()
            
        return {"account_id": account_id, "new_version": new_version, "rotated_at": now}

    async def request_account_registration(
        self,
        agent_id: str,
        task_id: str,
        service_name: str,
        website_url: str,
        category: str,
        reason: str,
        proposed_username: str,
        is_paid: bool = False
    ) -> Dict[str, Any]:
        """Allows an agent to submit a structured registration request requiring owner approval."""
        req_id = f"reg_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO credential_registration_requests (
                    id, agent_id, task_id, service_name, website_url, category,
                    reason, proposed_username_or_email, is_paid, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
            """, (req_id, agent_id, task_id, service_name, website_url, category, reason, proposed_username, 1 if is_paid else 0, now))
            
            await self._log_audit(
                db, account_id=None, actor_type="agent", actor_id=agent_id,
                task_id=task_id, action="REGISTER_REQUEST", status="PENDING_APPROVAL",
                details={"request_id": req_id, "service": service_name, "is_paid": is_paid}
            )
            await db.commit()
            
        return {
            "id": req_id,
            "status": "PENDING",
            "service_name": service_name,
            "requires_owner_approval": True,
            "is_paid": is_paid
        }

    async def list_registration_requests(self) -> List[Dict[str, Any]]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM credential_registration_requests ORDER BY created_at DESC") as cursor:
                return [dict(r) for r in await cursor.fetchall()]

    async def approve_registration(self, request_id: str, owner_decision: str = "APPROVED", notes: str = "") -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        async with get_db_connection() as db:
            await db.execute("""
                UPDATE credential_registration_requests
                SET status = ?, approval_notes = ?, responded_at = ?
                WHERE id = ?
            """, (owner_decision, notes, now, request_id))
            
            await self._log_audit(
                db, account_id=None, actor_type="owner", actor_id="owner",
                action="REGISTER_APPROVED" if owner_decision == "APPROVED" else "REGISTER_REJECTED",
                status="SUCCESS", details={"request_id": request_id, "decision": owner_decision, "notes": notes}
            )
            await db.commit()
        return {"request_id": request_id, "status": owner_decision, "responded_at": now}

    async def set_agent_policy(self, account_id: str, agent_id: str, permission_level: str, is_active: bool = True) -> Dict[str, Any]:
        """Grants or updates access permission level for an agent."""
        policy_id = f"pol_{uuid.uuid4().hex[:8]}"
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO credential_access_policies (id, account_id, agent_id, permission_level, is_active)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO NOTHING
            """, (policy_id, account_id, agent_id, permission_level, 1 if is_active else 0))
            
            await self._log_audit(
                db, account_id=account_id, actor_type="owner", actor_id="owner",
                action="SET_POLICY", status="SUCCESS",
                details={"agent_id": agent_id, "permission_level": permission_level, "active": is_active}
            )
            await db.commit()
        return {"account_id": account_id, "agent_id": agent_id, "permission_level": permission_level}

    async def revoke_session(self, session_id: str) -> Dict[str, Any]:
        async with get_db_connection() as db:
            await db.execute("UPDATE credential_access_sessions SET status = 'REVOKED' WHERE session_id = ?", (session_id,))
            await self._log_audit(
                db, account_id=None, actor_type="owner", actor_id="owner",
                action="REVOKE_SESSION", status="SUCCESS", details={"session_id": session_id}
            )
            await db.commit()
        return {"session_id": session_id, "status": "REVOKED"}

    async def get_audit_logs(self, limit: int = 100, account_id: Optional[str] = None, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM credential_audit_logs WHERE 1=1"
        params = []
        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)
        if agent_id:
            query += " AND actor_id = ?"
            params.append(agent_id)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        async with get_db_connection() as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                logs = []
                for r in rows:
                    log = dict(r)
                    log["details"] = json.loads(log["details"]) if log["details"] else {}
                    logs.append(log)
                return logs

    async def get_credential_health_report(self) -> Dict[str, Any]:
        """Analyzes vault health, security posture, and active policy risks."""
        async with get_db_connection() as db:
            # Total accounts
            async with db.execute("SELECT COUNT(*) as count FROM credential_accounts") as c:
                total_accounts = (await c.fetchone())["count"]
                
            # Missing credentials
            async with db.execute("""
                SELECT COUNT(*) as count FROM credential_accounts a
                LEFT JOIN credential_secrets s ON a.id = s.account_id
                WHERE s.encrypted_password IS NULL OR s.encrypted_password = ''
            """) as c:
                missing_creds = (await c.fetchone())["count"]
                
            # MFA disabled
            async with db.execute("SELECT COUNT(*) as count FROM credential_accounts WHERE mfa_status = 'DISABLED'") as c:
                mfa_disabled = (await c.fetchone())["count"]
                
            # Stale passwords (> 90 days)
            ninety_days_ago = (datetime.utcnow() - timedelta(days=90)).isoformat()
            async with db.execute("""
                SELECT COUNT(*) as count FROM credential_secrets WHERE last_rotated_at < ?
            """, (ninety_days_ago,)) as c:
                stale_passwords = (await c.fetchone())["count"]
                
            # Category breakdown
            async with db.execute("SELECT category, COUNT(*) as count FROM credential_accounts GROUP BY category") as c:
                cat_breakdown = {row["category"]: row["count"] for row in await c.fetchall()}
                
            # Recommendations
            recommendations = []
            if missing_creds > 0:
                recommendations.append(f"{missing_creds} accounts have no encrypted password stored in vault.")
            if mfa_disabled > 0:
                recommendations.append(f"{mfa_disabled} accounts have Multi-Factor Authentication disabled.")
            if stale_passwords > 0:
                recommendations.append(f"{stale_passwords} accounts have credentials older than 90 days; plan rotation.")
                
            return {
                "total_accounts": total_accounts,
                "missing_credentials": missing_creds,
                "mfa_disabled": mfa_disabled,
                "stale_passwords": stale_passwords,
                "category_breakdown": cat_breakdown,
                "recommendations": recommendations,
                "vault_status": "ENCRYPTED_FERNET_0600"
            }

    async def _log_audit(
        self,
        db: aiosqlite.Connection,
        account_id: Optional[str],
        actor_type: str,
        actor_id: str,
        action: str,
        status: str,
        details: Dict[str, Any],
        task_id: Optional[str] = None
    ):
        """Append-only security audit log."""
        await db.execute("""
            INSERT INTO credential_audit_logs (account_id, actor_type, actor_id, task_id, action, status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (account_id, actor_type, actor_id, task_id, action, status, json.dumps(details)))
