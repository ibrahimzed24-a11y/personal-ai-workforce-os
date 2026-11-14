from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class SpecialistModel(BaseModel):
    id: str
    name: str
    specialization: str
    skills: List[str]

class AgentBlueprintModel(BaseModel):
    id: str
    name: str
    department: str
    role: str
    description: str
    system_prompt: str
    capabilities: List[str]
    permissions: Dict[str, Any]
    default_model: Dict[str, str]
    specialists: List[SpecialistModel] = []
    version: str = "1.0.0"
    is_active: bool = True

class PlanStep(BaseModel):
    id: str
    step_number: int
    title: str
    description: str
    assigned_agent: str
    specialist_id: Optional[str] = None
    action_type: str = "execute" # execute, browser_navigate, write_file, shell_command, verify, report
    parameters: Dict[str, Any] = {}
    prerequisites: List[str] = []
    status: str = "pending" # pending, in_progress, completed, failed
    output: Optional[Dict[str, Any]] = None

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    context: Dict[str, Any] = {}
    target_agent: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    assigned_agent_id: Optional[str]
    status: str
    priority: str
    input_context: Dict[str, Any]
    output_result: Optional[Dict[str, Any]]
    verification_status: str
    created_at: str
    updated_at: str
    completed_at: Optional[str]

class ExecutionEventModel(BaseModel):
    id: Optional[int] = None
    task_id: str
    step_id: Optional[str] = None
    agent_id: Optional[str] = None
    event_type: str
    payload: Dict[str, Any]
    timestamp: Optional[str] = None

class ApprovalRequestModel(BaseModel):
    id: str
    task_id: str
    step_id: Optional[str]
    action_type: str
    details: Dict[str, Any]
    status: str = "pending" # pending, approved, rejected
    requested_at: str
    responded_at: Optional[str] = None
    notes: Optional[str] = None

class VerificationResultModel(BaseModel):
    id: str
    task_id: str
    verifier_type: str
    status: str # passed, failed
    checks_run: List[Dict[str, Any]]
    report_text: str
    timestamp: str

class SystemRequirementModel(BaseModel):
    id: str
    category: str
    title: str
    specification: Dict[str, Any]
    change_plan: Optional[List[Dict[str, Any]]] = None
    status: str = "draft"
    created_at: str
    applied_at: Optional[str] = None
