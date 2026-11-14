import enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class VerificationStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    IMPLEMENTED_NOT_VERIFIED = "IMPLEMENTED_NOT_VERIFIED"
    PARTIALLY_IMPLEMENTED = "PARTIALLY_IMPLEMENTED"
    MOCKED_OR_SIMULATED = "MOCKED_OR_SIMULATED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    BROKEN = "BROKEN"
    BLOCKED = "BLOCKED"

class SecuritySeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"

class VerificationProfile(str, enum.Enum):
    LIGHTWEIGHT = "lightweight"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    SECURITY_AUDIT = "security_audit"

class SecurityFinding(BaseModel):
    severity: SecuritySeverity
    category: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    remediation: Optional[str] = None

class TestExecutionRecord(BaseModel):
    command: str
    exit_code: int
    status: str # passed, failed, skipped, error
    duration_sec: float = 0.0
    stdout_preview: str = ""
    stderr_preview: str = ""
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0

class InspectionRecord(BaseModel):
    target_path: str
    inspection_type: str # ast_syntax, class_function_presence, mock_placeholder_detection, permissions, config_validation
    status: str # passed, failed, warning, info
    details: str
    findings: List[str] = Field(default_factory=list)

class RequirementEvaluation(BaseModel):
    requirement_id: str
    title: str
    description: str = ""
    status: VerificationStatus
    evidence_ref: str = ""
    notes: Optional[str] = None

class AuditCreateRequest(BaseModel):
    target_component: str
    profile: VerificationProfile = VerificationProfile.STANDARD
    requirements: Optional[List[Dict[str, Any]]] = None
    task_id: Optional[str] = None
    initiated_by: str = "user"
    options: Optional[Dict[str, Any]] = None

class AuditResponse(BaseModel):
    id: str
    task_id: Optional[str] = None
    target_component: str
    target_version: Optional[str] = None
    profile: str
    status: VerificationStatus
    initiated_by: str
    requirements_evaluated: List[Dict[str, Any]]
    inspections: List[Dict[str, Any]]
    tests_executed: List[Dict[str, Any]]
    security_findings: List[Dict[str, Any]]
    reliability_findings: List[Dict[str, Any]]
    evidence_summary: str
    evidence_artifact_path: Optional[str] = None
    remediation_plan: Optional[Dict[str, Any]] = None
    created_at: str
    completed_at: Optional[str] = None
