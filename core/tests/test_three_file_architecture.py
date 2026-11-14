import asyncio
import os
import shutil
from pathlib import Path
from core.agent_context import AgentContextLoader

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = WORKSPACE_ROOT / "config" / "agents"

async def run_full_validation():
    print("=" * 65)
    print("🚀 AI WORKFORCE OS: 32-AGENT UNIVERSAL THREE-FILE VALIDATION")
    print("=" * 65)
    
    loader = AgentContextLoader(AGENTS_DIR)
    agent_records = loader.list_all_agents()
    
    # -------------------------------------------------------------
    # SUITE 1: Universal Directory & File Existence Validation
    # -------------------------------------------------------------
    print("\n[SUITE 1] Auditing all 32 agent directories for AGENT.md, MEMORY.md, and skills/*/SKILL.md...")
    assert len(agent_records) == 32, f"Expected 32 agents, found {len(agent_records)}"
    
    for a in agent_records:
        agent_id = a["agent_id"]
        val = loader.validate_agent_architecture(agent_id)
        assert val["valid"], f"Universal validation failed for {agent_id}: {val}"
        
        # Verify MEMORY.md exact initial sentence
        mem_text = loader.load_agent_memory(agent_id).strip()
        assert mem_text.startswith("Only save feedback that applies to future jobs, not one-off edits."), \
            f"MEMORY.md corrupt for {agent_id}"
            
        # Verify AGENT.md required sections and mandatory prompts
        agent_text = loader.load_agent_instructions(agent_id)
        assert "Read MEMORY.md before every job" in agent_text, f"Missing startup prompt in {agent_id}/AGENT.md"
        assert "Use the skill for this job." in agent_text, f"Missing startup prompt in {agent_id}/AGENT.md"
        assert "## A. Agent Identity" in agent_text, f"Missing section A in {agent_id}/AGENT.md"
        assert "## H. Standard Startup Sequence" in agent_text, f"Missing section H in {agent_id}/AGENT.md"
        
        # Verify skills directory path is clean and universal (not .claude)
        skill_res = loader.resolve_agent_skill(agent_id)
        assert "skills/" in skill_res["path"] and ".claude" not in skill_res["path"], \
            f"Skill path contains legacy .claude: {skill_res['path']}"
        
    print(f"✓ All 32 agents verified with valid AGENT.md, MEMORY.md, and universal skills/*/SKILL.md.")

    # -------------------------------------------------------------
    # SUITE 2: Slash Command & Capability Resolution
    # -------------------------------------------------------------
    print("\n[SUITE 2] Testing skill slash command resolution and namespace collision...")
    seen_commands = set()
    for a in agent_records:
        cmd = a["slash_command"]
        assert cmd not in seen_commands, f"Duplicate slash command detected: {cmd}"
        seen_commands.add(cmd)
        
        resolved = loader.resolve_slash_command(cmd)
        assert resolved is not None, f"Slash command {cmd} failed to resolve"
        assert resolved["agent_id"] == a["agent_id"], f"Slash command mapped to wrong agent: {resolved}"
        assert Path(WORKSPACE_ROOT / resolved["skill_path"]).exists(), f"Skill file does not exist: {resolved['skill_path']}"

    assert len(seen_commands) == 32
    print(f"✓ All 32 slash commands resolved 1:1 with zero namespace collisions.")

    # -------------------------------------------------------------
    # SUITE 3: Runtime Context Loader & 9-Step Startup Sequence (Core)
    # -------------------------------------------------------------
    print("\n[SUITE 3] Testing OS runtime context builder across 8 Core Agents...")
    core_agents = [
        "coordinator", "market-seo-geo-researcher", "marketing-agent", "software-engineer",
        "browser-use-agent", "deployment-agent", "master-reporting-agent", "system-integrator-update-agent"
    ]
    for core_id in core_agents:
        ctx = loader.build_runtime_context(core_id, {"task_title": f"Test Task for {core_id}"})
        assert ctx["agent_id"] == core_id
        assert len(ctx["startup_checklist"]) == 9
        assert ctx["startup_checklist"][0]["status"] == "VERIFIED_LOADED" # AGENT.md
        assert ctx["startup_checklist"][1]["status"] == "VERIFIED_LOADED" # MEMORY.md
        assert ctx["startup_checklist"][3]["status"] == "VERIFIED_LOADED" # Active Skill
        assert core_id in ctx["composite_system_prompt"]
        print(f"  • Core Agent '{core_id}' runtime context verified ({ctx['active_skill']['slash_command']})")
    print("✓ All 8 core agents successfully built runtime contexts.")

    # -------------------------------------------------------------
    # SUITE 4: Runtime Context Loader across 24 Specialists
    # -------------------------------------------------------------
    print("\n[SUITE 4] Testing OS runtime context builder across 24 Specialists...")
    specialists = [
        "task-decomposer", "resource-allocator", "progress-monitor",
        "seo-auditor", "geo-targeting-analyst", "competitor-intelligence",
        "content-strategist", "campaign-planner", "brand-compliance",
        "frontend-specialist", "backend-specialist", "qa-test-engineer",
        "web-navigator", "data-extractor", "visual-inspector",
        "environment-provisioner", "service-manager", "release-verifier",
        "executive-summarizer", "audit-trail-compiler", "retrospective-analyst",
        "asset-classifier-auditor", "package-runtime-installer", "capability-knowledge-synchronizer"
    ]
    assert len(specialists) == 24
    for spec_id in specialists:
        ctx = loader.build_runtime_context(spec_id, {"task_title": f"Specialist Task for {spec_id}"})
        assert ctx["agent_id"] == spec_id
        assert len(ctx["startup_checklist"]) == 9
        assert ctx["active_skill"]["slash_command"].startswith("/")
        print(f"  • Specialist '{spec_id}' loaded with skill {ctx['active_skill']['slash_command']}")
    print(f"✓ All 24 specialist subagents successfully built runtime contexts.")

    # -------------------------------------------------------------
    # SUITE 5: Memory Isolation & Privacy Verification
    # -------------------------------------------------------------
    print("\n[SUITE 5] Verifying strict agent memory isolation...")
    agent_a = "frontend-specialist"
    agent_b = "backend-specialist"
    
    unique_lesson = f"Universal responsive standard guideline {os.urandom(4).hex()}"
    res = await loader.propose_memory_update(agent_a, unique_lesson, author="owner", auto_apply=True)
    assert res["status"] == "approved"
    
    mem_a = loader.load_agent_memory(agent_a)
    mem_b = loader.load_agent_memory(agent_b)
    
    assert unique_lesson in mem_a, "Lesson not found in target agent memory"
    assert unique_lesson not in mem_b, "CRITICAL: Agent memory leak! Agent B loaded Agent A's memory."
    
    # Cleanup memory file back to clean state
    clean_base = "Only save feedback that applies to future jobs, not one-off edits.\n"
    with open(AGENTS_DIR / agent_a / "MEMORY.md", "w", encoding="utf-8") as f:
        f.write(clean_base)
    print("✓ Agent memory isolation strictly verified (zero cross-agent leakage).")

    # -------------------------------------------------------------
    # SUITE 6: Durable Memory Rules Enforcement
    # -------------------------------------------------------------
    print("\n[SUITE 6] Testing durable memory update guardrails...")
    
    # Reject sensitive credential
    secret_test = await loader.propose_memory_update("seo-auditor", "Use token=ghp_secretTokenValue12345")
    assert secret_test["status"] == "rejected"
    assert "Security violation" in secret_test["reason"]
    print("✓ Negative Security Test: Secret in memory feedback rejected.")

    # Reject one-off edit
    ephemeral_test = await loader.propose_memory_update("seo-auditor", "For this task only, ignore h2 tags")
    assert ephemeral_test["status"] == "rejected"
    assert "Memory rule violation" in ephemeral_test["reason"]
    print("✓ Negative Policy Test: One-off edit rejected.")

    # Accept durable lesson
    durable_test = await loader.propose_memory_update(
        "seo-auditor",
        "Always evaluate OpenGraph image aspect ratios during audit steps.",
        author="owner",
        auto_apply=True
    )
    assert durable_test["status"] == "approved"
    updated_mem = loader.load_agent_memory("seo-auditor")
    assert "OpenGraph image aspect ratios" in updated_mem
    print("✓ Positive Test: Durable feedback approved and appended.")

    # Reset memory
    with open(AGENTS_DIR / "seo-auditor" / "MEMORY.md", "w", encoding="utf-8") as f:
        f.write(clean_base)

    # -------------------------------------------------------------
    # SUITE 7: Error Boundary & Missing Resource Handling
    # -------------------------------------------------------------
    print("\n[SUITE 7] Testing error boundary and missing resource handling...")
    try:
        loader.load_agent_instructions("non-existent-agent-xyz")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass
    print("✓ Graceful error handling for missing agent.")

    bad_cmd = loader.resolve_slash_command("/unknown-slash-command")
    assert bad_cmd is None
    print("✓ Graceful resolution failure for unknown slash command.")

    # -------------------------------------------------------------
    # SUITE 8: Live Orchestrator Step Execution with Universal Three-File Context
    # -------------------------------------------------------------
    print("\n[SUITE 8] Testing live Orchestrator step execution with Universal Three-File Context injection...")
    from core.orchestrator import Orchestrator
    orch = Orchestrator()
    sample_task = {
        "id": "task_universal_eval",
        "title": "Evaluate Universal Three-File Architecture",
        "priority": "high",
        "input_context": {}
    }
    sample_step = {
        "id": "step_1",
        "step_number": 1,
        "title": "Execute SEO Audit Task",
        "description": "Perform crawlability assessment under /seo-audit skill",
        "assigned_agent": "market-seo-geo-researcher",
        "specialist_id": "seo-auditor",
        "action_type": "research",
        "parameters": {}
    }
    res = await orch._execute_step(sample_task, sample_step)
    assert res is not None
    assert res.get("skill_invoked") == "/seo-audit"
    print(f"✓ Orchestrator successfully executed step with active skill: {res.get('skill_invoked')}")

    print("\n" + "=" * 65)
    print("🎉 ALL 8 TEST SUITES PASSED! 32/32 AGENTS 100% VERIFIED (UNIVERSAL STANDARD)!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_full_validation())
