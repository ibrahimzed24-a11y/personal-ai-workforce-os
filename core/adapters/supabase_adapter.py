import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger("ai_workforce_os.supabase_adapter")

class SupabaseAdapter:
    """
    Sovereign Cloud Adapter for Supabase PostgreSQL.
    Provides async PostgREST API and RPC communication between the
    local MacBook workstation and the cloud operational database.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        service_role_key: Optional[str] = None,
        anon_key: Optional[str] = None,
        timeout: float = 15.0
    ):
        self.supabase_url = (supabase_url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.service_role_key = service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self.anon_key = anon_key or os.environ.get("SUPABASE_ANON_KEY", "")
        self.timeout = timeout
        
        # Primary auth key: prefer service_role_key for worker/backend operations
        self.active_key = self.service_role_key or self.anon_key
        self.rest_url = f"{self.supabase_url}/rest/v1" if self.supabase_url else ""

    def is_configured(self) -> bool:
        """Check if required Supabase credentials are configured."""
        return bool(self.supabase_url and self.active_key)

    def _get_headers(self, prefer: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "apikey": self.active_key,
            "Authorization": f"Bearer {self.active_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    async def heartbeat_node(
        self,
        node_id: str,
        status: str = "online",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a heartbeat ping to register/update the local MacBook runtime node.
        """
        if not self.is_configured():
            return {"success": False, "error": "Supabase credentials not configured", "offline": True}

        payload = {
            "p_node_id": node_id,
            "p_status": status,
            "p_metadata": metadata or {}
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.rest_url}/rpc/heartbeat_runtime_node",
                    headers=self._get_headers(),
                    json=payload
                )
                if res.is_success:
                    return {"success": True, "data": res.json()}
                return {
                    "success": False,
                    "status_code": res.status_code,
                    "error": res.text
                }
        except Exception as e:
            logger.warning(f"Failed to heartbeat node {node_id} to Supabase: {e}")
            return {"success": False, "error": str(e), "offline": True}

    async def claim_hybrid_task(
        self,
        node_id: str,
        lease_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        Atomically claim the next eligible task from the hybrid queue using FOR UPDATE SKIP LOCKED.
        """
        if not self.is_configured():
            return {"success": False, "error": "Supabase credentials not configured", "offline": True}

        payload = {
            "p_node_id": node_id,
            "p_lease_seconds": lease_seconds
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.rest_url}/rpc/claim_hybrid_task",
                    headers=self._get_headers(),
                    json=payload
                )
                if res.is_success:
                    tasks = res.json()
                    task = tasks[0] if (isinstance(tasks, list) and len(tasks) > 0) else None
                    return {"success": True, "task": task}
                return {
                    "success": False,
                    "status_code": res.status_code,
                    "error": res.text
                }
        except Exception as e:
            logger.debug(f"Failed to claim hybrid task from Supabase: {e}")
            return {"success": False, "error": str(e), "offline": True}

    async def complete_hybrid_task(
        self,
        task_id: str,
        node_id: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mark a claimed task as completed with output results.
        """
        if not self.is_configured():
            return {"success": False, "error": "Supabase credentials not configured", "offline": True}

        payload = {
            "p_task_id": task_id,
            "p_node_id": node_id,
            "p_result": result
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.rest_url}/rpc/complete_hybrid_task",
                    headers=self._get_headers(),
                    json=payload
                )
                if res.is_success:
                    return {"success": True, "data": res.json()}
                return {
                    "success": False,
                    "status_code": res.status_code,
                    "error": res.text
                }
        except Exception as e:
            logger.error(f"Failed to complete task {task_id} in Supabase: {e}")
            return {"success": False, "error": str(e)}

    async def fail_hybrid_task(
        self,
        task_id: str,
        node_id: str,
        error_message: str,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Mark a claimed task as failed with error details, optionally re-queuing.
        """
        if not self.is_configured():
            return {"success": False, "error": "Supabase credentials not configured", "offline": True}

        payload = {
            "p_task_id": task_id,
            "p_node_id": node_id,
            "p_error": error_message,
            "p_retry": retry
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.rest_url}/rpc/fail_hybrid_task",
                    headers=self._get_headers(),
                    json=payload
                )
                if res.is_success:
                    return {"success": True, "data": res.json()}
                return {
                    "success": False,
                    "status_code": res.status_code,
                    "error": res.text
                }
        except Exception as e:
            logger.error(f"Failed to record task failure {task_id} in Supabase: {e}")
            return {"success": False, "error": str(e)}

    async def submit_hybrid_task(
        self,
        idempotency_key: str,
        title: str,
        assigned_agent_id: str,
        description: Optional[str] = None,
        runtime_target: str = "any",
        required_capabilities: Optional[List[str]] = None,
        priority: int = 50,
        input_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit a new hybrid task to the queue with idempotency protection.
        """
        if not self.is_configured():
            return {"success": False, "error": "Supabase credentials not configured", "offline": True}

        record = {
            "idempotency_key": idempotency_key,
            "title": title,
            "description": description,
            "assigned_agent_id": assigned_agent_id,
            "runtime_target": runtime_target,
            "required_capabilities": required_capabilities or [],
            "priority": priority,
            "input_payload": input_payload or {},
            "status": "pending"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.rest_url}/hybrid_tasks",
                    headers=self._get_headers(prefer="return=representation"),
                    json=record
                )
                if res.is_success:
                    data = res.json()
                    return {"success": True, "task": data[0] if isinstance(data, list) else data}
                # Check for 409 conflict (idempotency key violation)
                if res.status_code == 409:
                    # Query existing task
                    query_res = await client.get(
                        f"{self.rest_url}/hybrid_tasks?idempotency_key=eq.{idempotency_key}",
                        headers=self._get_headers()
                    )
                    if query_res.is_success and query_res.json():
                        return {"success": True, "task": query_res.json()[0], "idempotent_replay": True}
                return {
                    "success": False,
                    "status_code": res.status_code,
                    "error": res.text
                }
        except Exception as e:
            logger.error(f"Failed to submit hybrid task: {e}")
            return {"success": False, "error": str(e)}

    async def sync_agent_blueprints(self, blueprints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upsert all 32 agent blueprints into Supabase agent_blueprints table.
        """
        if not self.is_configured():
            return {"success": False, "error": "Supabase credentials not configured", "offline": True}

        records = []
        for bp in blueprints:
            records.append({
                "id": bp.get("id"),
                "name": bp.get("name"),
                "department": bp.get("department", "general"),
                "role": bp.get("role", "specialist"),
                "description": bp.get("description", ""),
                "system_prompt": bp.get("system_prompt", ""),
                "capabilities": bp.get("capabilities", []),
                "permissions": bp.get("permissions", []),
                "default_model": bp.get("default_model", "gemini-2.5-flash"),
                "version": bp.get("version", "2.0.0"),
                "is_active": bp.get("is_active", True)
            })

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.rest_url}/agent_blueprints",
                    headers=self._get_headers(prefer="resolution=merge-duplicates"),
                    json=records
                )
                if res.is_success:
                    return {"success": True, "count": len(records)}
                return {
                    "success": False,
                    "status_code": res.status_code,
                    "error": res.text
                }
        except Exception as e:
            logger.error(f"Failed to sync blueprints to Supabase: {e}")
            return {"success": False, "error": str(e)}
