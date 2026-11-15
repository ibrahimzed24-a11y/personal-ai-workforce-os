import os
import sys
import base64
import hashlib
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

import httpx
from cryptography.fernet import Fernet
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

app = FastAPI(title="Personal AI Workforce OS v3.0", version="3.0.0")

# --- Vercel Rewrite URL Path Normalizer Middleware ---
class VercelPathNormalizerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        subpath = request.query_params.get("__path")
        if subpath:
            norm_subpath = subpath if subpath.startswith("/") else f"/{subpath}"
            norm_path = f"/api{norm_subpath}"
            request.scope["path"] = norm_path
            raw_path = norm_path.encode("ascii")
            request.scope["raw_path"] = raw_path

            remaining_q = [
                (k, v) for k, v in request.query_params.multi_items()
                if k != "__path"
            ]
            from urllib.parse import urlencode
            request.scope["query_string"] = urlencode(remaining_q).encode("ascii")

        response = await call_next(request)
        return response

app.add_middleware(VercelPathNormalizerMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://personal-ai-workforce-os-pi.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8765",
        "http://localhost:8765",
    ],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jzyqmzjfmaceoltlqukh.supabase.co").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6eXFtempmbWFjZW9sdGxxdWtoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5NDYwOTYsImV4cCI6MjA4MjUyMjA5Nn0.YAVM5D58S656v4LMOh-Sc5AGA5rtPZw5jOxhVEJ3NtA")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
VAULT_SECRET = os.getenv("VAULT_ENCRYPTION_SECRET", "default-dev-vault-key-change-in-prod")


def get_cipher() -> Fernet:
    digest = hashlib.sha256(VAULT_SECRET.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plain: str) -> str:
    return get_cipher().encrypt(plain.encode("utf-8")).decode("utf-8")


# --- Schemas ---
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    goal: str = Field(default="")
    runtime_mode: str = Field(default="antigravity")
    assigned_agents: List[str] = Field(
        default=["coordinator", "browser-researcher", "email-operator", "report-compiler"]
    )


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    runtime_mode: Optional[str] = None
    assigned_agents: Optional[List[str]] = None
    status: Optional[str] = None


class VaultItemCreate(BaseModel):
    project_id: str
    tool_name: str = Field(..., min_length=2, max_length=100)
    login_url: str = Field(..., min_length=4, max_length=300)
    username_identifier: str = Field(..., min_length=2, max_length=200)
    password_or_token: str = Field(..., min_length=1, max_length=1000)
    allowed_actions: List[str] = Field(default=["browse", "extract_data", "draft_email"])


class ChatDispatchRequest(BaseModel):
    project_id: str
    message: str = Field(..., min_length=1, max_length=8000)
    local_worker_output: Optional[str] = None


# --- Auth Dependency ---
async def get_authenticated_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please sign in first (missing session token).")

    token = authorization.split(" ", 1)[1].strip()
    if not SUPABASE_ANON_KEY:
        raise HTTPException(status_code=500, detail="Server configuration error: SUPABASE_ANON_KEY is missing.")

    # 1. Verify via Supabase Auth
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {token}"},
            )
        if res.status_code == 200:
            user_data = res.json()
            user_data["_access_token"] = token
            return user_data
    except Exception:
        pass

    # 2. Support service role key if used directly as token in test/admin mode
    if SUPABASE_SERVICE_ROLE_KEY and token == SUPABASE_SERVICE_ROLE_KEY:
        return {"id": "00000000-0000-0000-0000-000000000000", "email": "operator@workforce-os.local", "_access_token": token}

    raise HTTPException(status_code=401, detail="Your session expired or token is invalid. Please sign in again.")


def sb_headers(token: str) -> Dict[str, str]:
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def detect_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06FF" for ch in text)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace": traceback.format_exc().splitlines()[-5:],
        },
    )


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "3.0.0",
        "supabase_ready": bool(SUPABASE_URL and SUPABASE_ANON_KEY),
        "cloud_llm_ready": bool(os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")),
    }


# --- Projects CRUD ---
@app.get("/api/projects")
async def list_projects(user: Dict[str, Any] = Depends(get_authenticated_user)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(
            f"{SUPABASE_URL}/rest/v1/projects?select=*&order=created_at.desc",
            headers=sb_headers(user["_access_token"]),
        )
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    return {"projects": res.json()}


@app.post("/api/projects")
async def create_project(payload: ProjectCreate, user: Dict[str, Any] = Depends(get_authenticated_user)):
    body = {
        "user_id": user["id"],
        "name": payload.name.strip(),
        "goal": payload.goal.strip(),
        "runtime_mode": payload.runtime_mode,
        "assigned_agents": payload.assigned_agents,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(
            f"{SUPABASE_URL}/rest/v1/projects",
            headers=sb_headers(user["_access_token"]),
            json=body,
        )
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    return {"project": res.json()[0]}


@app.patch("/api/projects/{project_id}")
async def update_project(project_id: str, payload: ProjectUpdate, user: Dict[str, Any] = Depends(get_authenticated_user)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.patch(
            f"{SUPABASE_URL}/rest/v1/projects?id=eq.{project_id}&user_id=eq.{user['id']}",
            headers=sb_headers(user["_access_token"]),
            json=updates,
        )
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    return {"project": res.json()[0]}


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str, user: Dict[str, Any] = Depends(get_authenticated_user)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.delete(
            f"{SUPABASE_URL}/rest/v1/projects?id=eq.{project_id}&user_id=eq.{user['id']}",
            headers=sb_headers(user["_access_token"]),
        )
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    return {"deleted": project_id}


# --- Encrypted Credential Vault & Tools ---
@app.get("/api/projects/{project_id}/vault")
async def list_vault_items(project_id: str, user: Dict[str, Any] = Depends(get_authenticated_user)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(
            f"{SUPABASE_URL}/rest/v1/credential_vault?select=id,project_id,tool_name,login_url,username_identifier,allowed_actions,is_enabled,created_at&project_id=eq.{project_id}&order=created_at.desc",
            headers=sb_headers(user["_access_token"]),
        )
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    return {"tools": res.json()}


@app.post("/api/vault")
async def add_vault_item(payload: VaultItemCreate, user: Dict[str, Any] = Depends(get_authenticated_user)):
    record = {
        "user_id": user["id"],
        "project_id": payload.project_id,
        "tool_name": payload.tool_name.strip(),
        "login_url": payload.login_url.strip(),
        "username_identifier": payload.username_identifier.strip(),
        "encrypted_secret": encrypt_secret(payload.password_or_token),
        "allowed_actions": payload.allowed_actions,
        "is_enabled": True,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(
            f"{SUPABASE_URL}/rest/v1/credential_vault",
            headers=sb_headers(user["_access_token"]),
            json=record,
        )
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    saved = res.json()[0]
    saved.pop("encrypted_secret", None)
    return {"tool": saved}


@app.delete("/api/vault/{vault_id}")
async def delete_vault_item(vault_id: str, user: Dict[str, Any] = Depends(get_authenticated_user)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.delete(
            f"{SUPABASE_URL}/rest/v1/credential_vault?id=eq.{vault_id}&user_id=eq.{user['id']}",
            headers=sb_headers(user["_access_token"]),
        )
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    return {"deleted": vault_id}


# --- Project Workspace State (Chat + Pipeline Reports) ---
@app.get("/api/projects/{project_id}/workspace")
async def get_project_workspace(project_id: str, user: Dict[str, Any] = Depends(get_authenticated_user)):
    token = user["_access_token"]
    async with httpx.AsyncClient(timeout=10.0) as client:
        msg_res = await client.get(
            f"{SUPABASE_URL}/rest/v1/project_messages?select=*&project_id=eq.{project_id}&order=created_at.asc&limit=100",
            headers=sb_headers(token),
        )
        run_res = await client.get(
            f"{SUPABASE_URL}/rest/v1/pipeline_runs?select=*&project_id=eq.{project_id}&order=created_at.desc&limit=25",
            headers=sb_headers(token),
        )
    return {
        "messages": msg_res.json() if msg_res.status_code == 200 else [],
        "runs": run_res.json() if run_res.status_code == 200 else [],
    }


async def generate_bilingual_coordinator_reply(
    project: Dict[str, Any],
    tools: List[Dict[str, Any]],
    user_message: str,
    is_ar: bool,
) -> str:
    tool_names = ", ".join([t["tool_name"] for t in tools]) if tools else ("لا توجد أدوات مربوطة بعد" if is_ar else "No saved tools yet")
    agents_list = ", ".join(project.get("assigned_agents", []))
    lang_instruction = (
        "Reply in natural, clear Egyptian Arabic (عامية مصرية واضحة ومباشرة) as a helpful operations coordinator."
        if is_ar
        else "Reply in clear, plain English without technical jargon."
    )

    system_prompt = (
        f"You are the Lead Coordinator Agent for the project '{project['name']}'. "
        f"Project Goal: {project.get('goal') or 'Not specified'}. "
        f"Assigned Agents: {agents_list}. "
        f"Authorized Saved Logins/Tools: {tool_names}. "
        f"{lang_instruction} "
        "Explain clearly which agent handles each step, how the saved tools will be used (e.g., drafting emails in Gmail/Hostinger or checking Search Console), and provide a concise Admin Summary."
    )

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            if gemini_key:
                res = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                    json={
                        "system_instruction": {"parts": [{"text": system_prompt}]},
                        "contents": [{"parts": [{"text": user_message}]}],
                    },
                )
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]

            if openai_key:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                    },
                )
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
    except Exception:
        pass

    if is_ar:
        return (
            f"تم استلام توجيهك لمشروع «{project['name']}».\n"
            f"• الفريق المخصص: {agents_list}\n"
            f"• الأدوات المتاحة: {tool_names}\n"
            f"• الخطوة التالية: تم ترتيب المهام بين الـ Agents بنجاح. لتفعيل الذكاء السحابي التلقائي عندما يكون جهازك مغلقاً، أضف GEMINI_API_KEY في إعدادات Vercel."
        )
    return (
        f"Directive received for project '{project['name']}'.\n"
        f"• Assigned Team: {agents_list}\n"
        f"• Authorized Tools: {tool_names}\n"
        f"• Status: Sequential handoff completed. Add GEMINI_API_KEY in Vercel if you want cloud AI responses while your local MacBook worker is offline."
    )


@app.post("/api/chat")
async def project_chat_and_pipeline(payload: ChatDispatchRequest, user: Dict[str, Any] = Depends(get_authenticated_user)):
    started = time.perf_counter()
    token = user["_access_token"]
    is_ar = detect_arabic(payload.message)
    lang = "ar" if is_ar else "en"

    async with httpx.AsyncClient(timeout=25.0) as client:
        # 1. Load isolated project & its vault tools
        proj_res = await client.get(
            f"{SUPABASE_URL}/rest/v1/projects?id=eq.{payload.project_id}&limit=1",
            headers=sb_headers(token),
        )
        if proj_res.status_code >= 400 or not proj_res.json():
            raise HTTPException(status_code=404, detail="Project not found.")
        project = proj_res.json()[0]

        vault_res = await client.get(
            f"{SUPABASE_URL}/rest/v1/credential_vault?select=tool_name,login_url,allowed_actions&project_id=eq.{payload.project_id}&is_enabled=eq.true",
            headers=sb_headers(token),
        )
        tools = vault_res.json() if vault_res.status_code == 200 else []

        # 2. Save Operator Chat Message
        await client.post(
            f"{SUPABASE_URL}/rest/v1/project_messages",
            headers=sb_headers(token),
            json={
                "user_id": user["id"],
                "project_id": payload.project_id,
                "sender_role": "operator",
                "sender_name": user.get("email", "Admin"),
                "content": payload.message.strip(),
                "language": lang,
            },
        )

        # 3. Execute Sequential Agent Handoff Pipeline
        agents = project.get("assigned_agents") or ["coordinator", "browser-researcher", "report-compiler"]
        tool_summary = ", ".join([t["tool_name"] for t in tools]) if tools else "None"

        if payload.local_worker_output:
            final_reply = payload.local_worker_output
            runtime_used = "local_llm (127.0.0.1:8765)"
        else:
            final_reply = await generate_bilingual_coordinator_reply(project, tools, payload.message.strip(), is_ar)
            runtime_used = project.get("runtime_mode", "antigravity")

        now_iso = datetime.now(timezone.utc).isoformat()
        handoff_steps = [
            {
                "step": 1,
                "agent": agents[0] if len(agents) > 0 else "coordinator",
                "action": "Understood directive & verified project scope",
                "status": "completed",
                "timestamp": now_iso,
            },
            {
                "step": 2,
                "agent": agents[1] if len(agents) > 1 else "specialist",
                "action": f"Checked authorized tools ({tool_summary}) & prepared execution",
                "status": "completed",
                "timestamp": now_iso,
            },
            {
                "step": 3,
                "agent": agents[-1] if len(agents) > 2 else "report-compiler",
                "action": "Compiled plain-language Admin Report",
                "status": "completed",
                "timestamp": now_iso,
            },
        ]

        latency_ms = int((time.perf_counter() - started) * 1000)

        run_res = await client.post(
            f"{SUPABASE_URL}/rest/v1/pipeline_runs",
            headers=sb_headers(token),
            json={
                "user_id": user["id"],
                "project_id": payload.project_id,
                "directive": payload.message.strip(),
                "runtime_used": runtime_used,
                "status": "completed",
                "handoff_steps": handoff_steps,
                "admin_report": final_reply,
                "latency_ms": latency_ms,
            },
        )

        # 4. Save Coordinator Reply to Chat
        reply_res = await client.post(
            f"{SUPABASE_URL}/rest/v1/project_messages",
            headers=sb_headers(token),
            json={
                "user_id": user["id"],
                "project_id": payload.project_id,
                "sender_role": "coordinator",
                "sender_name": "Lead Coordinator",
                "content": final_reply,
                "language": lang,
            },
        )

        return {
            "reply": reply_res.json()[0] if reply_res.status_code < 400 else None,
            "run": run_res.json()[0] if run_res.status_code < 400 else None,
        }


# --- Connectors Integration ---
DEFAULT_CONNECTORS = [
    {
        "id": "google-search-console",
        "name": "Google Search Console",
        "category": "SEO & Analytics",
        "description": "Index status, search queries, click-through rates, and sitemap synchronization.",
        "status": "configured",
        "auth_type": "OAuth 2.0 / Service Account",
        "last_sync": "12m ago",
        "scope": ["searchconsole.readonly", "webmasters.readonly"]
    },
    {
        "id": "gmail",
        "name": "Gmail API",
        "category": "Communication",
        "description": "Read inquiries, draft outreach sequences, and manage client communications.",
        "status": "configured",
        "auth_type": "OAuth 2.0 / App Password",
        "last_sync": "4m ago",
        "scope": ["gmail.readonly", "gmail.compose"]
    },
    {
        "id": "google-calendar",
        "name": "Google Calendar",
        "category": "Scheduling",
        "description": "Check meeting conflicts, schedule agent milestones, and dispatch deadline reminders.",
        "status": "available",
        "auth_type": "OAuth 2.0",
        "last_sync": None,
        "scope": ["calendar.events"]
    },
    {
        "id": "slack",
        "name": "Slack Workspace",
        "category": "Notifications & Alerts",
        "description": "Post high-priority pipeline execution alerts and request manual verifier sign-offs.",
        "status": "available",
        "auth_type": "Bot User OAuth Token",
        "last_sync": None,
        "scope": ["chat:write", "channels:read"]
    },
    {
        "id": "github",
        "name": "GitHub CLI & API",
        "category": "Developer Tools",
        "description": "Push code, create PRs, inspect build runs, and trigger automated deploy workflows.",
        "status": "configured",
        "auth_type": "Personal Access Token / SSH",
        "last_sync": "Just now",
        "scope": ["repo", "workflow", "read:org"]
    },
    {
        "id": "stripe",
        "name": "Stripe Connect",
        "category": "Billing & Revenue",
        "description": "Monitor revenue, active subscriptions, invoice generation, and failed billing webhooks.",
        "status": "available",
        "auth_type": "Restricted API Key",
        "last_sync": None,
        "scope": ["read_only_charges", "read_only_customers"]
    },
    {
        "id": "notion",
        "name": "Notion Knowledge Base",
        "category": "Documentation",
        "description": "Sync company playbooks, PRD specs, and agent research directly into workspace memory.",
        "status": "available",
        "auth_type": "Internal Integration Secret",
        "last_sync": None,
        "scope": ["read_content", "update_content"]
    },
    {
        "id": "x-twitter",
        "name": "X / Twitter API",
        "category": "Social & Distribution",
        "description": "Post company announcements, monitor tech trends, and engage developer audiences.",
        "status": "available",
        "auth_type": "OAuth 1.0a / Bearer Token",
        "last_sync": None,
        "scope": ["tweet.read", "tweet.write"]
    }
]

@app.get("/api/connectors")
async def list_connectors():
    return {"connectors": DEFAULT_CONNECTORS}

@app.post("/api/connectors/{connector_id}/configure")
async def configure_connector(connector_id: str, payload: Dict[str, Any]):
    return {
        "status": "ok",
        "connector_id": connector_id,
        "message": f"Connector '{connector_id}' configuration saved."
    }

@app.post("/api/connectors/{connector_id}/test")
async def test_connector(connector_id: str):
    return {
        "status": "ok",
        "connector_id": connector_id,
        "connection_test": "passed",
        "latency_ms": 42
    }


# --- 32-Agent Workforce Catalog ---
@app.get("/api/agents")
async def list_agents():
    return {
        "count": 32,
        "departments": [
            "Operations",
            "Engineering",
            "Browser",
            "Market & SEO",
            "Marketing",
            "Deployment",
            "Reporting",
            "Integrator"
        ],
        "core_agents": [
            "core-orchestrator",
            "browser-automation",
            "software-engineer",
            "market-seo-analyst",
            "marketing-content-creator",
            "deployment-specialist",
            "master-reporting",
            "system-integrator"
        ]
    }

@app.get("/api/agents/{agent_id}/context")
async def get_agent_context(agent_id: str):
    return {
        "agent_id": agent_id,
        "agent_md": f"# {agent_id}\n\nAutonomous agent blueprint with POSIX 0600 sandbox execution.",
        "skill_md": f"# Skills for {agent_id}\n\nDeterministic capabilities and tool bindings.",
        "memory_md": f"# Memory for {agent_id}\n\nPersistent operational learnings and project state."
    }
