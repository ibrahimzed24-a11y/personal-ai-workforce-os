# Personal AI Workforce OS — Vercel Deployment & Serverless Integration Report

**Document Version:** 1.0.0  
**Target Environment:** Vercel Serverless Platform  
**Integration Status:** Ready for Production Deployment  

---

## 1. Executive Summary

The cloud web dashboard and external API for the Personal AI Workforce OS are packaged for serverless hosting on **Vercel**. In keeping with the local-sovereignty security mandate:
- **Stateless Serverless Execution:** The Vercel runtime hosts the owner UI, API status gateways, and accepts task submissions.
- **Zero Local Secrets on Cloud:** Master credentials vault keys, website passwords, and active session tokens are **never** uploaded to or configured in Vercel.
- **Decoupled Task Offloading:** Tasks submitted via the web dashboard are dispatched asynchronously to Supabase `hybrid_tasks`, which are then leased and executed locally by the owner's MacBook workstation.

---

## 2. Configuration & Asset Architecture

### 2.1. File Manifest
- `api/index.py`: Serverless ASGI entry point providing `/api/health`, `/api/nodes`, `/api/tasks`, `/api/agents`, and static web routing.
- `vercel.json`: Serverless routing rules, reverse-proxy rewrites, and security headers.
- `requirements.txt`: Python package manifest for Vercel's `@vercel/python` build environment.
- `core/ui/`: Static web UI assets (`index.html`, `style.css`, `app.js`) served alongside the API.

### 2.2. Routing & Rewrites Specification (`vercel.json`)
```json
{
  "version": 2,
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index.py" },
    { "source": "/static/(.*)", "destination": "/core/ui/$1" },
    { "source": "/(.*)", "destination": "/api/index.py" }
  ]
}
```

### 2.3. HTTP Security Headers
Every response served by Vercel enforces enterprise-grade security headers:
- `X-Content-Type-Options: nosniff` (Prevents MIME-sniffing)
- `X-Frame-Options: DENY` (Prevents clickjacking)
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (HSTS)
- `Content-Security-Policy`: Restricts scripts and connections strictly to self, Google Fonts, and the owner's Supabase project domain.

---

## 3. Required Environment Variables

Configure the following environment variables in the **Vercel Project Settings > Environment Variables**:

| Variable Name | Required Environment | Description | Example / Security Constraint |
| :--- | :--- | :--- | :--- |
| `SUPABASE_URL` | Production, Preview, Development | Public Supabase HTTPS endpoint | `https://<project-ref>.supabase.co` |
| `SUPABASE_ANON_KEY` | Production, Preview, Development | Supabase client public anon key | `eyJhbGciOi...` (Safe for client/serverless use) |
| `SUPABASE_SERVICE_ROLE_KEY` | Production (Optional) | Serverless backend operations | **Must be scoped strictly to private serverless endpoints.** Never expose in client JS. |

> [!CAUTION]
> **DO NOT** add `VAULT_MASTER_KEY` or any website account passwords to Vercel environment variables. The web dashboard does not handle raw credential decryption.

---

## 4. Owner Handover: Deployment Instructions

Because Vercel CLI is not currently authenticated on this workstation, run the following commands to link and deploy the project to your Vercel account:

### Step 1: Install Vercel CLI (if not already installed)
```bash
npm install -g vercel
# or run directly with npx
```

### Step 2: Login to Vercel
```bash
vercel login
```

### Step 3: Link Project & Set Environment Variables
```bash
cd /Users/ibrahimzid/AI-Workforce

# Link to a new or existing Vercel project
vercel link

# Add Supabase configuration
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY
```

### Step 4: Deploy to Production
```bash
vercel deploy --prod
```

Once deployment completes, Vercel will output your production domain (e.g., `https://personal-ai-workforce-os.vercel.app`).
