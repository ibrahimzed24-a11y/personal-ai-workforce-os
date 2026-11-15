# Owner Guide: LLM and Model Management in AI Workforce OS

**Target Audience:** Non-technical OS Owner  
**System Environment:** MacBook Pro 15-inch (Intel Core i7, 16 GB RAM, macOS Sequoia)  
**Last Updated:** 2026-11-15  

---

## 1. What is an LLM and How Does It Fit Into Your OS?

A **Large Language Model (LLM)** is the "thinking engine" that powers artificial intelligence. In your AI Workforce OS:
- The **OS software** is the office building, the filing cabinets (database), and the security locks (vault).
- The **Agents** are the job descriptions and team roles (e.g., SEO Researcher, Developer, Coordinator).
- The **LLM** is the actual brainpower the agent rents or runs to understand instructions, draft reports, plan tasks, and solve problems.

---

## 2. Important Distinction: Antigravity vs. Your OS Model

It is very common to confuse the application you are talking to right now with the OS you own:
- **Google Antigravity:** The development studio where you are reading this. Antigravity runs its own cloud model to assist you with coding and system design.
- **Your AI Workforce OS:** Your private, independent software located in `~/AI-Workforce/`. 

> [!IMPORTANT]
> The AI Workforce OS does **not** automatically use Antigravity's model for its internal tasks. The OS has its own independent model manager so that your private system is never locked into one company, one API, or one pricing plan.

---

## 3. What Model Does Your OS Currently Use?

Right now, your OS is configured to run on an **offline deterministic reasoning engine (simulation)**:
- **Status:** `MOCKED_OR_SIMULATED`
- **Why:** To protect you from unexpected API bills, internet dependency, and accidental data exposure before you explicitly choose which models to connect.
- **What this means:** When an agent runs a task, the OS generates structured mock plans and deliverables to verify system plumbing and workflows offline.
- **Next Step:** You can easily connect a free local model (via Ollama) or a cloud provider (OpenAI, Gemini, Anthropic) whenever you are ready.

---

## 4. Local Models vs. Cloud Models

| Feature | Local Models (e.g. Ollama) | Cloud Models (e.g. Gemini, OpenAI, Claude) |
| :--- | :--- | :--- |
| **Where it runs** | Directly on your MacBook Pro | On the provider's server farms |
| **Privacy** | 100% Private (No data ever leaves your laptop) | Data is sent over the internet to the provider |
| **Cost** | Completely Free | Pay per token (usually fractions of a cent) |
| **Internet Required** | No (works completely offline on a plane) | Yes |
| **Hardware Strain** | Uses your Mac's RAM and CPU | Uses zero Mac CPU; runs instantly on the cloud |
| **Reasoning Power** | Good for summaries, simple coding, extraction | World-class for complex architecture and deep logic |

---

## 5. Your Mac Hardware Constraints (16 GB RAM Intel Mac)

Your MacBook Pro has **16 GB of RAM** and an **Intel Core i7 CPU**.
- Modern AI models require computer memory to run.
- **Recommended Local Models:** Small, highly optimized models between **2 Billion and 7 Billion parameters**:
  - `llama3.2:3b` (~2.0 GB RAM) — Super fast, great for simple text and summaries.
  - `qwen2.5-coder:7b` (~4.8 GB RAM) — Excellent for Python coding and local scripts.
- **Models to Avoid Locally:**
  - Do not install models larger than 14B or 70B parameters locally. They will overload your 16 GB RAM and make your Mac unresponsive.
  - For very heavy architectural planning or complex reasoning, use a cloud API (like Claude 3.5 Sonnet or Gemini 1.5 Pro).

---

## 6. How to Connect a Free Local Model (Ollama)

1. Open your browser and download Ollama from [https://ollama.com/download](https://ollama.com/download).
2. Install Ollama by dragging it into your `Applications` folder and start it.
3. Open your Mac Terminal and run:
   ```bash
   ollama run llama3.2:latest
   ```
4. Once downloaded, open your AI Workforce OS dashboard at `http://127.0.0.1:8765`.
5. Click the **LLM & Models** tab in the sidebar.
6. Click **Test Connection** on the "Local Ollama Inference" card. The OS will automatically discover your installed local model and mark it as `Healthy`!
7. Click **Make Default** next to `Llama 3.2 3B (Local)`. Your OS is now thinking 100% locally with zero cloud costs!

---

## 7. How to Connect a Cloud Provider (OpenAI, Gemini, Anthropic)

If you have an API key from Google AI Studio, OpenAI, or Anthropic:

1. Open the OS dashboard at `http://127.0.0.1:8765`.
2. Navigate to the **LLM & Models** tab.
3. Find the provider card (e.g., "Google Gemini API" or "OpenAI Cloud API") and click **Set API Key**.
4. Paste your API key into the secure dialog box and click **Encrypt & Save to Vault**.
   - Your key is immediately encrypted using AES-128-CBC encryption with your local vault master key (`~/.ai_workforce_vault.key`).
   - The plain text key is never saved in the database, never written to disk, and never displayed on screen.
5. Click **Test Connection**. Once verified, you can assign it to complex tasks or set it as default.

---

## 8. How Model Routing Protects Your Privacy & Wallet

Your OS has an automatic **Smart Router** ([MODEL_ROUTING_POLICY.md](file:///Users/ibrahimzid/AI-Workforce/documentation/MODEL_ROUTING_POLICY.md)):
1. **Local-Only Boundary:** If a task involves sensitive personal notes, local passwords, or confidential files, the router strictly locks the task to local models. It will **never** silently upload sensitive data to the cloud.
2. **No Silent Surprises:** If your local model fails or runs out of memory, the OS will **never** silently switch to a paid cloud model without your explicit authorization.
3. **Right Brain for the Right Job:**
   - Simple tasks & summaries $\rightarrow$ Fast, cheap local models.
   - Deep software engineering $\rightarrow$ High-capability coding models.
   - Large market research $\rightarrow$ Long-context research models.
