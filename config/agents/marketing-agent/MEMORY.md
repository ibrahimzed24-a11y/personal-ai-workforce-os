Only save feedback that applies to future jobs, not one-off edits.

# Agent Durable Memory Policy & Guidelines: Marketing Agent (`marketing-agent`)

## 1. Universal Memory Policy
This file contains permanent operational lessons, owner preferences, and durable domain constraints learned from feedback across tasks.

### What Belongs in Memory:
- Verified owner preferences and stylistic requirements applicable to all future jobs.
- Durable operational lessons learned from edge-case failures or post-mortem retrospectives.
- Project domain facts verified by tests or explicit owner confirmation (`[FACT: VERIFIED]`).
- Documented assumptions requiring ongoing validation (`[ASSUMPTION: UNVERIFIED]`).

### What Does NOT Belong in Memory:
- One-off task instructions, transient edits, or single-use parameter tweaks.
- Passwords, API keys, tokens, session IDs, or private credentials (STRICTLY PROHIBITED).
- Unverified speculations or fabricated task outcomes.
- Large code blocks or raw API response payloads (store in `logs/` instead).

---

## 2. Memory Guardrails
1. **Deduplication:** Always check existing memory before adding an entry. Never record duplicate lessons.
2. **Zero-Secret Guarantee:** Any proposed memory update containing credentials or API keys will be rejected by the OS runtime.
3. **Controlled Updates:** Memory proposals are filtered by the `AgentContextLoader` guardrails before persistence.

## Integrated Permanent Harnesses
- Department: Growth & Communications
- Active: DeepSeek CoT, Superpowers, ECC AgentShield, Addy Osmani, Browser-Use CDP
