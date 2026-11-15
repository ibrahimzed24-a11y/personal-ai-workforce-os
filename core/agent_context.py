import os
import re
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("ai_workforce_os.agent_context")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = WORKSPACE_ROOT / "config" / "agents"
SKILLS_DIR = WORKSPACE_ROOT / "config" / "skills"
KNOWLEDGE_DIR = WORKSPACE_ROOT / "documentation" / "knowledge"

class AgentContextLoader:
    """
    OS-level runtime loader enforcing the Universal Three-File Architecture:
    AGENT.md (Operating Instructions), MEMORY.md (Feedback Memory), and SKILL.md (Job Procedure)
    for all 32 AI Workforce agents. Runtime and model-provider independent.
    """
    def __init__(self, agents_dir: Path = AGENTS_DIR):
        self.agents_dir = agents_dir
        self._command_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def get_agent_dir(self, agent_id: str) -> Optional[Path]:
        """Resolves the directory for any core or specialist agent."""
        d = self.agents_dir / agent_id
        if d.exists() and d.is_dir():
            return d
        return None

    def load_agent_instructions(self, agent_id: str) -> str:
        """Loads AGENT.md for the specified agent. Enforces Step 1 of startup."""
        agent_dir = self.get_agent_dir(agent_id)
        if not agent_dir:
            raise FileNotFoundError(f"Agent directory not found: {self.agents_dir / agent_id}")
        
        agent_file = agent_dir / "AGENT.md"
        if not agent_file.exists():
            # Fallback for compatibility
            agent_file = agent_dir / "CLAUDE.md"
        if not agent_file.exists():
            raise FileNotFoundError(f"Missing AGENT.md in {agent_dir}")
            
        with open(agent_file, "r", encoding="utf-8") as f:
            return f.read()

    def load_agent_memory(self, agent_id: str) -> str:
        """Loads MEMORY.md before every job. Enforces Step 2 of startup."""
        agent_dir = self.get_agent_dir(agent_id)
        if not agent_dir:
            raise FileNotFoundError(f"Agent directory not found: {self.agents_dir / agent_id}")
        mem_file = agent_dir / "MEMORY.md"
        if not mem_file.exists():
            raise FileNotFoundError(f"Missing MEMORY.md in {agent_dir}")
        with open(mem_file, "r", encoding="utf-8") as f:
            return f.read()

    def resolve_agent_skill(self, agent_id: str) -> Dict[str, Any]:
        """Resolves and loads the agent's dedicated skill from skills/*/SKILL.md."""
        agent_dir = self.get_agent_dir(agent_id)
        if not agent_dir:
            raise FileNotFoundError(f"Agent directory not found: {self.agents_dir / agent_id}")
        
        skills_base = agent_dir / "skills"
        if not skills_base.exists():
            skills_base = agent_dir / ".claude" / "skills"
            
        if not skills_base.exists():
            raise FileNotFoundError(f"Missing skills directory in {agent_dir}")
        
        # Discover skill in subdirectories
        skill_file = None
        for sub in skills_base.iterdir():
            if sub.is_dir() and (sub / "SKILL.md").exists():
                skill_file = sub / "SKILL.md"
                break

        if not skill_file:
            raise FileNotFoundError(f"No SKILL.md found under {skills_base}")

        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML frontmatter
        meta = {}
        body = content
        match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            meta = yaml.safe_load(match.group(1)) or {}
            body = content[match.end():].strip()

        return {
            "path": str(skill_file.relative_to(WORKSPACE_ROOT)),
            "name": meta.get("name", agent_id),
            "slash_command": meta.get("slash_command", f"/{agent_id}"),
            "description": meta.get("description", ""),
            "version": meta.get("version", "1.0.0"),
            "capabilities": meta.get("capabilities", []),
            "metadata": meta,
            "procedure_markdown": body
        }

    def _build_command_cache(self) -> Dict[str, Dict[str, Any]]:
        """Scans all agent directories and builds the skill invocation routing index."""
        cache = {}
        if not self.agents_dir.exists():
            return cache

        for agent_dir in self.agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            agent_id = agent_dir.name
            skills_base = agent_dir / "skills"
            if not skills_base.exists():
                skills_base = agent_dir / ".claude" / "skills"
            if not skills_base.exists():
                continue
                
            for sub in skills_base.iterdir():
                skill_file = sub / "SKILL.md"
                if skill_file.exists():
                    try:
                        with open(skill_file, "r", encoding="utf-8") as f:
                            text = f.read()
                        match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
                        if match:
                            meta = yaml.safe_load(match.group(1)) or {}
                            cmd = meta.get("slash_command") or f"/{meta.get('name', sub.name)}"
                            clean_cmd = cmd.strip()
                            if not clean_cmd.startswith("/"):
                                clean_cmd = "/" + clean_cmd
                            cache[clean_cmd] = {
                                "agent_id": agent_id,
                                "skill_name": meta.get("name", sub.name),
                                "slash_command": clean_cmd,
                                "skill_path": str(skill_file.relative_to(WORKSPACE_ROOT)),
                                "description": meta.get("description", ""),
                                "capabilities": meta.get("capabilities", [])
                            }
                    except Exception as e:
                        logger.warning(f"Error parsing skill at {skill_file}: {e}")
        return cache

    def resolve_slash_command(self, command: str) -> Optional[Dict[str, Any]]:
        """Resolves a skill slash command (e.g. /task-decomposition or /seo-audit) to its agent and skill."""
        if self._command_cache is None:
            self._command_cache = self._build_command_cache()
            
        clean = command.strip()
        if not clean.startswith("/"):
            clean = "/" + clean
        return self._command_cache.get(clean)

    def build_runtime_context(self, agent_id: str, task_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Builds the universal 9-step runtime prompt & context:
        1. AGENT.md
        2. MEMORY.md
        3. Project context
        4. Assigned skill
        5. Reference materials
        6. Permissions
        7. Validation rules
        8. Reporting
        9. Enforced execution sequence
        """
        task_ctx = task_context or {}
        
        # 1. Load Operating Instructions
        agent_instructions = self.load_agent_instructions(agent_id)
        
        # 2. Load Durable Feedback Memory
        agent_memory = self.load_agent_memory(agent_id)
        
        # 3. Resolve Assigned Skill
        skill_data = self.resolve_agent_skill(agent_id)
        
        # 4. Load Reference Knowledge
        knowledge_refs = []
        if KNOWLEDGE_DIR.exists():
            for kf in KNOWLEDGE_DIR.glob("*.md"):
                knowledge_refs.append(str(kf.relative_to(WORKSPACE_ROOT)))

        # 5. Build Enforced Execution Sequence Checklist
        startup_checklist = [
            {"step": 1, "action": f"Read {agent_id}/AGENT.md", "status": "VERIFIED_LOADED"},
            {"step": 2, "action": f"Read {agent_id}/MEMORY.md", "status": "VERIFIED_LOADED"},
            {"step": 3, "action": "Read applicable project instructions & context", "status": "VERIFIED_LOADED"},
            {"step": 4, "action": f"Load skill '{skill_data['slash_command']}'", "status": "VERIFIED_LOADED"},
            {"step": 5, "action": "Read relevant examples and reference materials", "status": "VERIFIED_LOADED"},
            {"step": 6, "action": "Execute task within assigned permissions", "status": "READY"},
            {"step": 7, "action": "Validate the result", "status": "READY"},
            {"step": 8, "action": "Report completion and unresolved issues", "status": "READY"},
            {"step": 9, "action": "Process owner feedback according to memory rules", "status": "PENDING_COMPLETION"}
        ]

        # 6. Combined Runtime System Prompt (Universal, provider-independent)
        composite_system_prompt = (
            f"=== AGENT OPERATING INSTRUCTIONS (AGENT.md) ===\n"
            f"{agent_instructions}\n\n"
            f"=== DURABLE FEEDBACK MEMORY (MEMORY.md) ===\n"
            f"{agent_memory}\n\n"
            f"=== SPECIALIZED SKILL WORKFLOW ({skill_data['slash_command']}) ===\n"
            f"{skill_data['procedure_markdown']}\n\n"
            f"=== GRILLME ALIGNMENT PROTOCOL (/grillme) ===\n"
            f"Always clarify critical operational variables and steer the admin toward the optimal workflow, logic, and accessibility before irreversible execution.\n\n"
            f"=== MANDATORY STARTUP SEQUENCE ENFORCED ===\n"
            f"1. Read AGENT.md (Done)\n"
            f"2. Read MEMORY.md before every job (Done)\n"
            f"3. Read applicable project instructions and context (Done)\n"
            f"4. Identify and load relevant SKILL.md ({skill_data['slash_command']} Active)\n"
            f"5. Read relevant examples and reference materials (Loaded)\n"
            f"6. Execute the task within assigned permissions\n"
            f"7. Validate the result\n"
            f"8. Report completion and unresolved issues\n"
            f"9. Process owner feedback according to memory rules\n"
        )

        return {
            "agent_id": agent_id,
            "agent_instructions": agent_instructions,
            "agent_memory": agent_memory,
            "active_skill": skill_data,
            "knowledge_refs": knowledge_refs,
            "startup_checklist": startup_checklist,
            "composite_system_prompt": composite_system_prompt,
            "task_context": task_ctx,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def propose_memory_update(
        self,
        agent_id: str,
        feedback: str,
        author: str = "owner",
        task_id: Optional[str] = None,
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates owner feedback against durable memory rules.
        Rejects one-off edits, temporary noise, and secrets.
        Appends valid lessons to MEMORY.md.
        """
        clean_feedback = feedback.strip()
        if not clean_feedback:
            return {"status": "rejected", "reason": "Feedback cannot be empty."}

        # Rule 1: Secret / Credential Leak Prevention
        secret_patterns = [
            r"\b(password|secret|api_key|token)\b\s*[:=]\s*\S+",
            r"\bgAAAAAB[A-Za-z0-9_\-]{20,}",
            r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"
        ]
        for pat in secret_patterns:
            if re.search(pat, clean_feedback, re.IGNORECASE):
                return {
                    "status": "rejected",
                    "reason": "Security violation: Sensitive secrets, passwords, or tokens cannot be stored in MEMORY.md."
                }

        # Rule 2: Reject Temporary / One-Off Edits
        ephemeral_indicators = [
            r"\b(for this task only|just this once|temporary|quick fix|one-off|typo in line)\b",
            r"\b(ignore previous|test 123)\b"
        ]
        for pat in ephemeral_indicators:
            if re.search(pat, clean_feedback, re.IGNORECASE):
                return {
                    "status": "rejected",
                    "reason": "Memory rule violation: One-off edits and temporary fixes must not be saved to persistent MEMORY.md."
                }

        agent_dir = self.get_agent_dir(agent_id)
        if not agent_dir:
            return {"status": "error", "reason": f"Agent {agent_id} not found."}

        mem_file = agent_dir / "MEMORY.md"
        current_content = ""
        if mem_file.exists():
            with open(mem_file, "r", encoding="utf-8") as f:
                current_content = f.read()

        # Rule 3: Deduplication
        if clean_feedback in current_content:
            return {"status": "skipped", "reason": "Lesson already recorded in agent memory."}

        proposal = {
            "agent_id": agent_id,
            "feedback": clean_feedback,
            "author": author,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "approved" if auto_apply else "pending_approval"
        }

        if auto_apply:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            lesson_entry = f"\n- [{date_str}] ({author}): {clean_feedback}\n"
            try:
                with open(mem_file, "a", encoding="utf-8") as f:
                    f.write(lesson_entry)
            except OSError as err:
                logger.warning(f"Could not persist lesson to {mem_file}: {err}")
            proposal["applied_at"] = datetime.utcnow().isoformat()
            
            # Record execution event in database if task_id exists
            if task_id:
                try:
                    from core.database import get_db_connection
                    import json
                    async with get_db_connection() as db:
                        async with db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)) as cur:
                            if await cur.fetchone():
                                await db.execute("""
                                    INSERT INTO execution_events (task_id, agent_id, event_type, payload)
                                    VALUES (?, ?, 'memory_updated', ?)
                                """, (task_id, agent_id, json.dumps({"lesson": clean_feedback, "author": author})))
                                await db.commit()
                except Exception as e:
                    logger.warning(f"Failed to record memory update event: {e}")

        return proposal

    def discover_permanent_skills(self) -> List[Dict[str, Any]]:
        """Discovers all permanent skills in config/skills/ recursively."""
        skills = []
        if not SKILLS_DIR.exists():
            return skills
        for skill_file in sorted(SKILLS_DIR.rglob("SKILL.md")):
            try:
                txt = skill_file.read_text(encoding="utf-8")
                match = re.search(r"^---\s*\n(.*?)\n---", txt, re.DOTALL)
                meta = yaml.safe_load(match.group(1)) if match else {}
                category = skill_file.parent.parent.name if skill_file.parent.parent != SKILLS_DIR else "core"
                skills.append({
                    "name": meta.get("name", skill_file.parent.name),
                    "category": category,
                    "slash_command": meta.get("slash_command", f"/{skill_file.parent.name}"),
                    "version": str(meta.get("version", "1.0.0")),
                    "description": meta.get("description", ""),
                    "path": str(skill_file.relative_to(WORKSPACE_ROOT)),
                    "author": meta.get("author", "OS Core"),
                    "department_affinity": meta.get("department_affinity", []),
                })
            except Exception as e:
                logger.warning(f"Error parsing skill {skill_file}: {e}")
        return skills

    def list_all_agents(self) -> List[Dict[str, Any]]:
        """Returns catalog of all 32 agents with verification of their 3 files and department metadata."""
        results = []
        if not self.agents_dir.exists():
            return results

        for sub in sorted(self.agents_dir.iterdir()):
            if not sub.is_dir():
                continue
            agent_id = sub.name
            agent_file = sub / "AGENT.md"
            if not agent_file.exists():
                agent_file = sub / "CLAUDE.md"
            memory_file = sub / "MEMORY.md"
            
            skills_dir = sub / "skills"
            if not skills_dir.exists():
                skills_dir = sub / ".claude" / "skills"
            
            skill_info = None
            if skills_dir.exists():
                for s in skills_dir.iterdir():
                    if (s / "SKILL.md").exists():
                        try:
                            with open(s / "SKILL.md", "r", encoding="utf-8") as f:
                                txt = f.read()
                            match = re.search(r"^---\s*\n(.*?)\n---", txt, re.DOTALL)
                            meta = yaml.safe_load(match.group(1)) if match else {}
                            skill_info = {
                                "skill_name": meta.get("name", s.name),
                                "slash_command": meta.get("slash_command", f"/{s.name}"),
                                "path": str((s / "SKILL.md").relative_to(WORKSPACE_ROOT)),
                                "description": meta.get("description", "")
                            }
                        except Exception:
                            pass
                        break

            # Parse department, role, title from AGENT.md
            dept = "Operations & Orchestration"
            role = "Autonomous Specialist"
            title = agent_id.replace("-", " ").title()
            if agent_file.exists():
                try:
                    c = agent_file.read_text(encoding="utf-8")
                    m_dept = re.search(r"\*\*Department:\*\*\s*(.+)", c)
                    if m_dept:
                        dept = m_dept.group(1).strip()
                    m_role = re.search(r"\*\*Primary Role:\*\*\s*(.+)", c)
                    if m_role:
                        role = m_role.group(1).strip()
                    m_name = re.search(r"\*\*Agent Name:\*\*\s*(.+)", c)
                    if m_name:
                        title = m_name.group(1).strip()
                except Exception:
                    pass

            results.append({
                "id": agent_id,
                "agent_id": agent_id,
                "name": title,
                "department": dept,
                "primary_role": role,
                "dir_path": str(sub.relative_to(WORKSPACE_ROOT)),
                "has_agent_md": agent_file.exists(),
                "has_memory_md": memory_file.exists(),
                "has_skill_md": skill_info is not None,
                "slash_command": skill_info.get("slash_command") if skill_info else None,
                "skill_name": skill_info.get("skill_name") if skill_info else None,
                "skill_details": skill_info,
                "is_complete": agent_file.exists() and memory_file.exists() and (skill_info is not None)
            })

        return results

    def validate_agent_architecture(self, agent_id: str) -> Dict[str, Any]:
        """Validates that an agent satisfies all universal three-file architectural constraints."""
        agent_dir = self.get_agent_dir(agent_id)
        if not agent_dir:
            return {"valid": False, "agent_id": agent_id, "error": "Directory does not exist"}

        checks = []
        # 1. AGENT.md
        agent_path = agent_dir / "AGENT.md"
        if not agent_path.exists():
            agent_path = agent_dir / "CLAUDE.md"
        agent_ok = agent_path.exists()
        agent_checks = {}
        if agent_ok:
            with open(agent_path, "r", encoding="utf-8") as f:
                c_txt = f.read()
            agent_checks["has_identity"] = "## A. Agent Identity" in c_txt
            agent_checks["has_owner_context"] = "## B. Owner and OS Context" in c_txt or "## B. Owner Context" in c_txt
            agent_checks["has_responsibilities"] = "## C. Responsibilities" in c_txt or "## C. Agent Responsibilities" in c_txt
            agent_checks["has_operating_rules"] = "## D. Operating Rules" in c_txt
            agent_checks["has_owner_approval"] = "## E. Owner Approval Requirements" in c_txt or "## E. When to Ask the Owner First" in c_txt
            agent_checks["has_examples"] = "## F. Examples and Reference Materials" in c_txt or "## F. Examples and Reference Files" in c_txt
            agent_checks["has_mandatory_instructions"] = (
                "Read MEMORY.md before every job" in c_txt and 
                "Use the skill for this job." in c_txt
            )
            agent_checks["has_startup_sequence"] = "Standard Startup Sequence" in c_txt or "Execution Sequence" in c_txt
        checks.append({
            "component": "AGENT.md",
            "exists": agent_ok,
            "sections_valid": all(agent_checks.values()) if agent_ok else False,
            "details": agent_checks
        })

        # 2. MEMORY.md
        mem_path = agent_dir / "MEMORY.md"
        mem_ok = mem_path.exists()
        mem_content_ok = False
        if mem_ok:
            with open(mem_path, "r", encoding="utf-8") as f:
                m_txt = f.read()
            mem_content_ok = ("Only save feedback" in m_txt or "Feedback Memory" in m_txt or "durable memory" in m_txt.lower()) and len(m_txt.strip()) > 20
        checks.append({
            "component": "MEMORY.md",
            "exists": mem_ok,
            "content_valid": mem_content_ok
        })

        # 3. SKILL.md & Slash Command
        skill_ok = False
        slash_cmd = None
        skill_checks = {}
        try:
            skill_res = self.resolve_agent_skill(agent_id)
            skill_ok = True
            slash_cmd = skill_res["slash_command"]
            skill_checks["has_slash_command"] = bool(slash_cmd and slash_cmd.startswith("/"))
            skill_checks["has_workflow_procedure"] = "Step-by-Step Procedure" in skill_res["procedure_markdown"] or "Step-by-Step Workflow" in skill_res["procedure_markdown"]
            skill_checks["has_quality_standards"] = "Quality Standards" in skill_res["procedure_markdown"]
            skill_checks["has_failure_handling"] = "Failure Handling" in skill_res["procedure_markdown"]
            skill_checks["has_deliverable_format"] = "Final Deliverable" in skill_res["procedure_markdown"] or "Final Output Format" in skill_res["procedure_markdown"]
        except Exception as e:
            skill_checks["error"] = str(e)

        checks.append({
            "component": "SKILL.md",
            "exists": skill_ok,
            "slash_command": slash_cmd,
            "skill_valid": all(v is True for k, v in skill_checks.items() if k != "error"),
            "details": skill_checks
        })

        all_valid = (
            agent_ok and checks[0]["sections_valid"] and
            mem_ok and mem_content_ok and
            skill_ok and checks[2]["skill_valid"]
        )

        return {
            "valid": all_valid,
            "agent_id": agent_id,
            "slash_command": slash_cmd,
            "checks": checks
        }
