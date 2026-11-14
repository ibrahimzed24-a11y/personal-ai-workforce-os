import os
import re
import ast
import json
import time
import uuid
import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

from core.database import get_db_connection
from core.verification.models import (
    VerificationStatus,
    SecuritySeverity,
    VerificationProfile,
    SecurityFinding,
    TestExecutionRecord,
    InspectionRecord,
    RequirementEvaluation,
    AuditResponse
)

logger = logging.getLogger("ai_workforce_os.verification")
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = WORKSPACE_ROOT / "logs" / "evidence"

class PostImplementationVerificationEngine:
    """
    Standardized, evidence-driven engine for independently verifying implementations,
    changes, installations, agent executions, system updates, and workflows.
    """
    def __init__(self, workspace_root: Path = WORKSPACE_ROOT):
        self.workspace_root = workspace_root
        self.evidence_dir = workspace_root / "logs" / "evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        # Recursion guard to prevent infinite verification loops
        self._active_audits: Set[str] = set()

    def _get_git_commit(self) -> str:
        """Retrieves the current Git commit SHA if in a git repository."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return "unknown"

    def plan_verification(
        self,
        target_component: str,
        profile: VerificationProfile,
        requirements: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Formulates an evidence-driven verification plan before executing checks."""
        reqs = requirements or [
            {"id": "req_functional", "title": "Functional Implementation", "description": "Capability is implemented and operational."},
            {"id": "req_security", "title": "Security & Permission Enforcement", "description": "Component enforces strict security and zero credential leaks."}
        ]
        
        planned_checks = [
            "Source Code AST & Syntax Validation",
            "Functional Implementation vs. Mock/Placeholder Detection",
            "Security Risk Analysis & Secret Exposure Audit"
        ]
        
        if profile in [VerificationProfile.STANDARD, VerificationProfile.COMPREHENSIVE, VerificationProfile.SECURITY_AUDIT]:
            planned_checks.extend([
                "Automated Test Execution & Exit Code Verification",
                "Runtime Permission & Negative Access Probing"
            ])
            
        if profile == VerificationProfile.COMPREHENSIVE:
            planned_checks.extend([
                "Durable SQLite WAL Persistence Check",
                "Reliability & Error Boundary Verification",
                "Deliverable Artifact Integrity Assertion"
            ])
            
        if profile == VerificationProfile.SECURITY_AUDIT:
            planned_checks.extend([
                "Vault Master Key 0600 POSIX File Mode Verification",
                "Plaintext Password Leak Scan across Git & Filesystem",
                "Credential Broker Session Lifecycle Assertion"
            ])
            
        return {
            "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
            "target_component": target_component,
            "profile": profile.value,
            "requirements": reqs,
            "planned_checks": planned_checks,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def inspect_implementation(
        self,
        target_component: str
    ) -> Tuple[List[InspectionRecord], List[SecurityFinding], Dict[str, Any]]:
        """Inspects source code, AST, configurations, and detects mocks vs. operational code."""
        inspections: List[InspectionRecord] = []
        security_findings: List[SecurityFinding] = []
        metrics: Dict[str, Any] = {"files_inspected": 0, "mocks_detected": 0, "syntax_errors": 0}
        
        # Identify files relevant to target_component
        files_to_inspect: List[Path] = []
        if target_component.startswith("file:"):
            rel_p = target_component.replace("file:", "").strip()
            f = self.workspace_root / rel_p
            if f.exists():
                files_to_inspect.append(f)
        elif target_component.startswith("skill:"):
            skill_id = target_component.replace("skill:", "").strip().replace("-", "_")
            skill_dir = self.workspace_root / "config" / "skills" / skill_id
            if skill_dir.exists():
                files_to_inspect.extend([p for p in skill_dir.rglob("*") if p.is_file()])
            else:
                # Check incoming
                inc_dir = self.workspace_root / "incoming" / "skills" / skill_id
                if inc_dir.exists():
                    files_to_inspect.extend([p for p in inc_dir.rglob("*") if p.is_file()])
        elif target_component.startswith("agent:"):
            agent_id = target_component.replace("agent:", "").strip()
            agent_yaml = self.workspace_root / "config" / "agents" / f"{agent_id}.yaml"
            if agent_yaml.exists():
                files_to_inspect.append(agent_yaml)
        elif target_component.startswith("module:"):
            mod_p = target_component.replace("module:", "").strip()
            dir_path = self.workspace_root / mod_p
            if dir_path.exists():
                files_to_inspect.extend([p for p in dir_path.rglob("*") if p.is_file() and p.suffix in [".py", ".yaml", ".json", ".md"]])
        else:
            # Default: target might be a relative path or component name
            direct_p = self.workspace_root / target_component
            if direct_p.exists():
                if direct_p.is_file():
                    files_to_inspect.append(direct_p)
                else:
                    files_to_inspect.extend([p for p in direct_p.rglob("*") if p.is_file() and p.suffix in [".py", ".yaml", ".json", ".md"]])
            else:
                # Inspect core files
                files_to_inspect.extend([p for p in (self.workspace_root / "core").rglob("*.py") if p.is_file() and "test" not in p.name])

        if not files_to_inspect:
            inspections.append(InspectionRecord(
                target_path=target_component,
                inspection_type="file_resolution",
                status="failed",
                details=f"No matching source or configuration files located for '{target_component}'"
            ))
            return inspections, security_findings, metrics

        for file_path in files_to_inspect:
            metrics["files_inspected"] += 1
            rel_path = str(file_path.relative_to(self.workspace_root))
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                inspections.append(InspectionRecord(
                    target_path=rel_path,
                    inspection_type="file_read",
                    status="failed",
                    details=f"Could not read file: {e}"
                ))
                continue

            # AST Syntax Check for Python files
            if file_path.suffix == ".py":
                try:
                    tree = ast.parse(content, filename=str(file_path))
                    inspections.append(InspectionRecord(
                        target_path=rel_path,
                        inspection_type="ast_syntax",
                        status="passed",
                        details=f"Valid Python AST parsed. {len(tree.body)} root statements."
                    ))
                except SyntaxError as syn_err:
                    metrics["syntax_errors"] += 1
                    inspections.append(InspectionRecord(
                        target_path=rel_path,
                        inspection_type="ast_syntax",
                        status="failed",
                        details=f"Syntax Error on line {syn_err.lineno}: {syn_err.msg}"
                    ))

            # Mock / Placeholder / Stub Detection
            mock_indicators = []
            mock_patterns = [
                (r"\b(unittest\.mock|MagicMock|Mock\(\))\b", "Unit test mock library used in production path"),
                (r"#\s*TODO\s*:\s*(implement|replace|mock)", "Explicit TODO placeholder comment"),
                (r"\braise\s+NotImplementedError\b", "Unimplemented method with NotImplementedError"),
                (r"return\s+.*['\"](mock|simulated|placeholder)['\"]", "Hardcoded mock/simulated return value"),
                (r"\bclass\s+\w+Mock\b", "Mock class definition")
            ]
            
            # Avoid flagging test files themselves as mock defects
            is_test_file = "test" in file_path.name.lower() or "tests" in rel_path
            if not is_test_file:
                for pat, desc in mock_patterns:
                    matches = list(re.finditer(pat, content, re.IGNORECASE))
                    if matches:
                        metrics["mocks_detected"] += len(matches)
                        for m in matches:
                            line_no = content[:m.start()].count("\n") + 1
                            mock_indicators.append(f"Line {line_no}: {desc} ('{m.group(0)}')")
            
            if mock_indicators:
                inspections.append(InspectionRecord(
                    target_path=rel_path,
                    inspection_type="mock_placeholder_detection",
                    status="warning",
                    details=f"Detected {len(mock_indicators)} mock/placeholder patterns in non-test source.",
                    findings=mock_indicators
                ))
            else:
                inspections.append(InspectionRecord(
                    target_path=rel_path,
                    inspection_type="mock_placeholder_detection",
                    status="passed",
                    details="No unapproved mock or simulated logic detected in production path."
                ))

            # Security Pattern Analysis
            sec_patterns = [
                (r"(password|secret|api_key|token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "Possible hardcoded high-entropy secret", SecuritySeverity.HIGH),
                (r"\bsudo\b", "Command invokes sudo privileges", SecuritySeverity.HIGH),
                (r"\brm\s+-rf\s+[/~]", "Dangerous unprompted recursive deletion", SecuritySeverity.CRITICAL),
                (r"\beval\s*\(", "Dynamic code execution via eval()", SecuritySeverity.MEDIUM),
                (r"\bos\.system\s*\(", "Insecure shell execution via os.system()", SecuritySeverity.MEDIUM),
            ]
            for pat, desc, severity in sec_patterns:
                matches = list(re.finditer(pat, content))
                for m in matches:
                    line_no = content[:m.start()].count("\n") + 1
                    security_findings.append(SecurityFinding(
                        severity=severity,
                        category="static_code_analysis",
                        title=desc,
                        description=f"Pattern match at line {line_no} in {rel_path}",
                        file_path=rel_path,
                        line_number=line_no,
                        remediation="Remove hardcoded secret or use safe async subprocess abstraction."
                    ))

        return inspections, security_findings, metrics

    async def execute_automated_tests(
        self,
        target_component: str,
        test_commands: Optional[List[str]] = None,
        timeout: int = 60
    ) -> List[TestExecutionRecord]:
        """Discovers and executes real automated test commands, recording exact exit codes and outputs."""
        records: List[TestExecutionRecord] = []
        
        commands_to_run = test_commands or []
        if not commands_to_run:
            # Smart test discovery based on target
            if "verification" in target_component or "post-implementation" in target_component:
                commands_to_run.append("~/.local/bin/uv run python core/tests/test_verification_skill.py")
            elif "security" in target_component or "vault" in target_component:
                commands_to_run.append("~/.local/bin/uv run python core/tests/test_system.py")
            elif "audit" in target_component:
                commands_to_run.append("~/.local/bin/uv run python core/tests/run_audit_verification.py")
            else:
                # Default baseline system verification
                commands_to_run.append("~/.local/bin/uv run python core/tests/test_system.py")

        for cmd in commands_to_run:
            expanded_cmd = os.path.expanduser(cmd)
            start_time = time.time()
            
            try:
                proc = await asyncio.create_subprocess_shell(
                    expanded_cmd,
                    cwd=str(self.workspace_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, "PYTHONPATH": str(self.workspace_root)}
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                    stdout_str = stdout.decode("utf-8", errors="replace")
                    stderr_str = stderr.decode("utf-8", errors="replace")
                    exit_code = proc.returncode
                    duration = time.time() - start_time
                    
                    status = "passed" if exit_code == 0 else "failed"
                    
                    # Parse test counts
                    passed_count = len(re.findall(r"(✓|PASSED|ok)", stdout_str, re.IGNORECASE))
                    failed_count = len(re.findall(r"(FAILED|FAIL:|Error)", stdout_str, re.IGNORECASE))
                    skipped_count = len(re.findall(r"(skipped|skipping)", stdout_str, re.IGNORECASE))
                    
                    records.append(TestExecutionRecord(
                        command=cmd,
                        exit_code=exit_code,
                        status=status,
                        duration_sec=round(duration, 3),
                        stdout_preview=stdout_str[:1000] + ("..." if len(stdout_str) > 1000 else ""),
                        stderr_preview=stderr_str[:1000] + ("..." if len(stderr_str) > 1000 else ""),
                        tests_passed=passed_count,
                        tests_failed=failed_count,
                        tests_skipped=skipped_count
                    ))
                    
                except asyncio.TimeoutError:
                    proc.kill()
                    duration = time.time() - start_time
                    records.append(TestExecutionRecord(
                        command=cmd,
                        exit_code=-9,
                        status="timeout",
                        duration_sec=round(duration, 3),
                        stdout_preview="Test timed out after execution threshold.",
                        stderr_preview="Process killed due to timeout."
                    ))
                    
            except Exception as e:
                duration = time.time() - start_time
                records.append(TestExecutionRecord(
                    command=cmd,
                    exit_code=-1,
                    status="error",
                    duration_sec=round(duration, 3),
                    stdout_preview="",
                    stderr_preview=f"Subprocess spawn failure: {str(e)}"
                ))

        return records

    async def verify_security(
        self,
        target_component: str,
        profile: VerificationProfile
    ) -> List[SecurityFinding]:
        """Executes active security and permission verification."""
        findings: List[SecurityFinding] = []
        
        # 1. Master Vault Key File Mode
        vault_key_path = Path.home() / ".ai_workforce_vault.key"
        if vault_key_path.exists():
            st_mode = vault_key_path.stat().st_mode & 0o777
            if st_mode != 0o600:
                findings.append(SecurityFinding(
                    severity=SecuritySeverity.CRITICAL,
                    category="vault_security",
                    title="Vault Master Key Insecure File Permissions",
                    description=f"File mode for {vault_key_path} is {oct(st_mode)}, expected 0600 (owner read/write only).",
                    file_path=str(vault_key_path),
                    remediation="Run: chmod 0600 ~/.ai_workforce_vault.key"
                ))
        else:
            findings.append(SecurityFinding(
                severity=SecuritySeverity.INFORMATIONAL,
                category="vault_security",
                title="Vault Master Key Initialized On-Demand",
                description="Master vault key will be initialized upon first credential insertion.",
                remediation=None
            ))

        # 2. Database Permissions & Location Check
        db_path = self.workspace_root / "data" / "ai_workforce.db"
        if db_path.exists():
            st_mode = db_path.stat().st_mode & 0o777
            if st_mode & 0o077 != 0: # other/group read/write
                findings.append(SecurityFinding(
                    severity=SecuritySeverity.MEDIUM,
                    category="database_security",
                    title="Database File Accessible to Other Users",
                    description=f"Database file mode {oct(st_mode)} allows group or other access.",
                    file_path=str(db_path),
                    remediation=f"Run: chmod 0600 {db_path}"
                ))

        # 3. Active Negative Authorization Probing
        if profile in [VerificationProfile.COMPREHENSIVE, VerificationProfile.SECURITY_AUDIT]:
            try:
                from core.security.manager import CredentialsManager
                creds_mgr = CredentialsManager()
                # Negative test: unauthorized agent requesting access
                try:
                    await creds_mgr.request_credential_access(
                        account_id="acc_unauthorized_test",
                        agent_id="unauthorized-malicious-agent",
                        task_id="task_probe_sec"
                    )
                    findings.append(SecurityFinding(
                        severity=SecuritySeverity.CRITICAL,
                        category="access_control",
                        title="Unauthorized Agent Access Not Blocked",
                        description="Credential manager allowed access to an unauthorized agent without throwing PermissionError.",
                        remediation="Ensure enforce_agent_authorization() strictly raises PermissionError for unregistered agents."
                    ))
                except PermissionError:
                    # Expected positive behavior: negative test passed
                    pass
                except Exception:
                    pass
            except Exception as e:
                findings.append(SecurityFinding(
                    severity=SecuritySeverity.LOW,
                    category="security_harness",
                    title="Security Probe Execution Notice",
                    description=f"Could not execute live credential probe: {e}"
                ))

        return findings

    async def verify_reliability(self, target_component: str) -> List[Dict[str, Any]]:
        """Verifies database persistence, WAL journal mode, and failure recovery."""
        checks = []
        
        # SQLite Integrity & Journal Mode Check
        try:
            async with get_db_connection() as db:
                async with db.execute("PRAGMA integrity_check;") as cursor:
                    row = await cursor.fetchone()
                    integrity_ok = row and row[0] == "ok"
                    checks.append({
                        "check": "sqlite_integrity",
                        "status": "passed" if integrity_ok else "failed",
                        "details": f"PRAGMA integrity_check output: {row[0] if row else 'null'}"
                    })
                    
                async with db.execute("PRAGMA journal_mode;") as cursor:
                    row = await cursor.fetchone()
                    wal_ok = row and row[0].lower() == "wal"
                    checks.append({
                        "check": "sqlite_wal_journal_mode",
                        "status": "passed" if wal_ok else "failed",
                        "details": f"Journal mode verified: {row[0] if row else 'unknown'}"
                    })
        except Exception as e:
            checks.append({
                "check": "database_reliability",
                "status": "failed",
                "details": f"Database reliability check error: {e}"
            })

        return checks

    def evaluate_requirements(
        self,
        requirements: List[Dict[str, Any]],
        inspections: List[InspectionRecord],
        tests: List[TestExecutionRecord],
        security_findings: List[SecurityFinding],
        test_metrics: Dict[str, Any]
    ) -> List[RequirementEvaluation]:
        """Evaluates each requirement against concrete evidence to assign a standardized status."""
        evals: List[RequirementEvaluation] = []
        
        has_syntax_errors = test_metrics.get("syntax_errors", 0) > 0
        mocks_detected = test_metrics.get("mocks_detected", 0) > 0
        has_failed_tests = any(t.status in ["failed", "error", "timeout"] for t in tests)
        all_tests_passed = len(tests) > 0 and all(t.status == "passed" for t in tests)
        critical_sec = any(s.severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH] for s in security_findings)

        for req in requirements:
            req_id = req.get("id", f"req_{len(evals)+1}")
            req_title = req.get("title", "Requirement")
            req_desc = req.get("description", "")
            
            # Default determination logic
            if has_syntax_errors:
                status = VerificationStatus.BROKEN
                evidence = "Syntax error detected during AST inspection."
            elif critical_sec and ("security" in req_id or "security" in req_title.lower()):
                status = VerificationStatus.BROKEN
                evidence = "High/Critical security vulnerability detected."
            elif has_failed_tests:
                status = VerificationStatus.BROKEN
                evidence = "Automated test suite failed execution."
            elif mocks_detected and ("functional" in req_id or "implementation" in req_title.lower()):
                status = VerificationStatus.MOCKED_OR_SIMULATED
                evidence = "Target contains unapproved mock/placeholder patterns in production code."
            elif len(tests) == 0:
                # Code might exist, but no tests executed
                has_inspections = any(i.status == "passed" for i in inspections)
                status = VerificationStatus.IMPLEMENTED_NOT_VERIFIED if has_inspections else VerificationStatus.NOT_IMPLEMENTED
                evidence = "Code files exist on disk, but zero automated verification tests were executed."
            elif all_tests_passed:
                status = VerificationStatus.VERIFIED
                evidence = f"Passed {sum(t.tests_passed for t in tests)} automated test assertions with exit code 0."
            else:
                status = VerificationStatus.PARTIALLY_IMPLEMENTED
                evidence = "Partial test coverage or inconclusive evidence."
                
            evals.append(RequirementEvaluation(
                requirement_id=req_id,
                title=req_title,
                description=req_desc,
                status=status,
                evidence_ref=evidence
            ))
            
        return evals

    def determine_overall_status(
        self,
        req_evals: List[RequirementEvaluation],
        tests: List[TestExecutionRecord],
        security_findings: List[SecurityFinding]
    ) -> VerificationStatus:
        """Determines the authoritative overall status."""
        # 1. Any critical security findings immediately block or break
        if any(f.severity == SecuritySeverity.CRITICAL for f in security_findings):
            return VerificationStatus.BROKEN
            
        # 2. Any test failures -> BROKEN
        if any(t.status in ["failed", "error"] for t in tests):
            return VerificationStatus.BROKEN

        # 3. Any timeout / blocked -> BLOCKED
        if any(t.status == "timeout" for t in tests):
            return VerificationStatus.BLOCKED

        # 4. Check requirement statuses
        statuses = [r.status for r in req_evals]
        if any(s == VerificationStatus.BROKEN for s in statuses):
            return VerificationStatus.BROKEN
        if any(s == VerificationStatus.BLOCKED for s in statuses):
            return VerificationStatus.BLOCKED
        if any(s == VerificationStatus.NOT_IMPLEMENTED for s in statuses):
            return VerificationStatus.NOT_IMPLEMENTED
        if all(s == VerificationStatus.MOCKED_OR_SIMULATED for s in statuses):
            return VerificationStatus.MOCKED_OR_SIMULATED
        if any(s == VerificationStatus.MOCKED_OR_SIMULATED for s in statuses):
            return VerificationStatus.PARTIALLY_IMPLEMENTED
        if any(s == VerificationStatus.IMPLEMENTED_NOT_VERIFIED for s in statuses):
            return VerificationStatus.IMPLEMENTED_NOT_VERIFIED
        if any(s == VerificationStatus.PARTIALLY_IMPLEMENTED for s in statuses):
            return VerificationStatus.PARTIALLY_IMPLEMENTED
        if all(s == VerificationStatus.VERIFIED for s in statuses):
            return VerificationStatus.VERIFIED
            
        return VerificationStatus.IMPLEMENTED_NOT_VERIFIED

    def formulate_remediation(
        self,
        status: VerificationStatus,
        req_evals: List[RequirementEvaluation],
        security_findings: List[SecurityFinding],
        tests: List[TestExecutionRecord]
    ) -> Optional[Dict[str, Any]]:
        """Formulates actionable remediation steps if verification failed or was partial."""
        if status == VerificationStatus.VERIFIED:
            return None
            
        actions = []
        for sf in security_findings:
            if sf.severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH]:
                actions.append(f"Security Remediation: {sf.title} - {sf.remediation or sf.description}")
                
        for t in tests:
            if t.status in ["failed", "error", "timeout"]:
                actions.append(f"Test Fix: Resolve failures in '{t.command}' (Exit code: {t.exit_code}).")
                
        for r in req_evals:
            if r.status == VerificationStatus.MOCKED_OR_SIMULATED:
                actions.append(f"Implementation: Replace mock/placeholder logic in '{r.title}' with functional code.")
            elif r.status == VerificationStatus.IMPLEMENTED_NOT_VERIFIED:
                actions.append(f"Testing: Author automated test suite to verify '{r.title}'.")
            elif r.status == VerificationStatus.NOT_IMPLEMENTED:
                actions.append(f"Development: Implement missing capability for '{r.title}'.")

        return {
            "overall_status": status.value,
            "recommended_actions": actions,
            "requires_owner_approval": any(s.severity == SecuritySeverity.CRITICAL for s in security_findings),
            "generated_at": datetime.utcnow().isoformat()
        }

    async def run_audit(
        self,
        target_component: str,
        profile: VerificationProfile = VerificationProfile.STANDARD,
        requirements: Optional[List[Dict[str, Any]]] = None,
        task_id: Optional[str] = None,
        initiated_by: str = "user",
        test_commands: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main public orchestrator for running an end-to-end evidence-based audit.
        Prevents recursive loops and saves evidence directly to SQLite and disk.
        """
        audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        
        # Recursion Guard: Prevent infinite verification loops
        if target_component in self._active_audits or "audit_" in target_component:
            logger.info(f"Recursion guard triggered for {target_component}. Skipping nested audit.")
            return {
                "id": audit_id,
                "status": VerificationStatus.BLOCKED.value,
                "message": "Recursion guard prevented nested verification loop.",
                "target_component": target_component
            }

        self._active_audits.add(target_component)
        created_at = datetime.utcnow().isoformat()
        git_commit = self._get_git_commit()
        
        try:
            # Step 1: Verification Planning
            plan = self.plan_verification(target_component, profile, requirements)
            
            # Step 2: Implementation Inspection
            inspections, sec_findings_ast, metrics = await self.inspect_implementation(target_component)
            
            # Step 3: Active Security Verification
            sec_findings_active = await self.verify_security(target_component, profile)
            all_sec_findings = sec_findings_ast + sec_findings_active
            
            # Step 4: Automated Testing
            test_records = await self.execute_automated_tests(target_component, test_commands)
            
            # Step 5: Reliability Verification (if comprehensive)
            reliability_records = []
            if profile in [VerificationProfile.COMPREHENSIVE, VerificationProfile.STANDARD]:
                reliability_records = await self.verify_reliability(target_component)
                
            # Step 6: Requirement Evaluation
            req_evals = self.evaluate_requirements(
                plan["requirements"],
                inspections,
                test_records,
                all_sec_findings,
                metrics
            )
            
            # Step 7: Authoritative Overall Status
            overall_status = self.determine_overall_status(req_evals, test_records, all_sec_findings)
            
            # Step 8: Remediation Plan
            remediation = self.formulate_remediation(overall_status, req_evals, all_sec_findings, test_records)
            
            completed_at = datetime.utcnow().isoformat()
            
            # Step 9: Synthesize Evidence Artifact
            evidence_summary = (
                f"### Post-Implementation Verification Report\n"
                f"- **Audit ID:** `{audit_id}`\n"
                f"- **Target:** `{target_component}` (Version: `{git_commit[:8]}`)\n"
                f"- **Profile:** `{profile.value}`\n"
                f"- **Status:** **{overall_status.value}**\n"
                f"- **Tests Executed:** {len(test_records)} commands ({sum(t.tests_passed for t in test_records)} passed)\n"
                f"- **Security Findings:** {len(all_sec_findings)} (Critical: {sum(1 for s in all_sec_findings if s.severity == SecuritySeverity.CRITICAL)})\n"
                f"- **Completed:** {completed_at}\n"
            )
            
            artifact_file = self.evidence_dir / f"{audit_id}.json"
            audit_payload = {
                "id": audit_id,
                "task_id": task_id,
                "target_component": target_component,
                "target_version": git_commit,
                "profile": profile.value,
                "status": overall_status.value,
                "initiated_by": initiated_by,
                "requirements_evaluated": [r.model_dump() for r in req_evals],
                "inspections": [i.model_dump() for i in inspections],
                "tests_executed": [t.model_dump() for t in test_records],
                "security_findings": [s.model_dump() for s in all_sec_findings],
                "reliability_findings": reliability_records,
                "evidence_summary": evidence_summary,
                "evidence_artifact_path": str(artifact_file),
                "remediation_plan": remediation,
                "created_at": created_at,
                "completed_at": completed_at
            }
            
            # Write JSON evidence artifact
            with open(artifact_file, "w", encoding="utf-8") as f:
                json.dump(audit_payload, f, indent=2)
                
            # Step 10: Persist to SQLite Database
            async with get_db_connection() as db:
                await db.execute("""
                    INSERT INTO verification_audits (
                        id, task_id, target_component, target_version, profile, status,
                        initiated_by, requirements_evaluated, inspections, tests_executed,
                        security_findings, reliability_findings, evidence_summary,
                        evidence_artifact_path, remediation_plan, created_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audit_id,
                    task_id,
                    target_component,
                    git_commit,
                    profile.value,
                    overall_status.value,
                    initiated_by,
                    json.dumps(audit_payload["requirements_evaluated"]),
                    json.dumps(audit_payload["inspections"]),
                    json.dumps(audit_payload["tests_executed"]),
                    json.dumps(audit_payload["security_findings"]),
                    json.dumps(reliability_records),
                    evidence_summary,
                    str(artifact_file),
                    json.dumps(remediation) if remediation else None,
                    created_at,
                    completed_at
                ))
                
                # If tied to a task, also record to execution_events
                if task_id:
                    await db.execute("""
                        INSERT INTO execution_events (task_id, agent_id, event_type, payload)
                        VALUES (?, 'post_implementation_verifier', 'verification_audit_completed', ?)
                    """, (task_id, json.dumps({
                        "audit_id": audit_id,
                        "status": overall_status.value,
                        "profile": profile.value
                    })))
                    
                await db.commit()

            return audit_payload

        finally:
            self._active_audits.discard(target_component)

    async def list_audits(
        self,
        limit: int = 50,
        status: Optional[str] = None,
        profile: Optional[str] = None,
        target_component: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves past verification audits from SQLite with optional filtering."""
        query = "SELECT * FROM verification_audits WHERE 1=1"
        params: List[Any] = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        if profile:
            query += " AND profile = ?"
            params.append(profile)
        if target_component:
            query += " AND target_component LIKE ?"
            params.append(f"%{target_component}%")
            
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        async with get_db_connection() as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    item = dict(row)
                    item["requirements_evaluated"] = json.loads(item["requirements_evaluated"]) if item["requirements_evaluated"] else []
                    item["inspections"] = json.loads(item["inspections"]) if item["inspections"] else []
                    item["tests_executed"] = json.loads(item["tests_executed"]) if item["tests_executed"] else []
                    item["security_findings"] = json.loads(item["security_findings"]) if item["security_findings"] else []
                    item["reliability_findings"] = json.loads(item["reliability_findings"]) if item["reliability_findings"] else []
                    item["remediation_plan"] = json.loads(item["remediation_plan"]) if item["remediation_plan"] else None
                    results.append(item)
                return results

    async def get_audit(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single audit by ID."""
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM verification_audits WHERE id = ?", (audit_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                item = dict(row)
                item["requirements_evaluated"] = json.loads(item["requirements_evaluated"]) if item["requirements_evaluated"] else []
                item["inspections"] = json.loads(item["inspections"]) if item["inspections"] else []
                item["tests_executed"] = json.loads(item["tests_executed"]) if item["tests_executed"] else []
                item["security_findings"] = json.loads(item["security_findings"]) if item["security_findings"] else []
                item["reliability_findings"] = json.loads(item["reliability_findings"]) if item["reliability_findings"] else []
                item["remediation_plan"] = json.loads(item["remediation_plan"]) if item["remediation_plan"] else None
                return item
