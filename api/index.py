import os
import sys
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
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
    description="Stateless Serverless API and Dashboard for Personal AI Workforce OS on Vercel",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = SupabaseAdapter()

# --- Request / Response Models ---
class TaskSubmitRequest(BaseModel):
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Detailed instructions")
    assigned_agent_id: str = Field(default="core-orchestrator", description="Target agent blueprint ID")
    runtime_target: str = Field(default="local", description="Target runtime ('local', 'cloud', 'any')")
    required_capabilities: Optional[List[str]] = Field(default_factory=list)
    priority: int = Field(default=50, description="Priority (1-100)")
    input_payload: Optional[Dict[str, Any]] = Field(default_factory=dict)
    idempotency_key: Optional[str] = Field(default=None, description="Client-unique key")

# --- Cloud API Endpoints ---

@app.get("/ping")
@app.get("/api/ping")
def ping():
    return {"ping": "pong", "runtime": "vercel-serverless"}

@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint for Vercel serverless runtime."""
    return {
        "status": "healthy",
        "runtime": "vercel-serverless",
        "cloud_database_configured": supabase.is_configured(),
        "version": "1.0.0"
    }

@app.get("/api/nodes")
async def list_runtime_nodes():
    """List registered execution nodes (e.g. MacBook Pro status)."""
    if not supabase.is_configured():
        return {
            "success": False,
            "error": "Supabase credentials not configured",
            "nodes": [
                {
                    "node_id": "macbook-pro-local",
                    "status": "active_offline",
                    "capabilities": ["browser_automation", "local_shell", "credentials_vault"]
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
    """List tasks queued or executed in the hybrid cloud queue."""
    if not supabase.is_configured():
        return {"success": False, "error": "Supabase not configured", "tasks": []}

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{supabase.rest_url}/hybrid_tasks?order=created_at.desc&limit=50",
                headers=supabase._get_headers()
            )
            if res.is_success:
                return {"success": True, "tasks": res.json()}
            return {"success": False, "error": res.text, "tasks": []}
    except Exception as e:
        logger.error(f"Error fetching tasks from Supabase: {e}")
        return {"success": False, "error": str(e), "tasks": []}

@app.post("/api/tasks")
async def submit_cloud_task(req: TaskSubmitRequest):
    """Submit a task to the hybrid queue with idempotency protection."""
    idempotency_key = req.idempotency_key or f"task-{uuid.uuid4()}"
    
    res = await supabase.submit_hybrid_task(
        idempotency_key=idempotency_key,
        title=req.title,
        description=req.description,
        assigned_agent_id=req.assigned_agent_id,
        runtime_target=req.runtime_target,
        required_capabilities=req.required_capabilities,
        priority=req.priority,
        input_payload=req.input_payload
    )
    
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Task submission failed"))
    return res

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
                return data[0]
            raise HTTPException(status_code=res.status_code, detail=res.text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents")
async def list_cloud_agents():
    """List agent blueprints registered in the OS."""
    if supabase.is_configured():
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{supabase.rest_url}/agent_blueprints?order=department.asc,name.asc",
                    headers=supabase._get_headers()
                )
                if res.is_success and res.json():
                    return res.json()
        except Exception as e:
            logger.warning(f"Failed to query agents from Supabase, falling back to local files: {e}")

    # Fallback to local catalog if disk is accessible
    from core.agent_context import AgentContextLoader
    loader = AgentContextLoader()
    return loader.list_all_agents()

# --- Static UI Serving ---
UI_DIR = ROOT_DIR / "core" / "ui"
if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        index_file = UI_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"message": "AI Workforce OS Vercel API Active"})

@app.api_route("/{full_path:path}", methods=["GET", "POST"])
async def catch_all(full_path: str, request: Request):
    return {
        "status": "online",
        "runtime": "vercel-serverless",
        "requested_path": full_path,
        "request_url": str(request.url),
        "headers": dict(request.headers),
        "message": "AI Workforce OS Serverless Gateway"
    }
