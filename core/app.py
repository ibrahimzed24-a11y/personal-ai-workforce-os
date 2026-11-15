import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from core.database import init_db
from core.models import TaskCreate, TaskResponse
from core.orchestrator import Orchestrator
from core.requirements import RequirementsManager
from core.integrator import SystemIntegratorEngine
from core.security.manager import CredentialsManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ai_workforce_os.server")

orchestrator = Orchestrator()
requirements_mgr = RequirementsManager()
integrator_engine = SystemIntegratorEngine()
creds_mgr = CredentialsManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite schema & sync declarative blueprints
    logger.info("Initializing AI Workforce OS database...")
    await init_db()
    logger.info("Initializing baseline LLM providers & models...")
    await orchestrator.model_manager.initialize_defaults()
    logger.info("Syncing agent blueprints from disk...")
    await orchestrator.sync_blueprints_from_disk()
    logger.info("Scanning incoming capabilities directory...")
    await integrator_engine.scan_incoming()
    logger.info("AI Workforce OS is ready and listening.")
    yield
    logger.info("Shutting down AI Workforce OS.")

app = FastAPI(
    title="AI Workforce OS",
    description="Private Autonomous AI Development Operating System with Centralized Credentials Vault",
    version="1.0.0",
    lifespan=lifespan
)

# --- Tasks API ---
@app.get("/api/tasks")
async def list_tasks():
    return await orchestrator.list_tasks()

@app.post("/api/tasks")
async def create_task(task_in: TaskCreate):
    return await orchestrator.create_task(task_in)

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    task = await orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/api/tasks/{task_id}/run")
async def run_task(task_id: str):
    try:
        return await orchestrator.run_task(task_id)
    except Exception as e:
        logger.error(f"Error running task {task_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}/events")
async def get_task_events(task_id: str):
    return await orchestrator.get_task_events(task_id)

# --- Agents & Blueprints API ---
@app.get("/api/agents")
async def list_agents():
    return await orchestrator.get_all_blueprints()

# --- Standardized Three-File Architecture API ---
class MemoryFeedbackRequest(BaseModel):
    feedback: str
    author: str = "owner"
    auto_apply: bool = True

class SlashInvokeRequest(BaseModel):
    command: str
    task_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

@app.get("/api/agents/three-file-catalog")
async def get_three_file_catalog():
    from core.agent_context import AgentContextLoader
    loader = AgentContextLoader()
    return loader.list_all_agents()

@app.get("/api/agents/{agent_id}/context")
async def get_agent_runtime_context(agent_id: str):
    from core.agent_context import AgentContextLoader
    loader = AgentContextLoader()
    try:
        return loader.build_runtime_context(agent_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/agents/{agent_id}/memory/feedback")
async def submit_memory_feedback(agent_id: str, req: MemoryFeedbackRequest):
    from core.agent_context import AgentContextLoader
    loader = AgentContextLoader()
    try:
        res = await loader.propose_memory_update(
            agent_id=agent_id,
            feedback=req.feedback,
            author=req.author,
            auto_apply=req.auto_apply
        )
        if res.get("status") == "rejected":
            raise HTTPException(status_code=400, detail=res.get("reason"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/skills/invoke-slash")
async def invoke_slash_command(req: SlashInvokeRequest):
    from core.agent_context import AgentContextLoader
    loader = AgentContextLoader()
    resolved = loader.resolve_slash_command(req.command)
    if not resolved:
        raise HTTPException(status_code=404, detail=f"Slash command '{req.command}' not found")
    
    # Load agent context
    ctx = loader.build_runtime_context(resolved["agent_id"], req.parameters or {})
    return {
        "status": "success",
        "command": req.command,
        "resolved": resolved,
        "startup_checklist": ctx["startup_checklist"],
        "context_summary": f"Loaded AGENT.md, MEMORY.md, and {resolved['slash_command']} for {resolved['agent_id']}"
    }

# --- Post-Implementation Verification & Evidence Audit API ---
class VerificationAuditRequest(BaseModel):
    target_component: str
    profile: str = "standard"
    requirements: Optional[List[Dict[str, Any]]] = None
    task_id: Optional[str] = None
    initiated_by: str = "user"
    test_commands: Optional[List[str]] = None

@app.post("/api/verification/audit")
async def run_verification_audit(req: VerificationAuditRequest):
    from core.verification.engine import PostImplementationVerificationEngine
    from core.verification.models import VerificationProfile
    engine = PostImplementationVerificationEngine()
    try:
        profile_enum = VerificationProfile(req.profile.lower())
    except Exception:
        profile_enum = VerificationProfile.STANDARD
        
    try:
        return await engine.run_audit(
            target_component=req.target_component,
            profile=profile_enum,
            requirements=req.requirements,
            task_id=req.task_id,
            initiated_by=req.initiated_by,
            test_commands=req.test_commands
        )
    except Exception as e:
        logger.error(f"Error executing verification audit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/verification/audits")
async def list_verification_audits(
    limit: int = 50,
    status: Optional[str] = None,
    profile: Optional[str] = None,
    target: Optional[str] = None
):
    from core.verification.engine import PostImplementationVerificationEngine
    engine = PostImplementationVerificationEngine()
    return await engine.list_audits(limit=limit, status=status, profile=profile, target_component=target)

@app.get("/api/verification/audits/{audit_id}")
async def get_verification_audit_detail(audit_id: str):
    from core.verification.engine import PostImplementationVerificationEngine
    engine = PostImplementationVerificationEngine()
    audit = await engine.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return audit

@app.get("/api/verification/profiles")
async def get_verification_profiles():
    return {
        "profiles": [
            {
                "id": "lightweight",
                "name": "Lightweight Profile",
                "description": "For documentation, minor configs, and isolated updates.",
                "checks": ["AST parsing", "Path validation", "Basic secret leak scan"]
            },
            {
                "id": "standard",
                "name": "Standard Profile",
                "description": "For new skills, tools, agent changes, workflows, and features.",
                "checks": ["Lightweight checks", "Mock/placeholder detection", "Automated test execution", "Basic permission probing"]
            },
            {
                "id": "comprehensive",
                "name": "Comprehensive Profile",
                "description": "For core architecture changes, database migrations, runtimes, and releases.",
                "checks": ["Standard checks", "Full test suite exit codes", "SQLite WAL persistence", "State recovery", "Negative security probing"]
            },
            {
                "id": "security_audit",
                "name": "Security Audit Profile",
                "description": "For vault changes, auth/authz, permissions, and network exposure.",
                "checks": ["Comprehensive checks", "Vault key 0600 POSIX mode", "Negative agent authorization rejection", "Token lifecycle assertion"]
            }
        ]
    }

# --- Requirements & Change Management API ---
class RequirementCreate(BaseModel):
    category: str
    title: str
    specification: Dict[str, Any]

@app.get("/api/requirements")
async def list_requirements():
    return await requirements_mgr.list_requirements()

@app.post("/api/requirements")
async def submit_requirement(req_in: RequirementCreate):
    return await requirements_mgr.submit_requirement(req_in.category, req_in.title, req_in.specification)

@app.post("/api/requirements/{req_id}/apply")
async def apply_requirement(req_id: str):
    try:
        return await requirements_mgr.apply_requirement(req_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- System Integrator & Update Agent API ---
@app.get("/api/integrator/scan")
async def scan_incoming():
    return await integrator_engine.scan_incoming()

@app.get("/api/integrator/assets")
async def list_assets():
    return await integrator_engine.list_assets()

@app.post("/api/integrator/approve/{asset_id}")
async def approve_asset(asset_id: str):
    return await integrator_engine.approve_asset(asset_id)

@app.post("/api/integrator/install/{asset_id}")
async def install_asset(asset_id: str):
    try:
        return await integrator_engine.install_asset(asset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integrator/rollback/{asset_id}")
async def rollback_asset(asset_id: str):
    try:
        return await integrator_engine.rollback_asset(asset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/integrator/knowledge")
async def get_operational_knowledge():
    k_dir = Path(__file__).resolve().parent.parent / "documentation" / "knowledge"
    knowledge = {}
    if k_dir.exists():
        for f in k_dir.glob("*"):
            if f.is_file():
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        knowledge[f.name] = fp.read()
                except Exception:
                    pass
    return knowledge

# --- Security: Centralized Credentials & Access API ---
class AccountCreate(BaseModel):
    name: str
    url: str
    login_url: str
    username_or_email: str
    category: str
    password: Optional[str] = None
    api_key: Optional[str] = None
    project_id: str = "global"
    mfa_status: str = "DISABLED"
    notes: str = ""
    assigned_agents: Optional[List[str]] = None

class PasswordRevealRequest(BaseModel):
    master_key: str

class CredentialAccessRequest(BaseModel):
    agent_id: str
    task_id: str
    project_id: str = "global"

class PasswordUpdateRequest(BaseModel):
    new_password: str
    changed_by: str = "owner"
    reason: str = "Routine rotation"

class PolicyUpdateRequest(BaseModel):
    account_id: str
    agent_id: str
    permission_level: str
    is_active: bool = True

class RegistrationRequestCreate(BaseModel):
    agent_id: str
    task_id: str
    service_name: str
    website_url: str
    category: str
    reason: str
    proposed_username: str
    is_paid: bool = False

@app.get("/api/security/accounts")
async def list_security_accounts(
    agent_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    return await creds_mgr.list_accounts(agent_id=agent_id, category=category, project_id=project_id, search=search)

@app.post("/api/security/accounts")
async def create_security_account(acc_in: AccountCreate):
    return await creds_mgr.create_account(
        name=acc_in.name,
        url=acc_in.url,
        login_url=acc_in.login_url,
        username_or_email=acc_in.username_or_email,
        category=acc_in.category,
        password=acc_in.password,
        api_key=acc_in.api_key,
        project_id=acc_in.project_id,
        mfa_status=acc_in.mfa_status,
        notes=acc_in.notes,
        assigned_agents=acc_in.assigned_agents
    )

@app.get("/api/security/accounts/{account_id}")
async def get_security_account(account_id: str, agent_id: Optional[str] = Query(None)):
    try:
        acc = await creds_mgr.get_account_detail(account_id, agent_id=agent_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
        return acc
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))

@app.post("/api/security/accounts/{account_id}/reveal")
async def reveal_account_password(account_id: str, req: PasswordRevealRequest):
    try:
        return await creds_mgr.reveal_password(account_id, req.master_key)
    except PermissionError:
        raise HTTPException(status_code=401, detail="Invalid master authentication")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/security/accounts/{account_id}/request-access")
async def request_credential_access(account_id: str, req: CredentialAccessRequest):
    try:
        return await creds_mgr.request_credential_access(
            account_id=account_id,
            agent_id=req.agent_id,
            task_id=req.task_id,
            project_id=req.project_id
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/security/accounts/{account_id}/update-password")
async def update_account_password(account_id: str, req: PasswordUpdateRequest):
    try:
        return await creds_mgr.update_credentials(
            account_id=account_id,
            new_password=req.new_password,
            changed_by=req.changed_by,
            reason=req.reason
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/security/policies")
async def set_agent_policy(req: PolicyUpdateRequest):
    return await creds_mgr.set_agent_policy(
        account_id=req.account_id,
        agent_id=req.agent_id,
        permission_level=req.permission_level,
        is_active=req.is_active
    )

@app.get("/api/security/registrations")
async def list_registration_requests():
    return await creds_mgr.list_registration_requests()

@app.post("/api/security/registrations")
async def request_account_registration(req: RegistrationRequestCreate):
    return await creds_mgr.request_account_registration(
        agent_id=req.agent_id,
        task_id=req.task_id,
        service_name=req.service_name,
        website_url=req.website_url,
        category=req.category,
        reason=req.reason,
        proposed_username=req.proposed_username,
        is_paid=req.is_paid
    )

@app.post("/api/security/registrations/{req_id}/approve")
async def approve_registration(req_id: str, decision: str = "APPROVED", notes: str = ""):
    return await creds_mgr.approve_registration(req_id, owner_decision=decision, notes=notes)

@app.post("/api/security/sessions/{session_id}/revoke")
async def revoke_session(session_id: str):
    return await creds_mgr.revoke_session(session_id)

@app.get("/api/security/health")
async def get_credential_health():
    return await creds_mgr.get_credential_health_report()

@app.get("/api/security/audit")
async def get_security_audit_logs(limit: int = 100, account_id: Optional[str] = None, agent_id: Optional[str] = None):
    return await creds_mgr.get_audit_logs(limit=limit, account_id=account_id, agent_id=agent_id)

# --- Model Manager API ---
@app.get("/api/models/status")
async def get_reasoning_status():
    """Returns honest audit of active reasoning engine, model, and provider status."""
    return await orchestrator.model_manager.get_system_reasoning_status()

@app.get("/api/models/providers")
async def list_model_providers():
    """Lists all configured LLM providers (Ollama, OpenAI, Gemini, Anthropic, Mock)."""
    return await orchestrator.model_manager.list_providers()

@app.post("/api/models/providers/{provider_id}/credential")
async def configure_provider_credential(provider_id: str, payload: Dict[str, Any]):
    """Encrypts and safely stores API key in Fernet Vault."""
    api_key = payload.get("api_key", "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required.")
    return await orchestrator.model_manager.update_provider_credential(provider_id, api_key)

@app.post("/api/models/providers/{provider_id}/health")
async def check_provider_health(provider_id: str):
    """Executes live reachability and auth check on provider."""
    return await orchestrator.model_manager.check_provider_health(provider_id)

@app.get("/api/models")
async def list_models(active_only: bool = False):
    """Lists all registered models with capability tags and performance metrics."""
    return await orchestrator.model_manager.list_models(active_only=active_only)

@app.post("/api/models/default")
async def set_default_model(payload: Dict[str, Any]):
    """Sets the system default reasoning model."""
    model_id = payload.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required.")
    return await orchestrator.model_manager.set_default_model(model_id)

@app.get("/api/models/metrics")
async def get_model_metrics(limit: int = 50):
    """Retrieves recent LLM invocation metrics and token counts."""
    async with get_db_connection() as db:
        async with db.execute(
            """
            SELECT m.*, lm.display_name, lp.name as provider_name
            FROM llm_usage_metrics m
            LEFT JOIN llm_models lm ON m.model_id = lm.id
            LEFT JOIN llm_providers lp ON m.provider_id = lp.id
            ORDER BY m.timestamp DESC LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

# --- System Health API ---
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "system": "AI Workforce OS",
        "version": "1.0.0",
        "database": "SQLite WAL",
        "vault": "AES-128-CBC Fernet (0600 POSIX)",
        "runtime": "Python 3.12 (uv)"
    }

# --- Web UI Static Files ---
UI_DIR = Path(__file__).resolve().parent / "ui"
if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(UI_DIR / "index.html"))

    @app.get("/favicon.ico")
    async def favicon():
        return JSONResponse({"status": "no_icon"})
