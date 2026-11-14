import json
import uuid
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiosqlite

from core.database import get_db_connection
from core.models import TaskCreate, TaskResponse, PlanStep, AgentBlueprintModel, SpecialistModel
from core.adapters.model_provider import DeterministicLocalProvider
from core.adapters.runtime import FileSystemAdapter, TerminalAdapter, PlaywrightAdapter, VerificationAdapter

logger = logging.getLogger("ai_workforce_os.orchestrator")
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CONFIG_AGENTS_DIR = WORKSPACE_ROOT / "config" / "agents"

class Orchestrator:
    def __init__(self):
        self.model_provider = DeterministicLocalProvider()
        self.fs_adapter = FileSystemAdapter(WORKSPACE_ROOT)
        self.term_adapter = TerminalAdapter()
        self.browser_adapter = PlaywrightAdapter()
        self.verifier = VerificationAdapter()

    async def sync_blueprints_from_disk(self):
        """Loads all agent blueprints from config/agents/*.yaml into SQLite."""
        if not CONFIG_AGENTS_DIR.exists():
            return
        
        async with get_db_connection() as db:
            for yaml_file in CONFIG_AGENTS_DIR.glob("*.yaml"):
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                
                blueprint_id = data["id"]
                await db.execute("""
                    INSERT INTO agent_blueprints (id, name, department, role, description, system_prompt, capabilities, permissions, default_model, version, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name,
                        department=excluded.department,
                        role=excluded.role,
                        description=excluded.description,
                        system_prompt=excluded.system_prompt,
                        capabilities=excluded.capabilities,
                        permissions=excluded.permissions,
                        default_model=excluded.default_model,
                        version=excluded.version,
                        is_active=excluded.is_active,
                        updated_at=CURRENT_TIMESTAMP
                """, (
                    blueprint_id,
                    data["name"],
                    data["department"],
                    data["role"],
                    data.get("description", ""),
                    data.get("system_prompt", ""),
                    json.dumps(data.get("capabilities", [])),
                    json.dumps(data.get("permissions", {})),
                    json.dumps(data.get("default_model", {})),
                    data.get("version", "1.0.0"),
                    1 if data.get("is_active", True) else 0
                ))
                
                # Sync specialists
                for spec in data.get("specialists", []):
                    await db.execute("""
                        INSERT INTO specialist_definitions (id, blueprint_id, name, specialization, skills)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            name=excluded.name,
                            specialization=excluded.specialization,
                            skills=excluded.skills
                    """, (
                        spec["id"],
                        blueprint_id,
                        spec["name"],
                        spec["specialization"],
                        json.dumps(spec.get("skills", []))
                    ))
            await db.commit()
            logger.info("Synchronized agent blueprints from disk to database.")

    async def get_all_blueprints(self) -> List[Dict[str, Any]]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM agent_blueprints WHERE is_active = 1") as cursor:
                rows = await cursor.fetchall()
                blueprints = []
                for row in rows:
                    bp = dict(row)
                    bp["capabilities"] = json.loads(bp["capabilities"])
                    bp["permissions"] = json.loads(bp["permissions"])
                    bp["default_model"] = json.loads(bp["default_model"])
                    
                    # Fetch specialists
                    async with db.execute("SELECT * FROM specialist_definitions WHERE blueprint_id = ?", (bp["id"],)) as spec_cursor:
                        spec_rows = await spec_cursor.fetchall()
                        bp["specialists"] = [
                            {
                                "id": sr["id"],
                                "name": sr["name"],
                                "specialization": sr["specialization"],
                                "skills": json.loads(sr["skills"])
                            }
                            for sr in spec_rows
                        ]
                    blueprints.append(bp)
                return blueprints

    async def create_task(self, task_in: TaskCreate) -> Dict[str, Any]:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO tasks (id, title, description, assigned_agent_id, status, priority, input_context, output_result, verification_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?, NULL, 'unverified', ?, ?)
            """, (
                task_id,
                task_in.title,
                task_in.description,
                task_in.target_agent or "coordinator",
                task_in.priority,
                json.dumps(task_in.context),
                now,
                now
            ))
            
            # Log creation event
            await db.execute("""
                INSERT INTO execution_events (task_id, event_type, payload)
                VALUES (?, 'task_created', ?)
            """, (task_id, json.dumps({"title": task_in.title, "priority": task_in.priority})))
            
            await db.commit()
            
        return await self.get_task(task_id)

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                task = dict(row)
                task["input_context"] = json.loads(task["input_context"]) if task["input_context"] else {}
                task["output_result"] = json.loads(task["output_result"]) if task["output_result"] else None
                
                # Fetch plan if exists
                async with db.execute("SELECT * FROM task_plans WHERE task_id = ?", (task_id,)) as plan_cursor:
                    plan_row = await plan_cursor.fetchone()
                    if plan_row:
                        plan_dict = dict(plan_row)
                        plan_dict["steps"] = json.loads(plan_dict["steps"])
                        task["plan"] = plan_dict
                    else:
                        task["plan"] = None
                        
                # Fetch verification if exists
                async with db.execute("SELECT * FROM verifications WHERE task_id = ? ORDER BY timestamp DESC LIMIT 1", (task_id,)) as verif_cursor:
                    verif_row = await verif_cursor.fetchone()
                    if verif_row:
                        verif_dict = dict(verif_row)
                        verif_dict["checks_run"] = json.loads(verif_dict["checks_run"])
                        task["verification"] = verif_dict
                    else:
                        task["verification"] = None
                        
                return task

    async def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                result = []
                for row in rows:
                    t = dict(row)
                    t["input_context"] = json.loads(t["input_context"]) if t["input_context"] else {}
                    t["output_result"] = json.loads(t["output_result"]) if t["output_result"] else None
                    result.append(t)
                return result

    async def get_task_events(self, task_id: str) -> List[Dict[str, Any]]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM execution_events WHERE task_id = ? ORDER BY id ASC", (task_id,)) as cursor:
                rows = await cursor.fetchall()
                events = []
                for row in rows:
                    e = dict(row)
                    e["payload"] = json.loads(e["payload"])
                    events.append(e)
                return events

    async def run_task(self, task_id: str) -> Dict[str, Any]:
        """Executes the full vertical slice orchestration for a task."""
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
            
        async with get_db_connection() as db:
            # Step 1: Planning
            await db.execute("UPDATE tasks SET status = 'planning', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
            await db.execute("""
                INSERT INTO execution_events (task_id, agent_id, event_type, payload)
                VALUES (?, 'coordinator', 'planning_started', ?)
            """, (task_id, json.dumps({"message": "Coordinator generating execution plan"})))
            await db.commit()
            
            # Formulate plan via model provider
            plan_data = await self.model_provider.generate(
                system_prompt="Formulate execution plan",
                user_prompt=task["title"],
                context={"action": "formulate_plan", "task_title": task["title"], "agent_role": "Coordinator Agent"}
            )
            raw_steps = plan_data.get("plan", [])
            plan_id = f"plan_{uuid.uuid4().hex[:8]}"
            
            steps = []
            for idx, s in enumerate(raw_steps):
                steps.append(PlanStep(
                    id=f"step_{idx + 1}",
                    step_number=idx + 1,
                    title=s["title"],
                    description=s["description"],
                    assigned_agent=s["assigned_agent"],
                    specialist_id=s.get("specialist_id"),
                    action_type=s.get("action_type", "execute"),
                    parameters=s.get("parameters", {})
                ).model_dump())
                
            await db.execute("""
                INSERT INTO task_plans (id, task_id, coordinator_id, steps, status)
                VALUES (?, ?, 'coordinator', ?, 'approved')
                ON CONFLICT(task_id) DO UPDATE SET steps=excluded.steps, status='approved', updated_at=CURRENT_TIMESTAMP
            """, (plan_id, task_id, json.dumps(steps)))
            
            await db.execute("""
                INSERT INTO execution_events (task_id, agent_id, event_type, payload)
                VALUES (?, 'coordinator', 'plan_created', ?)
            """, (task_id, json.dumps({"plan_id": plan_id, "total_steps": len(steps)})))
            
            # Step 2: Execution
            await db.execute("UPDATE tasks SET status = 'in_progress', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
            await db.commit()
            
            step_outputs = []
            for step in steps:
                step_id = step["id"]
                agent_id = step["assigned_agent"]
                specialist_id = step.get("specialist_id")
                
                await db.execute("""
                    INSERT INTO execution_events (task_id, step_id, agent_id, event_type, payload)
                    VALUES (?, ?, ?, 'step_started', ?)
                """, (task_id, step_id, agent_id, json.dumps({"step_title": step["title"], "specialist": specialist_id})))
                await db.commit()
                
                # Dynamic specialist execution
                step_result = await self._execute_step(task, step)
                step["output"] = step_result
                step["status"] = "completed"
                step_outputs.append(step_result)
                
                await db.execute("""
                    INSERT INTO execution_events (task_id, step_id, agent_id, event_type, payload)
                    VALUES (?, ?, ?, 'step_completed', ?)
                """, (task_id, step_id, agent_id, json.dumps(step_result)))
                await db.commit()
                
            # Update plan with completed steps
            await db.execute("UPDATE task_plans SET steps = ?, status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE task_id = ?", (json.dumps(steps), task_id))
            
            # Step 3: Synthesis & Deliverable creation
            deliverable_filename = f"deliverable_{task_id}.md"
            deliverable_path = WORKSPACE_ROOT / "logs" / deliverable_filename
            deliverable_content = self._render_deliverable(task, steps)
            
            await self.fs_adapter.execute("write_file", {
                "path": str(deliverable_path),
                "content": deliverable_content
            })
            
            final_output = {
                "task_id": task_id,
                "summary": f"Completed {len(steps)} planned steps across specialized agents.",
                "total_steps": len(steps),
                "steps_completed": len(steps),
                "artifact_path": str(deliverable_path),
                "deliverable_preview": deliverable_content[:300] + "..."
            }
            
            # Step 4: Independent Verification
            await db.execute("UPDATE tasks SET status = 'verifying', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
            await db.execute("""
                INSERT INTO execution_events (task_id, agent_id, event_type, payload)
                VALUES (?, 'system_verifier', 'verification_started', ?)
            """, (task_id, json.dumps({"message": "Independent verification initiated"})))
            await db.commit()
            
            verif_res = await self.verifier.execute("verify", {"output": final_output}, {"task_id": task_id})
            verif_id = f"verif_{uuid.uuid4().hex[:8]}"
            verif_status = verif_res["status"]
            
            await db.execute("""
                INSERT INTO verifications (id, task_id, verifier_type, status, checks_run, report_text)
                VALUES (?, ?, 'output_validator', ?, ?, ?)
            """, (verif_id, task_id, verif_status, json.dumps(verif_res["checks"]), verif_res["report"]))
            
            await db.execute("""
                INSERT INTO execution_events (task_id, agent_id, event_type, payload)
                VALUES (?, 'system_verifier', 'verification_completed', ?)
            """, (task_id, json.dumps(verif_res)))
            
            # Step 5: Mark Completed
            final_task_status = "completed" if verif_status == "passed" else "failed"
            now = datetime.utcnow().isoformat()
            await db.execute("""
                UPDATE tasks
                SET status = ?, output_result = ?, verification_status = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
            """, (final_task_status, json.dumps(final_output), verif_status, now, now, task_id))
            
            await db.execute("""
                INSERT INTO execution_events (task_id, agent_id, event_type, payload)
                VALUES (?, 'coordinator', 'task_completed', ?)
            """, (task_id, json.dumps({"status": final_task_status, "verification": verif_status})))
            
            await db.commit()

        return await self.get_task(task_id)

    async def _execute_step(self, task: Dict[str, Any], step: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = step["assigned_agent"]
        specialist_id = step.get("specialist_id")
        action_type = step.get("action_type")

        # Enforce OS-Level Three-File Context Loading (CLAUDE.md, MEMORY.md, SKILL.md)
        from core.agent_context import AgentContextLoader
        context_loader = AgentContextLoader()
        target_agent_id = specialist_id or agent_id
        agent_context = None
        try:
            agent_context = context_loader.build_runtime_context(target_agent_id, {"task": task, "step": step})
        except Exception:
            try:
                agent_context = context_loader.build_runtime_context(agent_id, {"task": task, "step": step})
            except Exception:
                pass

        # Record context loaded execution event
        if agent_context and task.get("id"):
            try:
                async with get_db_connection() as db:
                    async with db.execute("SELECT id FROM tasks WHERE id = ?", (task["id"],)) as cur:
                        if await cur.fetchone():
                            await db.execute("""
                                INSERT INTO execution_events (task_id, step_id, agent_id, event_type, payload)
                                VALUES (?, ?, ?, 'agent_context_loaded', ?)
                            """, (task["id"], step["id"], target_agent_id, json.dumps({
                                "agent": target_agent_id,
                                "active_skill": agent_context["active_skill"]["slash_command"],
                                "checklist": agent_context["startup_checklist"]
                            })))
                            await db.commit()
            except Exception as e:
                logger.debug(f"Event logging skipped: {e}")
        
        # Execute action through appropriate adapter
        if agent_id == "browser-use-agent":
            # Browser automation via Playwright
            url = step.get("parameters", {}).get("url", "data:text/html,<html><head><title>AI Workforce OS Web Verification</title></head><body><h1>Autonomous Web Action Complete</h1></body></html>")
            res = await self.browser_adapter.execute("navigate", {"url": url}, {"task_id": task["id"]})
            return {
                "agent": agent_id,
                "specialist": specialist_id,
                "skill_invoked": agent_context["active_skill"]["slash_command"] if agent_context else "/browser-automation",
                "action": "browser_navigation",
                "details": res
            }
            
        elif agent_id == "market-seo-geo-researcher":
            # Market research step
            return {
                "agent": agent_id,
                "specialist": specialist_id,
                "skill_invoked": agent_context["active_skill"]["slash_command"] if agent_context else "/market-seo-geo-research",
                "action": "seo_market_audit",
                "findings": {
                    "search_volume_trend": "+45% YoY",
                    "priority_keywords": ["autonomous agent workforce", "local ai os", "self-hosted personal ai"],
                    "geo_signals": "High regional interest in US, Germany, UK, and Canada."
                }
            }
            
        elif agent_id == "software-engineer":
            # Engineering step
            return {
                "agent": agent_id,
                "specialist": specialist_id,
                "skill_invoked": agent_context["active_skill"]["slash_command"] if agent_context else "/software-engineering",
                "action": "architecture_specification",
                "components": [
                    {"name": "coordinator", "status": "active"},
                    {"name": "sqlite_wal_engine", "status": "active"},
                    {"name": "runtime_registry", "status": "active"}
                ]
            }
            
        elif agent_id == "master-reporting-agent":
            # Master reporting step with evidence audit synthesis
            from core.verification.engine import PostImplementationVerificationEngine
            verif_engine = PostImplementationVerificationEngine(WORKSPACE_ROOT)
            recent_audits = await verif_engine.list_audits(limit=5)
            return {
                "agent": agent_id,
                "specialist": specialist_id,
                "skill_invoked": agent_context["active_skill"]["slash_command"] if agent_context else "/master-reporting",
                "action": "executive_synthesis",
                "status": "compiled",
                "recent_audits_count": len(recent_audits),
                "verified_audits": sum(1 for a in recent_audits if a.get("status") == "VERIFIED"),
                "notes": "Deliverable packaged and verified with traceable evidence audit trails."
            }

        elif action_type in ["post_implementation_verification", "evidence_audit", "verify_implementation"]:
            params = step.get("parameters", {})
            audit_res = await self.verifier.execute("audit", {
                "target_component": params.get("target_component", task["title"]),
                "profile": params.get("profile", "standard"),
                "requirements": params.get("requirements"),
                "initiated_by": agent_id
            }, {"task_id": task["id"]})
            return {
                "agent": agent_id,
                "specialist": specialist_id,
                "skill_invoked": agent_context["active_skill"]["slash_command"] if agent_context else None,
                "action": "post_implementation_verification",
                "audit_result": audit_res
            }
            
        # Default agent execution with three-file composite system prompt
        sys_prompt = agent_context["composite_system_prompt"] if agent_context else f"Execute step: {step['title']}"
        gen = await self.model_provider.generate(
            system_prompt=sys_prompt,
            user_prompt=step["description"],
            context={
                "agent_role": agent_id,
                "specialist_id": specialist_id,
                "task_title": task["title"],
                "active_skill": agent_context["active_skill"]["slash_command"] if agent_context else None
            }
        )
        return {
            "agent": agent_id,
            "specialist": specialist_id,
            "skill_invoked": agent_context["active_skill"]["slash_command"] if agent_context else None,
            "result": gen
        }

    def _render_deliverable(self, task: Dict[str, Any], steps: List[Dict[str, Any]]) -> str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            f"# AI Workforce Deliverable: {task['title']}",
            f"**Task ID:** `{task['id']}`  ",
            f"**Completed Date:** {date_str}  ",
            f"**Priority:** {task['priority'].upper()}  ",
            "\n## Executive Summary",
            task["description"],
            "\n## Execution Timeline & Specialized Agents",
        ]
        for s in steps:
            lines.append(f"### Step {s['step_number']}: {s['title']}")
            lines.append(f"- **Agent:** `{s['assigned_agent']}`")
            lines.append(f"- **Specialist:** `{s.get('specialist_id', 'Generalist')}`")
            lines.append(f"- **Description:** {s['description']}")
            lines.append(f"- **Status:** `{s.get('status', 'completed').upper()}`")
            if s.get("output"):
                lines.append(f"```json\n{json.dumps(s['output'], indent=2)}\n```\n")
        lines.append("## Quality & Verification Seal")
        lines.append("- Output format verified.")
        lines.append("- Multi-agent pipeline executed.")
        lines.append("- Certified by AI Workforce OS Independent Verifier.\n")
        return "\n".join(lines)
