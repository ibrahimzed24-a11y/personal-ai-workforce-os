"""
GrillMe Engine: Adaptive Clarification & Alignment Interview Protocol
Operationalizes interactive interviews across all 32 Sovereign Autonomous Agents.
Steers the admin toward the optimal architecture, workflow logic, and safety constraints.
"""

import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Catalog of all 32 Sovereign Agents and their Department Affinity
AGENT_DIRECTORY = {
    "coordinator": ("Lead Coordinator Agent", "Operations & Orchestration"),
    "task-decomposer": ("Task Decomposer", "Operations & Orchestration"),
    "resource-allocator": ("Resource Allocator", "Operations & Orchestration"),
    "progress-monitor": ("Progress Monitor", "Operations & Orchestration"),

    "market-seo-geo-researcher": ("Market & SEO Geo-Researcher", "Research & Market Strategy"),
    "competitor-intelligence": ("Competitor Intelligence Specialist", "Research & Market Strategy"),
    "geo-targeting-analyst": ("Geo-Targeting Analyst", "Research & Market Strategy"),
    "seo-auditor": ("SEO Auditor", "Research & Market Strategy"),

    "marketing-agent": ("Growth Marketing Lead", "Growth & Communications"),
    "content-strategist": ("Content Strategist", "Growth & Communications"),
    "campaign-planner": ("Campaign Planner", "Growth & Communications"),
    "brand-compliance": ("Brand & Compliance Officer", "Growth & Communications"),

    "email-operator": ("Email Operations Lead", "Operations & Outreach"),
    "service-manager": ("Service & Outreach Manager", "Operations & Outreach"),

    "software-engineer": ("Lead Software Engineer", "Engineering & Technology"),
    "backend-specialist": ("Backend Architecture Specialist", "Engineering & Technology"),
    "frontend-specialist": ("Frontend UI/UX Specialist", "Engineering & Technology"),
    "qa-test-engineer": ("QA & Automated Test Engineer", "Engineering & Technology"),

    "browser-use-agent": ("Browser-Use Automation Agent", "Automation & Data Acquisition"),
    "web-navigator": ("Autonomous Web Navigator", "Automation & Data Acquisition"),
    "data-extractor": ("DOM & Structured Data Extractor", "Automation & Data Acquisition"),
    "visual-inspector": ("Visual QA Inspector", "Automation & Data Acquisition"),

    "master-reporting-agent": ("Master Reporting Agent", "Executive & Audit"),
    "executive-summarizer": ("Executive Summarizer", "Executive & Audit"),
    "audit-trail-compiler": ("Audit Trail Compiler", "Executive & Audit"),
    "retrospective-analyst": ("Retrospective Analyst", "Executive & Audit"),

    "system-integrator-update-agent": ("System Integrator & Update Agent", "System Architecture & Integration"),
    "capability-knowledge-synchronizer": ("Capability Knowledge Synchronizer", "System Architecture & Integration"),
    "release-verifier": ("Release Verifier", "System Architecture & Integration"),
    "asset-classifier-auditor": ("Asset Classifier Auditor", "System Architecture & Integration"),
    "package-runtime-installer": ("Package Runtime Installer", "System Architecture & Integration"),
    "environment-provisioner": ("Environment Provisioner", "System Architecture & Integration"),
}


class GrillMeEngine:
    def __init__(self):
        pass

    def generate_alignment_interview(
        self,
        directive: str,
        agent_id: Optional[str] = None,
        project: Optional[Dict[str, Any]] = None,
        documents: Optional[List[Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyzes the directive, active core documents, and tools to construct
        a tailored sequence of alignment questions and an optimal workflow proposal.
        """
        proj = project or {}
        docs = documents or []
        tls = tools or []
        directive_clean = directive.strip() if directive else "Execute project milestone"
        lower_dir = directive_clean.lower()

        # Resolve primary agent
        resolved_agent = agent_id or "coordinator"
        if not agent_id:
            if any(k in lower_dir for k in ["email", "outreach", "campaign", "lead", "dental", "sales"]):
                resolved_agent = "coordinator"
            elif any(k in lower_dir for k in ["code", "bug", "test", "build", "api", "database", "refactor", "software"]):
                resolved_agent = "software-engineer"
            elif any(k in lower_dir for k in ["browse", "scrape", "crawl", "navigate", "extract", "website"]):
                resolved_agent = "browser-use-agent"
            elif any(k in lower_dir for k in ["seo", "keyword", "competitor", "market", "geo"]):
                resolved_agent = "market-seo-geo-researcher"
            elif any(k in lower_dir for k in ["marketing", "copy", "brand", "content", "social"]):
                resolved_agent = "marketing-agent"
            elif any(k in lower_dir for k in ["report", "audit", "summary", "kpi"]):
                resolved_agent = "master-reporting-agent"

        # Resolve agent identity
        agent_info = AGENT_DIRECTORY.get(resolved_agent, (resolved_agent.replace("-", " ").title(), "Operations & Orchestration"))
        agent_name = agent_info[0]
        department = agent_info[1]

        # Inspect core documents for domain grounding
        doc_names = [d.get("file_name", "") for d in docs]
        has_dental_leads = any("dental" in d.lower() or "leads" in d.lower() for d in doc_names)
        lead_doc_name = next(
            (d.get("file_name") for d in docs if "lead" in d.get("file_name", "").lower() or "dental" in d.get("file_name", "").lower()),
            "Core Project Dataset"
        )

        # Inspect connected tools
        tool_names = [t.get("tool_name", "") for t in tls]
        has_hostinger = any("hostinger" in t.lower() or "mail" in t.lower() for t in tool_names)

        # 1. SALES & EMAIL OUTREACH VECTOR
        if has_dental_leads or any(k in lower_dir for k in ["email", "outreach", "campaign", "lead", "dental", "clinic", "sales"]) or resolved_agent in ("email-operator", "service-manager"):
            agent_name = "Lead Coordinator & Sales Squad"
            department = "Operations & Outreach"

            proposed_workflow = {
                "title": "Optimal 4-Stage High-Converting Outreach Pipeline",
                "logic": "Enforces pre-dispatch data cleansing, personalized clinical value proposition, live admin verification test, and staggered timezone delivery.",
                "stages": [
                    {"step": 1, "agent": "market-seo-geo-researcher", "action": f"Segment and enrich {lead_doc_name} by province & practice focus"},
                    {"step": 2, "agent": "marketing-agent", "action": "Draft personalized consultative copy with individualized clinic merge fields"},
                    {"step": 3, "agent": "email-operator", "action": "Send 1 live verification test to admin (ibrahim.zed24@gmail.com) via Hostinger SSL:465"},
                    {"step": 4, "agent": "master-reporting-agent", "action": "Compile executive Task Deliverables Package (PDF + DOCX brief)"}
                ]
            }

            questions = [
                {
                    "id": "target_segmentation",
                    "agent": "market-seo-geo-researcher",
                    "question": f"Which regional Canadian clinic segment in «{lead_doc_name}» should we prioritize for initial outreach?",
                    "why_this_matters": "Focusing on Tier-1 metropolitan hubs with verified decision-maker emails maximizes initial conversion rates and protects sender domain reputation.",
                    "recommended_option": "Tier-1 Metropolitan Hubs: Toronto (ON), Vancouver (BC), and Calgary (AB) with verified contact names",
                    "options": [
                        "Tier-1 Metropolitan Hubs: Toronto (ON), Vancouver (BC), and Calgary (AB) (Recommended)",
                        "All 50 Canadian Dental Clinics across all provinces",
                        "Ontario Practices only (Eastern Timezone EST business hours)"
                    ]
                },
                {
                    "id": "copy_value_proposition",
                    "agent": "content-strategist",
                    "question": "What primary value proposition and conversational tone should our copywriter apply in the cold outreach sequences?",
                    "why_this_matters": "Dental practice owners respond best to measurable patient acquisition metrics rather than generic marketing pitches.",
                    "recommended_option": "Consultative Patient Acquisition & ROI: Highlighting automated booking of high-margin cosmetic & implant leads",
                    "options": [
                        "Consultative Patient Acquisition & ROI (High-margin cosmetic & implant leads) (Recommended)",
                        "Operational Efficiency & Staff Time Savings (Automated scheduling & reduced chair vacancy)",
                        "Exclusive Regional Partnership Invitation for select Canadian clinics"
                    ]
                },
                {
                    "id": "dispatch_safety_cadence",
                    "agent": "email-operator",
                    "question": "How should we execute the email dispatch via Hostinger SMTP (sales@health.valioz.com)?",
                    "why_this_matters": "Staged safety dispatch prevents email deliverability penalties, warm-up throttling, and allows immediate admin review before full broadcast.",
                    "recommended_option": "Staged Safety Dispatch: Send 1 live test brief to admin (ibrahim.zed24@gmail.com) first, then queue remaining clinics with 4-minute staggered intervals",
                    "options": [
                        "Staged Safety Dispatch: Live test email to admin first, followed by staggered sequence (Recommended)",
                        "Draft Preview Only: Generate PDF/DOCX preview mockups without sending live emails",
                        "Immediate Full Dispatch: Schedule and send to all 50 verified clinic leads"
                    ]
                },
                {
                    "id": "deliverable_formats",
                    "agent": "master-reporting-agent",
                    "question": "Which delivery artifacts do you require upon task completion?",
                    "why_this_matters": "The reporting synthesizer creates deterministic multi-format executive exports.",
                    "recommended_option": "Task Deliverables Package: Consolidated Executive PDF, Word Brief DOCX, and Lead Merge Table",
                    "options": [
                        "Task Deliverables Package: Consolidated Executive PDF, Word Brief DOCX, and Lead Merge Table (Recommended)",
                        "Executive Summary PDF only",
                        "Raw Markdown Ledger & Verified CSV export"
                    ]
                }
            ]
            recommended_directive = (
                f"Execute verified Canadian dental clinics outreach using «{lead_doc_name}» targeting Tier-1 hubs (Toronto, Vancouver, Calgary). "
                f"Apply consultative ROI copy, dispatch 1 live test email to admin (ibrahim.zed24@gmail.com) via Hostinger SMTP, "
                f"and compile full Task Deliverables Package (PDF + DOCX)."
            )

        # 2. SOFTWARE ENGINEERING & CODE ARCHITECTURE VECTOR
        elif any(k in lower_dir for k in ["code", "bug", "test", "build", "api", "database", "migration", "refactor", "software"]) or resolved_agent in ("software-engineer", "backend-specialist", "frontend-specialist", "qa-test-engineer"):
            agent_name = "Lead Software Engineer & Code Squad"
            department = "Engineering & Technology"

            proposed_workflow = {
                "title": "Optimal 4-Stage Test-Driven Engineering Pipeline",
                "logic": "Adheres to Superpowers TDD, non-destructive backward compatibility, POSIX permission isolation, and automated verification pass gates.",
                "stages": [
                    {"step": 1, "agent": "backend-specialist", "action": "Design deterministic contract schema & state boundaries"},
                    {"step": 2, "agent": "software-engineer", "action": "Implement modular components adhering to zero-breaking-change rule"},
                    {"step": 3, "agent": "qa-test-engineer", "action": "Execute automated pytest regression suite with 100% pass rate"},
                    {"step": 4, "agent": "deployment-agent", "action": "Stage deployment build and verify production environment status"}
                ]
            }

            questions = [
                {
                    "id": "architecture_pattern",
                    "agent": "software-engineer",
                    "question": "Which architectural pattern and state isolation model should be enforced?",
                    "why_this_matters": "Ensures modular maintenance, zero cloud leaks, and serverless resilience across cold starts.",
                    "recommended_option": "Modular Resilient Micro-Service: Ephemeral /tmp fallback with Supabase durable state backing",
                    "options": [
                        "Modular Resilient Micro-Service (Ephemeral /tmp fallback with Supabase durable state) (Recommended)",
                        "In-Memory State with SQLite WAL local persistence",
                        "Pure Stateless Functional Handlers with deterministic contracts"
                    ]
                },
                {
                    "id": "test_verification_depth",
                    "agent": "qa-test-engineer",
                    "question": "What verification depth is required before committing code changes?",
                    "why_this_matters": "Guarantees regression immunity across existing workforce endpoints.",
                    "recommended_option": "Comprehensive End-to-End Suite: Unit tests + Mock API contracts + Live integration test",
                    "options": [
                        "Comprehensive End-to-End Suite (Unit tests + Mock contracts + Integration test) (Recommended)",
                        "Targeted Component Unit Tests only",
                        "Smoke Test with HTTP Status 200 health probe"
                    ]
                },
                {
                    "id": "deployment_rollback_policy",
                    "agent": "deployment-agent",
                    "question": "What is the rollback and deployment release policy for this change?",
                    "why_this_matters": "Safeguards live production availability on Vercel and local worker node.",
                    "recommended_option": "Instant Blue-Green Git Tagging with automated rollback on test suite failure",
                    "options": [
                        "Instant Blue-Green Git Tagging with automated rollback (Recommended)",
                        "Direct commit and live Vercel prod deployment with post-release QA",
                        "Staging branch isolation with manual admin approval gate"
                    ]
                }
            ]
            recommended_directive = (
                f"Implement «{directive_clean}» using modular resilient architecture with /tmp serverless fallback. "
                f"Enforce full pytest verification suite and deploy with automated production readiness checks."
            )

        # 3. WEB RESEARCH & BROWSER AUTOMATION VECTOR
        elif any(k in lower_dir for k in ["browse", "scrape", "crawl", "navigate", "extract", "website", "competitor"]) or resolved_agent in ("browser-use-agent", "web-navigator", "data-extractor", "visual-inspector"):
            agent_name = "Autonomous Browser-Use Navigator & Research Squad"
            department = "Automation & Data Acquisition"

            proposed_workflow = {
                "title": "Optimal 4-Stage Headless Browser Research Pipeline",
                "logic": "Leverages Browser-Use Chromium CDP, structured DOM extraction, anti-bot respectful throttling, and visual audit evidence.",
                "stages": [
                    {"step": 1, "agent": "web-navigator", "action": "Probe target domain and initialize headless Chromium session"},
                    {"step": 2, "agent": "browser-use-agent", "action": "Navigate interactive elements, resolve SPAs, and extract targeted data"},
                    {"step": 3, "agent": "data-extractor", "action": "Validate extracted fields, deduplicate entries, and compile structured table"},
                    {"step": 4, "agent": "visual-inspector", "action": "Capture visual layout screenshots and audit compliance"}
                ]
            }

            questions = [
                {
                    "id": "navigation_depth",
                    "agent": "browser-use-agent",
                    "question": "What is the target depth and pagination limit for this web extraction?",
                    "why_this_matters": "Prevents runaway crawler loops and ensures compliance with rate limits.",
                    "recommended_option": "Targeted High-Intent Depth: Extract top 25 high-authority results with full contact metadata",
                    "options": [
                        "Targeted High-Intent Depth (Top 25 verified results with contact metadata) (Recommended)",
                        "Broad Surface Scan (Top 100 domain listings with core text only)",
                        "Single-Page Deep Audit (Full DOM extraction and interactive SPA state inspection)"
                    ]
                },
                {
                    "id": "data_output_structure",
                    "agent": "data-extractor",
                    "question": "How should the extracted data be formatted and stored in the project harness?",
                    "why_this_matters": "Ensures downstream agents (email operator, reporting agent) can immediately query the findings.",
                    "recommended_option": "Structured CSV & JSON Dataset attached directly to Project Core Data Harness",
                    "options": [
                        "Structured CSV & JSON Dataset in Project Core Data Harness (Recommended)",
                        "Executive Dossier PDF with visual screenshot evidence",
                        "Raw Markdown summary in Team Chat"
                    ]
                }
            ]
            recommended_directive = (
                f"Execute autonomous web research for «{directive_clean}» using Browser-Use Chromium CDP. "
                f"Extract structured contact records into project harness and generate visual screenshot proof."
            )

        # 4. RESEARCH & MARKET STRATEGY VECTOR
        elif any(k in lower_dir for k in ["seo", "keyword", "market", "competitor", "geo", "ranking"]) or resolved_agent in ("market-seo-geo-researcher", "competitor-intelligence", "geo-targeting-analyst", "seo-auditor"):
            agent_name = "Market & SEO Intelligence Squad"
            department = "Research & Market Strategy"

            proposed_workflow = {
                "title": "Optimal 4-Stage Market Intelligence & Competitor Audit",
                "logic": "Combines search intent mapping, geographical search variance, competitor gap analysis, and high-ROI opportunity ranking.",
                "stages": [
                    {"step": 1, "agent": "seo-auditor", "action": "Audit search landscape and benchmark top ranking competitors"},
                    {"step": 2, "agent": "geo-targeting-analyst", "action": "Map regional search volume and demographic intent signals"},
                    {"step": 3, "agent": "competitor-intelligence", "action": "Profile competitor pricing, positioning, and service gaps"},
                    {"step": 4, "agent": "master-reporting-agent", "action": "Compile Strategic Market Intelligence Brief (PDF + Excel)"}
                ]
            }

            questions = [
                {
                    "id": "market_geographic_scope",
                    "agent": "geo-targeting-analyst",
                    "question": "What geographic boundary should frame this market and competitive analysis?",
                    "why_this_matters": "Search intent and competitor density vary significantly across provinces and regional trading zones.",
                    "recommended_option": "Metropolitan Canadian Hubs: Greater Toronto Area (GTA), Metro Vancouver, and Calgary Metro",
                    "options": [
                        "Metropolitan Canadian Hubs: GTA, Metro Vancouver, Calgary (Recommended)",
                        "National Pan-Canadian Overview across all 10 provinces",
                        "North American Cross-Border Comparative (Canada + US Northern Tier)"
                    ]
                },
                {
                    "id": "competitive_depth",
                    "agent": "competitor-intelligence",
                    "question": "Which competitor dimension should we analyze most aggressively?",
                    "why_this_matters": "Directs specialist agents toward actionable customer conversion gaps.",
                    "recommended_option": "Service & Offer Differentiation: Pricing models, warranty/guarantees, and client review sentiment",
                    "options": [
                        "Service & Offer Differentiation (Pricing models, guarantees, review sentiment) (Recommended)",
                        "Organic Search & Keyword Dominance (Backlinks, domain authority, organic traffic)",
                        "Ad Strategy & Paid Search Footprint (Google Ads, Meta ad campaigns)"
                    ]
                }
            ]
            recommended_directive = (
                f"Conduct market intelligence and competitive audit for «{directive_clean}» focusing on Tier-1 metropolitan hubs. "
                f"Analyze service differentiation and deliver strategic executive brief."
            )

        # 5. DEFAULT / EXECUTIVE COORDINATION VECTOR
        else:
            agent_name = "Lead Coordinator Agent"
            department = "Operations & Orchestration"

            proposed_workflow = {
                "title": "Optimal 4-Stage Sovereign Workforce Execution",
                "logic": "Decomposes directive into specialized stages with deterministic handovers and plain-language executive verification.",
                "stages": [
                    {"step": 1, "agent": "coordinator", "action": f"Deconstruct directive «{directive_clean[:60]}» into atomic subtasks"},
                    {"step": 2, "agent": "market-seo-geo-researcher", "action": "Hydrate domain facts from project core files and connected tools"},
                    {"step": 3, "agent": "software-engineer", "action": "Execute core specialist actions with code check verification"},
                    {"step": 4, "agent": "master-reporting-agent", "action": "Synthesize results into executive PDF and Word brief"}
                ]
            }

            questions = [
                {
                    "id": "milestone_priority",
                    "agent": "coordinator",
                    "question": f"What is the primary milestone priority for executing «{directive_clean[:80]}»?",
                    "why_this_matters": "Allows the Lead Coordinator to assign appropriate agent capability budgets and compute routing tiers.",
                    "recommended_option": "End-to-End Verified Delivery: High-fidelity execution with multi-stage verification and executive brief",
                    "options": [
                        "End-to-End Verified Delivery (Multi-stage verification + executive brief) (Recommended)",
                        "Rapid Feasibility Prototype (Fast agent draft for immediate review)",
                        "Strategic Roadmap Formulation (Task decomposition and architectural blueprint only)"
                    ]
                },
                {
                    "id": "agent_squad_assignment",
                    "agent": "resource-allocator",
                    "question": "Which agent squad should be allocated to own this pipeline execution?",
                    "why_this_matters": "Aligns the specific domain knowledge of the 32 Sovereign Agents with the task scope.",
                    "recommended_option": "Specialized Cross-Functional Squad: Coordinator, Domain Specialist, Verifier, and Reporting Lead",
                    "options": [
                        "Specialized Cross-Functional Squad (Coordinator + Specialist + Verifier + Reporting) (Recommended)",
                        "Single Dedicated Specialist Agent (Direct 1-on-1 execution)",
                        "Full 32-Agent Workforce Swarm with parallel review angles"
                    ]
                },
                {
                    "id": "reporting_deliverables",
                    "agent": "master-reporting-agent",
                    "question": "What executive deliverables should be generated upon completion?",
                    "why_this_matters": "Determines the exporter formats compiled into the Task Delivery Package.",
                    "recommended_option": "Consolidated Executive Delivery Package: Downloadable PDF report and Word brief DOCX",
                    "options": [
                        "Consolidated Executive Delivery Package: Downloadable PDF and Word DOCX (Recommended)",
                        "Executive PDF Summary only",
                        "Chat ledger with interactive DAG telemetry"
                    ]
                }
            ]
            recommended_directive = (
                f"Execute directive «{directive_clean}» across cross-functional sovereign pipeline stages with "
                f"deterministic verification and consolidated Task Deliverables Package (PDF + DOCX)."
            )

        # Build clean formatted Markdown presentation for chat
        md_lines = [
            f"🎯 **GrillMe Alignment Interview: Operationalizing Best Logic & Workflow**",
            f"**Assigned Lead:** `{agent_name}` • **Department:** `{department}`",
            "",
            f"### 1. Proposed Optimal Workflow & Architecture",
            f"**{proposed_workflow['title']}**",
            f"*{proposed_workflow['logic']}*",
            ""
        ]
        for s in proposed_workflow["stages"]:
            md_lines.append(f"  {s['step']}. **@{s['agent']}** ➔ {s['action']}")

        md_lines.extend([
            "",
            f"### 2. Tailored Operational Clarification Sequence",
            f"To achieve the highest precision and avoid unverified assumptions, please confirm or adjust the parameters below:"
        ])

        for idx, q in enumerate(questions, 1):
            md_lines.extend([
                "",
                f"**Question {idx}: {q['question']}**",
                f"💡 *Why this matters:* {q['why_this_matters']}",
                f"  ✓ **{q['recommended_option']}** *(Recommended)*"
            ])
            for alt in q["options"]:
                if "(Recommended)" not in alt:
                    md_lines.append(f"  • {alt}")

        md_lines.extend([
            "",
            "---",
            "### 3. Immediate Action Pathways",
            "👉 **Option A (Fastest & Recommended):** Click **[⚡ Proceed with Recommended Workflow]** below or reply `Proceed` to immediately execute this optimal pipeline.",
            "👉 **Option B (Custom Tuning):** Click any option pill below or reply in chat with your custom parameters."
        ])

        formatted_markdown = "\n".join(md_lines)

        return {
            "status": "ready",
            "agent_id": resolved_agent,
            "agent_name": agent_name,
            "department": department,
            "proposed_workflow": proposed_workflow,
            "questions": questions,
            "recommended_directive": recommended_directive,
            "formatted_markdown": formatted_markdown,
            "is_grillme": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
