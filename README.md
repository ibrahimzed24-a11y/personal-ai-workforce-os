# Personal AI Workforce OS

**Version:** 3.1.0 Sovereign Edition  
**Operating Environment:** macOS Workstation (`127.0.0.1:8765`) + Vercel Cloud Serverless + Supabase  
**Control Center Interface:** `https://personal-ai-workforce-os-pi.vercel.app` & `http://127.0.0.1:8765`  
**License:** Private & Proprietary (Owner-Controlled)  

---

## 1. What is the AI Workforce OS?

The **Personal AI Workforce OS** is your private operating system coordinating a sovereign team of 32 specialized autonomous AI agents across 8 departments.

- **Orchestration:** A **Lead Coordinator** decomposes goals into directed execution pipelines, guided by the **GrillMe Protocol** before execution.
- **Specialized Squads:** 32 agents covering **Operations**, **Market & SEO Research**, **Growth & Communications**, **Email Operations & Outreach**, **Software Engineering**, **Browser Automation**, **Executive Reporting**, and **System Architecture**.
- **Evidence-Driven Execution:** Step receipts, explicit verifications, and deterministic deliverable packages (PDF + Word DOCX).
- **Hybrid Sovereign Engine:** Runs with AntiGravity CLI (`agy`) and local models on your Mac, or securely via authenticated cloud providers with bank-grade AES-256 Vault encryption.

---

## 2. Quick Start: How to Run the OS

### Starting the System
Open your Mac Terminal, navigate to the project directory, and run:
```bash
cd ~/AI-Workforce
./start_os.sh
```
The OS daemon will start in the background. Open your browser and visit:
👉 **[http://127.0.0.1:8765](http://127.0.0.1:8765)**

### Stopping the System
When you are done working, stop the background process cleanly:
```bash
cd ~/AI-Workforce
./stop_os.sh
```

---

## 3. How to Run the Automated Test Suite

To verify that all 32 agents, the database, security vault, and model manager are healthy:

```bash
cd ~/AI-Workforce

# 1. Verify all 32 agents and their instruction files (8 suites)
PYTHONPATH=. ~/.local/bin/uv run python core/tests/test_three_file_architecture.py

# 2. Verify task orchestration, database, and vault security (5 suites)
PYTHONPATH=. ~/.local/bin/uv run python core/tests/test_system.py

# 3. Verify independent security, rollbacks, and backup integrity
PYTHONPATH=. ~/.local/bin/uv run python core/tests/run_audit_verification.py

# 4. Verify the web dashboard UI using headless Chromium
PYTHONPATH=. ~/.local/bin/uv run python core/tests/test_browser_ui.py
```

---

## 4. Main System Architecture

```text
~/AI-Workforce/
├── README.md                 <- This operations guide
├── AGENTS.md                 <- Universal developer instructions for AI agents
├── .gitignore                <- Exclusions for secrets, caches, and database
├── start_os.sh / stop_os.sh  <- Local process daemons
├── pyproject.toml / uv.lock  <- Python dependencies managed by uv
│
├── core/                     <- Operating System Engine
│   ├── app.py                <- FastAPI server and web dashboard routes
│   ├── orchestrator.py       <- Autonomous planning and task execution
│   ├── model_manager.py      <- Central LLM provider routing and privacy engine
│   ├── agent_context.py      <- Agent instruction and durable memory loader
│   ├── database.py           <- SQLite WAL database layer
│   ├── security/             <- Fernet AES-128 encrypted secrets vault
│   ├── adapters/             <- Local (Ollama), Cloud (OpenAI/Gemini/Claude), and Mock adapters
│   ├── ui/                   <- Web Control Center interface (HTML/CSS/JS)
│   └── tests/                <- Verification test suites
│
├── config/agents/            <- The 32 Agent Blueprints (AGENT.md, MEMORY.md, SKILL.md)
├── documentation/            <- Comprehensive architectural guides and policies
├── logs/                     <- System logs (os.log) and final task deliverables
└── backups/                  <- Automated checkpoints and project ZIP archives
```

---

## 5. Where Agent Files Are Stored

All 32 agents live under `config/agents/<agent-id>/`. Every agent uses the **Universal Three-File Standard**:
1. `AGENT.md`: The agent's permanent identity, boundaries, exclusions, approval requirements, and startup sequence.
2. `MEMORY.md`: Durable operational lessons and feedback learned from past jobs.
3. `skills/<job-name>/SKILL.md`: The agent's 10-step executable procedure, YAML frontmatter, and deliverable schema.

To inspect or customize an agent, open its folder in `config/agents/`.

---

## 6. How to Configure AI Models

Your OS includes a central **Model Manager** accessible via the web dashboard at `http://127.0.0.1:8765` under the **LLM & Models** tab:

1. **Offline Simulation (Default):** The OS starts in safe offline simulation mode (`mock-deterministic-v1`). No API keys or internet connection are required.
2. **Local AI (Free & 100% Private):** Install [Ollama](https://ollama.com), run `ollama run llama3.2:latest`, and click **Test Connection** in the dashboard. The OS will automatically connect to your local model with zero cloud costs.
3. **Cloud APIs (OpenAI, Gemini, Claude):** Click **Set API Key** on any cloud provider card. Your key is immediately encrypted using AES-128 encryption with your local vault master key (`~/.ai_workforce_vault.key`). Raw keys are never stored in plain text.
4. **Local-First Privacy Guarantee:** Tasks marked `local_only` will **never** be routed to cloud providers.

For full details, read [documentation/LLM_AND_MODEL_MANAGEMENT_GUIDE.md](file:///Users/ibrahimzid/AI-Workforce/documentation/LLM_AND_MODEL_MANAGEMENT_GUIDE.md).

---

## 7. Where to Find Documentation

- **System Architecture & Design:** `documentation/`
- **Model Routing & Privacy Policy:** `documentation/MODEL_ROUTING_POLICY.md`
- **Shared Capability Library:** `documentation/AGENT_CAPABILITY_CATALOG.md`
- **System Skills Catalog:** `documentation/knowledge/SKILLS_INDEX.md`
- **Verified Tool Inventory:** `documentation/knowledge/AVAILABLE_CAPABILITIES.md`
- **Future VPS Deployment Blueprint:** `documentation/VPS_HYBRID_DEPLOYMENT_BLUEPRINT.md`

---

## 8. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Port 8765 already in use** | A previous OS instance is still running | Run `./stop_os.sh`, wait 3 seconds, then run `./start_os.sh`. |
| **Database locked error** | SQLite WAL file busy | The database automatically recovers on restart. Run `./stop_os.sh && ./start_os.sh`. |
| **Vault key missing** | `~/.ai_workforce_vault.key` not found | The vault generates a new key automatically on startup with `0600` permissions. |
| **Tests fail with import error** | `PYTHONPATH` not set | Always run tests with `PYTHONPATH=. ~/.local/bin/uv run python <test_file>`. |
