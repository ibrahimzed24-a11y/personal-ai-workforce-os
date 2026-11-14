import json
import uuid
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.database import get_db_connection

logger = logging.getLogger("ai_workforce_os.requirements")
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CONFIG_AGENTS_DIR = WORKSPACE_ROOT / "config" / "agents"

class RequirementsManager:
    """
    Evaluates new user-provided requirements against current architecture,
    derives impact assessments, proposes change plans, and applies updates
    without rebuilding unrelated components.
    """
    async def list_requirements(self) -> List[Dict[str, Any]]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM system_requirements ORDER BY created_at DESC") as cursor:
                rows = await cursor.fetchall()
                result = []
                for row in rows:
                    r = dict(row)
                    r["specification"] = json.loads(r["specification"]) if r["specification"] else {}
                    r["change_plan"] = json.loads(r["change_plan"]) if r["change_plan"] else []
                    result.append(r)
                return result

    async def submit_requirement(self, category: str, title: str, specification: Dict[str, Any]) -> Dict[str, Any]:
        req_id = f"req_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        # Formulate change plan based on category
        change_plan = self._evaluate_and_plan(category, title, specification)
        
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO system_requirements (id, category, title, specification, change_plan, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'proposed', ?)
            """, (req_id, category, title, json.dumps(specification), json.dumps(change_plan), now))
            await db.commit()
            
        return {
            "id": req_id,
            "category": category,
            "title": title,
            "specification": specification,
            "change_plan": change_plan,
            "status": "proposed",
            "created_at": now
        }

    def _evaluate_and_plan(self, category: str, title: str, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        plan = []
        if category == "agent":
            agent_id = spec.get("id", title.lower().replace(" ", "-"))
            plan.append({
                "action": "create_agent_blueprint",
                "target_file": f"config/agents/{agent_id}.yaml",
                "component": "AgentRegistry",
                "details": f"Generate declarative blueprint for {spec.get('name', title)}"
            })
            plan.append({
                "action": "db_sync",
                "component": "SQLite_agent_blueprints",
                "details": f"Upsert record for agent {agent_id}"
            })
            if spec.get("specialists"):
                plan.append({
                    "action": "register_specialists",
                    "component": "SQLite_specialist_definitions",
                    "details": f"Register {len(spec['specialists'])} specialists"
                })
        elif category == "model":
            plan.append({
                "action": "update_provider_config",
                "target_file": "config/runtimes.yaml",
                "component": "ModelProviderRegistry",
                "details": f"Register new provider endpoint: {spec.get('provider_name', title)}"
            })
        elif category == "permission":
            plan.append({
                "action": "update_permission_policy",
                "target_file": "config/permissions.yaml",
                "component": "ApprovalGate",
                "details": f"Configure approval rule: {spec.get('rule_name', title)}"
            })
        else:
            plan.append({
                "action": "generic_configuration_update",
                "component": "SystemConfig",
                "details": f"Apply configuration change for {title}"
            })
        return plan

    async def apply_requirement(self, req_id: str) -> Dict[str, Any]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM system_requirements WHERE id = ?", (req_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    raise ValueError(f"Requirement not found: {req_id}")
                req = dict(row)
                
            spec = json.loads(req["specification"])
            category = req["category"]
            
            # Apply changes
            if category == "agent":
                agent_id = spec.get("id", req["title"].lower().replace(" ", "-"))
                yaml_data = {
                    "id": agent_id,
                    "name": spec.get("name", req["title"]),
                    "department": spec.get("department", "Custom Operations"),
                    "role": spec.get("role", "Specialized Agent"),
                    "description": spec.get("description", "Dynamically added specialized agent."),
                    "system_prompt": spec.get("system_prompt", f"You are the {spec.get('name', req['title'])}."),
                    "capabilities": spec.get("capabilities", ["general_task_execution"]),
                    "permissions": spec.get("permissions", {"can_execute_code": False, "can_modify_filesystem": True}),
                    "default_model": spec.get("default_model", {"provider": "mock_deterministic", "name": "deterministic-v1"}),
                    "specialists": spec.get("specialists", []),
                    "version": "1.0.0",
                    "is_active": True
                }
                yaml_path = CONFIG_AGENTS_DIR / f"{agent_id}.yaml"
                with open(yaml_path, "w", encoding="utf-8") as f:
                    yaml.dump(yaml_data, f, sort_keys=False)
                    
            now = datetime.utcnow().isoformat()
            await db.execute("""
                UPDATE system_requirements
                SET status = 'applied', applied_at = ?
                WHERE id = ?
            """, (now, req_id))
            await db.commit()
            
            # Trigger orchestrator sync
            from core.orchestrator import Orchestrator
            orch = Orchestrator()
            await orch.sync_blueprints_from_disk()
            
            return {"status": "applied", "requirement_id": req_id, "applied_at": now}
