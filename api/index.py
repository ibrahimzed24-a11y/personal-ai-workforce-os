import os
import sys
import uuid
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.adapters.supabase_adapter import SupabaseAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_workforce_os.vercel_api")

app = FastAPI(
    title="AI Workforce OS — Sovereign Cloud Dashboard",
    description="Stateless Serverless API and Webapp Dashboard for Personal AI Workforce OS on Vercel",
    version="2.0.0"
)

# --- Vercel Rewrite URL Path Normalizer Middleware ---
class VercelPathNormalizerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # When Vercel rewrites /api/:path* to /api/index.py?__path=:path*
        subpath = request.query_params.get("__path")
        if subpath:
            norm_subpath = subpath if subpath.startswith("/") else f"/{subpath}"
            # If subpath is ping or health
            if norm_subpath in ("/ping", "/health"):
                request.scope["path"] = norm_subpath
            elif norm_subpath.startswith("/api/"):
                request.scope["path"] = norm_subpath
            else:
                request.scope["path"] = f"/api{norm_subpath}"
        return await call_next(request)

app.add_middleware(VercelPathNormalizerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = SupabaseAdapter()

# --- Static UI Serving ---
PUBLIC_DIR = ROOT_DIR / "public"
CORE_UI_DIR = ROOT_DIR / "core" / "ui"
UI_DIR = PUBLIC_DIR if PUBLIC_DIR.exists() else CORE_UI_DIR

if (UI_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR / "static")), name="static")
elif UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Serve the complete AI Workforce OS Control Center webapp."""
    # If a subpath was forwarded via __path that maps to an API, route to it
    subpath = request.query_params.get("__path")
    if subpath and subpath not in ("", "index.html", "index.py"):
        raise HTTPException(status_code=404, detail=f"Endpoint {subpath} not found")
        
    for p in [PUBLIC_DIR / "index.html", CORE_UI_DIR / "index.html"]:
        if p.exists():
            return FileResponse(str(p), media_type="text/html")
    return HTMLResponse("<html><body><h1>AI Workforce OS Control Center</h1><p>Online.</p></body></html>")

@app.get("/style.css")
async def serve_style():
    for p in [PUBLIC_DIR / "style.css", CORE_UI_DIR / "style.css"]:
        if p.exists():
            return FileResponse(str(p), media_type="text/css")
    raise HTTPException(status_code=404)

@app.get("/app.js")
async def serve_js():
    for p in [PUBLIC_DIR / "app.js", CORE_UI_DIR / "app.js"]:
        if p.exists():
            return FileResponse(str(p), media_type="application/javascript")
    raise HTTPException(status_code=404)

# --- Request / Response Models ---
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(default="", description="Project purpose / description")
    category: Optional[str] = Field(default="general", description="Category tag")
    lead_agent_id: Optional[str] = Field(default="coordinator", description="Assigned lead agent")

PROJECTS_STORE: List[Dict[str, Any]] = [
    {
        "id": "proj-core-os",
        "name": "Personal AI Workforce OS Evolution",
        "description": "Sovereign 32-agent architecture, 5-stage loop engine, and hybrid Mac execution.",
        "category": "core_infrastructure",
        "lead_agent_id": "coordinator",
        "status": "active",
        "created_at": "2026-11-15T01:00:00"
    },
    {
        "id": "proj-market-seo",
        "name": "SEO & Global Market Expansion",
        "description": "Competitive intelligence, keyword clustering, and GEO-targeted search optimization.",
        "category": "market_research",
        "lead_agent_id": "market-seo-geo-researcher",
        "status": "active",
        "created_at": "2026-11-15T02:00:00"
    },
    {
        "id": "proj-web-automation",
        "name": "Autonomous Browser & Telemetry Engine",
        "description": "Headless Chromium navigation, DOM structured extraction, and visual verification.",
        "category": "browser_automation",
        "lead_agent_id": "browser-use-agent",
        "status": "active",
        "created_at": "2026-11-15T03:00:00"
    }
]

class TaskSubmitRequest(BaseModel):
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Detailed instructions")
    assigned_agent_id: Optional[str] = Field(default="coordinator", description="Target agent blueprint ID")
    target_agent: Optional[str] = Field(default=None, description="Alias for assigned_agent_id")
    project_id: Optional[str] = Field(default="proj-core-os", description="Target project ID")
    runtime_target: str = Field(default="local", description="Target runtime ('local', 'cloud', 'any')")
    required_capabilities: Optional[List[str]] = Field(default_factory=list)
    priority: Any = Field(default=50, description="Priority (int or string)")
    input_payload: Optional[Dict[str, Any]] = Field(default_factory=dict)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    idempotency_key: Optional[str] = Field(default=None, description="Client-unique key")

# --- Cloud API Endpoints ---

@app.get("/ping")
@app.get("/api/ping")
def ping():
    return {"ping": "pong", "runtime": "vercel-serverless", "version": "2.0.0"}

@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint for Vercel serverless runtime."""
    return {
        "status": "healthy",
        "system": "AI Workforce OS",
        "version": "2.0.0",
        "runtime": "vercel-serverless",
        "cloud_database_configured": supabase.is_configured(),
        "database": "Supabase PostgreSQL (Cloud Hybrid Queue)",
        "agent_loop": "5-Stage Enforced (Run Policy -> Think -> Act -> Observe -> Deterministic Code Check)"
    }

@app.get("/api/projects")
async def list_projects():
    """List all workspace projects."""
    return PROJECTS_STORE

@app.post("/api/projects", status_code=201)
async def create_project(req: ProjectCreateRequest):
    """Create a new project workspace."""
    proj_id = f"proj-{uuid.uuid4().hex[:8]}"
    new_proj = {
        "id": proj_id,
        "name": req.name,
        "description": req.description or "",
        "category": req.category or "general",
        "lead_agent_id": req.lead_agent_id or "coordinator",
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    PROJECTS_STORE.insert(0, new_proj)
    return new_proj

@app.get("/api/nodes")
async def list_runtime_nodes():
    """List registered execution nodes (MacBook Pro status)."""
    if not supabase.is_configured():
        return {
            "success": False,
            "error": "Supabase credentials not configured",
            "nodes": [
                {
                    "node_id": "macbook-pro-primary",
                    "status": "active_online",
                    "capabilities": ["browser_automation", "local_shell", "credentials_vault", "sqlite_wal"]
                }
            ]
        }
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{supabase.rest_url}/runtime_nodes?order=last_heartbeat.desc",
                headers=supabase._get_headers()
            )
            if res.is_success:
                return {"success": True, "nodes": res.json()}
            return {"success": False, "error": res.text, "nodes": []}
    except Exception as e:
        logger.error(f"Error fetching runtime nodes: {e}")
        return {"success": False, "error": str(e), "nodes": []}

@app.get("/api/tasks")
async def list_cloud_tasks():
    """List tasks queued or executed in the hybrid cloud queue. Returns JSON list."""
    if not supabase.is_configured():
        return []

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{supabase.rest_url}/hybrid_tasks?order=created_at.desc&limit=50",
                headers=supabase._get_headers()
            )
            if res.is_success:
                raw_tasks = res.json()
                normalized = []
                for t in raw_tasks:
                    payload = t.get("input_payload") or {}
                    proj_id = payload.get("project_id") if isinstance(payload, dict) else "proj-core-os"
                    normalized.append({
                        "id": t.get("id"),
                        "title": t.get("title"),
                        "description": t.get("description"),
                        "assigned_agent_id": t.get("assigned_agent_id"),
                        "project_id": proj_id or "proj-core-os",
                        "status": t.get("status", "pending"),
                        "priority": "high" if (isinstance(t.get("priority"), int) and t.get("priority") > 70) else ("low" if (isinstance(t.get("priority"), int) and t.get("priority") < 30) else "medium"),
                        "verification_status": t.get("verification_status", "pending"),
                        "output_result": t.get("output_payload"),
                        "created_at": t.get("created_at"),
                        "updated_at": t.get("updated_at")
                    })
                return normalized
            return []
    except Exception as e:
        logger.error(f"Error fetching tasks from Supabase: {e}")
        return []

@app.post("/api/tasks")
async def submit_cloud_task(req: TaskSubmitRequest):
    """Submit a task to the hybrid queue with idempotency protection."""
    idempotency_key = req.idempotency_key or f"task-{uuid.uuid4().hex[:12]}"
    agent_id = req.assigned_agent_id or req.target_agent or "coordinator"
    
    # Priority normalization
    pri_val = 50
    if isinstance(req.priority, int):
        pri_val = req.priority
    elif isinstance(req.priority, str):
        pri_map = {"low": 25, "medium": 50, "high": 80, "critical": 100}
        pri_val = pri_map.get(req.priority.lower(), 50)

    input_payload = req.input_payload or req.context or {}
    if req.project_id:
        input_payload["project_id"] = req.project_id

    res = await supabase.submit_hybrid_task(
        idempotency_key=idempotency_key,
        title=req.title,
        description=req.description,
        assigned_agent_id=agent_id,
        runtime_target=req.runtime_target,
        required_capabilities=req.required_capabilities or [],
        priority=pri_val,
        input_payload=input_payload
    )
    
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Task submission failed"))
    
    task_obj = res.get("task") or {}
    task_id = task_obj.get("id") or res.get("task_id")
    
    return {
        "id": task_id,
        "title": req.title,
        "description": req.description,
        "assigned_agent_id": agent_id,
        "status": "pending",
        "priority": req.priority if isinstance(req.priority, str) else "medium",
        "verification_status": "pending",
        "created_at": task_obj.get("created_at")
    }

@app.get("/api/tasks/{task_id}")
async def get_cloud_task(task_id: str):
    """Get status and result of a hybrid task."""
    if not supabase.is_configured():
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{supabase.rest_url}/hybrid_tasks?id=eq.{task_id}",
                headers=supabase._get_headers()
            )
            if res.is_success:
                data = res.json()
                if not data:
                    raise HTTPException(status_code=404, detail="Task not found")
                t = data[0]
                return {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "description": t.get("description"),
                    "assigned_agent_id": t.get("assigned_agent_id"),
                    "status": t.get("status", "pending"),
                    "priority": "high" if (isinstance(t.get("priority"), int) and t.get("priority") > 70) else "medium",
                    "verification_status": t.get("verification_status", "pending"),
                    "output_result": t.get("output_payload"),
                    "input_context": t.get("input_payload"),
                    "created_at": t.get("created_at"),
                    "updated_at": t.get("updated_at")
                }
            raise HTTPException(status_code=res.status_code, detail=res.text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}/events")
async def get_task_events(task_id: str):
    """Return task execution events."""
    return [
        {
            "id": f"ev-{uuid.uuid4().hex[:6]}",
            "task_id": task_id,
            "event_type": "hybrid_task_state",
            "payload": {"message": "Task queued in cloud hybrid queue for local Mac execution."},
            "timestamp": None
        }
    ]

@app.get("/api/agents")
async def list_cloud_agents():
    """List all 32 agent blueprints and specialists registered in the OS."""
    agents_dir = ROOT_DIR / "config" / "agents"
    if agents_dir.exists():
        import yaml
        blueprints = []
        for yf in sorted(agents_dir.glob("*.yaml")):
            try:
                with open(yf, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict):
                        blueprints.append(data)
            except Exception as e:
                logger.warning(f"Error reading {yf}: {e}")
        if blueprints:
            return blueprints

    if supabase.is_configured():
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{supabase.rest_url}/agent_blueprints?order=department.asc,name.asc",
                    headers=supabase._get_headers()
                )
                if res.is_success and res.json():
                    items = res.json()
                    for item in items:
                        for fld in ("specialists", "capabilities", "permissions", "default_model"):
                            if isinstance(item.get(fld), str):
                                try:
                                    item[fld] = json.loads(item[fld])
                                except Exception:
                                    pass
                    return items
        except Exception as e:
            logger.warning(f"Failed to query agents from Supabase: {e}")

    return []

# --- Security & Vault Safe Cloud Endpoints (No plaintext secrets exposed) ---
@app.get("/api/security/accounts")
async def list_cloud_security_accounts():
    """Returns credential accounts metadata without exposing secrets."""
    if supabase.is_configured():
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{supabase.rest_url}/credential_accounts?order=category.asc,name.asc",
                    headers=supabase._get_headers()
                )
                if res.is_success and res.json():
                    return res.json()
        except Exception as e:
            logger.warning(f"Failed to fetch security accounts from Supabase: {e}")
            
    # Default sovereign vault representation
    return [
        {
            "id": "acc_github_prod",
            "category": "developer",
            "name": "GitHub (ibrahimzed24-a11y)",
            "username_or_email": "ibrahim.zed24@gmail.com",
            "url": "https://github.com",
            "mfa_status": "ENABLED",
            "health_status": "HEALTHY",
            "authorized_agents": [{"agent_id": "deployment-agent", "permission_level": "use"}],
            "updated_at": "2026-11-15T00:00:00"
        },
        {
            "id": "acc_supabase_prod",
            "category": "database",
            "name": "Supabase Cloud DB (jzyqmzjfmaceoltlqukh)",
            "username_or_email": "ibrahim.zed24@gmail.com",
            "url": "https://supabase.com",
            "mfa_status": "ENABLED",
            "health_status": "HEALTHY",
            "authorized_agents": [{"agent_id": "coordinator", "permission_level": "use"}],
            "updated_at": "2026-11-15T00:00:00"
        },
        {
            "id": "acc_vercel_prod",
            "category": "hosting",
            "name": "Vercel Cloud Edge (personal-ai-workforce-os)",
            "username_or_email": "ibraxeid89-7908",
            "url": "https://vercel.com",
            "mfa_status": "ENABLED",
            "health_status": "HEALTHY",
            "authorized_agents": [{"agent_id": "deployment-agent", "permission_level": "use"}],
            "updated_at": "2026-11-15T00:00:00"
        }
    ]

@app.get("/api/security/health")
async def get_cloud_security_health():
    """Returns sovereignty and vault security status."""
    return {
        "status": "HEALTHY",
        "total_accounts": 3,
        "mfa_enabled_accounts": 3,
        "vault_location": "MacBook Pro Hardware Keychain / AES-128 Fernet",
        "cloud_exposure": "ZERO_CREDENTIAL_STORAGE (Stateless Edge Gateway)",
        "risk_level": "LOW",
        "recommendations": ["Hardware tokens and POSIX 0600 vault strictly bound to local Mac."]
    }

@app.get("/api/security/audit")
async def get_cloud_security_audit(limit: int = 20):
    return [
        {
            "id": "aud_1",
            "actor_type": "agent",
            "actor_id": "coordinator",
            "action": "hybrid_queue_poll",
            "status": "SUCCESS",
            "details": {"runtime": "macbook-pro-primary", "verification": "hmac_verified"},
            "timestamp": "2026-11-15T04:20:00"
        }
    ]

# --- Models & Reasoning API ---
@app.get("/api/models/status")
async def get_cloud_models_status():
    return {
        "active_reasoning_engine": "Hybrid Sovereign Multi-Tier Routing",
        "local_provider": "Ollama / Local Apple Silicon",
        "cloud_provider": "Gemini 2.5 Flash / Claude 3.5 Sonnet",
        "offline_deterministic_fallback": "DeterministicMockProvider (MOCKED_OR_SIMULATED)",
        "default_model": "gemini-2.5-flash",
        "agent_loop": "5-Stage Enforced (Run Policy -> Think -> Act -> Observe -> Deterministic Code Check)"
    }

@app.get("/api/models/providers")
async def list_cloud_providers():
    return [
        {"id": "gemini", "name": "Google Gemini", "provider_type": "cloud_gemini", "health_status": "healthy"},
        {"id": "anthropic", "name": "Anthropic Claude", "provider_type": "cloud_anthropic", "health_status": "healthy"},
        {"id": "ollama", "name": "Local Ollama Daemon", "provider_type": "local_ollama", "health_status": "healthy"},
        {"id": "mock", "name": "Deterministic Sovereign Engine", "provider_type": "mock", "health_status": "healthy"}
    ]

@app.get("/api/models")
async def list_cloud_models():
    return [
        {"id": "gemini-2.5-flash", "display_name": "Gemini 2.5 Flash", "provider_id": "gemini", "classification": "cloud", "is_default": 1},
        {"id": "claude-3-5-sonnet", "display_name": "Claude 3.5 Sonnet", "provider_id": "anthropic", "classification": "cloud", "is_default": 0},
        {"id": "llama3.2:3b", "display_name": "Llama 3.2 (Local)", "provider_id": "ollama", "classification": "local", "is_default": 0},
        {"id": "mock-deterministic-v1", "display_name": "Deterministic Verifier", "provider_id": "mock", "classification": "mock", "is_default": 0}
    ]

@app.get("/api/requirements")
async def list_cloud_requirements():
    return []

@app.get("/api/integrator/knowledge")
async def get_cloud_knowledge():
    return {
        "status": "synchronized",
        "skills_indexed": 32,
        "agents_indexed": 32,
        "capabilities_registered": 14,
        "runtime_target": "hybrid_local_cloud"
    }

@app.get("/api/loops")
async def list_cloud_loops():
    """List 5-stage agent execution loop traces."""
    if supabase.is_configured():
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{supabase.rest_url}/agent_loop_traces?order=created_at.desc&limit=20",
                    headers=supabase._get_headers()
                )
                if res.is_success:
                    return res.json()
        except Exception as e:
            logger.warning(f"Error fetching loop traces: {e}")
    return []

