---
name: deepseek-self-repair-and-eval
description: DeepSeek Automated Self-Repair, Syntax Evaluation, and Regression Testing Harness. Diagnoses failures, parses tracebacks, and applies minimal deterministic patches.
version: "1.0.0"
author: "DeepSeek AI & Workforce OS Core"
slash_command: "/deepseek-repair"
department_affinity: ["Engineering & Technology", "Infrastructure & Operations", "Executive & Audit"]
tools_required: ["pytest", "ast_parser", "linters", "git_diff"]
verification_gate: "Zero syntax errors, 100% test pass rate on modified modules"
---

# DeepSeek Automated Self-Repair & Evaluation Harness

## Overview
Automated diagnostic and self-healing procedure inspired by DeepSeek's continuous evaluation harness. When an agent action fails, encounters a syntax violation, or fails a deterministic test, this skill takes over to isolate the fault, generate a focused repair hypothesis, and apply atomic corrections without side effects.

## The Iron Rule of Self-Repair
```
NEVER GUESS A FIX. ISOLATE THE ROOT CAUSE WITH TRACE EVIDENCE BEFORE EDITING A SINGLE BYTE.
```

## Self-Healing Protocol
1. **Traceback Analysis:** Capture exit code, stdout, stderr, and line numbers of the exact failure point.
2. **AST / Syntax Check:** Run a static verification on modified files before executing them.
3. **Hypothesis Formulation:** Document the exact cause (e.g. `NameError: name 're' is not defined` -> missing import).
4. **Minimal Patch:** Apply the smallest contiguous edit that resolves the failure without altering surrounding behavior.
5. **Regression Verification:** Re-run the failing test suite and all dependent unit tests. Maximum 2 self-healing attempts before human escalation.
