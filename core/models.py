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
    description: Optional[str] = ""
    priority: str = "medium"
    context: Dict[str, Any] = {}
    target_agent: Optional[str] = None
    project_id: Optional[str] = None

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

class LLMProviderModel(BaseModel):
    id: str
    name: str
    provider_type: str # local_ollama, cloud_openai, cloud_gemini, cloud_anthropic, openai_compatible, mock
    base_url: str
    api_key_ref: Optional[str] = None
    is_active: bool = True
    health_status: str = "unknown"
    last_health_check: Optional[str] = None
    config_json: Dict[str, Any] = {}
    created_at: Optional[str] = None

class LLMModelInfo(BaseModel):
    id: str
    provider_id: str
    model_name: str
    display_name: str
    classification: str # local, cloud, mock
    context_window: int = 8192
    supports_tools: bool = True
    supports_structured_output: bool = True
    supports_vision: bool = False
    capabilities: List[str] = [] # coding, reasoning, fast, general
    is_active: bool = True
    is_default: bool = False
    latency_p50_ms: float = 0.0
    success_rate: float = 1.0
    created_at: Optional[str] = None

class LLMRoutingRuleModel(BaseModel):
    id: str
    rule_name: str
    task_category: str = "*" # code, research, marketing, coordination, general, sensitive
    agent_id_match: str = "*"
    privacy_level: str = "standard" # local_only, standard, cloud_allowed
    preferred_model_id: str
    fallback_model_id: Optional[str] = None
    allow_cloud_fallback: bool = False
    priority: int = 10
    is_active: bool = True
    created_at: Optional[str] = None

class LLMUsageMetricModel(BaseModel):
    id: Optional[int] = None
    task_id: Optional[str] = None
    step_id: Optional[str] = None
    agent_id: Optional[str] = None
    model_id: str
    provider_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    timestamp: Optional[str] = None

class ModelGenerationRequest(BaseModel):
    task_type: str = "general"
    agent_id: Optional[str] = None
    system_prompt: str
    user_prompt: str
    context: Dict[str, Any] = {}
    tools: Optional[List[Dict[str, Any]]] = None
    privacy_level: str = "standard" # local_only, standard, sensitive, cloud_allowed
    force_model_id: Optional[str] = None

class ModelGenerationResponse(BaseModel):
    content: str
    parsed_json: Optional[Dict[str, Any]] = None
    provider: str
    model: str
    classification: str
    usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    latency_ms: float
    raw: Optional[Dict[str, Any]] = None

