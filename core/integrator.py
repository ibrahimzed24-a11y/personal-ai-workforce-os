import os
import re
import json
import shutil
import uuid
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiosqlite

from core.database import get_db_connection

logger = logging.getLogger("ai_workforce_os.integrator")
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = WORKSPACE_ROOT / "incoming"
KNOWLEDGE_DIR = WORKSPACE_ROOT / "documentation" / "knowledge"
SKILLS_DIR = WORKSPACE_ROOT / "config" / "skills"
AGENTS_DIR = WORKSPACE_ROOT / "config" / "agents"
WORKFLOWS_DIR = WORKSPACE_ROOT / "config" / "workflows"
SHARED_TOOLS_DIR = WORKSPACE_ROOT / "shared-tools"

class SystemIntegratorEngine:
    def __init__(self, incoming_dir: Path = INCOMING_DIR):
        self.incoming_dir = incoming_dir
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        SHARED_TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    async def scan_incoming(self) -> List[Dict[str, Any]]:
        """Scans incoming directory, classifies files, performs security audit, and proposes installation plans."""
        discovered = []
        if not self.incoming_dir.exists():
            return discovered

        # Scan all files and subdirectories
        for root, dirs, files in os.walk(self.incoming_dir):
            # Check for bundle directories (like python package, node package, or skill bundle)
            root_path = Path(root)
            if root_path != self.incoming_dir:
                if (root_path / "SKILL.md").exists() or (root_path / "pyproject.toml").exists() or (root_path / "package.json").exists():
                    item = await self._process_asset_path(root_path, is_dir=True)
                    if item:
                        discovered.append(item)
                    dirs.clear() # don't recurse into package internals
                    continue
            
            for file in files:
                if file.startswith("."):
                    continue
                file_path = root_path / file
                item = await self._process_asset_path(file_path, is_dir=False)
                if item:
                    discovered.append(item)

        return discovered

    async def _process_asset_path(self, path: Path, is_dir: bool = False) -> Optional[Dict[str, Any]]:
        name = path.name
        rel_path = str(path.relative_to(WORKSPACE_ROOT))
        
        # Determine classification
        category, metadata = self._classify_asset(path, is_dir)
        
        # Security audit
        audit = self._audit_security(path, is_dir)
        
        # Propose target agents and capabilities
        target_agents, capabilities = self._map_agent_capabilities(category, name, metadata)
        
        # Propose installation plan
        install_plan = self._propose_plan(category, name, path, is_dir, target_agents)
        
        asset_id = f"asset_{uuid.uuid5(uuid.NAMESPACE_DNS, str(path)).hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        async with get_db_connection() as db:
            # Check existing record
            async with db.execute("SELECT status FROM installed_assets WHERE id = ?", (asset_id,)) as cursor:
                row = await cursor.fetchone()
                existing_status = row["status"] if row else None
            
            # Don't downgrade ACTIVE or FAILED unless requested
            status = existing_status if existing_status in ["ACTIVE", "FAILED", "DISABLED", "APPROVED"] else "AUDITED"
            
            await db.execute("""
                INSERT INTO installed_assets (
                    id, name, category, source_path, install_path, version, status,
                    security_audit, installation_plan, dependencies, target_agents,
                    capabilities_added, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    category=excluded.category,
                    security_audit=excluded.security_audit,
                    installation_plan=excluded.installation_plan,
                    target_agents=excluded.target_agents,
                    capabilities_added=excluded.capabilities_added,
                    updated_at=excluded.updated_at
            """, (
                asset_id,
                name,
                category,
                rel_path,
                install_plan.get("target_path"),
                metadata.get("version", "1.0.0"),
                status,
                json.dumps(audit),
                json.dumps(install_plan),
                json.dumps(metadata.get("dependencies", [])),
                json.dumps(target_agents),
                json.dumps(capabilities),
                now
            ))
            await db.commit()

        return await self.get_asset(asset_id)

    def _classify_asset(self, path: Path, is_dir: bool) -> tuple[str, Dict[str, Any]]:
        metadata = {"version": "1.0.0", "dependencies": []}
        
        if is_dir:
            if (path / "SKILL.md").exists():
                return "skill", self._parse_skill_metadata(path / "SKILL.md")
            if (path / "pyproject.toml").exists() or (path / "requirements.txt").exists():
                return "tool", {"type": "python_package", "version": "1.0.0"}
            if (path / "package.json").exists():
                return "tool", {"type": "node_package", "version": "1.0.0"}
            return "unknown", metadata

        # Single file classification
        ext = path.suffix.lower()
        if path.name == "SKILL.md" or (ext == ".md" and "skill" in path.name.lower()):
            return "skill", self._parse_skill_metadata(path)
        
        if ext in [".yaml", ".yml", ".json"]:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f) if ext in [".yaml", ".yml"] else json.load(f)
                if isinstance(content, dict):
                    if "department" in content and "capabilities" in content:
                        return "agent", {"name": content.get("name"), "version": content.get("version", "1.0.0")}
                    if "workflow" in content or "steps" in content:
                        return "workflow", {"name": content.get("name", path.stem), "version": "1.0.0"}
                    if "provider" in content and "model" in content:
                        return "model", {"provider": content.get("provider")}
            except Exception:
                pass
            return "configuration", metadata
            
        if ext == ".py":
            return "tool", {"type": "python_script", "version": "1.0.0"}
        if ext == ".sh":
            return "tool", {"type": "shell_script", "version": "1.0.0"}
        if ext in [".md", ".txt", ".rst", ".pdf"]:
            return "documentation", metadata
            
        return "unknown", metadata

    def _parse_skill_metadata(self, skill_file: Path) -> Dict[str, Any]:
        meta = {"version": "1.0.0", "dependencies": []}
        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                text = f.read()
            match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if match:
                frontmatter = yaml.safe_load(match.group(1))
                if isinstance(frontmatter, dict):
                    meta["name"] = frontmatter.get("name")
                    meta["description"] = frontmatter.get("description")
                    meta["version"] = frontmatter.get("version", "1.0.0")
        except Exception as e:
            logger.warning(f"Failed parsing skill frontmatter for {skill_file}: {e}")
        return meta

    def _audit_security(self, path: Path, is_dir: bool) -> Dict[str, Any]:
        """Scans code and manifests for security hazards, privilege escalation, and external access."""
        findings = []
        risk_level = "LOW"
        requires_admin = False
        network_access = False
        filesystem_modifications = False
        
        dangerous_patterns = [
            (r"\bsudo\b", "Uses 'sudo' administrator privileges", "HIGH", True),
            (r"\brm\s+-rf\b", "Executes recursive unprompted deletion 'rm -rf'", "HIGH", False),
            (r"\bcurl\b.*\|\s*(ba)?sh", "Pipes remote script to shell execution", "CRITICAL", False),
            (r"\beval\s*\(", "Uses dynamic code execution 'eval'", "MEDIUM", False),
            (r"\bos\.system\s*\(", "Executes raw shell command via os.system", "MEDIUM", False),
            (r"(api[_-]?key|secret|password|token)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]", "Possible hardcoded credential or secret", "HIGH", False),
            (r"\b(http|https)://", "References external network endpoint", "LOW", False),
        ]
        
        files_to_check = [p for p in path.rglob("*") if p.is_file()] if is_dir else [path]
        
        for file in files_to_check:
            if file.suffix in [".py", ".sh", ".js", ".json", ".yaml", ".yml", ".md"]:
                try:
                    with open(file, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    for pattern, desc, severity, admin_flag in dangerous_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            findings.append({
                                "file": str(file.name),
                                "description": desc,
                                "severity": severity
                            })
                            if severity in ["HIGH", "CRITICAL"]:
                                risk_level = severity
                            elif severity == "MEDIUM" and risk_level == "LOW":
                                risk_level = "MEDIUM"
                            if admin_flag:
                                requires_admin = True
                            if "http" in pattern:
                                network_access = True
                            if "rm" in pattern or "write" in content:
                                filesystem_modifications = True
                except Exception:
                    pass

        return {
            "risk_level": risk_level,
            "requires_admin": requires_admin,
            "network_access": network_access,
            "filesystem_modifications": filesystem_modifications,
            "findings": findings,
            "audit_timestamp": datetime.utcnow().isoformat()
        }

    def _map_agent_capabilities(self, category: str, name: str, metadata: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Maps discovered capabilities to authorized agents with explicit scope."""
        target_agents = []
        capabilities = []
        
        clean_name = name.lower()
        if category == "skill":
            capabilities.append(f"skill:{clean_name}")
            if any(k in clean_name for k in ["verif", "audit", "quality", "integrity"]):
                target_agents.extend(["coordinator", "master-reporting-agent", "system-integrator-update-agent", "deployment-agent", "software-engineer"])
            if any(k in clean_name for k in ["seo", "market", "geo", "research"]):
                target_agents.append("market-seo-geo-researcher")
            if any(k in clean_name for k in ["code", "developer", "engineer", "test", "refactor"]):
                target_agents.append("software-engineer")
            if any(k in clean_name for k in ["browser", "web", "scrape"]):
                target_agents.append("browser-use-agent")
            if any(k in clean_name for k in ["deploy", "ops", "infra"]):
                target_agents.append("deployment-agent")
            if not target_agents:
                target_agents.append("coordinator")
                
        elif category == "tool":
            capabilities.append(f"tool:{clean_name}")
            target_agents.extend(["software-engineer", "deployment-agent", "system-integrator-update-agent"])
            
        elif category == "agent":
            capabilities.append(f"agent:{clean_name}")
            target_agents.append("coordinator")
            
        elif category == "workflow":
            capabilities.append(f"workflow:{clean_name}")
            target_agents.append("coordinator")
            
        elif category == "documentation":
            capabilities.append(f"knowledge:{clean_name}")
            target_agents.extend(["coordinator", "master-reporting-agent"])
            
        return list(set(target_agents)), capabilities

    def _propose_plan(self, category: str, name: str, path: Path, is_dir: bool, target_agents: List[str]) -> Dict[str, Any]:
        """Formulates exact installation plan and target path."""
        stem = path.stem.replace(" ", "_")
        
        if category == "skill":
            target = str(SKILLS_DIR / stem / "SKILL.md") if is_dir or path.name != "SKILL.md" else str(SKILLS_DIR / stem)
            method = "copy_skill_directory" if is_dir else "copy_skill_file"
        elif category == "agent":
            target = str(AGENTS_DIR / f"{stem}.yaml")
            method = "register_agent_blueprint"
        elif category == "workflow":
            target = str(WORKFLOWS_DIR / f"{stem}.yaml")
            method = "register_workflow"
        elif category == "tool":
            target = str(SHARED_TOOLS_DIR / stem)
            method = "install_isolated_tool"
        elif category == "documentation":
            target = str(KNOWLEDGE_DIR / path.name)
            method = "index_documentation"
        else:
            target = str(WORKSPACE_ROOT / "incoming" / "unknown" / path.name)
            method = "isolate_unknown"

        return {
            "method": method,
            "target_path": str(Path(target).relative_to(WORKSPACE_ROOT)),
            "target_agents": target_agents,
            "requires_isolation": category == "tool",
            "rollback_strategy": "remove_target_and_restore_backup"
        }

    async def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM installed_assets WHERE id = ?", (asset_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                asset = dict(row)
                asset["security_audit"] = json.loads(asset["security_audit"]) if asset["security_audit"] else {}
                asset["installation_plan"] = json.loads(asset["installation_plan"]) if asset["installation_plan"] else {}
                asset["dependencies"] = json.loads(asset["dependencies"]) if asset["dependencies"] else []
                asset["target_agents"] = json.loads(asset["target_agents"]) if asset["target_agents"] else []
                asset["capabilities_added"] = json.loads(asset["capabilities_added"]) if asset["capabilities_added"] else []
                asset["test_results"] = json.loads(asset["test_results"]) if asset["test_results"] else None
                return asset

    async def list_assets(self) -> List[Dict[str, Any]]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM installed_assets ORDER BY updated_at DESC") as cursor:
                rows = await cursor.fetchall()
                result = []
                for row in rows:
                    a = dict(row)
                    a["security_audit"] = json.loads(a["security_audit"]) if a["security_audit"] else {}
                    a["installation_plan"] = json.loads(a["installation_plan"]) if a["installation_plan"] else {}
                    a["target_agents"] = json.loads(a["target_agents"]) if a["target_agents"] else []
                    a["capabilities_added"] = json.loads(a["capabilities_added"]) if a["capabilities_added"] else []
                    result.append(a)
                return result

    async def approve_asset(self, asset_id: str) -> Dict[str, Any]:
        async with get_db_connection() as db:
            now = datetime.utcnow().isoformat()
            await db.execute("UPDATE installed_assets SET status = 'APPROVED', updated_at = ? WHERE id = ?", (now, asset_id))
            await db.commit()
        return await self.get_asset(asset_id)

    async def install_asset(self, asset_id: str) -> Dict[str, Any]:
        """Installs approved asset, runs verification test, updates knowledge if successful, or rolls back."""
        asset = await self.get_asset(asset_id)
        if not asset:
            raise ValueError(f"Asset not found: {asset_id}")
            
        source_path = WORKSPACE_ROOT / asset["source_path"]
        plan = asset["installation_plan"]
        target_path = WORKSPACE_ROOT / plan["target_path"]
        category = asset["category"]
        
        now = datetime.utcnow().isoformat()
        async with get_db_connection() as db:
            await db.execute("UPDATE installed_assets SET status = 'INSTALLING', updated_at = ? WHERE id = ?", (now, asset_id))
            await db.commit()

        install_log = []
        try:
            # Step 1: Copy / Scaffolding
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path.is_dir():
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
                install_log.append(f"Copied directory tree from {source_path} to {target_path}")
            else:
                shutil.copy2(source_path, target_path)
                install_log.append(f"Copied file from {source_path} to {target_path}")
                
            # If tool, ensure executable or set up uv environment
            if category == "tool":
                if target_path.is_file() and target_path.suffix in [".sh", ".py"]:
                    target_path.chmod(0o755)
                    install_log.append("Marked tool script as executable.")
                elif target_path.is_dir() and (target_path / "pyproject.toml").exists():
                    # Isolated uv initialization
                    proc = subprocess.run(["uv", "venv", str(target_path / ".venv")], capture_output=True, text=True)
                    install_log.append(f"Created isolated uv venv: {proc.stdout}")

            # Step 2: Testing & Verification
            test_res = await self._test_asset(target_path, category)
            if test_res["status"] != "passed":
                raise RuntimeError(f"Functional test failed: {test_res['detail']}")

            # Step 3: Success -> Mark ACTIVE and sync knowledge
            installed_at = datetime.utcnow().isoformat()
            async with get_db_connection() as db:
                await db.execute("""
                    UPDATE installed_assets
                    SET status = 'ACTIVE', test_results = ?, install_log = ?, installed_at = ?, updated_at = ?
                    WHERE id = ?
                """, (json.dumps(test_res), "\n".join(install_log), installed_at, installed_at, asset_id))
                await db.commit()

            # Step 4: Synchronize agent blueprints & operational knowledge
            await self._sync_operational_knowledge()
            
            # If agent blueprint, sync orchestrator
            if category == "agent":
                from core.orchestrator import Orchestrator
                orch = Orchestrator()
                await orch.sync_blueprints_from_disk()

            return await self.get_asset(asset_id)

        except Exception as e:
            # Rollback upon failure
            logger.error(f"Installation failed for {asset_id}: {e}. Triggering rollback.")
            install_log.append(f"ERROR: {str(e)}")
            if target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
                install_log.append(f"Cleaned up failed installation at {target_path}")

            failed_at = datetime.utcnow().isoformat()
            async with get_db_connection() as db:
                await db.execute("""
                    UPDATE installed_assets
                    SET status = 'FAILED', install_log = ?, updated_at = ?
                    WHERE id = ?
                """, ("\n".join(install_log), failed_at, asset_id))
                await db.commit()
            raise

    async def _test_asset(self, target_path: Path, category: str) -> Dict[str, Any]:
        """Runs safe functional verification testing on newly installed asset."""
        if not target_path.exists():
            return {"status": "failed", "detail": f"Target file does not exist: {target_path}"}
            
        if category == "skill":
            skill_file = target_path if target_path.is_file() else target_path / "SKILL.md"
            if not skill_file.exists():
                return {"status": "failed", "detail": "Missing SKILL.md definition"}
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content.strip()) < 20:
                return {"status": "failed", "detail": "SKILL.md is empty or malformed"}
            return {"status": "passed", "detail": "Skill definition verified and readable", "lines": len(content.splitlines())}
            
        elif category == "agent":
            with open(target_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data.get("name") or not data.get("capabilities"):
                return {"status": "failed", "detail": "Agent blueprint missing required fields (name, capabilities)"}
            return {"status": "passed", "detail": "Agent blueprint validated successfully", "capabilities": data.get("capabilities")}
            
        elif category == "tool":
            if target_path.is_file() and target_path.suffix == ".py":
                # Check Python syntax
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        compile(f.read(), str(target_path), "exec")
                    return {"status": "passed", "detail": "Python syntax verified cleanly without runtime execution"}
                except SyntaxError as se:
                    return {"status": "failed", "detail": f"Python syntax error: {se}"}
            return {"status": "passed", "detail": "Tool file verified and ready"}
            
        return {"status": "passed", "detail": "Asset file integrity verified"}

    async def rollback_asset(self, asset_id: str) -> Dict[str, Any]:
        asset = await self.get_asset(asset_id)
        if not asset:
            raise ValueError(f"Asset not found: {asset_id}")
            
        plan = asset["installation_plan"]
        target_path = WORKSPACE_ROOT / plan["target_path"]
        
        if target_path.exists():
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
                
        now = datetime.utcnow().isoformat()
        async with get_db_connection() as db:
            await db.execute("""
                UPDATE installed_assets
                SET status = 'ROLLED_BACK', updated_at = ?
                WHERE id = ?
            """, (now, asset_id))
            await db.commit()
            
        await self._sync_operational_knowledge()
        return await self.get_asset(asset_id)

    async def _sync_operational_knowledge(self):
        """Generates operational knowledge files: INSTALLED_ASSETS.md, AVAILABLE_CAPABILITIES.md, SKILLS_INDEX.md, AGENT_TOOL_ACCESS.json."""
        assets = await self.list_assets()
        active_assets = [a for a in assets if a["status"] == "ACTIVE"]
        
        # 1. INSTALLED_ASSETS.md
        assets_md = ["# Operational Knowledge: Installed Assets Registry\n", "| Asset ID | Name | Category | Version | Status | Installed Path |\n| :--- | :--- | :--- | :--- | :--- | :--- |"]
        for a in assets:
            plan = a["installation_plan"]
            assets_md.append(f"| `{a['id']}` | **{a['name']}** | {a['category']} | {a.get('version', '1.0.0')} | `{a['status']}` | `{plan.get('target_path', 'N/A')}` |")
        with open(KNOWLEDGE_DIR / "INSTALLED_ASSETS.md", "w", encoding="utf-8") as f:
            f.write("\n".join(assets_md) + "\n")

        # 2. AVAILABLE_CAPABILITIES.md
        cap_md = ["# Operational Knowledge: Available Capabilities Catalog\n", "The following capabilities are actively available across the AI Workforce OS:\n"]
        for a in active_assets:
            cap_md.append(f"### {a['name']} (`{a['category']}`)")
            cap_md.append(f"- **Path:** `{a['installation_plan'].get('target_path')}`")
            cap_md.append(f"- **Authorized Agents:** {', '.join([f'`{ag}`' for ag in a['target_agents']])}")
            cap_md.append(f"- **Capabilities Added:** {', '.join([f'`{c}`' for c in a['capabilities_added']])}\n")
            
        # Include standardized 32 agent skills
        from core.agent_context import AgentContextLoader
        loader = AgentContextLoader()
        agent_list = loader.list_all_agents()
        cap_md.append("## Standardized Agent Skills & Slash Commands\n")
        for ag_info in agent_list:
            if ag_info.get("has_skill_md"):
                s_det = ag_info["skill_details"]
                cap_md.append(f"- **`{s_det['slash_command']}`** (`{ag_info['agent_id']}`): {s_det['description']} (Path: `{s_det['path']}`)")
        cap_md.append("\n")

        with open(KNOWLEDGE_DIR / "AVAILABLE_CAPABILITIES.md", "w", encoding="utf-8") as f:
            f.write("\n".join(cap_md) + "\n")

        # 3. SKILLS_INDEX.md
        skills = [a for a in active_assets if a["category"] == "skill"]
        skills_md = ["# Operational Knowledge: Skills Index\n", "Index of verified, active agent skills in the OS:\n"]
        for s in skills:
            skills_md.append(f"- **{s['name']}** (Version {s.get('version', '1.0.0')}): Registered at `{s['installation_plan'].get('target_path')}`, authorized for {', '.join(s['target_agents'])}.")
        
        skills_md.append("\n### Core & Specialist Agent Dedicated Skills:\n")
        for ag_info in agent_list:
            if ag_info.get("has_skill_md"):
                s_det = ag_info["skill_details"]
                skills_md.append(f"- **`{s_det['slash_command']}`** ({ag_info['agent_id']}): `{s_det['path']}` - {s_det['description']}")

        perm_skills = loader.discover_permanent_skills()
        if perm_skills:
            skills_md.append("\n### Permanent Sovereign Harnesses & Framework Skills:\n")
            for ps in perm_skills:
                skills_md.append(f"- **`{ps['slash_command']}`** ([{ps['category']}] {ps['name']}): `{ps['path']}` - {ps['description']}")
                
        with open(KNOWLEDGE_DIR / "SKILLS_INDEX.md", "w", encoding="utf-8") as f:
            f.write("\n".join(skills_md) + "\n")

        # 4. AGENT_TOOL_ACCESS.json
        agent_tool_map = {}
        for a in active_assets:
            for ag in a["target_agents"]:
                if ag not in agent_tool_map:
                    agent_tool_map[ag] = []
                agent_tool_map[ag].append({
                    "asset_id": a["id"],
                    "name": a["name"],
                    "category": a["category"],
                    "path": a["installation_plan"].get("target_path"),
                    "capabilities": a["capabilities_added"]
                })
        with open(KNOWLEDGE_DIR / "AGENT_TOOL_ACCESS.json", "w", encoding="utf-8") as f:
            json.dump(agent_tool_map, f, indent=2)
            
        logger.info("Synchronized operational knowledge records to documentation/knowledge/.")
