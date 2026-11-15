// AI Workforce OS Client Application
let currentTask = null;
let activeTab = 'tasks';
let activeSecSubTab = 'accounts';
let cachedAccounts = [];

document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    loadTasks();
    loadAgents();
    loadSecurityAccounts();
    loadSecurityHealth();
    loadRequirements();
    loadKnowledge();
    loadGlobalEvents();

    // Periodic live status polling
    setInterval(() => {
        if (activeTab === 'tasks') {
            loadTasks(true);
            if (currentTask) refreshTaskDetail(currentTask.id);
        } else if (activeTab === 'security') {
            loadSecurityAccounts(true);
            loadSecurityHealth();
        } else if (activeTab === 'models') {
            loadModelsData();
        } else if (activeTab === 'events') {
            loadGlobalEvents();
        }
    }, 4000);
});

function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

            button.classList.add('active');
            activeTab = button.dataset.tab;
            const targetPane = document.getElementById(`${activeTab}Tab`);
            if (targetPane) targetPane.classList.add('active');

            const tabTitleMap = {
                tasks: 'Tasks & Execution',
                agents: 'Agent Blueprints',
                security: 'Security & Credentials Vault',
                models: 'LLM & Model Management',
                integrator: 'System Integrator & Update Agent',
                requirements: 'Requirements & Change Engine',
                events: 'System Execution Audit Log'
            };
            document.getElementById('currentTabTitle').textContent = tabTitleMap[activeTab] || 'Control Center';
            if (activeTab === 'models') loadModelsData();
            
            // Adjust topbar button based on tab
            const topBtn = document.getElementById('topbarActionBtn');
            if (activeTab === 'security') {
                topBtn.textContent = '+ Add Account';
                topBtn.onclick = window.openNewAccountModal;
            } else {
                topBtn.textContent = '+ Create Task';
                topBtn.onclick = window.openNewTaskModal;
            }

            window.refreshActiveTab();
        });
    });
}

window.refreshActiveTab = function() {
    if (activeTab === 'tasks') loadTasks();
    else if (activeTab === 'agents') loadAgents();
    else if (activeTab === 'security') { loadSecurityAccounts(); loadSecurityHealth(); loadSecurityAuditLogs(); }
    else if (activeTab === 'integrator') { loadAssets(); loadKnowledge(); }
    else if (activeTab === 'requirements') loadRequirements();
    else if (activeTab === 'events') loadGlobalEvents();
};

// --- Tasks ---
async function loadTasks(silent = false) {
    try {
        const res = await fetch('/api/tasks');
        const tasks = await res.json();
        const container = document.getElementById('taskListContainer');
        document.getElementById('taskCountBadge').textContent = `${tasks.length} tasks`;

        if (!tasks.length) {
            container.innerHTML = '<div class="empty-state">No tasks created yet. Click "+ Create Task" to begin.</div>';
            return;
        }

        container.innerHTML = tasks.map(t => `
            <div class="task-card ${currentTask && currentTask.id === t.id ? 'active' : ''}" onclick="window.selectTask('${t.id}')">
                <div class="task-card-header">
                    <span class="task-card-title">${t.title}</span>
                    <span class="tag status-${t.status}">${t.status.toUpperCase()}</span>
                </div>
                <div class="task-meta">
                    <span>Priority: ${t.priority.toUpperCase()}</span>
                    <span>Verified: ${t.verification_status}</span>
                </div>
            </div>
        `).join('');

        if (!currentTask && tasks.length && !silent) {
            window.selectTask(tasks[0].id);
        }
    } catch (e) {
        console.error('Failed loading tasks:', e);
    }
}

window.selectTask = async function(taskId) {
    try {
        const res = await fetch(`/api/tasks/${taskId}`);
        currentTask = await res.json();
        renderTaskDetail(currentTask);
        document.querySelectorAll('.task-card').forEach(c => c.classList.remove('active'));
        const activeCard = Array.from(document.querySelectorAll('.task-card')).find(c => c.textContent.includes(currentTask.title));
        if (activeCard) activeCard.classList.add('active');
    } catch (e) {
        console.error('Failed selecting task:', e);
    }
};

async function refreshTaskDetail(taskId) {
    try {
        const res = await fetch(`/api/tasks/${taskId}`);
        currentTask = await res.json();
        renderTaskDetail(currentTask);
    } catch (e) {
        console.error('Failed refreshing task detail:', e);
    }
}

function renderTaskDetail(task) {
    const container = document.getElementById('taskDetailContainer');
    const badges = document.getElementById('taskStatusBadges');

    badges.innerHTML = `
        <span class="tag status-${task.status}">${task.status.toUpperCase()}</span>
        <span class="tag">Verification: ${task.verification_status.toUpperCase()}</span>
    `;

    let planHtml = '<p class="subtext">No execution plan created yet.</p>';
    if (task.plan && task.plan.steps) {
        planHtml = task.plan.steps.map(s => `
            <div class="plan-step">
                <div class="step-header">
                    <span>Step ${s.step_number}: ${s.title}</span>
                    <span class="tag status-${s.status}">${s.status.toUpperCase()}</span>
                </div>
                <div class="step-desc">${s.description}</div>
                <div class="task-meta">
                    <span>Assigned: <strong>${s.assigned_agent}</strong></span>
                    <span>Specialist: <strong>${s.specialist_id || 'Generalist'}</strong></span>
                </div>
            </div>
        `).join('');
    }

    let outputHtml = '';
    if (task.output_result) {
        outputHtml = `
            <div class="panel" style="margin-top: 14px; background: #131922;">
                <h3>Execution Deliverable & Results</h3>
                <p style="margin: 6px 0; color: #a1a1aa;">${task.output_result.summary || ''}</p>
                ${task.output_result.artifact_path ? `<p style="font-size: 11px; color: #38bdf8;">Artifact: <code>${task.output_result.artifact_path}</code></p>` : ''}
                ${task.output_result.deliverable_preview ? `<pre style="font-size:11px; background:#0a0e14; padding:10px; border-radius:4px; margin-top:8px;">${task.output_result.deliverable_preview}</pre>` : ''}
            </div>
        `;
    }

    let verifHtml = '';
    if (task.verification) {
        verifHtml = `
            <div class="panel" style="margin-top: 14px; background: #131922;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3>Independent Quality Verification</h3>
                    <span class="badge ${task.verification.status === 'passed' ? 'online' : 'risk-HIGH'}">${task.verification.status.toUpperCase()}</span>
                </div>
                <p style="font-size: 12px; margin: 6px 0;">${task.verification.report_text}</p>
                <div style="font-size: 11px; color: #94a3b8;">
                    ${task.verification.checks_run.map(c => `<div>✓ ${c.check}: ${c.detail} (${c.passed ? 'PASSED' : 'FAILED'})</div>`).join('')}
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <h1 style="font-size: 18px; margin-bottom: 4px;">${task.title}</h1>
                <p style="color: var(--text-secondary); font-size: 13px;">${task.description}</p>
            </div>
            <div>
                ${task.status === 'pending' || task.status === 'failed' ? `
                    <button class="btn btn-primary" onclick="window.runTaskNow('${task.id}')">▶ Run Task Pipeline</button>
                ` : `
                    <button class="btn btn-secondary" disabled>Executing...</button>
                `}
            </div>
        </div>

        <div style="margin-top: 16px;">
            <h3 style="font-size: 14px; margin-bottom: 10px;">Execution Plan & Autonomous Delegation</h3>
            ${planHtml}
        </div>

        ${outputHtml}
        ${verifHtml}
    `;
}

window.runTaskNow = async function(taskId) {
    try {
        const btn = event.target;
        btn.disabled = true;
        btn.textContent = 'Running Pipeline...';
        await fetch(`/api/tasks/${taskId}/run`, { method: 'POST' });
        await window.selectTask(taskId);
        loadTasks(true);
    } catch (e) {
        alert('Task run failed: ' + e);
    }
};

window.openNewTaskModal = function() {
    document.getElementById('newTaskModal').classList.add('active');
};

window.closeNewTaskModal = function() {
    document.getElementById('newTaskModal').classList.remove('active');
};

window.handleCreateTask = async function(e) {
    e.preventDefault();
    const title = document.getElementById('taskTitleInput').value;
    const description = document.getElementById('taskDescInput').value;
    const priority = document.getElementById('taskPriorityInput').value;
    const targetAgent = document.getElementById('taskAgentInput').value;

    try {
        const res = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description, priority, target_agent: targetAgent, context: {} })
        });
        const created = await res.json();
        window.closeNewTaskModal();
        await loadTasks();
        window.selectTask(created.id);
    } catch (err) {
        alert('Failed creating task: ' + err);
    }
};

// --- Agent Blueprints ---
async function loadAgents() {
    try {
        const res = await fetch('/api/agents');
        const agents = await res.json();
        const container = document.getElementById('agentGridContainer');
        container.innerHTML = agents.map(a => `
            <div class="agent-card">
                <div>
                    <span class="agent-dept">${a.department}</span>
                    <h3 class="agent-card-title">${a.name}</h3>
                </div>
                <p>${a.description}</p>
                <div class="specialist-list">
                    <strong>Specialists (${a.specialists.length}):</strong>
                    ${a.specialists.map(s => `
                        <div class="specialist-item">• <strong>${s.name}</strong>: ${s.specialization}</div>
                    `).join('')}
                </div>
                <div class="task-meta">
                    <span>Model: <code>${a.default_model.name}</code></span>
                    <span>Version: ${a.version}</span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed loading agents:', e);
    }
}

// --- Security & Credentials Vault ---
window.switchSecuritySubTab = function(subTab) {
    activeSecSubTab = subTab;
    document.querySelectorAll('.sub-nav-bar .btn-sub').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.sec-sub-pane').forEach(p => p.style.display = 'none');

    if (subTab === 'accounts') {
        document.getElementById('secSubBtnAccounts').classList.add('active');
        document.getElementById('secSubAccounts').style.display = 'flex';
        loadSecurityAccounts();
    } else if (subTab === 'registrations') {
        document.getElementById('secSubBtnRegistrations').classList.add('active');
        document.getElementById('secSubRegistrations').style.display = 'flex';
        loadRegistrations();
    } else if (subTab === 'monitoring') {
        document.getElementById('secSubBtnMonitoring').classList.add('active');
        document.getElementById('secSubMonitoring').style.display = 'flex';
        loadSecurityHealth();
    } else if (subTab === 'audit') {
        document.getElementById('secSubBtnAudit').classList.add('active');
        document.getElementById('secSubAudit').style.display = 'flex';
        loadSecurityAuditLogs();
    }
};

async function loadSecurityAccounts(silent = false) {
    try {
        const res = await fetch('/api/security/accounts');
        cachedAccounts = await res.json();
        renderAccountsGrid(cachedAccounts);
    } catch (e) {
        console.error('Failed loading security accounts:', e);
    }
}

function renderAccountsGrid(accounts) {
    const container = document.getElementById('accountsGridContainer');
    if (!accounts.length) {
        container.innerHTML = '<div class="empty-state">No accounts registered in vault yet. Click "+ Add Account" to store credentials securely.</div>';
        return;
    }

    container.innerHTML = accounts.map(a => {
        const authorizedPills = (a.authorized_agents || []).map(ag => `<span class="agent-badge">${ag.agent_id} (${ag.permission_level})</span>`).join('');
        return `
            <div class="account-card">
                <div class="account-header">
                    <div>
                        <span class="tag" style="margin-right:6px;">${a.category.toUpperCase()}</span>
                        <strong class="account-title">${a.name}</strong>
                    </div>
                    <span class="badge ${a.health_status === 'HEALTHY' ? 'online' : 'risk-MEDIUM'}">${a.health_status}</span>
                </div>
                <div class="account-meta">
                    <div>User/Email: <code>${a.username_or_email}</code></div>
                    <div>Website: <a href="${a.url}" target="_blank" style="color:var(--accent); text-decoration:none;">${a.url}</a></div>
                    <div>MFA: <strong>${a.mfa_status}</strong> | Password: <span class="pw-mask">••••••••••••</span></div>
                    <div style="margin-top:4px;">Authorized Agents:</div>
                    <div class="agent-badges">${authorizedPills || '<span style="color:#64748b; font-size:11px;">None assigned</span>'}</div>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px; border-top:1px solid var(--border-color); padding-top:8px;">
                    <span style="font-size:11px; color:var(--text-muted);">Updated: ${a.updated_at.split('T')[0]}</span>
                    <button class="btn btn-secondary btn-small" onclick="window.inspectAccount('${a.id}')">Inspect & Manage</button>
                </div>
            </div>
        `;
    }).join('');
}

window.filterAccounts = function() {
    const search = document.getElementById('secSearchInput').value.toLowerCase();
    const category = document.getElementById('secCategoryFilter').value;
    const filtered = cachedAccounts.filter(a => {
        const matchSearch = !search || a.name.toLowerCase().includes(search) || a.username_or_email.toLowerCase().includes(search) || a.url.toLowerCase().includes(search);
        const matchCat = !category || a.category === category;
        return matchSearch && matchCat;
    });
    renderAccountsGrid(filtered);
};

window.openNewAccountModal = function() {
    document.getElementById('newAccountModal').classList.add('active');
};

window.closeNewAccountModal = function() {
    document.getElementById('newAccountModal').classList.remove('active');
};

window.handleCreateAccount = async function(e) {
    e.preventDefault();
    const name = document.getElementById('accNameInput').value;
    const category = document.getElementById('accCategoryInput').value;
    const mfa_status = document.getElementById('accMfaInput').value;
    const url = document.getElementById('accUrlInput').value;
    const login_url = document.getElementById('accLoginUrlInput').value;
    const username_or_email = document.getElementById('accUserInput').value;
    const password = document.getElementById('accPassInput').value;

    const assigned_agents = [];
    document.querySelectorAll('input[name="authAgentCheck"]:checked').forEach(cb => assigned_agents.push(cb.value));

    try {
        await fetch('/api/security/accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name, category, mfa_status, url, login_url, username_or_email, password, assigned_agents
            })
        });
        window.closeNewAccountModal();
        await loadSecurityAccounts();
        await loadSecurityHealth();
    } catch (err) {
        alert('Failed saving account: ' + err);
    }
};

window.inspectAccount = async function(accountId) {
    try {
        const res = await fetch(`/api/security/accounts/${accountId}`);
        const acc = await res.json();
        document.getElementById('detailAccName').textContent = `${acc.name} — Vault Details`;

        const body = document.getElementById('accountDetailBody');
        body.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:12px;">
                <div class="form-row">
                    <div><strong>URL:</strong> <a href="${acc.url}" target="_blank" style="color:var(--accent);">${acc.url}</a></div>
                    <div><strong>Login URL:</strong> <code>${acc.login_url}</code></div>
                </div>
                <div class="form-row">
                    <div><strong>Username/Email:</strong> <code>${acc.username_or_email}</code></div>
                    <div><strong>Status:</strong> <span class="tag status-completed">${acc.status}</span></div>
                </div>
                <div><strong>Category:</strong> ${acc.category} | <strong>MFA:</strong> ${acc.mfa_status}</div>

                <div style="background:#0f141c; border:1px solid var(--border-color); border-radius:6px; padding:12px; margin-top:6px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>Encrypted Password in Vault:</strong>
                        <span id="revealedPwArea" style="font-family:monospace; color:#38bdf8;">••••••••••••</span>
                    </div>
                    <div style="margin-top:8px; display:flex; gap:8px;">
                        <input type="password" id="masterKeyPrompt" class="input-field" placeholder="Enter Master Vault Key to Reveal" style="flex:1;">
                        <button class="btn btn-secondary btn-small" onclick="window.revealPasswordNow('${acc.id}')">Reveal Password</button>
                    </div>
                </div>

                <div style="margin-top:10px;">
                    <h4>Authorized Agents & Policies</h4>
                    <div style="font-size:12px; margin-top:6px;">
                        ${(acc.authorized_agents || []).map(p => `<div>• <strong>${p.agent_id}</strong>: <code>${p.permission_level}</code></div>`).join('')}
                    </div>
                </div>

                <div style="margin-top:10px; border-top:1px solid var(--border-color); padding-top:10px;">
                    <h4>Rotate / Update Password</h4>
                    <div style="display:flex; gap:8px; margin-top:6px;">
                        <input type="password" id="newRotatePassInput" class="input-field" placeholder="Enter new password" style="flex:1;">
                        <button class="btn btn-primary btn-small" onclick="window.rotatePasswordNow('${acc.id}')">Rotate Password</button>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('accountDetailModal').classList.add('active');
    } catch (e) {
        alert('Failed fetching account details: ' + e);
    }
};

window.closeAccountDetailModal = function() {
    document.getElementById('accountDetailModal').classList.remove('active');
};

window.revealPasswordNow = async function(accountId) {
    const masterKey = document.getElementById('masterKeyPrompt').value;
    if (!masterKey) {
        alert('Please enter your master vault key to decrypt.');
        return;
    }
    try {
        const res = await fetch(`/api/security/accounts/${accountId}/reveal`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ master_key: masterKey })
        });
        if (!res.ok) throw new Error('Authorization failed. Invalid master key.');
        const data = await res.json();
        document.getElementById('revealedPwArea').textContent = data.password;
    } catch (e) {
        alert(e.message);
    }
};

window.rotatePasswordNow = async function(accountId) {
    const newPass = document.getElementById('newRotatePassInput').value;
    if (!newPass) return alert('Enter a new password');
    try {
        await fetch(`/api/security/accounts/${accountId}/update-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_password: newPass, reason: 'Owner manual rotation' })
        });
        alert('Credentials successfully updated and rotated in vault.');
        window.closeAccountDetailModal();
        await loadSecurityAccounts();
    } catch (e) {
        alert('Password rotation failed: ' + e);
    }
};

async function loadRegistrations() {
    try {
        const res = await fetch('/api/security/registrations');
        const reqs = await res.json();
        const container = document.getElementById('registrationsListContainer');
        if (!reqs.length) {
            container.innerHTML = '<div class="empty-state">No pending account registration requests from agents.</div>';
            return;
        }

        container.innerHTML = reqs.map(r => `
            <div class="asset-card">
                <div class="asset-header">
                    <strong>${r.service_name}</strong>
                    <span class="tag status-${r.status.toLowerCase()}">${r.status}</span>
                </div>
                <div style="font-size:12px; color:var(--text-secondary);">
                    <div>Requesting Agent: <code>${r.agent_id}</code> | Task: <code>${r.task_id}</code></div>
                    <div>Website: <a href="${r.website_url}" target="_blank" style="color:var(--accent);">${r.website_url}</a></div>
                    <div>Proposed Username: <code>${r.proposed_username_or_email}</code></div>
                    <div>Financial Commitment: ${r.is_paid ? '<strong style="color:red;">PAID SUBSCRIPTION</strong>' : 'Free / Standard'}</div>
                    <div style="margin-top:4px;"><strong>Reason:</strong> ${r.reason}</div>
                </div>
                ${r.status === 'PENDING' ? `
                    <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:8px;">
                        <button class="btn btn-secondary btn-small" onclick="window.decideRegistration('${r.id}', 'REJECTED')">Reject</button>
                        <button class="btn btn-primary btn-small" onclick="window.decideRegistration('${r.id}', 'APPROVED')">Approve Account Creation</button>
                    </div>
                ` : `<span style="font-size:11px; color:#10b981;">Resolved: ${r.status}</span>`}
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed loading registrations:', e);
    }
}

window.decideRegistration = async function(reqId, decision) {
    try {
        await fetch(`/api/security/registrations/${reqId}/approve?decision=${decision}`, { method: 'POST' });
        await loadRegistrations();
    } catch (e) {
        alert('Failed resolving registration: ' + e);
    }
};

async function loadSecurityHealth() {
    try {
        const res = await fetch('/api/security/health');
        const health = await res.json();
        document.getElementById('statTotalAccounts').textContent = health.total_accounts;
        document.getElementById('statMfaDisabled').textContent = health.mfa_disabled;
        document.getElementById('statStalePass').textContent = health.stale_passwords;

        const recContainer = document.getElementById('securityRecommendationsContainer');
        if (!health.recommendations || !health.recommendations.length) {
            recContainer.innerHTML = '<div style="color:#10b981; padding:12px; background:#0f141c; border-radius:6px;">✓ All security health checks passed. No high-risk posture warnings.</div>';
        } else {
            recContainer.innerHTML = health.recommendations.map(r => `
                <div style="background:#1d2532; border-left:4px solid var(--warning); padding:10px 14px; margin-bottom:8px; border-radius:4px;">
                    ⚠ ${r}
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Failed loading security health:', e);
    }
}

async function loadSecurityAuditLogs() {
    try {
        const res = await fetch('/api/security/audit?limit=50');
        const logs = await res.json();
        const container = document.getElementById('securityAuditLogContainer');
        if (!logs.length) {
            container.innerHTML = '<div class="empty-state">No security audit events recorded yet.</div>';
            return;
        }

        container.innerHTML = logs.map(l => `
            <div style="background: #1d2532; border: 1px solid #2b3544; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                    <span><strong>[${l.action}]</strong> Status: <span class="badge ${l.status === 'SUCCESS' ? 'online' : 'risk-HIGH'}">${l.status}</span> Actor: <code>${l.actor_id}</code> (${l.actor_type})</span>
                    <span style="color: #6e7681; font-family: monospace;">${l.timestamp}</span>
                </div>
                <pre style="font-size: 11px; background: #0f141c; padding: 6px 10px; border-radius: 4px; overflow: auto;">${JSON.stringify(l.details, null, 2)}</pre>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed loading security audit logs:', e);
    }
}

// --- System Integrator ---
window.scanIncomingAssets = async function() {
    try {
        const res = await fetch('/api/integrator/scan');
        const assets = await res.json();
        loadAssets();
    } catch (e) {
        alert('Scan failed: ' + e);
    }
};

async function loadAssets() {
    try {
        const res = await fetch('/api/integrator/assets');
        const assets = await res.json();
        const container = document.getElementById('incomingAssetsContainer');

        if (!assets.length) {
            container.innerHTML = '<div class="empty-state">No assets detected. Place skills, tools, or blueprints into <code>~/AI-Workforce/incoming/</code> and click "Scan Incoming".</div>';
            return;
        }

        container.innerHTML = assets.map(a => {
            const audit = a.security_audit || {};
            const plan = a.installation_plan || {};
            const risk = audit.risk_level || 'LOW';
            
            let actionBtn = '';
            if (a.status === 'AUDITED' || a.status === 'PLANNED') {
                actionBtn = `<button class="btn btn-primary btn-small" onclick="window.approveAndInstallAsset('${a.id}')">Approve & Install</button>`;
            } else if (a.status === 'APPROVED') {
                actionBtn = `<button class="btn btn-primary btn-small" onclick="window.installAssetNow('${a.id}')">Execute Install</button>`;
            } else if (a.status === 'ACTIVE') {
                actionBtn = `<button class="btn btn-danger btn-small" onclick="window.rollbackAssetNow('${a.id}')">Rollback</button>`;
            } else if (a.status === 'FAILED') {
                actionBtn = `<span class="badge" style="background:#ef4444; color:#fff;">INSTALL FAILED</span>`;
            }

            return `
                <div class="asset-card">
                    <div class="asset-header">
                        <div>
                            <strong>${a.name}</strong>
                            <span class="tag" style="margin-left: 6px;">${a.category.toUpperCase()}</span>
                        </div>
                        <span class="risk-badge risk-${risk}">Risk: ${risk}</span>
                    </div>
                    <div style="font-size: 12px; color: var(--text-secondary);">
                        <div>Source: <code>${a.source_path}</code></div>
                        <div>Target: <code>${plan.target_path || 'Pending'}</code></div>
                        <div>Authorized Agents: ${a.target_agents.map(ag => `<code>${ag}</code>`).join(', ')}</div>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
                        <span class="tag status-${a.status.toLowerCase()}">${a.status}</span>
                        ${actionBtn}
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Failed loading assets:', e);
    }
}

window.approveAndInstallAsset = async function(assetId) {
    try {
        await fetch(`/api/integrator/approve/${assetId}`, { method: 'POST' });
        await fetch(`/api/integrator/install/${assetId}`, { method: 'POST' });
        await loadAssets();
        await loadKnowledge();
    } catch (e) {
        alert('Approval/Install failed: ' + e);
    }
};

window.installAssetNow = async function(assetId) {
    try {
        await fetch(`/api/integrator/install/${assetId}`, { method: 'POST' });
        await loadAssets();
        await loadKnowledge();
    } catch (e) {
        alert('Install failed: ' + e);
    }
};

window.rollbackAssetNow = async function(assetId) {
    if (!confirm('Are you sure you want to rollback and remove this asset?')) return;
    try {
        await fetch(`/api/integrator/rollback/${assetId}`, { method: 'POST' });
        await loadAssets();
        await loadKnowledge();
    } catch (e) {
        alert('Rollback failed: ' + e);
    }
};

let operationalKnowledgeCache = {};
async function loadKnowledge() {
    try {
        const res = await fetch('/api/integrator/knowledge');
        operationalKnowledgeCache = await res.json();
        window.showKnowledgeDoc('INSTALLED_ASSETS.md');
    } catch (e) {
        console.error('Failed loading knowledge:', e);
    }
}

window.showKnowledgeDoc = function(docName) {
    document.querySelectorAll('.btn-sub').forEach(b => {
        b.classList.toggle('active', b.textContent.includes(docName.split('.')[0]));
    });
    const content = operationalKnowledgeCache[docName] || `No records found in ${docName}.`;
    document.getElementById('docContentArea').innerHTML = `<pre>${content}</pre>`;
};

// --- Requirements Engine ---
async function loadRequirements() {
    try {
        const res = await fetch('/api/requirements');
        const reqs = await res.json();
        const container = document.getElementById('requirementsListContainer');
        if (!reqs.length) {
            container.innerHTML = '<div class="empty-state">No requirements proposed yet.</div>';
            return;
        }

        container.innerHTML = reqs.map(r => `
            <div class="asset-card">
                <div class="asset-header">
                    <strong>${r.title}</strong>
                    <span class="tag">${r.category.toUpperCase()}</span>
                </div>
                <div style="font-size: 12px; margin: 4px 0;">
                    Status: <span class="tag status-${r.status}">${r.status.toUpperCase()}</span>
                </div>
                <div style="font-size: 11px; background: #0f141c; padding: 8px; border-radius: 4px;">
                    <strong>Proposed Change Plan:</strong>
                    ${r.change_plan.map(p => `<div>• [${p.action}] ${p.details}</div>`).join('')}
                </div>
                ${r.status === 'proposed' ? `
                    <button class="btn btn-primary btn-small" style="align-self: flex-end; margin-top: 6px;" onclick="window.applyRequirementNow('${r.id}')">Apply Requirement</button>
                ` : `
                    <span style="font-size: 11px; color: #10b981;">✓ Applied at ${r.applied_at || ''}</span>
                `}
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed loading requirements:', e);
    }
}

window.submitRequirement = async function(e) {
    e.preventDefault();
    const category = document.getElementById('reqCategory').value;
    const title = document.getElementById('reqTitle').value;
    let spec = {};
    try {
        spec = JSON.parse(document.getElementById('reqSpec').value);
    } catch (err) {
        alert('Invalid JSON in specification');
        return;
    }

    try {
        await fetch('/api/requirements', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, title, specification: spec })
        });
        document.getElementById('reqTitle').value = '';
        await loadRequirements();
    } catch (err) {
        alert('Submission failed: ' + err);
    }
};

window.applyRequirementNow = async function(reqId) {
    try {
        await fetch(`/api/requirements/${reqId}/apply`, { method: 'POST' });
        await loadRequirements();
        await loadAgents();
    } catch (err) {
        alert('Apply failed: ' + err);
    }
};

// --- Event Log Stream ---
async function loadGlobalEvents() {
    try {
        const res = await fetch('/api/tasks');
        const tasks = await res.json();
        const container = document.getElementById('globalEventStreamContainer');

        if (!tasks.length) {
            container.innerHTML = '<div class="empty-state">No execution events recorded yet.</div>';
            return;
        }

        let allEvents = [];
        for (const t of tasks.slice(0, 5)) {
            const evRes = await fetch(`/api/tasks/${t.id}/events`);
            const events = await evRes.json();
            allEvents.push(...events);
        }

        allEvents.sort((a, b) => b.id - a.id);

        container.innerHTML = allEvents.map(e => `
            <div style="background: #1d2532; border: 1px solid #2b3544; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                    <span><strong>[${e.event_type.toUpperCase()}]</strong> Task: <code>${e.task_id}</code> Agent: <code>${e.agent_id || 'System'}</code></span>
                    <span style="color: #6e7681; font-family: monospace;">${e.timestamp}</span>
                </div>
                <pre style="font-size: 11px; background: #0f141c; padding: 6px 10px; border-radius: 4px; overflow: auto;">${JSON.stringify(e.payload, null, 2)}</pre>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed loading events:', e);
    }
}

// --- LLM & Model Manager Functions ---
async function loadModelsData() {
    await loadReasoningStatus();
    await loadModelProviders();
    await loadModelsCatalog();
    await loadModelMetrics();
}

async function loadReasoningStatus() {
    try {
        const res = await fetch('/api/models/status');
        const data = await res.json();
        const badge = document.getElementById('reasoningStatusBadge');
        const notice = document.getElementById('reasoningNoticeText');
        const activeLabel = document.getElementById('activeModelLabel');

        if (data.is_real_llm_active) {
            badge.className = 'badge online';
            badge.textContent = 'LIVE REASONING ACTIVE';
        } else {
            badge.className = 'badge warning';
            badge.textContent = 'OFFLINE SIMULATION (MOCK)';
        }
        notice.textContent = data.notice;
        activeLabel.textContent = `${data.active_model} (${data.classification.toUpperCase()})`;
    } catch (e) {
        console.error('Failed to load reasoning status:', e);
    }
}

async function loadModelProviders() {
    try {
        const res = await fetch('/api/models/providers');
        const providers = await res.json();
        const container = document.getElementById('providerGridContainer');
        if (!container) return;

        container.innerHTML = providers.map(p => {
            let statusBadge = '<span class="badge warning">Unknown</span>';
            if (p.health_status === 'healthy') statusBadge = '<span class="badge online">Healthy</span>';
            else if (p.health_status === 'unreachable') statusBadge = '<span class="badge offline">Unreachable</span>';
            else if (p.health_status === 'unauthenticated') statusBadge = '<span class="badge warning">No Key</span>';

            const isCloud = p.provider_type.startsWith('cloud_');
            return `
                <div class="panel" style="background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                        <div>
                            <h3 style="margin:0; font-size:14px; font-weight:600;">${p.name}</h3>
                            <span style="font-size:11px; color:var(--text-muted);">${p.base_url}</span>
                        </div>
                        ${statusBadge}
                    </div>
                    <div style="margin-top:12px; display:flex; gap:8px;">
                        <button class="btn btn-secondary" style="font-size:11px; padding:4px 8px;" onclick="window.testProviderHealth('${p.id}')">Test Connection</button>
                        ${isCloud ? `<button class="btn btn-primary" style="font-size:11px; padding:4px 8px;" onclick="window.openApiKeyModal('${p.id}', '${p.name}')">Set API Key</button>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Failed loading providers:', e);
    }
}

async function loadModelsCatalog() {
    try {
        const res = await fetch('/api/models');
        const models = await res.json();
        const container = document.getElementById('modelsGridContainer');
        if (!container) return;

        container.innerHTML = models.map(m => {
            const isDef = m.is_default;
            return `
                <div class="panel" style="background:var(--bg-card); border:1px solid ${isDef ? 'var(--accent)' : 'var(--border)'}; border-radius:8px; padding:16px; position:relative;">
                    ${isDef ? '<span style="position:absolute; top:12px; right:12px; background:var(--accent); color:#fff; font-size:10px; font-weight:bold; padding:2px 6px; border-radius:4px;">DEFAULT</span>' : ''}
                    <h3 style="margin:0 0 4px 0; font-size:14px;">${m.display_name}</h3>
                    <div style="font-size:11px; color:var(--text-muted); margin-bottom:8px;"><code>${m.model_name}</code> &bull; ${m.classification.toUpperCase()}</div>
                    <div style="font-size:11px; margin-bottom:12px; display:flex; gap:4px; flex-wrap:wrap;">
                        ${(m.capabilities || []).map(c => `<span class="tag" style="font-size:10px;">${c}</span>`).join('')}
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:11px; color:var(--text-muted);">Ctx: ${m.context_window.toLocaleString()} tok</span>
                        ${!isDef ? `<button class="btn btn-secondary" style="font-size:11px; padding:4px 8px;" onclick="window.setDefaultModel('${m.id}')">Make Default</button>` : '<span style="font-size:11px; color:var(--accent); font-weight:600;">Active Default</span>'}
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Failed loading models catalog:', e);
    }
}

async function loadModelMetrics() {
    try {
        const res = await fetch('/api/models/metrics?limit=15');
        const metrics = await res.json();
        const tbody = document.getElementById('llmMetricsTableBody');
        if (!tbody) return;

        if (!metrics.length) {
            tbody.innerHTML = '<tr><td colspan="6" style="padding:16px; text-align:center; color:var(--text-muted);">No invocation metrics recorded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = metrics.map(m => `
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                <td style="padding:8px 14px; font-family:monospace; font-size:11px;">${m.timestamp || '-'}</td>
                <td style="padding:8px 14px;"><strong>${m.agent_id || 'System'}</strong><br><span style="font-size:10px; color:var(--text-muted);">${m.task_id || '-'}</span></td>
                <td style="padding:8px 14px;">${m.display_name || m.model_id}</td>
                <td style="padding:8px 14px; font-family:monospace;">${m.prompt_tokens} / ${m.completion_tokens} / ${m.prompt_tokens + m.completion_tokens}</td>
                <td style="padding:8px 14px; font-family:monospace;">${Math.round(m.latency_ms)} ms</td>
                <td style="padding:8px 14px;">${m.success ? '<span style="color:var(--online); font-weight:bold;">OK</span>' : '<span style="color:var(--offline); font-weight:bold;">FAILED</span>'}</td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Failed loading model metrics:', e);
    }
}

window.testProviderHealth = async function(providerId) {
    try {
        const res = await fetch(`/api/models/providers/${providerId}/health`, { method: 'POST' });
        const result = await res.json();
        alert(`Health Check Result for ${providerId}:\nStatus: ${result.status}\nMessage: ${result.message || 'Ready'}`);
        await loadModelProviders();
        await loadReasoningStatus();
    } catch (e) {
        alert('Failed to execute health check: ' + e);
    }
};

window.setDefaultModel = async function(modelId) {
    try {
        const res = await fetch('/api/models/default', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_id: modelId })
        });
        if (res.ok) {
            await loadModelsData();
        } else {
            alert('Failed to set default model');
        }
    } catch (e) {
        alert('Error: ' + e);
    }
};

window.openApiKeyModal = function(providerId, providerName) {
    document.getElementById('selectedProviderId').value = providerId;
    document.getElementById('modalProviderName').value = providerName;
    document.getElementById('modalProviderApiKey').value = '';
    document.getElementById('configureApiKeyModal').classList.add('active');
};

window.closeApiKeyModal = function() {
    document.getElementById('configureApiKeyModal').classList.remove('active');
};

window.handleSaveApiKey = async function(e) {
    e.preventDefault();
    const providerId = document.getElementById('selectedProviderId').value;
    const apiKey = document.getElementById('modalProviderApiKey').value;

    try {
        const res = await fetch(`/api/models/providers/${providerId}/credential`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });
        const result = await res.json();
        if (res.ok) {
            alert('API key securely encrypted with Fernet Vault!');
            window.closeApiKeyModal();
            await loadModelProviders();
            await loadReasoningStatus();
        } else {
            alert('Error: ' + (result.detail || 'Failed to save API key'));
        }
    } catch (err) {
        alert('Error saving API key: ' + err);
    }
};

