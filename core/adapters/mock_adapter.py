import time
import logging
import json
from typing import Dict, Any, List, Optional
from core.adapters.base import ModelProvider

logger = logging.getLogger("ai_workforce_os.adapters.mock")

class DeterministicMockProvider(ModelProvider):
    """
    Deterministic, offline local reasoning engine.
    Ensures the OS can formulate execution plans, synthesize deliverables,
    and make decisions completely offline with zero API cost and zero network latency.
    """
    def __init__(self, model_name: str = "mock-deterministic-v1"):
        self.model_name = model_name
        self.provider_id = "mock"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        agent_role = context.get("agent_role", "Assistant")
        specialist_id = context.get("specialist_id")
        task_title = context.get("task_title", "Task")
        action = context.get("action", "")

        # 1. Coordinator Planning Generation
        if "Coordinator" in agent_role or action == "formulate_plan":
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
            content = json.dumps({"thought": f"Analyzed objective '{task_title}'. Decomposed into 3 specialized steps.", "plan": plan}, indent=2)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "content": content,
                "parsed_json": {"thought": f"Analyzed objective '{task_title}'. Decomposed into 3 specialized steps.", "plan": plan},
                "provider": "mock",
                "model": self.model_name,
                "classification": "mock",
                "usage": {"prompt_tokens": len(system_prompt.split()) + len(user_prompt.split()), "completion_tokens": len(content.split()), "total_tokens": len(system_prompt.split()) + len(user_prompt.split()) + len(content.split())},
                "latency_ms": elapsed_ms,
                "raw": {"status": "success", "plan_steps": len(plan)}
            }

        # 2. General Specialist Execution Generation
        findings = {
            "role": agent_role,
            "specialist": specialist_id or "core",
            "summary": f"Completed execution for '{task_title}' according to {agent_role} procedures.",
            "metrics": {
                "confidence_score": 0.98,
                "validation_status": "verified"
            }
        }
        content = json.dumps({
            "thought": f"Specialist [{specialist_id or 'core'}] executed analysis under {agent_role}.",
            "status": "success",
            "findings": findings
        }, indent=2)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "content": content,
            "parsed_json": json.loads(content),
            "provider": "mock",
            "model": self.model_name,
            "classification": "mock",
            "usage": {"prompt_tokens": len(system_prompt.split()) + len(user_prompt.split()), "completion_tokens": len(content.split()), "total_tokens": len(system_prompt.split()) + len(user_prompt.split()) + len(content.split())},
            "latency_ms": elapsed_ms,
            "raw": {"status": "success"}
        }
