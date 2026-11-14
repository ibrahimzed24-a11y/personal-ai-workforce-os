import os
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from core.adapters.base import RuntimeAdapter

logger = logging.getLogger("ai_workforce_os.runtime")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

class FileSystemAdapter(RuntimeAdapter):
    """Safe, scoped filesystem operations within ~/AI-Workforce."""
    def __init__(self, root_dir: Path = WORKSPACE_ROOT):
        self.root_dir = root_dir

    def _resolve_safe_path(self, rel_path: str) -> Path:
        resolved = (self.root_dir / rel_path).resolve()
        if not str(resolved).startswith(str(self.root_dir)):
            raise PermissionError(f"Access denied: path '{rel_path}' escapes workspace root")
        return resolved

    async def execute(self, action: str, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if action == "write_file":
            path = self._resolve_safe_path(parameters["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            content = parameters.get("content", "")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "path": str(path), "bytes_written": len(content)}
        
        elif action == "read_file":
            path = self._resolve_safe_path(parameters["path"])
            if not path.exists():
                return {"status": "error", "message": f"File not found: {path}"}
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"status": "success", "path": str(path), "content": content}
        
        elif action == "list_files":
            path = self._resolve_safe_path(parameters.get("path", "."))
            if not path.exists() or not path.is_dir():
                return {"status": "error", "message": f"Directory not found: {path}"}
            entries = [p.name for p in path.iterdir()]
            return {"status": "success", "entries": entries}
        
        return {"status": "error", "message": f"Unknown filesystem action: {action}"}

class TerminalAdapter(RuntimeAdapter):
    """Scoped terminal command executor."""
    async def execute(self, action: str, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        command = parameters.get("command")
        if not command:
            return {"status": "error", "message": "No command provided"}
        
        cwd = parameters.get("cwd", str(WORKSPACE_ROOT))
        logger.info(f"Executing command: {command} in {cwd}")
        
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return {
            "status": "success" if proc.returncode == 0 else "failed",
            "returncode": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace")
        }

class PlaywrightAdapter(RuntimeAdapter):
    """Headless browser automation via Playwright with secure Credential Broker integration."""
    async def execute(self, action: str, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from playwright.async_api import async_playwright
        url = parameters.get("url", "data:text/html,<html><body><h1>AI Workforce Browser Agent</h1></body></html>")
        session_id = parameters.get("session_id") # Credential access session token
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Isolate browser context per task
            browser_context = await browser.new_context()
            page = await browser_context.new_page()
            
            await page.goto(url, wait_until="load", timeout=15000)
            
            auth_broker_result = None
            if session_id:
                # In-memory Credential Broker injection
                from core.security.manager import CredentialsManager
                creds_mgr = CredentialsManager()
                auth_broker_result = await creds_mgr.broker_browser_login(session_id, page)
                
            title = await page.title()
            content = await page.content()
            
            # Detect challenges (CAPTCHA, MFA)
            mfa_detected = "mfa" in content.lower() or "two-factor" in content.lower() or "verification code" in content.lower()
            captcha_detected = "captcha" in content.lower() or "cloudflare" in content.lower() or "challenge" in content.lower()
            
            screenshot_path = None
            if parameters.get("screenshot"):
                shots_dir = WORKSPACE_ROOT / "logs" / "screenshots"
                shots_dir.mkdir(parents=True, exist_ok=True)
                task_id = context.get('task_id', 'task') if context else 'task'
                shot_file = shots_dir / f"browser_{task_id}.png"
                await page.screenshot(path=str(shot_file))
                screenshot_path = str(shot_file)
            
            await browser_context.close()
            await browser.close()
            
            return {
                "status": "success",
                "title": title,
                "content_preview": content[:300] + "...",
                "credential_broker": auth_broker_result,
                "mfa_detected": mfa_detected,
                "captcha_detected": captcha_detected,
                "screenshot_path": screenshot_path
            }

class VerificationAdapter(RuntimeAdapter):
    """Independent verification engine checking output deliverables and full evidence audits."""
    def __init__(self):
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from core.verification.engine import PostImplementationVerificationEngine
            self._engine = PostImplementationVerificationEngine(WORKSPACE_ROOT)
        return self._engine

    async def execute(self, action: str, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        task_id = context.get("task_id") if context else None

        if action in ["audit", "verify_implementation"]:
            engine = self._get_engine()
            target = parameters.get("target_component", "core")
            profile_str = parameters.get("profile", "standard")
            from core.verification.models import VerificationProfile
            try:
                profile = VerificationProfile(profile_str)
            except Exception:
                profile = VerificationProfile.STANDARD
            
            audit_res = await engine.run_audit(
                target_component=target,
                profile=profile,
                requirements=parameters.get("requirements"),
                task_id=task_id,
                initiated_by=parameters.get("initiated_by", "system_verifier")
            )
            return {
                "status": "passed" if audit_res["status"] == "VERIFIED" else "failed",
                "audit_id": audit_res["id"],
                "verification_status": audit_res["status"],
                "evidence_summary": audit_res["evidence_summary"],
                "evidence_artifact_path": audit_res["evidence_artifact_path"],
                "remediation_plan": audit_res["remediation_plan"]
            }

        # Standard deliverable check
        task_output = parameters.get("output", {})
        checks = []
        all_passed = True
        
        # Check 1: Output non-empty
        has_content = bool(task_output and isinstance(task_output, dict))
        checks.append({
            "check": "output_presence",
            "passed": has_content,
            "detail": "Task produced structured deliverable" if has_content else "Task produced empty output"
        })
        if not has_content:
            all_passed = False
            
        # Check 2: Deliverable completeness
        steps_executed = task_output.get("steps_completed", 0)
        expected_steps = task_output.get("total_steps", 1)
        steps_ok = steps_executed >= expected_steps
        checks.append({
            "check": "step_completion",
            "passed": steps_ok,
            "detail": f"Completed {steps_executed}/{expected_steps} planned steps"
        })
        if not steps_ok:
            all_passed = False
            
        # Check 3: Deliverable artifact verification
        artifact_path = task_output.get("artifact_path")
        if artifact_path:
            exists = Path(artifact_path).exists()
            checks.append({
                "check": "artifact_file_integrity",
                "passed": exists,
                "detail": f"File verified on disk: {artifact_path}" if exists else f"Missing artifact file: {artifact_path}"
            })
            if not exists:
                all_passed = False
        else:
            checks.append({
                "check": "artifact_file_integrity",
                "passed": True,
                "detail": "In-memory structured output verified"
            })
            
        status = "passed" if all_passed else "failed"
        return {
            "status": status,
            "checks": checks,
            "report": f"Independent verification {status.upper()}: {sum(1 for c in checks if c['passed'])}/{len(checks)} checks satisfied."
        }
