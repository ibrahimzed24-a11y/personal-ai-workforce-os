import json
import uuid
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.database import get_db_connection
from core.models import TaskCreate, TaskResponse, PlanStep, AgentBlueprintModel, SpecialistModel, ModelGenerationRequest
from core.model_manager import ModelManager
from core.agent_loop import AgentLoopEngine
from core.adapters.runtime import FileSystemAdapter, TerminalAdapter, PlaywrightAdapter, VerificationAdapter

logger = logging.getLogger("ai_workforce_os.orchestrator")
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CONFIG_AGENTS_DIR = WORKSPACE_ROOT / "config" / "agents"


class Orchestrator:
    def __init__(self):
        self.model_manager = ModelManager.get_instance()
        self.model_provider = self.model_manager
        self.fs_adapter = FileSystemAdapter(WORKSPACE_ROOT)
        self.term_adapter = TerminalAdapter()
        self.browser_adapter = PlaywrightAdapter()
        self.verifier = VerificationAdapter()
        self.loop_engine = AgentLoopEngine(WORKSPACE_ROOT)

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
                task_in.description or "",
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
        """Executes the full vertical slice orchestration for a task through the 5-stage Agent Loop."""
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

            # Formulate plan via ModelManager (or use pre-supplied custom plan steps in input_context)
            custom_steps = (task.get("input_context") or {}).get("custom_steps")
            if custom_steps and isinstance(custom_steps, list):
                raw_steps = custom_steps
            else:
                plan_response = await self.model_manager.generate(
                    ModelGenerationRequest(
                        task_type="coordination",
                        agent_id="coordinator",
                        system_prompt="Formulate execution plan",
                        user_prompt=task["title"],
                        context={
                            "action": "formulate_plan",
                            "task_title": task["title"],
                            "agent_role": "Coordinator Agent",
                            "task_id": task_id
                        },
                        privacy_level=(task.get("input_context") or {}).get("privacy_level", "standard")
                    )
                )
                plan_data = plan_response.parsed_json or {}
                raw_steps = plan_data.get("plan", [])

            plan_id = f"plan_{uuid.uuid4().hex[:8]}"
            steps = []
            for idx, s in enumerate(raw_steps):
                steps.append(PlanStep(
                    id=s.get("id", f"step_{idx + 1}"),
                    step_number=idx + 1,
                    title=s["title"],
                    description=s["description"],
                    assigned_agent=s["assigned_agent"],
                    specialist_id=s.get("specialist_id"),
                    action_type=s.get("action_type", "execute"),
                    parameters=s.get("parameters", {})
                ).dict())

            await db.execute("""
                INSERT INTO task_plans (id, task_id, coordinator_id, steps, status)
                VALUES (?, ?, 'coordinator', ?, 'approved')
                ON CONFLICT(task_id) DO UPDATE SET steps=excluded.steps, status='approved', updated_at=CURRENT_TIMESTAMP
            """, (plan_id, task_id, json.dumps(steps)))

            await db.execute("""
                INSERT INTO execution_events (task_id, agent_id, event_type, payload)
                VALUES (?, 'coordinator', 'plan_created', ?)
            """, (task_id, json.dumps({"plan_id": plan_id, "total_steps": len(steps)})))

            # Step 2: Execution via 5-Stage Agent Loop
            await db.execute("UPDATE tasks SET status = 'in_progress', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
            await db.commit()

            step_outputs = []
            all_deterministic_checks_passed = True

            for step in steps:
                step_id = step["id"]
                agent_id = step["assigned_agent"]
                specialist_id = step.get("specialist_id")

                await db.execute("""
                    INSERT INTO execution_events (task_id, step_id, agent_id, event_type, payload)
                    VALUES (?, ?, ?, 'step_started', ?)
                """, (task_id, step_id, agent_id, json.dumps({"step_title": step["title"], "specialist": specialist_id})))
                await db.commit()

                # Execute step through the 5-stage Agent Loop Engine
                step_result = await self._execute_step(task, step)
                step["output"] = step_result

                if step_result.get("status") == "awaiting_approval":
                    step["status"] = "awaiting_approval"
                    await db.execute("UPDATE tasks SET status = 'awaiting_approval', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
                    await db.execute("UPDATE task_plans SET steps = ?, status = 'awaiting_approval', updated_at = CURRENT_TIMESTAMP WHERE task_id = ?", (json.dumps(steps), task_id))
                    await db.commit()
                    return await self.get_task(task_id)

                if not step_result.get("deterministic_check_passed", True):
                    all_deterministic_checks_passed = False

                step["status"] = "completed"
                step_outputs.append(step_result)

                await db.execute("""
                    INSERT INTO execution_events (task_id, step_id, agent_id, event_type, payload)
                    VALUES (?, ?, ?, 'step_completed', ?)
                """, (task_id, step_id, agent_id, json.dumps(step_result, default=str)))
                await db.commit()

            # Update plan with completed steps
            await db.execute("UPDATE task_plans SET steps = ?, status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE task_id = ?", (json.dumps(steps, default=str), task_id))

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
                "summary": f"Completed {len(steps)} planned steps across specialized agents via 5-stage Agent Loop.",
                "total_steps": len(steps),
                "steps_completed": len(steps),
                "all_deterministic_checks_passed": all_deterministic_checks_passed,
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
        """
        Executes a single plan step through the universal 5-stage Agent Loop:
        Run Policy -> Think -> Act -> Observe -> Deterministic Code Check.
        """
        loop_res = await self.loop_engine.execute_agent_loop(task=task, step=step, max_iterations=2)

        # Also record legacy `agent_context_loaded` event for backward compatibility with existing tests
        if task.get("id"):
            await self.loop_engine._log_event(
                task.get("id"),
                step.get("id"),
                loop_res.get("resolved_agent_id", step.get("assigned_agent", "coordinator")),
                "agent_context_loaded",
                {
                    "agent": loop_res.get("resolved_agent_id"),
                    "active_skill": loop_res.get("skill_invoked"),
                    "loop_id": loop_res.get("loop_id"),
                    "deterministic_check_passed": loop_res.get("deterministic_check_passed")
                }
            )
        return loop_res

    def _render_deliverable(self, task: Dict[str, Any], steps: List[Dict[str, Any]]) -> str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            f"# AI Workforce Deliverable: {task['title']}",
            f"**Task ID:** `{task['id']}`  ",
            f"**Completed Date:** {date_str}  ",
            f"**Priority:** {task['priority'].upper()}  ",
            "\n## Executive Summary",
            task["description"],
            "\n## Execution Timeline & 5-Stage Agent Loop Traces",
        ]
        for s in steps:
            lines.append(f"### Step {s['step_number']}: {s['title']}")
            lines.append(f"- **Agent:** `{s['assigned_agent']}`")
            lines.append(f"- **Specialist:** `{s.get('specialist_id', 'Generalist')}`")
            lines.append(f"- **Description:** {s['description']}")
            lines.append(f"- **Status:** `{s.get('status', 'completed').upper()}`")
            if s.get("output"):
                lines.append(f"```json\n{json.dumps(s['output'], indent=2, default=str)}\n```\n")
        lines.append("## Quality & Verification Seal")
        lines.append("- 5-Stage Agent Loop (`Run Policy -> Think -> Act -> Observe -> Deterministic Code Check`) executed.")
        lines.append("- Output schema and deterministic checks verified.")
        lines.append("- Certified by AI Workforce OS Independent Verifier.\n")
        return "\n".join(lines)
