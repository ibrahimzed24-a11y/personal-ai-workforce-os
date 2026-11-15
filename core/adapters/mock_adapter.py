import time
import logging
import json
from typing import Dict, Any, List, Optional
from core.adapters.base import ModelProvider

logger = logging.getLogger("ai_workforce_os.adapters.mock")


class DeterministicMockProvider(ModelProvider):
    """
    Deterministic, offline local reasoning engine (MOCKED_OR_SIMULATED).
    Supports both Coordinator DAG planning and the 5-stage Agent Execution Loop
    (Run Policy -> Think -> Act -> Observe -> Deterministic Code Check) across all 32 agents
    by inspecting the agent's SKILL.md output schema and authorized capabilities.
    """
    def __init__(self, model_name: str = "mock-deterministic-v1"):
        self.model_name = model_name
        self.provider_id = "mock"

    @staticmethod
    def _synthesize_value_for_prop(prop_name: str, prop_spec: Dict[str, Any], agent_id: str, task_title: str) -> Any:
        ptype = prop_spec.get("type", "string")
        if ptype == "string":
            if "path" in prop_name:
                return f"logs/deliverable_{agent_id}.md"
            if "status" in prop_name or "verdict" in prop_name:
                return "verified"
            if "id" in prop_name:
                return f"{agent_id}_artifact_01"
            return f"Executed {prop_name} for '{task_title}' via {agent_id}"
        elif ptype == "array":
            return [
                {
                    "item": f"{prop_name}_item_1",
                    "agent": agent_id,
                    "status": "completed",
                    "detail": f"Verified step output for {task_title}"
                }
            ]
        elif ptype == "object":
            return {
                "agent": agent_id,
                "task": task_title,
                "verified": True
            }
        elif ptype in ("number", "integer"):
            if "score" in prop_name or "rate" in prop_name:
                return 98
            return 1
        elif ptype == "boolean":
            return True
        return f"verified_{prop_name}"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        agent_role = context.get("agent_role", "Assistant")
        agent_id = context.get("agent_id") or agent_role
        specialist_id = context.get("specialist_id")
        task_title = context.get("task_title", "Task")
        action = context.get("action", "")
        loop_stage = context.get("loop_stage", "")

        # 1. Coordinator DAG Planning Generation
        if action == "formulate_plan":
            plan = [
                {
                    "step_number": 1,
                    "title": "Market & Technical SEO Research",
                    "description": "Analyze target search keywords, competitive signals, and geographical ranking factors.",
                    "assigned_agent": "market-seo-geo-researcher",
                    "specialist_id": "seo-auditor",
                    "action_type": "research",
                    "parameters": {
                        "topics": ["local_ai_workforce", "autonomous_systems_architecture"],
                        "regions": ["US", "EU"]
                    }
                },
                {
                    "step_number": 2,
                    "title": "Technical Specification & Software Architecture",
                    "description": "Design modular component schemas, interface contracts, and implementation blueprints.",
                    "assigned_agent": "software-engineer",
                    "specialist_id": "backend-specialist",
                    "action_type": "design_architecture",
                    "parameters": {
                        "module": "core_orchestration",
                        "database": "sqlite_wal"
                    }
                },
                {
                    "step_number": 3,
                    "title": "Master Synthesis & Executive Reporting",
                    "description": "Synthesize execution results, compile audit metrics, and package executive deliverable.",
                    "assigned_agent": "master-reporting-agent",
                    "specialist_id": "executive-summarizer",
                    "action_type": "report",
                    "parameters": {
                        "output_format": "executive_markdown"
                    }
                }
            ]
            parsed = {
                "thought": f"Analyzed objective '{task_title}'. Decomposed into 3 specialized DAG steps.",
                "plan": plan
            }
            content = json.dumps(parsed, indent=2)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "content": content,
                "parsed_json": parsed,
                "provider": "mock",
                "model": self.model_name,
                "classification": "mock",
                "usage": {
                    "prompt_tokens": len(system_prompt.split()) + len(user_prompt.split()),
                    "completion_tokens": len(content.split()),
                    "total_tokens": len(system_prompt.split()) + len(user_prompt.split()) + len(content.split())
                },
                "latency_ms": elapsed_ms,
                "raw": {"status": "success", "plan_steps": len(plan)}
            }

        # 2. 5-Stage Agent Execution Loop (Think -> Act -> Observe -> Deterministic Check)
        target_agent = specialist_id or agent_id
        output_schema = context.get("output_schema", {})
        authorized_caps = context.get("authorized_capabilities", [])
        selected_cap = authorized_caps[0] if authorized_caps else "cap:reporting_compile"

        schema_props = output_schema.get("properties", {}) if isinstance(output_schema, dict) else {}
        structured_deliverable: Dict[str, Any] = {}
        for prop_name, prop_spec in schema_props.items():
            structured_deliverable[prop_name] = self._synthesize_value_for_prop(
                prop_name,
                prop_spec if isinstance(prop_spec, dict) else {"type": "string"},
                str(target_agent),
                task_title
            )

        if not structured_deliverable:
            structured_deliverable = {
                "summary": f"Completed '{task_title}' via {target_agent}.",
                "status": "verified"
            }

        parsed_loop = {
            "thought": (
                f"[{target_agent}] Evaluated policy constraints, loaded 3-file context "
                f"({context.get('active_skill', '/' + str(target_agent))}), and selected capability '{selected_cap}' "
                f"to fulfill objective: {user_prompt[:120]}"
            ),
            "selected_capability": selected_cap,
            "tool_action": context.get("requested_tool_action", "execute_capability"),
            "tool_parameters": context.get("step_parameters", {}),
            "deliverable": structured_deliverable,
            "findings": {
                "role": agent_role,
                "agent_id": target_agent,
                "specialist": specialist_id or "core",
                "summary": f"Completed execution for '{task_title}' according to {target_agent} skill procedure.",
                "metrics": {
                    "confidence_score": 0.98,
                    "validation_status": "verified"
                }
            },
            "ready_to_finalize": True,
            "status": "success"
        }

        content = json.dumps(parsed_loop, indent=2)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "content": content,
            "parsed_json": parsed_loop,
            "provider": "mock",
            "model": self.model_name,
            "classification": "mock",
            "usage": {
                "prompt_tokens": len(system_prompt.split()) + len(user_prompt.split()),
                "completion_tokens": len(content.split()),
                "total_tokens": len(system_prompt.split()) + len(user_prompt.split()) + len(content.split())
            },
            "latency_ms": elapsed_ms,
            "raw": {"status": "success", "loop_stage": loop_stage or "think"}
        }
