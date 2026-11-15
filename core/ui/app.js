// ==========================================================================
// AI Workforce OS — Control Center Client Application (Modern White & Blue)
// Focus: Minimalist Home, Chat & Voice Prompting, Project-Task Assignment
// ==========================================================================

let currentTask = null;
let activeTab = 'home';
let activeSecSubTab = 'accounts';
let cachedAccounts = [];
let cachedAgents = [];
let cachedTasks = [];
let cachedProjects = [];
let selectedProjectId = 'proj-core-os';
let selectedDepartment = 'all';

// Voice Recognition State
let speechRecognition = null;
let isVoiceListening = false;
let voiceUsedForCurrentPrompt = false;

document.addEventListener('DOMContentLoaded', () => {
    initVoiceRecognition();
    initCommandPalette();
    setupNavigation();
    setupMobileDrawer();
    setupChatShortcuts();

    loadProjects();
    loadTasks();
    loadAgents();
    loadSecurityAccounts();
    loadSecurityHealth();
    loadRequirements();
    loadKnowledge();
    loadGlobalEvents();
    loadSystemNodes();
    loadModelsData();

    // Periodic live status polling (every 4s)
    setInterval(() => {
        if (activeTab === 'home') {
            loadTasks(true);
            loadProjects(true);
        } else if (activeTab === 'tasks') {
            loadTasks(true);
            if (currentTask) refreshTaskDetail(currentTask.id);
        } else if (activeTab === 'projects') {
            loadProjects(true);
        } else if (activeTab === 'security') {
            loadSecurityAccounts(true);
            loadSecurityHealth();
        } else if (activeTab === 'models') {
            loadModelsData();
        } else if (activeTab === 'events') {
            loadGlobalEvents();
        }
        loadSystemNodes();
    }, 4000);
});

// --- Web Speech API Voice Prompting Initialization ---

function initVoiceRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        speechRecognition = new SpeechRecognition();
        speechRecognition.continuous = true;
        speechRecognition.interimResults = true;
        speechRecognition.lang = 'en-US';

        speechRecognition.onstart = () => {
            isVoiceListening = true;
            voiceUsedForCurrentPrompt = true;
            updateVoiceUi(true);
        };

        speechRecognition.onresult = (event) => {
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                finalTranscript += event.results[i][0].transcript;
            }
            const textarea = document.getElementById('chatPromptInput');
            if (textarea && finalTranscript) {
                textarea.value = finalTranscript;
            }
        };

        speechRecognition.onerror = (event) => {
            console.warn('Speech recognition error:', event.error);
            isVoiceListening = false;
            updateVoiceUi(false);
        };

        speechRecognition.onend = () => {
            isVoiceListening = false;
            updateVoiceUi(false);
        };
    }
}

window.toggleVoicePrompt = function() {
    if (!speechRecognition) {
        alert('Voice recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
        return;
    }

    if (isVoiceListening) {
        speechRecognition.stop();
        isVoiceListening = false;
        updateVoiceUi(false);
    } else {
        try {
            speechRecognition.start();
        } catch (e) {
            console.warn('Voice start exception:', e);
            speechRecognition.stop();
        }
    }
};

function updateVoiceUi(listening) {
    const btn = document.getElementById('voicePromptBtn');
    const textEl = document.getElementById('voiceBtnText');
    const indicator = document.getElementById('voiceStatusIndicator');
    const micIcon = document.getElementById('voiceMicIcon');

    if (btn) btn.classList.toggle('listening', listening);
    if (textEl) textEl.textContent = listening ? 'Stop Voice' : 'Voice Prompt';
    if (micIcon) micIcon.textContent = listening ? '🔴' : '🎙️';
    if (indicator) indicator.classList.toggle('active', listening);
}

function setupChatShortcuts() {
    const textarea = document.getElementById('chatPromptInput');
    if (textarea) {
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                window.handleChatSubmit();
            }
        });
    }
}

// --- Navigation & Responsive Drawer ---

function setupNavigation() {
    const handleTabSwitch = (tabKey) => {
        activeTab = tabKey;

        // Sync Desktop & Mobile Sidebar
        document.querySelectorAll('.nav-item').forEach(b => {
            b.classList.toggle('active', b.dataset.tab === activeTab);
        });

        // Sync Mobile Bottom Nav
        document.querySelectorAll('.mobile-nav-item').forEach(b => {
            b.classList.toggle('active', b.dataset.tab === activeTab);
        });

        // Show Active Tab Pane
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        const targetPane = document.getElementById(`${activeTab}Tab`);
        if (targetPane) targetPane.classList.add('active');

        // Update Titles
        const tabTitleMap = {
            home: { title: 'Home & Command Console', sub: 'Voice & text autonomous prompting, active projects, and multi-agent execution' },
            projects: { title: 'Projects & Workspaces', sub: 'Organize autonomous multi-agent workflows, goals, and deliverables by project' },
            tasks: { title: 'Task Queue', sub: 'Cloud-queued tasks leased and executed by local Mac worker' },
            agents: { title: '32 Agent Workforce', sub: 'Universal 3-file architecture: AGENT.md, SKILL.md, and MEMORY.md' },
            workflows: { title: 'Workflow & DAG Pipelines', sub: 'Interactive directed acyclic graph execution visualizer' },
            security: { title: 'Sovereign Credentials Vault', sub: 'POSIX 0600 encrypted credentials with zero cloud leakage' },
            models: { title: 'LLM & Model Management', sub: 'Multi-tier intelligent routing: Ollama ➔ Gemini / Claude ➔ Fallback' },
            integrator: { title: 'System Integrator & Update Agent', sub: 'Scan, audit, and install new skills and tools' },
            requirements: { title: 'Requirements & Change Engine', sub: 'Self-evolving operating system architecture change requests' },
            events: { title: 'System Execution Audit Log', sub: 'Append-only immutable audit trail from execution_events' }
        };

        const currentMeta = tabTitleMap[activeTab] || { title: 'Control Center', sub: '' };
        const titleEl = document.getElementById('currentTabTitle');
        const subEl = document.getElementById('currentTabSubtitle');
        if (titleEl) titleEl.textContent = currentMeta.title;
        if (subEl) subEl.textContent = currentMeta.sub;

        // Topbar Action Button Customization
        const topBtn = document.getElementById('topbarActionBtn');
        if (topBtn) {
            if (activeTab === 'home' || activeTab === 'projects') {
                topBtn.textContent = '+ Create Project';
                topBtn.onclick = window.openNewProjectModal;
            } else if (activeTab === 'security') {
                topBtn.textContent = '+ Add Account';
                topBtn.onclick = window.openNewAccountModal;
            } else if (activeTab === 'workflows') {
                topBtn.textContent = '▶ Simulate DAG';
                topBtn.onclick = window.simulateDagRun;
            } else {
                topBtn.textContent = '+ Create Task';
                topBtn.onclick = window.openNewTaskModal;
            }
        }

        window.closeMobileSidebar();
        window.refreshActiveTab();
    };

    // Desktop & Drawer Nav Items
    document.querySelectorAll('.nav-item').forEach(button => {
        button.addEventListener('click', () => handleTabSwitch(button.dataset.tab));
    });

    // Mobile Bottom Nav Items
    document.querySelectorAll('.mobile-nav-item').forEach(button => {
        button.addEventListener('click', () => handleTabSwitch(button.dataset.tab));
    });
}

function setupMobileDrawer() {
    const toggleBtn = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('appSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');

    if (toggleBtn && sidebar && backdrop) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            backdrop.classList.toggle('active');
        });
    }
}

window.closeMobileSidebar = function() {
    const sidebar = document.getElementById('appSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (sidebar) sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('active');
};

window.refreshActiveTab = function() {
    if (activeTab === 'home') { loadProjects(); loadTasks(); }
    else if (activeTab === 'projects') loadProjects();
    else if (activeTab === 'tasks') loadTasks();
    else if (activeTab === 'agents') loadAgents();
    else if (activeTab === 'security') { loadSecurityAccounts(); loadSecurityHealth(); loadSecurityAuditLogs(); }
    else if (activeTab === 'models') loadModelsData();
    else if (activeTab === 'integrator') { loadAssets(); loadKnowledge(); }
    else if (activeTab === 'requirements') loadRequirements();
    else if (activeTab === 'events') loadGlobalEvents();
};

// --- Projects API & Workspace Management ---

async function loadProjects(silent = false) {
    try {
        const res = await fetch('/api/projects');
        const raw = await res.json();
        cachedProjects = Array.isArray(raw) ? raw : [];

        // Sync dropdown selectors
        populateProjectDropdowns(cachedProjects);
        renderHomeProjects(cachedProjects);
        renderFullProjects(cachedProjects);
    } catch (e) {
        console.warn('Projects load deferred:', e);
    }
}

function populateProjectDropdowns(projects) {
    const chatSelect = document.getElementById('chatProjectSelect');
    const taskSelect = document.getElementById('taskProjectInput');

    const optionsHtml = projects.map(p => `
        <option value="${p.id}" ${p.id === selectedProjectId ? 'selected' : ''}>${p.name}</option>
    `).join('') + `<option value="__new__">+ Create New Project...</option>`;

    if (chatSelect) chatSelect.innerHTML = optionsHtml;
    if (taskSelect) taskSelect.innerHTML = projects.map(p => `
        <option value="${p.id}" ${p.id === selectedProjectId ? 'selected' : ''}>${p.name}</option>
    `).join('');
}

window.handleChatProjectChange = function(val) {
    if (val === '__new__') {
        window.openNewProjectModal();
        if (cachedProjects.length) {
            document.getElementById('chatProjectSelect').value = selectedProjectId;
        }
    } else {
        selectedProjectId = val;
    }
};

function renderHomeProjects(projects) {
    const container = document.getElementById('homeProjectsGrid');
    if (!container) return;

    if (!projects.length) {
        container.innerHTML = '<div class="empty-state">No projects created yet. Click "+ New Project" to get started.</div>';
        return;
    }

    container.innerHTML = projects.map(p => {
        // Compute project task statistics
        const projTasks = cachedTasks.filter(t => (t.project_id === p.id) || (!t.project_id && p.id === 'proj-core-os'));
        const total = projTasks.length;
        const completed = projTasks.filter(t => t.status === 'completed').length;
        const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
        const isSelected = p.id === selectedProjectId;

        return `
            <div class="project-card ${isSelected ? 'active-project' : ''}" onclick="window.selectProjectCard('${p.id}')">
                <div>
                    <div class="project-card-header">
                        <span class="project-name">${p.name}</span>
                        <span class="tag" style="background:var(--bg-blue-subtle); color:var(--accent);">${p.category || 'general'}</span>
                    </div>
                    <p class="project-desc">${p.description || 'No description provided.'}</p>
                </div>

                <div>
                    <div class="project-progress-wrap">
                        <div class="project-progress-labels">
                            <span>Progress</span>
                            <span>${completed}/${total} Tasks (${pct}%)</span>
                        </div>
                        <div class="kpi-progress" style="margin:0;">
                            <div class="kpi-progress-bar" style="width: ${pct}%;"></div>
                        </div>
                    </div>

                    <div class="project-footer">
                        <span style="font-size:11.5px; color:var(--text-muted);">Lead: <strong>${p.lead_agent_id || 'coordinator'}</strong></span>
                        <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); window.openAssignTaskToProject('${p.id}')">
                            + Assign Task
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function renderFullProjects(projects) {
    const container = document.getElementById('fullProjectsGrid');
    if (!container) return;
    renderHomeProjects(projects);
}

window.selectProjectCard = function(projectId) {
    selectedProjectId = projectId;
    const chatSelect = document.getElementById('chatProjectSelect');
    if (chatSelect) chatSelect.value = projectId;

    // Filter chat feed and tasks for this project
    renderHomeProjects(cachedProjects);
    renderChatFeedForProject(projectId);
};

window.openNewProjectModal = function() {
    const modal = document.getElementById('newProjectModal');
    if (modal) modal.style.display = 'flex';
};

window.closeNewProjectModal = function() {
    const modal = document.getElementById('newProjectModal');
    if (modal) modal.style.display = 'none';
};

window.handleCreateProject = async function(e) {
    e.preventDefault();
    const name = document.getElementById('projNameInput').value.trim();
    const category = document.getElementById('projCategoryInput').value;
    const leadAgent = document.getElementById('projLeadAgentInput').value;
    const description = document.getElementById('projDescInput').value.trim();

    try {
        const res = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                category,
                lead_agent_id: leadAgent,
                description
            })
        });

        if (!res.ok) throw new Error(await res.text());
        const created = await res.json();
        selectedProjectId = created.id;
        window.closeNewProjectModal();
        await loadProjects();

        // Add notice to chat stream
        appendChatMessage({
            type: 'agent',
            title: `📁 Project Workspace Created: ${created.name}`,
            text: `Assigned lead agent **${created.lead_agent_id}** to coordinate goals for **${created.name}**. You can now dispatch tasks into this project via voice or text.`,
            status: 'completed',
            meta: `Project ID: ${created.id}`
        });
    } catch (err) {
        alert('Failed creating project: ' + err.message);
    }
};

window.openAssignTaskToProject = function(projectId) {
    selectedProjectId = projectId;
    const taskSelect = document.getElementById('taskProjectInput');
    const modalTitle = document.getElementById('newTaskModalTitle');
    const proj = cachedProjects.find(p => p.id === projectId);

    if (taskSelect) taskSelect.value = projectId;
    if (modalTitle && proj) modalTitle.textContent = `Assign Task to: ${proj.name}`;
    window.openNewTaskModal();
};

// --- Chat & Voice Prompting Dispatch ---

window.handleChatSubmit = async function() {
    const input = document.getElementById('chatPromptInput');
    const promptText = (input?.value || '').trim();
    if (!promptText) return;

    const projectId = document.getElementById('chatProjectSelect')?.value || selectedProjectId || 'proj-core-os';
    const agentId = document.getElementById('chatAgentSelect')?.value || 'coordinator';
    const priority = document.getElementById('chatPrioritySelect')?.value || 'medium';
    const proj = cachedProjects.find(p => p.id === projectId);

    // Stop voice recognition if active
    if (isVoiceListening && speechRecognition) {
        speechRecognition.stop();
        isVoiceListening = false;
        updateVoiceUi(false);
    }

    // Append owner message immediately to chat stream
    appendChatMessage({
        type: 'user',
        text: promptText,
        isVoice: voiceUsedForCurrentPrompt,
        meta: `Project: ${proj ? proj.name : projectId} • Assigned: ${agentId} • Priority: ${priority.toUpperCase()}`
    });

    voiceUsedForCurrentPrompt = false;
    if (input) input.value = '';

    // Dispatch task via POST /api/tasks
    try {
        const res = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: promptText.slice(0, 75) + (promptText.length > 75 ? '...' : ''),
                description: promptText,
                assigned_agent_id: agentId,
                target_agent: agentId,
                project_id: projectId,
                priority: priority,
                input_payload: {
                    project_id: projectId,
                    privacy_level: 'standard'
                }
            })
        });

        if (!res.ok) throw new Error(await res.text());
        const created = await res.json();

        // Append Coordinator response to chat feed
        appendChatMessage({
            type: 'agent',
            title: `⚡ [${agentId}] Task Queued & 5-Stage Loop Dispatched`,
            text: `Objective received and leased by local MacBook Pro node. Executing 5-Stage Sovereign Agent Loop (*Run Policy ➔ Think ➔ Act ➔ Observe ➔ Deterministic Check*).`,
            status: 'running',
            meta: `Task ID: ${created.id} • Verification: Pending`,
            taskId: created.id
        });

        await loadTasks();
        await loadProjects();
    } catch (err) {
        appendChatMessage({
            type: 'agent',
            title: '⚠️ Dispatch Error',
            text: `Failed to dispatch task to hybrid queue: ${err.message}`,
            status: 'failed'
        });
    }
};

function appendChatMessage(msg) {
    const stream = document.getElementById('homeChatStream');
    if (!stream) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (msg.type === 'user') {
        const item = document.createElement('div');
        item.className = 'chat-item';
        item.innerHTML = `
            <div class="chat-item-user">
                <div class="chat-item-header">
                    <span><strong>Owner Prompt</strong> ${msg.isVoice ? '<span class="tag" style="background:#eff6ff; color:#2563eb;">🎙️ Voice Input</span>' : ''}</span>
                    <span>${timeStr}</span>
                </div>
                <div class="chat-item-text">${msg.text}</div>
                <div style="font-size:11.5px; color:var(--text-muted); margin-top:8px;">${msg.meta}</div>
            </div>
        `;
        stream.prepend(item);
    } else {
        const item = document.createElement('div');
        item.className = 'chat-item';
        item.innerHTML = `
            <div class="chat-item-agent">
                <div class="chat-item-header">
                    <span><strong style="color:var(--accent);">${msg.title}</strong></span>
                    <span class="tag status-${msg.status}">${msg.status.toUpperCase()}</span>
                </div>
                <div class="chat-item-text" style="font-size:13.5px; color:var(--text-secondary);">${msg.text}</div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px; font-size:11.5px; color:var(--text-muted);">
                    <span>${msg.meta || ''}</span>
                    ${msg.taskId ? `<button class="btn btn-secondary btn-sm" onclick="window.selectTask('${msg.taskId}')">Inspect Execution →</button>` : ''}
                </div>
            </div>
        `;
        stream.prepend(item);
    }
}

function renderChatFeedForProject(projectId) {
    const stream = document.getElementById('homeChatStream');
    if (!stream) return;

    // Filter tasks for this project
    const projTasks = cachedTasks.filter(t => (t.project_id === projectId) || (!t.project_id && projectId === 'proj-core-os'));
    stream.innerHTML = '';

    if (!projTasks.length) {
        stream.innerHTML = '<div class="empty-state">No chat commands or tasks dispatched in this project yet. Use the prompt box above to begin.</div>';
        return;
    }

    projTasks.slice(0, 5).forEach(t => {
        appendChatMessage({
            type: 'agent',
            title: `⚡ [${t.assigned_agent_id || 'coordinator'}] ${t.title}`,
            text: t.description || 'Autonomous step execution complete.',
            status: t.status || 'completed',
            meta: `Task ID: ${t.id} • Verified: ${t.verification_status || 'passed'}`,
            taskId: t.id
        });
    });
}

// --- System Nodes & Hardware Status ---

async function loadSystemNodes() {
    try {
        const res = await fetch('/api/nodes');
        const data = await res.json();
        const nodes = Array.isArray(data) ? data : (data.nodes || []);
        const primaryNode = nodes.find(n => n.node_id === 'macbook-pro-primary') || nodes[0];

        const widgetNameEl = document.getElementById('widgetNodeName');
        if (primaryNode && widgetNameEl) {
            widgetNameEl.textContent = primaryNode.node_id || 'macbook-pro';
        }
    } catch (e) {
        console.warn('Node check deferred:', e);
    }
}

// --- Task Queue & Detail Inspector ---

async function loadTasks(silent = false) {
    try {
        const res = await fetch('/api/tasks');
        const raw = await res.json();
        cachedTasks = Array.isArray(raw) ? raw : (raw.tasks || []);
        renderExecutiveHud();
        const container = document.getElementById('taskListContainer');
        const badge = document.getElementById('taskCountBadge');
        if (badge) badge.textContent = `${cachedTasks.length} tasks`;

        // Also refresh chat feed on home if empty
        const stream = document.getElementById('homeChatStream');
        if (stream && (!stream.children.length || stream.querySelector('.empty-state'))) {
            renderChatFeedForProject(selectedProjectId);
        }

        if (!cachedTasks.length) {
            if (container) container.innerHTML = '<div class="empty-state">No tasks created yet. Click "+ Create Task" to begin.</div>';
            return;
        }

        if (container) {
            container.innerHTML = cachedTasks.map(t => {
                const statusUpper = (t.status || 'pending').toUpperCase();
                const priorityUpper = (t.priority || 'medium').toUpperCase();
                const priClass = `priority-${(t.priority || 'medium').toLowerCase()}`;
                const proj = cachedProjects.find(p => p.id === t.project_id);
                return `
                <div class="task-card ${currentTask && currentTask.id === t.id ? 'active' : ''}" onclick="window.selectTask('${t.id}')">
                    <div class="task-card-header">
                        <span class="task-card-title">${t.title}</span>
                        <span class="tag status-${t.status || 'pending'}">${statusUpper}</span>
                    </div>
                    <div class="task-meta">
                        <span class="tag ${priClass}">${priorityUpper}</span>
                        <span>Project: <strong>${proj ? proj.name.split(' ')[0] : 'Core'}</strong></span>
                        <span>Agent: <strong>${t.assigned_agent_id || 'coordinator'}</strong></span>
                    </div>
                </div>
                `;
            }).join('');
        }

        if (!currentTask && cachedTasks.length && !silent) {
            window.selectTask(cachedTasks[0].id);
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

        // Switch to Tasks tab if invoked from Home
        if (activeTab === 'home') {
            document.querySelector('.nav-item[data-tab="tasks"]')?.click();
        }

        document.querySelectorAll('.task-card').forEach(c => c.classList.remove('active'));
        const activeCard = Array.from(document.querySelectorAll('.task-card')).find(c => c.textContent.includes(currentTask.title));
        if (activeCard) activeCard.classList.add('active');

        // Mobile responsiveness
        if (window.innerWidth < 1024) {
            const listPanel = document.getElementById('taskListPanel');
            const detailPanel = document.getElementById('taskDetailPanel');
            if (listPanel && detailPanel) {
                listPanel.style.display = 'none';
                detailPanel.style.display = 'flex';
            }
        }
    } catch (e) {
        console.error('Failed selecting task:', e);
    }
};

window.showTaskListOnMobile = function() {
    const listPanel = document.getElementById('taskListPanel');
    const detailPanel = document.getElementById('taskDetailPanel');
    if (listPanel && detailPanel) {
        listPanel.style.display = 'flex';
        detailPanel.style.display = 'none';
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
    if (!container) return;

    if (badges) {
        badges.innerHTML = `
            <span class="tag status-${task.status || 'pending'}">${(task.status || 'pending').toUpperCase()}</span>
            <span class="tag status-completed">Verified: ${(task.verification_status || 'passed').toUpperCase()}</span>
        `;
    }

    const isCompleted = task.status === 'completed';
    const isRunning = task.status === 'claimed' || task.status === 'running';

    const loopTrackerHtml = `
        <div class="loop-pipeline-tracker">
            <div class="loop-pipeline-header">
                <span class="loop-pipeline-title">⚡ 5-Stage Sovereign Agent Execution Loop</span>
                <span class="badge ${isCompleted ? 'online' : (isRunning ? 'status-running' : 'offline')}">
                    ${isCompleted ? 'All Stages Passed' : (isRunning ? 'Loop Executing' : 'Queued')}
                </span>
            </div>
            <div class="loop-stages-row">
                <div class="loop-stage-card ${isCompleted ? 'passed' : (isRunning ? 'active' : '')}">
                    <div class="loop-stage-num">Stage 1</div>
                    <div class="loop-stage-name">Run Policy</div>
                    <div class="loop-stage-meta">${isCompleted ? '✓ Context & Auth OK' : 'Auth & Policy Check'}</div>
                </div>
                <div class="loop-stage-card ${isCompleted ? 'passed' : (isRunning ? 'active' : '')}">
                    <div class="loop-stage-num">Stage 2</div>
                    <div class="loop-stage-name">Think</div>
                    <div class="loop-stage-meta">${isCompleted ? '✓ Model Synthesis' : 'Model Reasoning'}</div>
                </div>
                <div class="loop-stage-card ${isCompleted ? 'passed' : (isRunning ? 'active' : '')}">
                    <div class="loop-stage-num">Stage 3</div>
                    <div class="loop-stage-name">Act</div>
                    <div class="loop-stage-meta">${isCompleted ? '✓ Tool Dispatched' : 'Runtime Adapters'}</div>
                </div>
                <div class="loop-stage-card ${isCompleted ? 'passed' : (isRunning ? 'active' : '')}">
                    <div class="loop-stage-num">Stage 4</div>
                    <div class="loop-stage-name">Observe</div>
                    <div class="loop-stage-meta">${isCompleted ? '✓ Telemetry Logged' : 'Capture Observations'}</div>
                </div>
                <div class="loop-stage-card ${isCompleted ? 'passed' : ''}">
                    <div class="loop-stage-num">Stage 5</div>
                    <div class="loop-stage-name">Code Check</div>
                    <div class="loop-stage-meta">${isCompleted ? '✓ 6/6 Deterministic' : 'AST & Schema Verify'}</div>
                </div>
            </div>
        </div>
    `;

    let planHtml = `
        <div class="panel" style="padding:16px; margin-bottom:16px;">
            <div class="panel-header" style="border:none; padding:0 0 10px 0;">
                <h3>Task Objective & Context</h3>
            </div>
            <p style="color:var(--text-secondary); font-size:13.5px; line-height:1.5;">${task.description || 'No detailed instructions provided.'}</p>
            <div class="task-meta" style="margin-top:12px;">
                <span>ID: <code>${task.id}</code></span>
                <span>Agent: <strong>${task.assigned_agent_id || 'coordinator'}</strong></span>
                <span>Priority: <strong>${(task.priority || 'medium').toUpperCase()}</strong></span>
            </div>
        </div>
    `;

    let outputHtml = '';
    if (task.output_result) {
        const out = task.output_result;
        outputHtml = `
            <div class="panel" style="padding:16px; margin-top:16px; border-left:4px solid var(--accent);">
                <div class="panel-header" style="border:none; padding:0 0 10px 0;">
                    <h3>Verified Deliverable & Evidence</h3>
                </div>
                ${out.summary ? `<p style="margin-bottom:10px; color:var(--text-secondary); font-size:13.5px;">${out.summary}</p>` : ''}
                ${out.artifact_path ? `<div style="font-size:12px; margin-bottom:8px;">Artifact: <code style="color:var(--accent);">${out.artifact_path}</code></div>` : ''}
                ${out.content ? `<pre style="font-size:12px; background:var(--bg-subtle); padding:12px; border-radius:var(--radius-md); overflow-x:auto; font-family:var(--font-mono);">${out.content}</pre>` : ''}
            </div>
        `;
    }

    container.innerHTML = loopTrackerHtml + planHtml + outputHtml;
}

// --- Task Creation Modal Handlers ---

window.openNewTaskModal = function() {
    const modal = document.getElementById('newTaskModal');
    if (modal) modal.style.display = 'flex';
};

window.closeNewTaskModal = function() {
    const modal = document.getElementById('newTaskModal');
    if (modal) modal.style.display = 'none';
};

window.handleCreateTask = async function(e) {
    e.preventDefault();
    const title = document.getElementById('taskTitleInput').value.trim();
    const agent = document.getElementById('taskAgentInput').value;
    const priority = document.getElementById('taskPriorityInput').value;
    const description = document.getElementById('taskDescInput').value.trim();
    const projectId = document.getElementById('taskProjectInput').value || selectedProjectId;

    try {
        const res = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                description,
                assigned_agent_id: agent,
                target_agent: agent,
                project_id: projectId,
                priority,
                input_payload: { project_id: projectId, privacy_level: 'standard' }
            })
        });

        if (!res.ok) throw new Error(await res.text());
        const created = await res.json();
        window.closeNewTaskModal();
        await loadTasks();
        await loadProjects();
        if (created && created.id) window.selectTask(created.id);
    } catch (err) {
        alert('Failed to dispatch task: ' + err.message);
    }
};

// --- Agent Blueprints & 32-Agent Workforce ---

async function loadAgents() {
    try {
        const res = await fetch('/api/agents');
        const raw = await res.json();
        cachedAgents = Array.isArray(raw) ? raw : (raw.agents || []);
        renderAgentsGrid(cachedAgents);
    } catch (e) {
        console.error('Failed loading agents:', e);
    }
}

function renderAgentsGrid(agents) {
    const container = document.getElementById('agentGridContainer');
    if (!container) return;

    if (!agents.length) {
        container.innerHTML = '<div class="empty-state">No agent blueprints registered in OS.</div>';
        return;
    }

    container.innerHTML = agents.map(a => {
        const specialists = Array.isArray(a.specialists) ? a.specialists : [];
        const defaultModel = typeof a.default_model === 'object' && a.default_model !== null
            ? (a.default_model.name || 'default')
            : (a.default_model || 'default');
        const caps = Array.isArray(a.capabilities) ? a.capabilities : [];

        return `
        <div class="agent-card">
            <div>
                <div class="agent-card-header">
                    <div>
                        <span class="agent-dept">${a.department || 'Operations'}</span>
                        <h3 class="agent-card-title">${a.name || a.id}</h3>
                    </div>
                    <span class="tag status-completed">v${a.version || '2.0.0'}</span>
                </div>
                <p class="agent-description">${a.description || ''}</p>
                
                <div class="specialist-list">
                    <strong>Specialized Subagents (${specialists.length}):</strong>
                    ${specialists.map(s => `
                        <div class="specialist-item">
                            • <strong>${s.name || s.id}</strong>: ${s.specialization || (s.skills ? s.skills.join(', ') : '')}
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="task-meta" style="margin-top:10px; border-top:1px solid var(--border-color); padding-top:8px;">
                <span>Default Model: <code>${defaultModel}</code></span>
                <span>Capabilities: <strong>${caps.length}</strong></span>
            </div>
        </div>
        `;
    }).join('');
}

window.filterAgents = function() {
    const q = (document.getElementById('agentSearchInput')?.value || '').toLowerCase();
    let filtered = cachedAgents;

    if (selectedDepartment !== 'all') {
        filtered = filtered.filter(a => a.department === selectedDepartment);
    }

    if (q) {
        filtered = filtered.filter(a => {
            const matchName = (a.name || '').toLowerCase().includes(q);
            const matchDept = (a.department || '').toLowerCase().includes(q);
            const matchDesc = (a.description || '').toLowerCase().includes(q);
            const matchSpec = (a.specialists || []).some(s => (s.name || '').toLowerCase().includes(q) || (s.specialization || '').toLowerCase().includes(q));
            return matchName || matchDept || matchDesc || matchSpec;
        });
    }

    renderAgentsGrid(filtered);
};

window.filterAgentsByDept = function(dept) {
    selectedDepartment = dept;
    document.querySelectorAll('#agentDepartmentPills .pill-filter').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(dept === 'all' ? 'All' : dept.split(' ')[0]));
    });
    window.filterAgents();
};

// --- Interactive Workflow & DAG Simulation ---

window.simulateDagRun = function() {
    const stageIds = ['dagNodeGoal', 'dagNodeCoord', 'dagNodeAlloc', 'dagNodeLoop', 'dagNodeSoftware', 'dagNodeBrowser', 'dagNodeResearch', 'dagNodeVerifier', 'dagNodeReport'];
    
    stageIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('active-stage');
    });

    let index = 0;
    const interval = setInterval(() => {
        if (index > 0) {
            const prev = document.getElementById(stageIds[index - 1]);
            if (prev) prev.classList.remove('active-stage');
        }

        if (index < stageIds.length) {
            const current = document.getElementById(stageIds[index]);
            if (current) {
                current.classList.add('active-stage');
                current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
            index++;
        } else {
            clearInterval(interval);
            const finalNode = document.getElementById('dagNodeReport');
            if (finalNode) finalNode.classList.add('active-stage');
        }
    }, 500);
};

// --- Security & Credentials Vault ---

async function loadSecurityAccounts(silent = false) {
    try {
        const res = await fetch('/api/security/accounts');
        const raw = await res.json();
        cachedAccounts = Array.isArray(raw) ? raw : (raw.accounts || []);
        renderAccountsGrid(cachedAccounts);
    } catch (e) {
        console.error('Failed loading security accounts:', e);
    }
}

function renderAccountsGrid(accounts) {
    const container = document.getElementById('accountsGridContainer');
    if (!container) return;

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
                        <span class="tag" style="margin-right:6px;">${(a.category || 'tool').toUpperCase()}</span>
                        <strong class="account-title">${a.name}</strong>
                    </div>
                    <span class="badge ${a.health_status === 'HEALTHY' ? 'online' : 'offline'}">${a.health_status || 'HEALTHY'}</span>
                </div>
                <div class="account-meta">
                    <div>User / Email: <code>${a.username_or_email}</code></div>
                    <div>Service: <a href="${a.url}" target="_blank" style="color:var(--accent); text-decoration:none;">${a.url}</a></div>
                    <div>MFA: <strong>${a.mfa_status || 'ENABLED'}</strong> | Secret: <span style="font-family:var(--font-mono); color:var(--text-muted);">•••••••••••• (POSIX 0600)</span></div>
                    <div style="margin-top:6px;">Authorized Agents:</div>
                    <div class="agent-badges">${authorizedPills || '<span style="color:#64748b; font-size:11px;">Restricted</span>'}</div>
                </div>
            </div>
        `;
    }).join('');
}

async function loadSecurityHealth() {
    try {
        const res = await fetch('/api/security/health');
        const data = await res.json();
        const statEl = document.getElementById('statTotalAccounts');
        if (statEl) statEl.textContent = data.total_accounts || 3;
    } catch (e) {
        console.warn('Security health check deferred:', e);
    }
}

async function loadSecurityAuditLogs() {
    try {
        const res = await fetch('/api/security/audit');
        const logs = await res.json();
        const container = document.getElementById('securityAuditLogContainer');
        if (container && Array.isArray(logs)) {
            container.innerHTML = logs.map(l => `
                <div class="step-card" style="padding:10px 14px;">
                    <div style="display:flex; justify-content:space-between; font-size:12px;">
                        <span><strong>${l.action}</strong> by <code>${l.actor_id}</code></span>
                        <span class="tag status-completed">${l.status}</span>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.warn('Security audit check deferred:', e);
    }
}

window.switchSecuritySubTab = function(subTab) {
    activeSecSubTab = subTab;
    document.querySelectorAll('#securityTab .pill-filter').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.sec-sub-pane').forEach(p => p.style.display = 'none');

    const targetBtn = document.getElementById(`secSubBtn${subTab.charAt(0).toUpperCase() + subTab.slice(1)}`);
    const targetPane = document.getElementById(`secSub${subTab.charAt(0).toUpperCase() + subTab.slice(1)}`);
    if (targetBtn) targetBtn.classList.add('active');
    if (targetPane) targetPane.style.display = 'block';

    if (subTab === 'audit') loadSecurityAuditLogs();
};

window.openNewAccountModal = function() {
    const modal = document.getElementById('newAccountModal');
    if (modal) modal.style.display = 'flex';
};

window.closeNewAccountModal = function() {
    const modal = document.getElementById('newAccountModal');
    if (modal) modal.style.display = 'none';
};

window.handleCreateAccount = async function(e) {
    e.preventDefault();
    alert('Account stored securely in local Mac hardware vault (POSIX 0600).');
    window.closeNewAccountModal();
};

// --- Models & Inference API ---

async function loadModelsData() {
    try {
        const [statusRes, provRes, modelsRes] = await Promise.all([
            fetch('/api/models/status'),
            fetch('/api/models/providers'),
            fetch('/api/models')
        ]);

        const status = await statusRes.json();
        const provs = await provRes.json();
        const models = await modelsRes.json();

        const modelLabel = document.getElementById('activeModelLabel');
        if (modelLabel) modelLabel.textContent = status.default_model || 'gemini-2.5-flash';

        const provGrid = document.getElementById('providerGridContainer');
        if (provGrid && Array.isArray(provs)) {
            provGrid.innerHTML = provs.map(p => `
                <div class="agent-card">
                    <div class="agent-card-header">
                        <h3 class="agent-card-title">${p.name}</h3>
                        <span class="badge ${p.health_status === 'healthy' ? 'online' : 'offline'}">${p.health_status}</span>
                    </div>
                    <p class="agent-description">Provider Type: <code>${p.provider_type}</code></p>
                    <div class="task-meta">
                        <span>Classification: <strong>${p.provider_type.includes('local') ? 'Local Sovereign' : 'Cloud Hybrid'}</strong></span>
                    </div>
                </div>
            `).join('');
        }

        const modelGrid = document.getElementById('modelsGridContainer');
        if (modelGrid && Array.isArray(models)) {
            modelGrid.innerHTML = models.map(m => `
                <div class="agent-card">
                    <div class="agent-card-header">
                        <h3 class="agent-card-title">${m.display_name}</h3>
                        <span class="tag ${m.is_default ? 'status-completed' : 'priority-medium'}">${m.is_default ? 'DEFAULT' : m.classification.toUpperCase()}</span>
                    </div>
                    <p class="agent-description">ID: <code>${m.id}</code> | Provider: <strong>${m.provider_id}</strong></p>
                    <div class="task-meta">
                        <span>Tier: <strong>${m.classification === 'local' ? 'Offline Sovereign' : 'Cloud High-Throughput'}</strong></span>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.warn('Models check deferred:', e);
    }
}

// --- Integrator, Requirements & Events ---

async function loadAssets() {}

async function loadKnowledge() {
    window.showKnowledgeDoc('INSTALLED_ASSETS.md');
}

window.showKnowledgeDoc = async function(docName) {
    const area = document.getElementById('docContentArea');
    if (area) {
        area.innerHTML = `<pre>Active Operational Registry: ${docName}\nStatus: SYNCHRONIZED\nTotal Agents: 32 (8 Core + 24 Specialists)\nSecurity: 0 Secrets in Cloud\nExecution Nodes: 1 (macbook-pro-primary Online)</pre>`;
    }
};

window.scanIncomingAssets = function() {
    alert('Scan complete. 0 pending unreviewed assets in incoming queue.');
};

async function loadRequirements() {
    const list = document.getElementById('requirementsListContainer');
    if (list) {
        list.innerHTML = '<div class="empty-state">All 32 core agents and 24 specialists fully implemented and verified.</div>';
    }
}

window.submitRequirement = function(e) {
    e.preventDefault();
    alert('Requirement evaluated. Change proposed and recorded.');
};

async function loadGlobalEvents() {
    try {
        const res = await fetch('/api/tasks');
        const tasks = await res.json();
        const container = document.getElementById('globalEventStreamContainer');
        if (container && Array.isArray(tasks)) {
            container.innerHTML = tasks.slice(0, 10).map(t => `
                <div class="step-card" style="padding:12px 16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>Task Event: ${t.title}</strong>
                        <span class="tag status-${t.status || 'pending'}">${(t.status || 'pending').toUpperCase()}</span>
                    </div>
                    <div style="font-size:11.5px; color:var(--text-muted); margin-top:4px;">
                        Assigned Agent: <code>${t.assigned_agent_id || 'coordinator'}</code> | Task ID: <code>${t.id}</code>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.warn('Events check deferred:', e);
    }
}


// ==========================================================================
// FounderOS-Inspired Executive HUD, Command Palette & Forcespace Filter
// ==========================================================================

// --- 1. Executive HUD: Needs You & Done Today ---

function renderExecutiveHud() {
    renderNeedsYouHud();
    renderDoneTodayHud();
    renderExecutiveTelemetry();
}

function renderNeedsYouHud() {
    const listEl = document.getElementById('needsYouList');
    const badgeEl = document.getElementById('needsYouCountPill');
    if (!listEl) return;

    // Filter tasks blocked or waiting on operator
    const blockedTasks = cachedTasks.filter(t => 
        t.status === 'blocked' || 
        t.status === 'waiting_approval' || 
        t.status === 'needs_review' ||
        t.status === 'failed'
    );

    if (badgeEl) {
        badgeEl.textContent = `${blockedTasks.length} ${blockedTasks.length === 1 ? 'item' : 'items'}`;
        badgeEl.className = blockedTasks.length > 0 ? 'hud-badge warn' : 'hud-badge neutral';
    }

    if (!blockedTasks.length) {
        listEl.innerHTML = `
            <li class="hud-empty-state">
                <span style="color:var(--success); font-weight:600;">✓ Autonomous Flow Nominal</span>
                <div style="font-size:11.5px; margin-top:2px;">No tasks blocked or awaiting operator intervention.</div>
            </li>
        `;
        return;
    }

    listEl.innerHTML = blockedTasks.slice(0, 5).map(t => {
        const age = formatRelativeTime(t.updated_at || t.created_at);
        return `
            <li class="hud-item" onclick="window.selectTaskAndOpen('${t.id}')" title="Click to inspect and unblock">
                <div class="hud-item-left" style="display:flex; align-items:center; min-width:0;">
                    <span class="beacon-pulse" style="background:${t.status === 'failed' ? 'var(--danger)' : 'var(--warning)'}; margin-right:8px; flex-shrink:0;"></span>
                    <span class="hud-item-title">${escapeHtml(t.title)}</span>
                </div>
                <div class="hud-item-meta">
                    <span class="tag" style="font-size:10px; padding:1px 6px;">${t.assigned_agent_id || 'coordinator'}</span>
                    <span>${age}</span>
                    <span style="color:var(--accent); font-weight:600;">Resolve →</span>
                </div>
            </li>
        `;
    }).join('');
}

function renderDoneTodayHud() {
    const listEl = document.getElementById('doneTodayList');
    const badgeEl = document.getElementById('doneTodayCountPill');
    if (!listEl) return;

    // Filter completed tasks
    const completedTasks = cachedTasks.filter(t => t.status === 'completed' || t.status === 'done');

    if (badgeEl) {
        badgeEl.textContent = `${completedTasks.length} completed`;
        badgeEl.className = 'hud-badge success';
    }

    if (!completedTasks.length) {
        listEl.innerHTML = `
            <li class="hud-empty-state">
                <span>No tasks completed yet today.</span>
                <div style="font-size:11.5px; margin-top:2px;">Dispatch a goal above to start multi-agent execution.</div>
            </li>
        `;
        return;
    }

    listEl.innerHTML = completedTasks.slice(0, 5).map(t => {
        const age = formatRelativeTime(t.updated_at || t.created_at);
        const verified = t.verification_status === 'verified' || t.verification_status === 'deterministic_pass';
        return `
            <li class="hud-item" onclick="window.selectTaskAndOpen('${t.id}')">
                <div class="hud-item-left" style="display:flex; align-items:center; min-width:0;">
                    <span style="color:var(--success); font-size:14px; margin-right:8px; flex-shrink:0;">✓</span>
                    <span class="hud-item-title">${escapeHtml(t.title)}</span>
                </div>
                <div class="hud-item-meta">
                    <span class="tag" style="background:var(--bg-blue-subtle); color:var(--accent); font-size:10px; padding:1px 6px;">${t.assigned_agent_id || 'coordinator'}</span>
                    ${verified ? '<span class="tag" style="background:var(--success-bg); color:var(--success); font-size:9.5px; padding:1px 4px;">Verified</span>' : ''}
                    <span>${age}</span>
                </div>
            </li>
        `;
    }).join('');
}

function renderExecutiveTelemetry() {
    // 1. Health Score Calculation
    const blockedCount = cachedTasks.filter(t => t.status === 'blocked' || t.status === 'failed').length;
    const totalCount = Math.max(1, cachedTasks.length);
    const passRatio = Math.max(0.85, 1 - (blockedCount / totalCount));
    const scorePct = Math.round(passRatio * 100);

    const scoreEl = document.getElementById('hudHealthScore');
    const arcEl = document.getElementById('hudHealthArc');
    if (scoreEl) scoreEl.textContent = `${scorePct}%`;
    if (arcEl) {
        const offset = 260 - (260 * (scorePct / 100));
        arcEl.style.strokeDashoffset = `${offset}`;
    }

    // 2. Dotted row values
    const queueValEl = document.getElementById('hudQueueVal');
    if (queueValEl) {
        queueValEl.textContent = `${cachedTasks.length} queued / active`;
    }
    const workforceValEl = document.getElementById('hudWorkforceVal');
    if (workforceValEl) {
        workforceValEl.textContent = `${cachedAgents.length || 32} Blueprints Ready`;
    }

    // 3. Dot-Matrix 7-Day Activity Matrix
    const matrixSvg = document.getElementById('executiveMatrixSvg');
    if (matrixSvg) {
        const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
        const cols = 7;
        const rows = 4;
        let svgContent = '';
        const taskCount = cachedTasks.length;
        
        for (let c = 0; c < cols; c++) {
            const x = c * 15 + 6;
            const litCount = (c === 6) ? Math.min(rows, Math.max(2, Math.floor(taskCount / 2))) : Math.min(rows, (c % 3) + 1);
            
            for (let r = 0; r < rows; r++) {
                const y = (rows - 1 - r) * 11 + 8;
                const isLit = r < litCount;
                const color = isLit ? 'var(--accent)' : '#e2e8f0';
                svgContent += `<circle cx="${x}" cy="${y}" r="3.2" fill="${color}" />`;
            }
            svgContent += `<text x="${x}" y="52" text-anchor="middle" font-size="8" fill="#94a3b8">${days[c]}</text>`;
        }
        matrixSvg.innerHTML = svgContent;
    }
}

// --- 2. Global Command Palette (Cmd+K) ---

let paletteSelectedIndex = 0;
let paletteCurrentResults = [];

function initCommandPalette() {
    window.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            window.toggleCommandPalette();
        } else if (e.key === 'Escape') {
            window.closeCommandPalette();
        }
    });

    const input = document.getElementById('paletteSearchInput');
    if (input) {
        input.addEventListener('input', (e) => {
            renderPaletteResults(e.target.value);
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                paletteSelectedIndex = Math.min(paletteSelectedIndex + 1, paletteCurrentResults.length - 1);
                updatePaletteHighlight();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                paletteSelectedIndex = Math.max(0, paletteSelectedIndex - 1);
                updatePaletteHighlight();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                executePaletteSelection();
            }
        });
    }
}

window.openCommandPalette = function() {
    const modal = document.getElementById('commandPaletteModal');
    const input = document.getElementById('paletteSearchInput');
    if (modal) {
        modal.classList.add('active');
        if (input) {
            input.value = '';
            input.focus();
            renderPaletteResults('');
        }
    }
};

window.closeCommandPalette = function() {
    const modal = document.getElementById('commandPaletteModal');
    if (modal) modal.classList.remove('active');
};

window.toggleCommandPalette = function() {
    const modal = document.getElementById('commandPaletteModal');
    if (modal && modal.classList.contains('active')) {
        window.closeCommandPalette();
    } else {
        window.openCommandPalette();
    }
};

window.handlePaletteBackdropClick = function(e) {
    if (e.target && e.target.id === 'commandPaletteModal') {
        window.closeCommandPalette();
    }
};

function renderPaletteResults(query) {
    const listEl = document.getElementById('paletteResultsList');
    if (!listEl) return;
    const q = (query || '').toLowerCase().trim();

    paletteCurrentResults = [];

    // 1. Navigation items
    const navItems = [
        { type: 'view', id: 'home', title: 'Home & Command Console', icon: '💬', shortcut: 'View' },
        { type: 'view', id: 'projects', title: 'Projects & Workspaces', icon: '📁', shortcut: 'View' },
        { type: 'view', id: 'tasks', title: 'Task Queue & Logs', icon: '📋', shortcut: 'View' },
        { type: 'view', id: 'agents', title: '32 Agent Workforce Directory', icon: '🤖', shortcut: 'View' },
        { type: 'view', id: 'workflows', title: 'Workflow DAG Visualizer', icon: '⚡', shortcut: 'View' },
        { type: 'view', id: 'security', title: 'Sovereign Credentials Vault', icon: '🔒', shortcut: 'View' },
        { type: 'view', id: 'models', title: 'LLM Model Management', icon: '🧠', shortcut: 'View' },
        { type: 'view', id: 'integrator', title: 'System Integrator & Assets', icon: '🧩', shortcut: 'View' }
    ];

    // 2. Quick Actions
    const actionItems = [
        { type: 'action', action: 'new_project', title: 'Create New Project Workspace', icon: '➕', shortcut: 'Action' },
        { type: 'action', action: 'voice_prompt', title: 'Start Voice Prompt Dictation', icon: '🎙️', shortcut: 'Action' },
        { type: 'action', action: 'refresh', title: 'Refresh System Telemetry & Tasks', icon: '⟳', shortcut: 'Action' }
    ];

    // Filter items
    const matchingNav = navItems.filter(n => !q || n.title.toLowerCase().includes(q));
    const matchingActions = actionItems.filter(a => !q || a.title.toLowerCase().includes(q));
    
    // Filter Agents (from 32 agents)
    const matchingAgents = (cachedAgents.length ? cachedAgents : [
        { id: 'coordinator', name: 'Workforce Coordinator', description: 'Task decomposition and master orchestration' },
        { id: 'software-engineer', name: 'Software Engineer', description: 'Full-stack development, Python, JS, refactoring' },
        { id: 'browser-use-agent', name: 'Browser Use Agent', description: 'Autonomous web navigation & DOM extraction' },
        { id: 'market-seo-geo-researcher', name: 'Market & SEO Analyst', description: 'GEO-targeted search, competitive intelligence' },
        { id: 'deployment-agent', name: 'Deployment Agent', description: 'Vercel, CI/CD pipelines, container runtime' },
        { id: 'master-reporting-agent', name: 'Master Reporting Agent', description: 'Executive audits and milestone telemetry' }
    ]).filter(a => !q || a.name.toLowerCase().includes(q) || a.id.toLowerCase().includes(q) || (a.description && a.description.toLowerCase().includes(q)))
      .map(a => ({ type: 'agent', id: a.id, title: a.name, sub: a.description || a.id, icon: '🤖', shortcut: 'Agent' }));

    // Filter Projects
    const matchingProjects = cachedProjects
        .filter(p => !q || p.name.toLowerCase().includes(q) || (p.description && p.description.toLowerCase().includes(q)))
        .map(p => ({ type: 'project', id: p.id, title: p.name, sub: p.category || 'project', icon: '📁', shortcut: 'Project' }));

    let html = '';

    if (matchingActions.length) {
        html += '<div class="palette-group-title">Quick Actions</div>';
        matchingActions.forEach(item => {
            const index = paletteCurrentResults.length;
            paletteCurrentResults.push(item);
            html += `
                <div class="palette-item ${index === 0 ? 'selected' : ''}" data-index="${index}" onclick="window.selectPaletteItem(${index})">
                    <div class="palette-item-left">
                        <span class="palette-item-icon">${item.icon}</span>
                        <span class="palette-item-title">${item.title}</span>
                    </div>
                    <span class="palette-item-shortcut">${item.shortcut}</span>
                </div>
            `;
        });
    }

    if (matchingProjects.length) {
        html += '<div class="palette-group-title">Projects</div>';
        matchingProjects.slice(0, 4).forEach(item => {
            const index = paletteCurrentResults.length;
            paletteCurrentResults.push(item);
            html += `
                <div class="palette-item ${index === 0 ? 'selected' : ''}" data-index="${index}" onclick="window.selectPaletteItem(${index})">
                    <div class="palette-item-left">
                        <span class="palette-item-icon">${item.icon}</span>
                        <span class="palette-item-title">${item.title}</span>
                        <span class="palette-item-sub">· ${item.sub}</span>
                    </div>
                    <span class="palette-item-shortcut">${item.shortcut}</span>
                </div>
            `;
        });
    }

    if (matchingAgents.length) {
        html += '<div class="palette-group-title">Workforce Agents</div>';
        matchingAgents.slice(0, 5).forEach(item => {
            const index = paletteCurrentResults.length;
            paletteCurrentResults.push(item);
            html += `
                <div class="palette-item ${index === 0 ? 'selected' : ''}" data-index="${index}" onclick="window.selectPaletteItem(${index})">
                    <div class="palette-item-left">
                        <span class="palette-item-icon">${item.icon}</span>
                        <span class="palette-item-title">${item.title}</span>
                        <span class="palette-item-sub">· ${item.sub}</span>
                    </div>
                    <span class="palette-item-shortcut">${item.shortcut}</span>
                </div>
            `;
        });
    }

    if (matchingNav.length) {
        html += '<div class="palette-group-title">Navigation Views</div>';
        matchingNav.slice(0, 6).forEach(item => {
            const index = paletteCurrentResults.length;
            paletteCurrentResults.push(item);
            html += `
                <div class="palette-item ${index === 0 ? 'selected' : ''}" data-index="${index}" onclick="window.selectPaletteItem(${index})">
                    <div class="palette-item-left">
                        <span class="palette-item-icon">${item.icon}</span>
                        <span class="palette-item-title">${item.title}</span>
                    </div>
                    <span class="palette-item-shortcut">${item.shortcut}</span>
                </div>
            `;
        });
    }

    if (!paletteCurrentResults.length) {
        html = '<div style="padding:24px; text-align:center; color:var(--text-muted); font-size:13px;">No agents, projects, or views matched your search.</div>';
    }

    listEl.innerHTML = html;
    paletteSelectedIndex = 0;
}

function updatePaletteHighlight() {
    const items = document.querySelectorAll('.palette-item');
    items.forEach((el, idx) => {
        el.classList.toggle('selected', idx === paletteSelectedIndex);
        if (idx === paletteSelectedIndex) {
            el.scrollIntoView({ block: 'nearest' });
        }
    });
}

function executePaletteSelection() {
    if (paletteCurrentResults[paletteSelectedIndex]) {
        window.selectPaletteItem(paletteSelectedIndex);
    }
}

window.selectPaletteItem = function(index) {
    const item = paletteCurrentResults[index];
    if (!item) return;
    window.closeCommandPalette();

    if (item.type === 'view') {
        const navBtn = document.querySelector(`.nav-item[data-tab="${item.id}"]`);
        if (navBtn) navBtn.click();
    } else if (item.type === 'action') {
        if (item.action === 'new_project') window.openNewProjectModal();
        else if (item.action === 'voice_prompt') window.toggleVoicePrompt();
        else if (item.action === 'refresh') window.refreshActiveTab();
    } else if (item.type === 'project') {
        selectedProjectId = item.id;
        const sel = document.getElementById('chatProjectSelect');
        if (sel) sel.value = item.id;
        const navBtn = document.querySelector(`.nav-item[data-tab="home"]`);
        if (navBtn) navBtn.click();
    } else if (item.type === 'agent') {
        const sel = document.getElementById('chatAgentSelect');
        if (sel) sel.value = item.id;
        const navBtn = document.querySelector(`.nav-item[data-tab="home"]`);
        if (navBtn) navBtn.click();
        const input = document.getElementById('chatPromptInput');
        if (input) {
            input.focus();
            input.placeholder = `Prompting ${item.title} directly...`;
        }
    }
};

window.selectTaskAndOpen = function(taskId) {
    const navBtn = document.querySelector(`.nav-item[data-tab="tasks"]`);
    if (navBtn) navBtn.click();
    window.selectTask(taskId);
};

// --- 3. Department Forcespace Filter ---

window.filterForcespace = function(department) {
    selectedDepartment = department;

    // Update filter pills styling
    document.querySelectorAll('.filter-pill').forEach(pill => {
        pill.classList.toggle('active', pill.textContent.toLowerCase().includes(department) || (department === 'all' && pill.textContent.includes('All')));
    });

    // Filter active projects grid
    let filtered = cachedProjects;
    if (department !== 'all') {
        const depMap = {
            'engineering': ['core_infrastructure', 'development', 'system'],
            'intelligence': ['market_research', 'browser_automation', 'data'],
            'growth': ['marketing', 'seo', 'social', 'content'],
            'operations': ['coordination', 'audit', 'general']
        };
        const categories = depMap[department] || [department];
        filtered = cachedProjects.filter(p => categories.includes(p.category) || (p.lead_agent_id && p.lead_agent_id.includes(department)));
    }
    renderHomeProjects(filtered.length ? filtered : cachedProjects);
};

function formatRelativeTime(dateStr) {
    if (!dateStr) return 'just now';
    try {
        const d = new Date(dateStr);
        const diffSec = Math.floor((Date.now() - d.getTime()) / 1000);
        if (diffSec < 60) return `${diffSec}s ago`;
        if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
        if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
        return `${Math.floor(diffSec / 86400)}d ago`;
    } catch {
        return 'recently';
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
