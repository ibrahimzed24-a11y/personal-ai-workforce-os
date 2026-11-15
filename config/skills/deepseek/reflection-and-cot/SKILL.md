---
name: deepseek-reflection-and-cot
description: DeepSeek R1/V3 Test-Time Compute & Reflection Harness. Enforces explicit reasoning tokens, chain-of-thought decomposition, step verification, and reflection prior to tool dispatch.
version: "1.0.0"
author: "DeepSeek AI & Workforce OS Core"
slash_command: "/deepseek-reflect"
department_affinity: ["Operations & Orchestration", "Engineering & Technology", "System Architecture & Integration"]
tools_required: ["local_worker", "python_repl", "syntax_validator"]
verification_gate: "Mandatory CoT reflection tokens and verification check before execution"
---

# DeepSeek R1/V3 Test-Time Compute & Reflection Harness

## Overview
This skill operationalizes DeepSeek's advanced reasoning methodology inside the AI Workforce OS 5-Stage Agent Loop. It scales inference-time compute by forcing agents to enter an explicit `<think>` reasoning phase, explore alternative hypothesis paths, evaluate constraints, verify edge cases, and self-reflect before any action (`Act`) is committed.

## Core Principles
1. **Explicit Monologue:** All non-trivial decisions must be preceded by structured thinking enclosed in `<think>...</think>` tokens or a formal Stage 2 reasoning trace.
2. **Path Exploration:** Evaluate at least two architectural or implementation hypotheses before selecting the execution path.
3. **Constraint Auditing:** Actively verify project boundaries, POSIX permissions, and safety policies against the proposed action.
4. **Pre-Execution Proof:** If generating code or executing bash commands, simulate expected side effects and failure modes mentally before execution.

## The DeepSeek Reasoning Loop
```
[Intake] -> <think> (Problem Decomposition -> Hypothesis Generation -> Counter-Factual Testing -> Verification Criteria) </think> -> [Verified Action]
```

## Step-by-Step Procedure
1. **Deconstruct the Objective:** Extract explicit inputs, implicit constraints, and acceptance criteria.
2. **Formulate Hypotheses:** Document 2-3 possible solution paths and rank them by simplicity, robustness, and preservation of existing code.
3. **Simulate Execution:** For the chosen path, predict inputs, outputs, side-effects, and file changes.
4. **Verify Preconditions:** Confirm that dependencies, environment variables, and directories exist.
5. **Commit & Transition:** Emit the verified action payload into Stage 3 (`Act`).
