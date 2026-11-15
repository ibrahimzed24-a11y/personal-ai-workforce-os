const SUPABASE_URL = 'https://jzyqmzjfmaceoltlqukh.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6eXFtempmbWFjZW9sdGxxdWtoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5NDYwOTYsImV4cCI6MjA4MjUyMjA5Nn0.YAVM5D58S656v4LMOh-Sc5AGA5rtPZw5jOxhVEJ3NtA';
const LOCAL_WORKER_URL = 'http://127.0.0.1:8765';

const sb = window.supabase ? window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY) : null;

let session = null;
let projects = [];
let activeProjectId = null;
let workerOnline = false;
let isSignUpMode = false;

function showToast(msg) {
  const bar = document.getElementById('toast-bar');
  if (!bar) return;
  bar.textContent = msg;
  bar.classList.remove('hidden');
  setTimeout(() => bar.classList.add('hidden'), 6000);
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

async function apiFetch(path, options = {}) {
  const token = session?.access_token || SUPABASE_ANON_KEY;
  const res = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || 'Request failed');
  return data;
}

async function checkLocalWorker() {
  const badge = document.getElementById('worker-badge');
  if (!badge) return;
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 1500);
    const res = await fetch(`${LOCAL_WORKER_URL}/health`, { signal: ctrl.signal });
    clearTimeout(t);
    workerOnline = res.ok;
  } catch {
    workerOnline = false;
  }
  badge.textContent = workerOnline
    ? '● Local Worker Connected (8765)'
    : '○ Cloud / AntiGravity Mode';
  badge.classList.toggle('online', workerOnline);
}

// --- Projects ---
async function loadProjects() {
  try {
    const data = await apiFetch('/api/projects');
    projects = data.projects || [];
    if (!activeProjectId && projects.length > 0) {
      activeProjectId = projects[0].id;
    }
    renderProjects();
    if (activeProjectId) await loadActiveWorkspace();
  } catch (err) {
    showToast(err.message);
  }
}

function renderProjects() {
  const list = document.getElementById('project-list');
  if (!list) return;
  if (projects.length === 0) {
    list.innerHTML = `<div class="subtext" style="font-size:0.8rem; padding:0.5rem;">No projects yet. Click "+ New Project" to begin.</div>`;
    return;
  }
  list.innerHTML = projects
    .map(
      (p) =>
        `<div class="project-item ${p.id === activeProjectId ? 'active' : ''}" onclick="selectProject('${p.id}')">
          ${escapeHtml(p.name)}
        </div>`
    )
    .join('');

  const current = projects.find((p) => p.id === activeProjectId);
  if (current) {
    const nameEl = document.getElementById('active-project-name');
    const goalEl = document.getElementById('active-project-goal');
    if (nameEl) nameEl.textContent = current.name;
    if (goalEl) goalEl.textContent = current.goal || 'No project goal set yet. Edit in Project Settings.';

    const setName = document.getElementById('set-name');
    const setGoal = document.getElementById('set-goal');
    const setRuntime = document.getElementById('set-runtime');
    const setAgents = document.getElementById('set-agents');
    if (setName) setName.value = current.name;
    if (setGoal) setGoal.value = current.goal || '';
    if (setRuntime) setRuntime.value = current.runtime_mode || 'antigravity';
    if (setAgents) setAgents.value = (current.assigned_agents || []).join(', ');
  }
}

window.selectProject = async function (id) {
  activeProjectId = id;
  renderProjects();
  await loadActiveWorkspace();
};

async function loadActiveWorkspace() {
  if (!activeProjectId) return;
  try {
    const [ws, vault] = await Promise.all([
      apiFetch(`/api/projects/${activeProjectId}/workspace`),
      apiFetch(`/api/projects/${activeProjectId}/vault`),
    ]);
    renderChat(ws.messages || []);
    renderReports(ws.runs || []);
    renderVault(vault.tools || []);
  } catch (err) {
    showToast(err.message);
  }
}

function renderChat(messages) {
  const feed = document.getElementById('chat-feed');
  if (!feed) return;
  if (messages.length === 0) {
    feed.innerHTML = `
      <div class="empty-card">
        <h3>Talk to your project team</h3>
        <p>Write a task in plain English or Egyptian Arabic (اتكلم بالمصري أو بالإنجليزي). Your Lead Coordinator will execute the workflow and generate an Admin Report.</p>
      </div>`;
    return;
  }
  feed.innerHTML = messages
    .map(
      (m) => `
      <div class="msg-bubble ${m.sender_role === 'operator' ? 'msg-operator' : 'msg-coordinator'}" dir="auto">
        <div class="msg-meta">${escapeHtml(m.sender_name)}</div>
        <div>${escapeHtml(m.content)}</div>
      </div>`
    )
    .join('');
  feed.scrollTop = feed.scrollHeight;
}

function renderReports(runs) {
  const container = document.getElementById('reports-container');
  if (!container) return;
  if (runs.length === 0) {
    container.innerHTML = `<div class="empty-card"><h3>No Admin Reports yet</h3><p>Send a task in the Team Chat tab to run the agent pipeline and generate your first report.</p></div>`;
    return;
  }
  container.innerHTML = runs
    .map(
      (r) => `
      <div class="report-card">
        <div class="row-between">
          <strong>${escapeHtml(r.directive)}</strong>
          <span class="subtext" style="margin:0;font-size:0.78rem;">${r.runtime_used} • ${r.latency_ms}ms</span>
        </div>
        <div class="pipeline-steps">
          ${(r.handoff_steps || [])
            .map((s) => `<span class="step-chip">${s.step}. ${escapeHtml(s.agent)}: ${escapeHtml(s.action)}</span>`)
            .join('')}
        </div>
        <div class="report-body" dir="auto">${escapeHtml(r.admin_report)}</div>
      </div>`
    )
    .join('');
}

function renderVault(tools) {
  const list = document.getElementById('vault-list');
  if (!list) return;
  if (tools.length === 0) {
    list.innerHTML = `<p class="subtext" style="margin-top:0.75rem;">No saved logins attached to this project yet.</p>`;
    return;
  }
  list.innerHTML = tools
    .map(
      (t) => `
      <div class="vault-row">
        <div>
          <strong>${escapeHtml(t.tool_name)}</strong>
          <div class="subtext" style="margin:0;font-size:0.8rem;">${escapeHtml(t.username_identifier)} • ${escapeHtml(t.login_url)}</div>
          <div style="font-size:0.76rem;color:#059669;margin-top:0.2rem;">Allowed actions: ${(t.allowed_actions || []).join(', ')}</div>
        </div>
        <button class="btn-danger" onclick="removeVaultTool('${t.id}')">Remove</button>
      </div>`
    )
    .join('');
}

window.removeVaultTool = async function (vaultId) {
  try {
    await apiFetch(`/api/vault/${vaultId}`, { method: 'DELETE' });
    await loadActiveWorkspace();
  } catch (err) {
    showToast(err.message);
  }
};

// --- Connectors ---
async function loadConnectors() {
  const grid = document.getElementById('connectors-grid');
  if (!grid) return;
  try {
    const data = await apiFetch('/api/connectors');
    const list = data.connectors || [];
    grid.innerHTML = list
      .map(
        (c) => `
        <div class="connector-card">
          <div>
            <div class="connector-header">
              <span class="connector-title">${escapeHtml(c.name)}</span>
              <span class="connector-badge ${c.status === 'configured' ? 'badge-configured' : 'badge-available'}">
                <span class="dot ${c.status === 'configured' ? 'emerald' : 'blue'}" style="width:6px;height:6px;"></span>
                ${escapeHtml(c.status)}
              </span>
            </div>
            <p class="connector-desc" style="margin-top:0.5rem;">${escapeHtml(c.description)}</p>
          </div>
          <div>
            <div class="connector-meta">${escapeHtml(c.auth_type)}</div>
            <div style="margin-top:0.6rem; display:flex; gap:0.5rem;">
              <button class="btn-secondary small" onclick="testConnector('${c.id}')">Test</button>
            </div>
          </div>
        </div>`
      )
      .join('');
  } catch (err) {
    grid.innerHTML = `<p class="subtext">Error loading connectors: ${err.message}</p>`;
  }
}

window.testConnector = async function (connectorId) {
  try {
    const res = await apiFetch(`/api/connectors/${connectorId}/test`, { method: 'POST' });
    alert(`Connection test passed for ${connectorId}! Latency: ${res.latency_ms}ms`);
  } catch (err) {
    alert(`Test error: ${err.message}`);
  }
};

// --- 32 Workforce Agents ---
const WORKFORCE_32_AGENTS = [
  { id: "core-orchestrator", name: "Core Orchestrator", dept: "Operations" },
  { id: "coordinator", name: "Lead Coordinator", dept: "Operations" },
  { id: "task-decomposer", name: "Task Decomposer", dept: "Operations" },
  { id: "context-manager", name: "Context Manager", dept: "Operations" },
  { id: "software-engineer", name: "Software Engineer", dept: "Engineering" },
  { id: "code-reviewer", name: "Code Reviewer", dept: "Engineering" },
  { id: "ast-security-auditor", name: "AST Security Auditor", dept: "Engineering" },
  { id: "test-automation-lead", name: "Test Lead", dept: "Engineering" },
  { id: "browser-automation", name: "Browser Automation", dept: "Browser" },
  { id: "web-navigator", name: "Web Navigator", dept: "Browser" },
  { id: "dom-extractor", name: "DOM Extractor", dept: "Browser" },
  { id: "session-persister", name: "Session Persister", dept: "Browser" },
  { id: "market-seo-analyst", name: "Market & SEO Analyst", dept: "Market & SEO" },
  { id: "search-console-specialist", name: "Search Console Specialist", dept: "Market & SEO" },
  { id: "keyword-discovery-agent", name: "Keyword Discovery", dept: "Market & SEO" },
  { id: "competitor-intelligence", name: "Competitor Intel", dept: "Market & SEO" },
  { id: "marketing-content-creator", name: "Marketing Creator", dept: "Marketing" },
  { id: "copywriting-lead", name: "Copywriting Lead", dept: "Marketing" },
  { id: "social-distributor", name: "Social Distributor", dept: "Marketing" },
  { id: "email-campaign-architect", name: "Email Campaign Lead", dept: "Marketing" },
  { id: "deployment-specialist", name: "Deployment Specialist", dept: "Deployment" },
  { id: "vercel-cloud-engineer", name: "Vercel Cloud Engineer", dept: "Deployment" },
  { id: "github-actions-operator", name: "GitHub Actions Operator", dept: "Deployment" },
  { id: "posix-vault-curator", name: "POSIX Vault Curator", dept: "Deployment" },
  { id: "master-reporting", name: "Master Reporting", dept: "Reporting" },
  { id: "admin-summary-compiler", name: "Admin Summary Compiler", dept: "Reporting" },
  { id: "verification-auditor", name: "Independent Verifier", dept: "Reporting" },
  { id: "telemetry-aggregator", name: "Telemetry Aggregator", dept: "Reporting" },
  { id: "system-integrator", name: "System Integrator", dept: "Integrator" },
  { id: "asset-ingestion-worker", name: "Asset Ingestion Worker", dept: "Integrator" },
  { id: "dependency-resolver", name: "Dependency Resolver", dept: "Integrator" },
  { id: "rollback-safety-guardian", name: "Rollback Guardian", dept: "Integrator" }
];

function loadAgents() {
  const grid = document.getElementById('agents-grid');
  if (!grid) return;
  grid.innerHTML = WORKFORCE_32_AGENTS
    .map(
      (a) => `
      <div class="agent-card" onclick="inspectAgent('${a.id}', '${a.name}')">
        <div>
          <span class="agent-dept">${escapeHtml(a.dept)}</span>
          <div class="agent-card-title">${escapeHtml(a.name)}</div>
        </div>
        <div class="row-between" style="margin-top:0.4rem;">
          <span style="font-size:0.75rem; color:var(--muted); font-family:var(--mono);">AGENT.md • SKILL.md</span>
          <span style="font-size:0.75rem; color:var(--accent); font-weight:600;">View →</span>
        </div>
      </div>`
    )
    .join('');
}

window.inspectAgent = async function (agentId, agentName) {
  const modal = document.getElementById('agent-blueprint-modal');
  const title = document.getElementById('modal-agent-name');
  const body = document.getElementById('blueprint-content');
  title.textContent = `${agentName} (${agentId})`;
  body.textContent = 'Loading agent blueprint and memory...';
  modal.classList.remove('hidden');

  try {
    const data = await apiFetch(`/api/agents/${agentId}/context`);
    body.textContent = `${data.agent_md}\n\n---\n\n${data.skill_md}\n\n---\n\n${data.memory_md}`;
  } catch (err) {
    body.textContent = `# Blueprint: ${agentId}\n\nDepartment: Sovereign Workforce\nRuntime: AntiGravity Local Mac Sandboxed\nMemory: Persistent across project pipeline handoffs.`;
  }
};

// --- Event Listeners ---
document.querySelectorAll('.tab-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach((c) => c.classList.add('hidden'));
    btn.classList.add('active');
    const tabSection = document.getElementById(`tab-${btn.dataset.tab}`);
    if (tabSection) tabSection.classList.remove('hidden');

    if (btn.dataset.tab === 'connectors') loadConnectors();
    if (btn.dataset.tab === 'agents') loadAgents();
  });
});

const closeAgentBtn = document.getElementById('close-agent-modal-btn');
if (closeAgentBtn) {
  closeAgentBtn.addEventListener('click', () => {
    document.getElementById('agent-blueprint-modal').classList.add('hidden');
  });
}

document.getElementById('auth-toggle').addEventListener('click', () => {
  isSignUpMode = !isSignUpMode;
  document.getElementById('auth-submit').textContent = isSignUpMode ? 'Create Account' : 'Sign in';
  document.getElementById('auth-toggle').textContent = isSignUpMode
    ? 'Already have an account? Sign in'
    : 'Create a new operator account';
});

document.getElementById('auth-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('auth-email').value.trim();
  const password = document.getElementById('auth-password').value;
  const errEl = document.getElementById('auth-error');
  errEl.classList.add('hidden');

  if (!sb) {
    startApp({ user: { email }, access_token: SUPABASE_ANON_KEY });
    return;
  }

  const { data, error } = isSignUpMode
    ? await sb.auth.signUp({ email, password })
    : await sb.auth.signInWithPassword({ email, password });

  if (error) {
    errEl.textContent = error.message;
    errEl.classList.remove('hidden');
    return;
  }
  if (data?.session) {
    startApp(data.session);
  } else if (data?.user) {
    // If autoconfirmed, try sign in
    const signInRes = await sb.auth.signInWithPassword({ email, password });
    if (signInRes.data?.session) {
      startApp(signInRes.data.session);
    } else {
      errEl.textContent = 'Account created! Please sign in.';
      errEl.classList.remove('hidden');
      isSignUpMode = false;
      document.getElementById('auth-submit').textContent = 'Sign in';
    }
  }
});

// Guest / Sovereign Local Mode
const guestBtn = document.getElementById('guest-login-btn');
if (guestBtn) {
  guestBtn.addEventListener('click', () => {
    startApp({
      user: { email: 'operator@sovereign-workforce.local' },
      access_token: SUPABASE_ANON_KEY,
    });
  });
}

document.getElementById('signout-btn').addEventListener('click', async () => {
  if (sb) await sb.auth.signOut();
  location.reload();
});

document.getElementById('new-project-btn').addEventListener('click', () => {
  document.getElementById('project-modal').classList.remove('hidden');
});

document.getElementById('close-modal-btn').addEventListener('click', () => {
  document.getElementById('project-modal').classList.add('hidden');
});

document.getElementById('create-project-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    const data = await apiFetch('/api/projects', {
      method: 'POST',
      body: JSON.stringify({
        name: document.getElementById('new-proj-name').value.trim(),
        goal: document.getElementById('new-proj-goal').value.trim(),
        runtime_mode: document.getElementById('new-proj-runtime').value,
      }),
    });
    document.getElementById('project-modal').classList.add('hidden');
    e.target.reset();
    activeProjectId = data.project.id;
    await loadProjects();
  } catch (err) {
    showToast(err.message);
  }
});

document.getElementById('settings-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!activeProjectId) return;
  const agents = document
    .getElementById('set-agents')
    .value.split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  try {
    await apiFetch(`/api/projects/${activeProjectId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        name: document.getElementById('set-name').value.trim(),
        goal: document.getElementById('set-goal').value.trim(),
        runtime_mode: document.getElementById('set-runtime').value,
        assigned_agents: agents,
      }),
    });
    await loadProjects();
  } catch (err) {
    showToast(err.message);
  }
});

document.getElementById('delete-project-btn').addEventListener('click', async () => {
  if (!activeProjectId || !confirm('Delete this project and all its saved logins and reports?')) return;
  try {
    await apiFetch(`/api/projects/${activeProjectId}`, { method: 'DELETE' });
    activeProjectId = null;
    await loadProjects();
  } catch (err) {
    showToast(err.message);
  }
});

document.getElementById('vault-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!activeProjectId) return showToast('Create or select a project first.');
  const actions = document
    .getElementById('vault-actions')
    .value.split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  try {
    await apiFetch('/api/vault', {
      method: 'POST',
      body: JSON.stringify({
        project_id: activeProjectId,
        tool_name: document.getElementById('vault-tool').value.trim(),
        login_url: document.getElementById('vault-url').value.trim(),
        username_identifier: document.getElementById('vault-user').value.trim(),
        password_or_token: document.getElementById('vault-secret').value,
        allowed_actions: actions,
      }),
    });
    e.target.reset();
    await loadActiveWorkspace();
  } catch (err) {
    showToast(err.message);
  }
});

document.getElementById('chat-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!activeProjectId) return showToast('Create or select a project first.');
  const input = document.getElementById('chat-input');
  const btn = document.getElementById('chat-send-btn');
  const msg = input.value.trim();
  if (!msg) return;

  btn.disabled = true;
  btn.textContent = 'Working...';

  let localOutput = null;
  const currentProj = projects.find((p) => p.id === activeProjectId);
  if (workerOnline && currentProj?.runtime_mode === 'local_llm') {
    try {
      const wRes = await fetch(`${LOCAL_WORKER_URL}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: msg }),
      });
      if (wRes.ok) {
        const wData = await wRes.json();
        localOutput = wData.output;
      }
    } catch {
      // Fallback to cloud runtime seamlessly
    }
  }

  try {
    await apiFetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        project_id: activeProjectId,
        message: msg,
        local_worker_output: localOutput,
      }),
    });
    input.value = '';
    await loadActiveWorkspace();
  } catch (err) {
    showToast(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Send to Team';
  }
});

function startApp(activeSession) {
  session = activeSession;
  document.getElementById('auth-view').classList.add('hidden');
  document.getElementById('app-view').classList.remove('hidden');
  document.getElementById('user-email').textContent = session.user?.email || 'Operator';
  checkLocalWorker();
  setInterval(checkLocalWorker, 15000);
  loadProjects();
}

(async function boot() {
  if (sb) {
    try {
      const { data } = await sb.auth.getSession();
      if (data?.session) {
        startApp(data.session);
        return;
      }
    } catch (e) {
      console.warn('Supabase session lookup error:', e);
    }
  }
})();
