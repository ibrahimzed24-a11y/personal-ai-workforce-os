import os
import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = WORKSPACE_ROOT / "config" / "agents"

DEPARTMENTS = {
    "coordinator": "Operations & Orchestration",
    "task-decomposer": "Operations & Orchestration",
    "resource-allocator": "Operations & Orchestration",
    "progress-monitor": "Operations & Orchestration",
    
    "market-seo-geo-researcher": "Research & Market Strategy",
    "competitor-intelligence": "Research & Market Strategy",
    "geo-targeting-analyst": "Research & Market Strategy",
    "seo-auditor": "Research & Market Strategy",
    
    "marketing-agent": "Growth & Communications",
    "campaign-planner": "Growth & Communications",
    "content-strategist": "Growth & Communications",
    "brand-compliance": "Growth & Communications",
    
    "software-engineer": "Engineering & Technology",
    "frontend-specialist": "Engineering & Technology",
    "backend-specialist": "Engineering & Technology",
    "qa-test-engineer": "Engineering & Technology",
    
    "browser-use-agent": "Automation & Data Acquisition",
    "web-navigator": "Automation & Data Acquisition",
    "data-extractor": "Automation & Data Acquisition",
    "visual-inspector": "Automation & Data Acquisition",
    
    "deployment-agent": "Infrastructure & Operations",
    "environment-provisioner": "Infrastructure & Operations",
    "package-runtime-installer": "Infrastructure & Operations",
    "release-verifier": "Infrastructure & Operations",
    
    "master-reporting-agent": "Executive & Audit",
    "executive-summarizer": "Executive & Audit",
    "audit-trail-compiler": "Executive & Audit",
    "retrospective-analyst": "Executive & Audit",
    
    "system-integrator-update-agent": "System Architecture & Integration",
    "asset-classifier-auditor": "System Architecture & Integration",
    "capability-knowledge-synchronizer": "System Architecture & Integration",
    "service-manager": "System Architecture & Integration"
}

DEPARTMENT_HARNESSES = {
    "Operations & Orchestration": [
        "DeepSeek R1/V3 CoT Reasoning & Reflection Harness (`/deepseek-reflect`)",
        "ECC Team Agent Orchestration Protocol (`/team-orchestration`)",
        "Addy Osmani Planning & Task Breakdown (`/planning-and-task-breakdown`)",
        "Superpowers Subagent Delegation & Worktree Isolation (`/subagent-delegation`)"
    ],
    "Research & Market Strategy": [
        "DeepSeek R1/V3 CoT Reasoning & Reflection Harness (`/deepseek-reflect`)",
        "Browser-Use Direct CDP Browser Automation (`/browser-use`)",
        "ECC Strategic Context Compactor & Memory Pruning (`/strategic-compact`)"
    ],
    "Growth & Communications": [
        "ECC AgentShield Security & Brand Compliance Review (`/security-review`)",
        "Addy Osmani Spec-Driven Development (`/spec-driven-development`)",
        "DeepSeek R1/V3 CoT Reasoning & Reflection Harness (`/deepseek-reflect`)"
    ],
    "Engineering & Technology": [
        "Superpowers Test-Driven Development (TDD) Iron Law (`/test-driven-development`)",
        "Superpowers Systematic Debugging Protocol (`/systematic-debugging`)",
        "Addy Osmani Incremental Implementation & Clean Refactoring (`/incremental-implementation`)",
        "DeepSeek Automated Self-Repair & Syntax Evaluator (`/deepseek-repair`)",
        "ECC AgentShield Code Security & Secret Exposure Review (`/security-review`)"
    ],
    "Automation & Data Acquisition": [
        "Browser-Use Direct CDP Browser Agent Controller (`/browser-use`)",
        "Browser-Use Remote & QA Assertion Engine (`/qa-browser-test`)",
        "Superpowers Systematic Debugging Protocol (`/systematic-debugging`)",
        "DeepSeek R1/V3 CoT Reflection Prior to Web Action"
    ],
    "Infrastructure & Operations": [
        "Addy Osmani Shipping & Launch Gatekeeper (`/shipping-and-launch`)",
        "Superpowers Verification Before Completion (`/verification-before-completion`)",
        "ECC AgentShield Infrastructure Security & Secret Auditing (`/security-review`)"
    ],
    "Executive & Audit": [
        "Superpowers Verification Before Completion Gate (`/verification-before-completion`)",
        "ECC Strategic Context Compactor & Audit Pruning (`/strategic-compact`)",
        "DeepSeek Benchmark Evaluation & Quality Synthesis Harness (`/deepseek-eval`)"
    ],
    "System Architecture & Integration": [
        "DeepSeek R1/V3 CoT Reasoning & Reflection Harness (`/deepseek-reflect`)",
        "ECC Universal Multi-Harness Bridge & Capability Indexer",
        "Addy Osmani Architecture Decision Records (ADRs) & Spec Lifecycle"
    ]
}

def update_agent_md(agent_dir: Path, agent_id: str, dept: str):
    agent_file = agent_dir / "AGENT.md"
    if not agent_file.exists():
        agent_file = agent_dir / "CLAUDE.md"
    content = agent_file.read_text(encoding="utf-8")
    
    harnesses = DEPARTMENT_HARNESSES.get(dept, [])
    harness_section = "\n\n## M. Sovereign Harnesses & Permanent Skills Authorized\n"
    harness_section += f"This agent is authorized to invoke and enforce the following permanent OS harnesses within **{dept}**:\n"
    for h in harnesses:
        harness_section += f"- {h}\n"
    harness_section += "- **DeepSeek CoT Protocol:** Enter explicit `<think>...</think>` reflection prior to committing state changes.\n"
    harness_section += "- **Superpowers Verification Gate:** No step is marked complete without deterministic evidence.\n"

    if "## M. Sovereign Harnesses & Permanent Skills Authorized" in content:
        content = re.sub(r"## M\. Sovereign Harnesses & Permanent Skills Authorized.*", harness_section.strip(), content, flags=re.DOTALL)
    else:
        content = content.strip() + harness_section

    agent_file.write_text(content.strip() + "\n", encoding="utf-8")

def update_memory_md(agent_dir: Path, agent_id: str, dept: str):
    mem_file = agent_dir / "MEMORY.md"
    if not mem_file.exists() or mem_file.stat().st_size < 50:
        base_mem = f"""# Durable Feedback Memory: {agent_id}

## Department Context
- **Department:** {dept}
- **Architectural Standard:** Sovereign 3-File Architecture (AGENT.md, SKILL.md, MEMORY.md)
- **Active Harnesses:** DeepSeek CoT, Superpowers TDD, ECC AgentShield, Addy Osmani Lifecycle, Browser-Use CDP

## Persistent Lessons & Error Avoidance
1. **Deterministic Verification Gate:** Never emit a completion status or handover payload without concrete verification proof (file checks, exit codes, non-empty outputs).
2. **Strict Project Isolation:** File operations must resolve strictly within the active `./projects/<project_slug>/` directory. Cross-project writes are prohibited.
3. **DeepSeek Reflection:** Execute structured reflection in Stage 2 (`Think`) before executing actions in Stage 3 (`Act`).
4. **Secret Protection:** Never disclose or echo unmasked credentials from the POSIX 0600 Fernet vault.
"""
        mem_file.write_text(base_mem.strip() + "\n", encoding="utf-8")
    else:
        # Check if active harnesses are referenced
        text = mem_file.read_text(encoding="utf-8")
        if "Active Harnesses:" not in text:
            addition = f"\n\n## Integrated Permanent Harnesses\n- Department: {dept}\n- Active: DeepSeek CoT, Superpowers, ECC AgentShield, Addy Osmani, Browser-Use CDP\n"
            mem_file.write_text(text.strip() + addition, encoding="utf-8")

def run():
    updated = 0
    for agent_id, dept in DEPARTMENTS.items():
        agent_dir = AGENTS_DIR / agent_id
        if agent_dir.exists():
            update_agent_md(agent_dir, agent_id, dept)
            update_memory_md(agent_dir, agent_id, dept)
            updated += 1
            print(f"Updated {agent_id} ({dept})")
    print(f"\nSuccessfully upgraded {updated} / 32 agents across all 8 departments!")

if __name__ == "__main__":
    run()
