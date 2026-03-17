/* Dubai Prod Agent — Platform JS */

let ws;
let currentPage = 'dashboard';
let pendingConfirm = null;
let chatHistory = []; // Persist chat messages across page switches
let chatInputDraft = ''; // Remember what user was typing

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
    connectWS();
    navigateTo('dashboard');
});

// ---- WebSocket ----
function connectWS() {
    ws = new WebSocket(`ws://${location.host}/ws`);
    ws.onopen = () => console.log('WS connected');
    ws.onclose = () => setTimeout(connectWS, 2000);
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        // Always capture chat messages, even when on another page
        handleWSMessage(data);
    };
}

// ---- Navigation ----
function navigateTo(page) {
    currentPage = page;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const active = document.querySelector(`.nav-item[data-page="${page}"]`);
    if (active) active.classList.add('active');

    const main = document.getElementById('mainContent');

    const pages = {
        dashboard: renderDashboard,
        clients: renderClients,
        content: renderContent,
        design: renderDesignStudio,
        video: renderVideoStudio,
        media: renderMediaLibrary,
        pipeline: renderPipeline,
        tasks: renderTasks,
        leads: renderLeads,
        social: renderSocialWorkspace,
        research: renderResearchWorkspace,
        inbox: renderInbox,
        chat: renderChat,
        settings: renderSettings,
    };

    if (pages[page]) pages[page](main);
}

// ---- Dashboard ----
// ---- Agent Office Space ----
const OFFICE_AGENTS = {
    sarah:  { name: 'Sarah Chen', title: 'Agency Director', emoji: '👩‍💼', avatar: '/static/img/avatar_sarah.png', color: '#c9a44e', role: 'manager', initials: 'SC', voice: 'nova' },
    marcus: { name: 'Marcus Rivera', title: 'Content Strategist', emoji: '✍️', avatar: '/static/img/avatar_marcus.png', color: '#3498db', role: 'content', initials: 'MR', voice: 'echo' },
    zara:   { name: 'Zara Okafor', title: 'Creative Director', emoji: '🎨', avatar: '/static/img/avatar_zara.png', color: '#9b59b6', role: 'designer', initials: 'ZO', voice: 'shimmer' },
    kai:    { name: 'Kai Tanaka', title: 'Research Lead', emoji: '🔍', avatar: '/static/img/avatar_kai.png', color: '#1abc9c', role: 'browser', initials: 'KT', voice: 'onyx' },
    elena:  { name: 'Elena Voronova', title: 'Communications Mgr', emoji: '📧', avatar: '/static/img/avatar_elena.png', color: '#e67e22', role: 'email', initials: 'EV', voice: 'alloy' },
    alex:   { name: 'Alex Kim', title: 'Analytics Director', emoji: '📊', avatar: '/static/img/avatar_alex.png', color: '#2ecc71', role: 'analytics', initials: 'AK', voice: 'fable' },
};

// Voice state
let voiceEnabled = true;
let voicePlaying = false;
let currentAudio = null;
let micRecording = false;
let speechRecognition = null;

// Per-agent chat history (client-side for display)
const agentChats = {};
let activeAgentChat = null; // which agent panel is open
let meetingMessages = [];

async function renderDashboard(el) {
    const [dashRes, tasksRes, logsRes] = await Promise.all([
        fetch('/api/dashboard'), fetch('/api/tasks'), fetch('/api/agent-logs?limit=30')
    ]);
    const d = await dashRes.json();
    const tasks = await tasksRes.json();
    const logs = await logsRes.json();

    // Determine agent statuses from tasks
    const agentTasks = {};
    tasks.forEach(t => {
        if (t.status === 'in_progress') {
            const agentKey = Object.keys(OFFICE_AGENTS).find(k => OFFICE_AGENTS[k].role === t.assigned_agent);
            if (agentKey) {
                if (!agentTasks[agentKey]) agentTasks[agentKey] = [];
                agentTasks[agentKey].push(t.title);
            }
        }
    });

    // Recent log per agent
    const agentLastAction = {};
    logs.forEach(l => {
        const agentKey = Object.keys(OFFICE_AGENTS).find(k => OFFICE_AGENTS[k].role === l.agent);
        if (agentKey && !agentLastAction[agentKey]) {
            agentLastAction[agentKey] = { action: l.action, time: l.created_at };
        }
    });

    // Office room positions (CSS grid areas)
    const rooms = {
        sarah:  { grid: '1/1/2/3', furniture: '🖥️', roomLabel: 'Director Office' },
        marcus: { grid: '1/3/2/4', furniture: '📝', roomLabel: 'Content Lab' },
        zara:   { grid: '1/4/2/5', furniture: '🖌️', roomLabel: 'Creative Studio' },
        kai:    { grid: '2/1/3/2', furniture: '🔬', roomLabel: 'Research Center' },
        elena:  { grid: '2/2/3/3', furniture: '💼', roomLabel: 'Comms Office' },
        alex:   { grid: '2/3/3/4', furniture: '📈', roomLabel: 'Analytics Hub' },
    };

    const workingCount = Object.keys(agentTasks).length;

    el.innerHTML = `
        <!-- Mini stats row -->
        <div class="of2-topbar">
            <div class="of2-title">Dubai Prod Agency</div>
            <div class="of2-stats-row">
                <span class="of2-chip">${d.total_clients} clients</span>
                <span class="of2-chip of2-chip-green">$${d.monthly_revenue.toLocaleString()}</span>
                <span class="of2-chip of2-chip-blue">${d.pending_tasks} pending</span>
                <span class="of2-chip">${workingCount}/6 working</span>
                <button class="of2-report-btn" onclick="ofGenerateReport()">📄 Generate Report</button>
            </div>
        </div>

        <!-- 2D OFFICE FLOOR PLAN -->
        <div class="of2-floor">
            <!-- Grid of rooms -->
            <div class="of2-grid">
                ${Object.entries(OFFICE_AGENTS).map(([key, a]) => {
                    const r = rooms[key];
                    const busy = agentTasks[key];
                    const last = agentLastAction[key];
                    const statusText = busy ? busy[0].substring(0,30) : (last ? last.action.replace(/_/g,' ') : 'idle');
                    const isBusy = !!busy;
                    return `
                    <div class="of2-room ${isBusy ? 'of2-room-busy' : ''}" style="grid-area:${r.grid}" onclick="openAgentChat('${key}')">
                        <div class="of2-card-glow" style="background:${a.color}"></div>
                        <div class="of2-room-label">${r.roomLabel}</div>
                        <div class="of2-card-avatar" style="background-image:url(${a.avatar});border-color:${a.color}"></div>
                        <div class="of2-card-name">${a.name.split(' ')[0]}</div>
                        <div class="of2-card-title">${a.title}</div>
                        <div class="of2-card-status">
                            <div class="of2-status-dot ${isBusy ? 'of2-dot-busy' : 'of2-dot-idle'}"></div>
                            <span>${isBusy ? statusText.substring(0,22)+'...' : 'Available'}</span>
                        </div>
                    </div>`;
                }).join('')}

                <!-- Meeting Room (special cell) -->
                <div class="of2-room of2-meeting-room" style="grid-area:2/4/3/5" onclick="openMeetingRoom()">
                    <div class="of2-room-label">Meeting Room</div>
                    <div class="of2-meeting-table">
                        <div class="of2-table-surface">🏢</div>
                        ${Object.entries(OFFICE_AGENTS).map(([k,a], i) =>
                            `<div class="of2-meeting-seat" style="--si:${i}"><div class="of2-seat-face" style="background-image:url(${a.avatar});border-color:${a.color}"></div></div>`
                        ).join('')}
                    </div>
                    <div class="of2-nameplate"><strong>Team Meeting</strong><span>Click to start</span></div>
                    <div class="of2-room-hover">
                        <div style="font-size:20px;margin-bottom:4px">🏢</div>
                        <strong>Meeting Room</strong>
                        <div style="font-size:10px;color:var(--text-muted)">All agents present</div>
                        <button class="of2-talk-btn">Start Meeting</button>
                    </div>
                </div>
            </div>

            <!-- Hallway / Corridor label -->
            <div class="of2-corridor">
                <div class="of2-corridor-line"></div>
                <span>CORRIDOR</span>
                <div class="of2-corridor-line"></div>
            </div>
        </div>

        <!-- Live Activity -->
        <div class="of-activity">
            <div class="of-activity-title">Live Activity</div>
            <div class="of-activity-feed">
                ${logs.slice(0,6).map(l => {
                    const agentKey = Object.keys(OFFICE_AGENTS).find(k => OFFICE_AGENTS[k].role === l.agent);
                    const a = agentKey ? OFFICE_AGENTS[agentKey] : { emoji: '⚙️', name: l.agent, color: '#888' };
                    return `<div class="of-activity-item">
                        <span class="of-activity-emoji">${a.emoji}</span>
                        <span class="of-activity-name" style="color:${a.color}">${a.name}</span>
                        <span class="of-activity-text">${l.action.replace(/_/g,' ')}</span>
                        <span class="of-activity-time">${tkTimeAgo(l.created_at)}</span>
                    </div>`;
                }).join('')}
            </div>
        </div>

    `;

    // Populate meeting agents row (once, since panel is persistent in HTML)
    const agentsRow = document.getElementById('ofMeetingAgentsRow');
    if (agentsRow && !agentsRow.innerHTML.trim()) {
        agentsRow.innerHTML = Object.entries(OFFICE_AGENTS).map(([k,a]) =>
            `<img src="${a.avatar}" class="of-meeting-face" title="${a.name}" style="border-color:${a.color}">`
        ).join('');
    }
}

// ---- Agent 1-on-1 Chat ----
function openAgentChat(key) {
    activeAgentChat = key;
    const a = OFFICE_AGENTS[key];
    if (!agentChats[key]) agentChats[key] = [];

    const panel = document.getElementById('ofChatPanel');
    panel.style.display = 'flex';

    document.getElementById('ofChatHeader').innerHTML = `
        <div style="display:flex;align-items:center;gap:10px;flex:1">
            <img src="${a.avatar}" class="of-avatar-img-sm">
            <div>
                <strong>${a.name}</strong>
                <div style="font-size:10px;color:var(--text-muted)">${a.title}</div>
            </div>
        </div>
        <div style="display:flex;gap:4px;align-items:center">
            <button class="of-voice-btn ${voiceEnabled?'of-voice-on':''}" onclick="ofToggleVoice()" title="Toggle voice responses" id="ofVoiceToggle">
                ${voiceEnabled ? '🔊' : '🔇'}
            </button>
            <button class="of-clear-btn" onclick="ofClearAgentChat('${key}')" title="Clear history">Clear</button>
            <button class="of-close-btn" onclick="closeAgentChat()">✕</button>
        </div>
    `;

    ofRenderChatMessages(key);
    setTimeout(() => document.getElementById('ofChatInput')?.focus(), 100);
}

function closeAgentChat() {
    activeAgentChat = null;
    document.getElementById('ofChatPanel').style.display = 'none';
}

function ofClearAgentChat(key) {
    if (!confirm(`Clear chat history with ${OFFICE_AGENTS[key]?.name}?`)) return;
    agentChats[key] = [];
    ofRenderChatMessages(key);
    // Also clear backend memory
    fetch(`/api/agents/${key}/chat`, { method: 'DELETE' });
}

function ofClearMeeting() {
    if (!confirm('Clear meeting history?')) return;
    meetingMessages = [];
    ofRenderMeetingMessages();
    fetch('/api/chat/meeting', { method: 'DELETE' });
}

function ofRenderChatMessages(key) {
    const el = document.getElementById('ofChatMessages');
    const msgs = agentChats[key] || [];
    const a = OFFICE_AGENTS[key];

    if (!msgs.length) {
        el.innerHTML = `<div style="text-align:center;padding:30px;color:var(--text-muted)">
            <img src="${a.avatar}" class="of-welcome-avatar">
            <div style="margin-top:8px">Hey! I'm <strong>${a.name}</strong>, ${a.title}.</div>
            <div style="margin-top:4px;font-size:12px">Ask me anything or give me a task.</div>
        </div>`;
        return;
    }

    el.innerHTML = msgs.map(m => {
        if (m.role === 'user') {
            return `<div class="of-msg of-msg-user"><div class="of-msg-bubble of-msg-user-bubble">${escapeHTML(m.text)}</div></div>`;
        } else {
            return `<div class="of-msg of-msg-agent">
                <img src="${a.avatar}" class="of-avatar-img-xs">
                <div class="of-msg-bubble of-msg-agent-bubble">${formatMD(m.text)}</div>
            </div>`;
        }
    }).join('');
    el.scrollTop = el.scrollHeight;
}

function ofSendChat() {
    const input = document.getElementById('ofChatInput');
    const text = input.value.trim();
    if (!text || !activeAgentChat) return;
    input.value = '';

    const key = activeAgentChat;
    if (!agentChats[key]) agentChats[key] = [];
    agentChats[key].push({ role: 'user', text });
    ofRenderChatMessages(key);

    // Show typing
    const el = document.getElementById('ofChatMessages');
    el.innerHTML += `<div class="of-msg of-msg-agent" id="ofTyping">
        <img src="${OFFICE_AGENTS[key].avatar}" class="of-avatar-img-xs">
        <div class="of-msg-bubble of-msg-agent-bubble"><span class="of-typing-dots"><span></span><span></span><span></span></span></div>
    </div>`;
    el.scrollTop = el.scrollHeight;

    // Send to backend
    ws.send(JSON.stringify({ type: 'agent_chat', content: text, agent: key }));
}

// ---- Meeting Room ----
function openMeetingRoom() {
    const panel = document.getElementById('ofMeetingPanel');
    panel.style.display = 'flex';
    // Populate agents row if empty
    const agentsRow = document.getElementById('ofMeetingAgentsRow');
    if (agentsRow && !agentsRow.innerHTML.trim()) {
        agentsRow.innerHTML = Object.entries(OFFICE_AGENTS).map(([k,a]) =>
            `<img src="${a.avatar}" class="of-meeting-face" title="${a.name}" style="border-color:${a.color}">`
        ).join('');
    }
    ofRenderMeetingMessages();
    setTimeout(() => document.getElementById('ofMeetingInput')?.focus(), 100);
}

function closeMeeting() {
    document.getElementById('ofMeetingPanel').style.display = 'none';
}

function ofRenderMeetingMessages() {
    const el = document.getElementById('ofMeetingMessages');
    if (!meetingMessages.length) {
        el.innerHTML = `<div style="text-align:center;padding:30px;color:var(--text-muted)">
            <div style="font-size:24px;margin-bottom:8px">🏢</div>
            <div>The team is ready for the meeting.</div>
            <div style="margin-top:4px">Start the discussion — relevant team members will respond.</div>
        </div>`;
        return;
    }
    el.innerHTML = meetingMessages.map(m => {
        if (m.role === 'user') {
            return `<div class="of-msg of-msg-user"><div class="of-msg-bubble of-msg-user-bubble">${escapeHTML(m.text)}</div></div>`;
        } else {
            return `<div class="of-msg of-msg-meeting"><div class="of-msg-bubble of-msg-meeting-bubble">${formatMD(m.text)}</div></div>`;
        }
    }).join('');
    el.scrollTop = el.scrollHeight;
}

function ofSendMeeting() {
    const input = document.getElementById('ofMeetingInput');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';

    meetingMessages.push({ role: 'user', text });
    ofRenderMeetingMessages();

    const el = document.getElementById('ofMeetingMessages');
    el.innerHTML += `<div class="of-msg of-msg-meeting" id="ofMeetingTyping">
        <div class="of-msg-bubble of-msg-meeting-bubble"><span class="of-typing-dots"><span></span><span></span><span></span></span> Team is discussing...</div>
    </div>`;
    el.scrollTop = el.scrollHeight;

    ws.send(JSON.stringify({ type: 'meeting', content: text }));
}

// Handle agent/meeting replies from WebSocket
function handleAgentReply(data) {
    if (data.type === 'agent_reply' && data.agent) {
        document.getElementById('ofTyping')?.remove();
        if (!agentChats[data.agent]) agentChats[data.agent] = [];
        agentChats[data.agent].push({ role: 'agent', text: data.content });
        if (activeAgentChat === data.agent) ofRenderChatMessages(data.agent);
        // Agent speaks their response
        const agentVoice = OFFICE_AGENTS[data.agent]?.voice || 'nova';
        ofSpeak(data.content, agentVoice);
        // Browser notification if tab not focused
        if (document.hidden) {
            const agentName = OFFICE_AGENTS[data.agent]?.name || data.agent;
            browserNotify(agentName, data.content.substring(0, 100));
        }
    }
    if (data.type === 'meeting_reply') {
        document.getElementById('ofMeetingTyping')?.remove();
        meetingMessages.push({ role: 'meeting', text: data.content });
        ofRenderMeetingMessages();
        // Meeting: use first mentioned agent's voice or default
        ofSpeak(data.content, 'nova');
    }
    // Typing indicators
    if (data.type === 'agent_typing' && data.agent) {
        if (activeAgentChat === data.agent) {
            const el = document.getElementById('ofChatMessages');
            if (el && !document.getElementById('ofTyping')) {
                const a = OFFICE_AGENTS[data.agent];
                el.innerHTML += `<div class="of-msg of-msg-agent" id="ofTyping">
                    <img src="${a.avatar}" class="of-avatar-img-xs">
                    <div class="of-msg-bubble of-msg-agent-bubble"><span class="of-typing-dots"><span></span><span></span><span></span></span></div>
                </div>`;
                el.scrollTop = el.scrollHeight;
            }
        }
    }
    if (data.type === 'meeting_typing') {
        const el = document.getElementById('ofMeetingMessages');
        if (el && !document.getElementById('ofMeetingTyping')) {
            el.innerHTML += `<div class="of-msg of-msg-meeting" id="ofMeetingTyping">
                <div class="of-msg-bubble of-msg-meeting-bubble"><span class="of-typing-dots"><span></span><span></span><span></span></span> Team is discussing...</div>
            </div>`;
            el.scrollTop = el.scrollHeight;
        }
    }
}

// ---- Voice: Text-to-Speech (agent speaks) ----
function ofToggleVoice() {
    voiceEnabled = !voiceEnabled;
    // Update all voice toggle buttons
    document.querySelectorAll('.of-voice-btn').forEach(b => {
        b.classList.toggle('of-voice-on', voiceEnabled);
        b.textContent = voiceEnabled ? '🔊' : '🔇';
    });
    if (!voiceEnabled && currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
}

async function ofSpeak(text, voiceName) {
    if (!voiceEnabled || !text) return;

    // Stop any current playback
    if (currentAudio) { currentAudio.pause(); currentAudio = null; }

    // Strip markdown for cleaner speech
    const cleanText = text
        .replace(/\*\*([^*]+)\*\*/g, '$1')  // bold
        .replace(/\*([^*]+)\*/g, '$1')       // italic
        .replace(/#{1,6}\s/g, '')            // headers
        .replace(/```[\s\S]*?```/g, '')      // code blocks
        .replace(/`([^`]+)`/g, '$1')         // inline code
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // links
        .replace(/[-*] /g, '')               // list markers
        .replace(/\n+/g, '. ')              // newlines to pauses
        .trim();

    if (!cleanText || cleanText.length < 3) return;

    try {
        voicePlaying = true;
        const res = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: cleanText, voice: voiceName || 'nova' }),
        });

        if (!res.ok) { voicePlaying = false; return; }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        currentAudio = new Audio(url);
        currentAudio.onended = () => { voicePlaying = false; currentAudio = null; URL.revokeObjectURL(url); };
        currentAudio.onerror = () => { voicePlaying = false; currentAudio = null; };
        await currentAudio.play();
    } catch (e) {
        console.error('[voice] TTS error:', e);
        voicePlaying = false;
    }
}

// ---- Voice: Speech-to-Text (user speaks) ----
function ofInitSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn('[voice] Speech recognition not supported');
        return null;
    }
    const sr = new SpeechRecognition();
    sr.continuous = false;
    sr.interimResults = true;
    sr.lang = 'en-US';
    sr.maxAlternatives = 1;
    return sr;
}

function ofToggleMic(inputId, chatType) {
    const input = document.getElementById(inputId);
    const micBtn = chatType === 'agent' ? document.getElementById('ofMicBtn') : document.getElementById('ofMeetingMicBtn');
    if (!input) return;

    if (micRecording) {
        // Stop recording
        if (speechRecognition) speechRecognition.stop();
        micRecording = false;
        if (micBtn) { micBtn.classList.remove('of-mic-active'); micBtn.textContent = '🎤'; }
        return;
    }

    speechRecognition = ofInitSpeechRecognition();
    if (!speechRecognition) {
        alert('Speech recognition is not supported in this browser. Use Chrome.');
        return;
    }

    micRecording = true;
    if (micBtn) { micBtn.classList.add('of-mic-active'); micBtn.textContent = '⏺'; }

    let finalTranscript = '';

    speechRecognition.onresult = (event) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const t = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += t + ' ';
            } else {
                interim = t;
            }
        }
        input.value = finalTranscript + interim;
    };

    speechRecognition.onend = () => {
        micRecording = false;
        if (micBtn) { micBtn.classList.remove('of-mic-active'); micBtn.textContent = '🎤'; }
        // Auto-send if we got text
        if (finalTranscript.trim()) {
            input.value = finalTranscript.trim();
            if (chatType === 'agent') ofSendChat();
            else ofSendMeeting();
        }
    };

    speechRecognition.onerror = (e) => {
        console.error('[voice] Recognition error:', e.error);
        micRecording = false;
        if (micBtn) { micBtn.classList.remove('of-mic-active'); micBtn.textContent = '🎤'; }
    };

    speechRecognition.start();
}

// ---- Report Generation ----
async function ofGenerateReport() {
    const title = prompt('Report title:', 'Agency Performance Report') || 'Agency Report';
    const btn = document.querySelector('.of2-report-btn');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Generating...'; }

    try {
        const res = await fetch('/api/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                include_clients: true,
                include_tasks: true,
                include_content: true,
                include_activity: true,
            }),
        });
        const data = await res.json();
        if (data.path) {
            if (btn) { btn.textContent = '✅ Report Ready!'; }
            // Ask if they want Elena to email it
            const action = confirm(`Report generated!\n\n${data.filename}\n\nClick OK to open, or Cancel to ask Elena to email it.`);
            if (action) {
                window.open(data.path, '_blank');
            } else {
                // Open Elena chat and ask her to send it
                openAgentChat('elena');
                setTimeout(() => {
                    const input = document.getElementById('ofChatInput');
                    if (input) {
                        input.value = `Please send the report "${title}" (file: ${data.path}) via email to Amine. Attach a brief summary of the key findings.`;
                        ofSendChat();
                    }
                }, 500);
            }
        } else {
            alert('Report generation failed: ' + (data.error || 'unknown error'));
        }
    } catch (e) {
        alert('Error generating report: ' + e.message);
    }

    if (btn) { btn.disabled = false; btn.textContent = '📄 Generate Report'; }
}

// Legacy compatibility
async function showAgentWork(agentName) {
    const key = Object.keys(OFFICE_AGENTS).find(k => OFFICE_AGENTS[k].role === agentName) || 'sarah';
    openAgentChat(key);
}
async function showLogDetail(logId) { /* legacy — no-op for now */ }
async function loadActivityFeed() { /* handled inline now */ }

// ---- Clients ----
async function renderClients(el) {
    el.innerHTML = `
        <div class="page-header">
            <div><h2>Clients</h2><div class="subtitle">Manage your agency clients</div></div>
            <button class="btn btn-primary" onclick="showClientModal()">+ Add Client</button>
        </div>
        <div id="clientsList">Loading...</div>
        <div class="modal-overlay" id="clientModal">
            <div class="modal">
                <h3 id="clientModalTitle">Add Client</h3>
                <input type="hidden" id="clientEditId">
                <div class="form-group"><label>Name</label><input id="cName" placeholder="Client name"></div>
                <div class="form-group"><label>Company</label><input id="cCompany" placeholder="Company name"></div>
                <div class="form-group"><label>Email</label><input id="cEmail" placeholder="email@example.com"></div>
                <div class="form-group"><label>Phone</label><input id="cPhone" placeholder="+971..."></div>
                <div class="form-group"><label>Platform</label><input id="cPlatform" placeholder="Instagram, TikTok, etc."></div>
                <div class="form-group"><label>Monthly Fee ($)</label><input id="cFee" type="number" placeholder="0"></div>
                <div class="form-group"><label>Status</label><select id="cStatus"><option value="active">Active</option><option value="paused">Paused</option></select></div>
                <div class="form-group"><label>Notes</label><textarea id="cNotes" placeholder="Notes..."></textarea></div>
                <div class="form-actions">
                    <button class="btn btn-secondary" onclick="closeModal('clientModal')">Cancel</button>
                    <button class="btn btn-primary" onclick="saveClient()">Save</button>
                </div>
            </div>
        </div>
    `;
    await loadClients();
}

async function loadClients() {
    const res = await fetch('/api/clients');
    const clients = await res.json();
    const el = document.getElementById('clientsList');

    if (!clients.length) {
        el.innerHTML = '<div class="empty-state"><div class="empty-icon">+</div><p>No clients yet. Add your first client to get started.</p></div>';
        return;
    }

    el.innerHTML = `<table class="data-table"><thead><tr><th>Name</th><th>Company</th><th>Platform</th><th>Monthly Fee</th><th>Status</th><th>Actions</th></tr></thead><tbody>${clients.map(c => `
        <tr>
            <td><strong>${c.name}</strong></td>
            <td>${c.company||'—'}</td>
            <td>${c.platform||'—'}</td>
            <td>$${(c.monthly_fee||0).toLocaleString()}</td>
            <td><span class="badge badge-${c.status}">${c.status}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="editClient(${c.id})">Edit</button>
                <button class="btn btn-danger btn-sm" onclick="deleteClient(${c.id})">Delete</button>
            </td>
        </tr>
    `).join('')}</tbody></table>`;
}

function showClientModal(data) {
    document.getElementById('clientModalTitle').textContent = data ? 'Edit Client' : 'Add Client';
    document.getElementById('clientEditId').value = data?.id || '';
    document.getElementById('cName').value = data?.name || '';
    document.getElementById('cCompany').value = data?.company || '';
    document.getElementById('cEmail').value = data?.email || '';
    document.getElementById('cPhone').value = data?.phone || '';
    document.getElementById('cPlatform').value = data?.platform || '';
    document.getElementById('cFee').value = data?.monthly_fee || '';
    document.getElementById('cStatus').value = data?.status || 'active';
    document.getElementById('cNotes').value = data?.notes || '';
    document.getElementById('clientModal').classList.add('active');
}

async function editClient(id) {
    const res = await fetch(`/api/clients/${id}`);
    const data = await res.json();
    showClientModal(data);
}

async function saveClient() {
    const id = document.getElementById('clientEditId').value;
    const body = {
        name: document.getElementById('cName').value,
        company: document.getElementById('cCompany').value,
        email: document.getElementById('cEmail').value,
        phone: document.getElementById('cPhone').value,
        platform: document.getElementById('cPlatform').value,
        monthly_fee: parseFloat(document.getElementById('cFee').value) || 0,
        status: document.getElementById('cStatus').value,
        notes: document.getElementById('cNotes').value,
    };

    const url = id ? `/api/clients/${id}` : '/api/clients';
    const method = id ? 'PUT' : 'POST';
    await fetch(url, { method, headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
    closeModal('clientModal');
    await loadClients();
}

async function deleteClient(id) {
    if (!confirm('Delete this client?')) return;
    await fetch(`/api/clients/${id}`, { method: 'DELETE' });
    await loadClients();
}

// ---- Tasks ----
const AGENT_INFO = {
    manager:   { icon: '🧠', color: '#c9a44e', label: 'Manager' },
    content:   { icon: '✍️', color: '#3498db', label: 'Content' },
    designer:  { icon: '🎨', color: '#9b59b6', label: 'Designer' },
    browser:   { icon: '🌐', color: '#1abc9c', label: 'Browser' },
    email:     { icon: '📧', color: '#e67e22', label: 'Email' },
    analytics: { icon: '📊', color: '#2ecc71', label: 'Analytics' },
};

async function renderTasks(el) {
    el.innerHTML = `
        <div class="page-header">
            <div><h2>Tasks</h2><div class="subtitle">Track agency work</div></div>
            <div style="display:flex;gap:6px">
                <button class="btn btn-secondary btn-sm tk-view-btn active" data-view="board" onclick="tkSetView('board')">Board</button>
                <button class="btn btn-secondary btn-sm tk-view-btn" data-view="list" onclick="tkSetView('list')">List</button>
                <button class="btn btn-secondary btn-sm" onclick="cleanupStaleTasks()">Clean Stale</button>
                <button class="btn btn-primary" onclick="showTaskModal()">+ Add Task</button>
            </div>
        </div>
        <div id="tasksList">Loading...</div>
        <div class="modal-overlay" id="taskModal">
            <div class="modal">
                <h3 id="taskModalTitle">Add Task</h3>
                <input type="hidden" id="taskEditId">
                <div class="form-group"><label>Title</label><input id="tTitle" placeholder="Task title"></div>
                <div class="form-group"><label>Description</label><textarea id="tDesc" placeholder="Details..."></textarea></div>
                <div class="form-group"><label>Client</label><select id="tClient"><option value="">None</option></select></div>
                <div class="form-group"><label>Assigned Agent</label><select id="tAgent"><option value="manager">Manager</option><option value="content">Content Creator</option><option value="browser">Browser Agent</option><option value="designer">Designer</option><option value="email">Email Agent</option><option value="analytics">Analytics</option></select></div>
                <div class="form-group"><label>Priority</label><select id="tPriority"><option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option></select></div>
                <div class="form-group"><label>Status</label><select id="tStatus"><option value="pending">Pending</option><option value="in_progress">In Progress</option><option value="completed">Completed</option></select></div>
                <div class="form-group"><label>Due Date</label><input id="tDue" type="date"></div>
                <div class="form-actions">
                    <button class="btn btn-secondary" onclick="closeModal('taskModal')">Cancel</button>
                    <button class="btn btn-primary" onclick="saveTask()">Save</button>
                </div>
            </div>
        </div>
    `;
    await loadTasks();
}

let tkViewMode = 'board';
function tkSetView(mode) {
    tkViewMode = mode;
    document.querySelectorAll('.tk-view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === mode));
    loadTasks();
}

function tkAgentBadge(agent, showLabel) {
    const a = AGENT_INFO[agent] || { icon: '⚙️', color: '#888', label: agent };
    return `<div class="tk-agent" style="--agent-color:${a.color}" title="${a.label}">
        <span class="tk-agent-icon">${a.icon}</span>${showLabel ? `<span class="tk-agent-label">${a.label}</span>` : ''}
    </div>`;
}

function tkStatusBadge(status) {
    const map = {
        pending: { label: 'Pending', cls: 'tk-status-pending', icon: '○' },
        in_progress: { label: 'In Progress', cls: 'tk-status-active', icon: '◉' },
        completed: { label: 'Completed', cls: 'tk-status-done', icon: '✓' },
    };
    const s = map[status] || map.pending;
    return `<span class="tk-status ${s.cls}"><span>${s.icon}</span> ${s.label}</span>`;
}

function tkPriorityDot(p) {
    const colors = { high: '#e74c3c', medium: '#f39c12', low: '#2ecc71' };
    return `<span class="tk-priority" style="--pri-color:${colors[p]||'#888'}" title="${p} priority"></span>`;
}

function tkTimeAgo(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff/60) + 'm ago';
    if (diff < 86400) return Math.floor(diff/3600) + 'h ago';
    return Math.floor(diff/86400) + 'd ago';
}

function tkCard(t) {
    const a = AGENT_INFO[t.assigned_agent] || { icon: '⚙️', color: '#888', label: t.assigned_agent };
    const isActive = t.status === 'in_progress';
    const isPending = t.status === 'pending';
    return `<div class="tk-card ${isActive ? 'tk-card-active' : ''}" onclick="editTask(${t.id})">
        <div class="tk-card-top">
            ${tkPriorityDot(t.priority)}
            <span class="tk-card-title">${t.title}</span>
            <div class="tk-card-btns" onclick="event.stopPropagation()">
                ${isPending ? `<button class="tk-mini-btn tk-btn-start" onclick="startTask(${t.id})" title="Start">▶</button>` : ''}
                ${isActive ? `<button class="tk-mini-btn tk-btn-stop" onclick="cancelTask(${t.id})" title="Stop">■</button>` : ''}
                ${isActive ? `<button class="tk-mini-btn tk-btn-done" onclick="quickUpdateTask(${t.id},'completed')" title="Mark done">✓</button>` : ''}
                <button class="tk-mini-btn tk-btn-del" onclick="deleteTask(${t.id})" title="Delete">×</button>
            </div>
        </div>
        ${t.description ? `<div class="tk-card-desc">${t.description.substring(0,80)}${t.description.length>80?'...':''}</div>` : ''}
        <div class="tk-card-bottom">
            <div class="tk-agent-chip" style="--agent-color:${a.color}">
                <span>${a.icon}</span>
                <span>${a.label}</span>
                ${isActive ? '<span class="tk-pulse"></span>' : ''}
            </div>
            ${t.client_name ? `<span class="tk-client">${t.client_name}</span>` : ''}
            <span class="tk-time">${t.completed_at ? '✓ ' + tkTimeAgo(t.completed_at) : t.status === 'failed' ? '✗ failed' : tkTimeAgo(t.created_at)}</span>
        </div>
    </div>`;
}

async function loadTasks() {
    const [tasksRes, clientsRes, logsRes] = await Promise.all([
        fetch('/api/tasks'), fetch('/api/clients'), fetch('/api/agent-logs?limit=20')
    ]);
    const tasks = await tasksRes.json();
    const clients = await clientsRes.json();
    const logs = await logsRes.json();

    const sel = document.getElementById('tClient');
    if (sel) sel.innerHTML = '<option value="">None</option>' + clients.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

    const el = document.getElementById('tasksList');
    if (!tasks.length) {
        el.innerHTML = '<div class="empty-state"><div class="empty-icon">+</div><p>No tasks yet.</p></div>';
        return;
    }

    const total = tasks.length;
    const completed = tasks.filter(t => t.status === 'completed').length;
    const inProgress = tasks.filter(t => t.status === 'in_progress').length;
    const pending = tasks.filter(t => t.status === 'pending').length;
    const pct = total ? Math.round((completed / total) * 100) : 0;

    // Agent workload summary
    const agentWork = {};
    tasks.filter(t => t.status === 'in_progress').forEach(t => {
        if (!agentWork[t.assigned_agent]) agentWork[t.assigned_agent] = [];
        agentWork[t.assigned_agent].push(t);
    });

    const agentSummary = Object.keys(agentWork).length ?
        `<div class="tk-agents-bar">
            <div class="tk-agents-title">Active Agents</div>
            <div class="tk-agents-list">${Object.entries(agentWork).map(([agent, agentTasks]) => {
                const a = AGENT_INFO[agent] || { icon: '⚙️', color: '#888', label: agent };
                return `<div class="tk-agent-work" style="--agent-color:${a.color}">
                    <div class="tk-agent-work-icon"><span>${a.icon}</span><span class="tk-pulse"></span></div>
                    <div class="tk-agent-work-info">
                        <strong>${a.label}</strong>
                        <span>${agentTasks.length} task${agentTasks.length>1?'s':''}: ${agentTasks.map(t=>t.title.substring(0,30)).join(', ')}</span>
                    </div>
                </div>`;
            }).join('')}</div>
        </div>` : '';

    // Recent activity from logs
    const recentActivity = logs.length ?
        `<div class="tk-activity">
            <div class="tk-activity-title">Recent Activity</div>
            ${logs.slice(0,5).map(l => {
                const a = AGENT_INFO[l.agent] || { icon: '⚙️', color: '#888' };
                return `<div class="tk-activity-item">
                    <span class="tk-activity-dot" style="background:${a.color}"></span>
                    <span class="tk-activity-agent">${a.icon} ${l.agent}</span>
                    <span class="tk-activity-action">${l.action}</span>
                    <span class="tk-activity-time">${tkTimeAgo(l.created_at)}</span>
                </div>`;
            }).join('')}
        </div>` : '';

    const statsHtml = `
        <div class="tk-stats-row">
            <div class="tk-stat"><div class="tk-stat-num">${total}</div><div class="tk-stat-label">Total</div></div>
            <div class="tk-stat tk-stat-pending"><div class="tk-stat-num">${pending}</div><div class="tk-stat-label">Queued</div></div>
            <div class="tk-stat tk-stat-active"><div class="tk-stat-num">${inProgress}</div><div class="tk-stat-label">Working</div></div>
            <div class="tk-stat tk-stat-done"><div class="tk-stat-num">${completed}</div><div class="tk-stat-label">Done</div></div>
            <div class="tk-progress-bar">
                <div class="tk-progress-fill" style="width:${pct}%"></div>
                <span class="tk-progress-label">${pct}%</span>
            </div>
        </div>
        ${agentSummary}`;

    if (tkViewMode === 'board') {
        const pendingTasks = tasks.filter(t => t.status === 'pending');
        const activeTasks = tasks.filter(t => t.status === 'in_progress');
        const doneTasks = tasks.filter(t => t.status === 'completed');

        el.innerHTML = `${statsHtml}
            <div class="tk-board">
                <div class="tk-column">
                    <div class="tk-col-header tk-col-pending"><span>○ Queued</span><span class="tk-col-count">${pendingTasks.length}</span></div>
                    <div class="tk-col-body">${pendingTasks.map(tkCard).join('') || '<div class="tk-col-empty">No pending tasks</div>'}</div>
                </div>
                <div class="tk-column">
                    <div class="tk-col-header tk-col-active"><span>◉ In Progress</span><span class="tk-col-count">${activeTasks.length}</span></div>
                    <div class="tk-col-body">${activeTasks.map(tkCard).join('') || '<div class="tk-col-empty">Nothing in progress</div>'}</div>
                </div>
                <div class="tk-column">
                    <div class="tk-col-header tk-col-done"><span>✓ Completed</span><span class="tk-col-count">${doneTasks.length}</span></div>
                    <div class="tk-col-body">${doneTasks.map(tkCard).join('') || '<div class="tk-col-empty">No completed tasks</div>'}</div>
                </div>
            </div>
            ${recentActivity}`;
    } else {
        // List view
        el.innerHTML = `${statsHtml}
            <table class="data-table"><thead><tr><th style="width:30px"></th><th>Task</th><th>Agent</th><th>Client</th><th>Status</th><th>Actions</th></tr></thead><tbody>${tasks.map(t => {
                const a = AGENT_INFO[t.assigned_agent] || { icon: '⚙️', color: '#888', label: t.assigned_agent };
                const isActive = t.status === 'in_progress';
                return `<tr class="${isActive ? 'tk-row-active' : ''} ${t.status === 'completed' ? 'tk-row-done' : ''}">
                    <td>${tkPriorityDot(t.priority)}</td>
                    <td>
                        <strong>${t.title}</strong>
                        ${t.description ? `<br><small style="color:var(--text-muted)">${t.description.substring(0,60)}</small>` : ''}
                        ${t.completed_at ? `<br><small style="color:var(--success)">Done ${tkTimeAgo(t.completed_at)}</small>` : ''}
                    </td>
                    <td>
                        <div class="tk-agent-chip" style="--agent-color:${a.color}">
                            <span>${a.icon}</span><span>${a.label}</span>
                            ${isActive ? '<span class="tk-pulse"></span>' : ''}
                        </div>
                    </td>
                    <td style="color:var(--text-muted)">${t.client_name || '—'}</td>
                    <td>${tkStatusBadge(t.status)}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="editTask(${t.id})">Edit</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteTask(${t.id})">Delete</button>
                    </td>
                </tr>`;
            }).join('')}</tbody></table>
            ${recentActivity}`;
    }
}

async function showTaskModal(data) {
    const clients = await (await fetch('/api/clients')).json();
    const sel = document.getElementById('tClient');
    sel.innerHTML = '<option value="">None</option>' + clients.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

    document.getElementById('taskModalTitle').textContent = data ? 'Edit Task' : 'Add Task';
    document.getElementById('taskEditId').value = data?.id || '';
    document.getElementById('tTitle').value = data?.title || '';
    document.getElementById('tDesc').value = data?.description || '';
    document.getElementById('tClient').value = data?.client_id || '';
    document.getElementById('tAgent').value = data?.assigned_agent || 'manager';
    document.getElementById('tPriority').value = data?.priority || 'medium';
    document.getElementById('tStatus').value = data?.status || 'pending';
    document.getElementById('tDue').value = data?.due_date?.split('T')[0] || '';
    document.getElementById('taskModal').classList.add('active');
}

async function editTask(id) {
    const tasks = await (await fetch('/api/tasks')).json();
    const t = tasks.find(t => t.id === id);
    if (t) showTaskModal(t);
}

async function saveTask() {
    const id = document.getElementById('taskEditId').value;
    const body = {
        title: document.getElementById('tTitle').value,
        description: document.getElementById('tDesc').value,
        client_id: parseInt(document.getElementById('tClient').value) || null,
        assigned_agent: document.getElementById('tAgent').value,
        priority: document.getElementById('tPriority').value,
        status: document.getElementById('tStatus').value,
        due_date: document.getElementById('tDue').value || null,
    };

    const url = id ? `/api/tasks/${id}` : '/api/tasks';
    const method = id ? 'PUT' : 'POST';
    await fetch(url, { method, headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
    closeModal('taskModal');
    await loadTasks();
}

async function quickUpdateTask(id, newStatus) {
    // Fetch current task data to preserve fields
    const tasks = await (await fetch('/api/tasks')).json();
    const t = tasks.find(t => t.id === id);
    if (!t) return;
    t.status = newStatus;
    await fetch(`/api/tasks/${id}`, {
        method: 'PUT',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(t),
    });
    await loadTasks();
}

async function cancelTask(id) {
    await quickUpdateTask(id, 'failed');
}

async function startTask(id) {
    await quickUpdateTask(id, 'in_progress');
}

async function cleanupStaleTasks() {
    const res = await fetch('/api/tasks/cleanup', { method: 'POST' });
    const data = await res.json();
    if (data.cleaned > 0) {
        alert(`Cleaned ${data.cleaned} stale tasks`);
    } else {
        alert('No stale tasks found');
    }
    loadTasks();
}

async function deleteTask(id) {
    if (!confirm('Delete this task?')) return;
    await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
    await loadTasks();
}

// ---- Content ----
async function renderContent(el) {
    el.innerHTML = `
        <div class="page-header">
            <div><h2>Content Studio</h2><div class="subtitle">Create and manage social media content</div></div>
            <button class="btn btn-primary" onclick="showContentModal()">+ New Post</button>
        </div>
        <div id="contentList">Loading...</div>
        <div class="modal-overlay" id="contentModal">
            <div class="modal">
                <h3>New Content</h3>
                <div class="form-group"><label>Client</label><select id="coClient"><option value="">None</option></select></div>
                <div class="form-group"><label>Platform</label><select id="coPlatform"><option value="instagram">Instagram</option><option value="tiktok">TikTok</option><option value="facebook">Facebook</option><option value="twitter">Twitter/X</option><option value="linkedin">LinkedIn</option><option value="youtube">YouTube</option></select></div>
                <div class="form-group"><label>Type</label><select id="coType"><option value="post">Post</option><option value="story">Story</option><option value="reel">Reel</option><option value="carousel">Carousel</option><option value="video">Video</option></select></div>
                <div class="form-group"><label>Caption</label><textarea id="coCaption" rows="4" placeholder="Write your caption..."></textarea></div>
                <div class="form-group"><label>Status</label><select id="coStatus"><option value="draft">Draft</option><option value="scheduled">Scheduled</option><option value="published">Published</option></select></div>
                <div class="form-group"><label>Schedule Date</label><input id="coSchedule" type="datetime-local"></div>
                <div class="form-group"><label>Notes</label><textarea id="coNotes" placeholder="Internal notes..."></textarea></div>
                <div class="form-actions">
                    <button class="btn btn-secondary" onclick="closeModal('contentModal')">Cancel</button>
                    <button class="btn btn-primary" onclick="saveContent()">Save</button>
                </div>
            </div>
        </div>
    `;
    await loadContent();
}

async function loadContent() {
    const res = await fetch('/api/content');
    const content = await res.json();
    const el = document.getElementById('contentList');

    if (!content.length) {
        el.innerHTML = '<div class="empty-state"><div class="empty-icon">+</div><p>No content yet. Create your first post.</p></div>';
        return;
    }

    el.innerHTML = `<table class="data-table"><thead><tr><th>Caption</th><th>Client</th><th>Platform</th><th>Type</th><th>Status</th></tr></thead><tbody>${content.map(c => `
        <tr>
            <td>${(c.caption||'').substring(0,80)}${(c.caption||'').length>80?'...':''}</td>
            <td>${c.client_name||'—'}</td>
            <td>${c.platform}</td>
            <td>${c.content_type}</td>
            <td><span class="badge badge-${c.status}">${c.status}</span></td>
        </tr>
    `).join('')}</tbody></table>`;
}

async function showContentModal() {
    const clients = await (await fetch('/api/clients')).json();
    document.getElementById('coClient').innerHTML = '<option value="">None</option>' + clients.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    document.getElementById('coCaption').value = '';
    document.getElementById('coNotes').value = '';
    document.getElementById('coSchedule').value = '';
    document.getElementById('contentModal').classList.add('active');
}

async function saveContent() {
    const body = {
        client_id: parseInt(document.getElementById('coClient').value) || null,
        platform: document.getElementById('coPlatform').value,
        content_type: document.getElementById('coType').value,
        caption: document.getElementById('coCaption').value,
        status: document.getElementById('coStatus').value,
        scheduled_at: document.getElementById('coSchedule').value || null,
        notes: document.getElementById('coNotes').value,
    };
    await fetch('/api/content', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
    closeModal('contentModal');
    await loadContent();
}

// ---- Inbox ----
async function renderInbox(el) {
    el.innerHTML = `
        <div class="page-header">
            <div><h2>Inbox</h2><div class="subtitle">Email overview</div></div>
            <button class="btn btn-primary" onclick="fetchInbox()">Refresh</button>
        </div>
        <div id="inboxList"><div class="empty-state"><p>Click Refresh to fetch emails.</p></div></div>
    `;
}

async function fetchInbox() {
    const el = document.getElementById('inboxList');
    el.innerHTML = '<p style="color:var(--text-secondary)">Fetching emails...</p>';

    // Use websocket to trigger inbox command
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'message', content: '/inbox 10' }));

        // Temporarily capture inbox response
        const origHandler = ws.onmessage;
        ws.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.type === 'reply') {
                el.innerHTML = `<div class="stat-card" style="white-space:pre-wrap;font-size:13px;line-height:1.6">${formatMD(data.content)}</div>`;
            } else if (data.type === 'error') {
                el.innerHTML = `<div class="empty-state"><p style="color:var(--danger)">${data.content}</p></div>`;
            } else if (data.type === 'typing') {
                return; // ignore typing
            }
            ws.onmessage = origHandler;
        };
    }
}

// ---- Chat ----
function renderChat(el) {
    el.innerHTML = `
        <div class="chat-container">
            <div class="page-header" style="margin-bottom:12px">
                <div><h2>Agent Chat</h2><div class="subtitle">Talk to your AI agents</div></div>
            </div>
            <div class="chat-messages" id="chatMessages"></div>
            <div class="chat-input-area">
                <div class="chat-input-wrap">
                    <textarea id="chatInput" rows="1" placeholder="Type a message or command..."></textarea>
                    <button class="chat-btn" id="chatVoice" title="Voice">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/></svg>
                    </button>
                    <button class="chat-btn" id="chatSend" title="Send">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                    </button>
                </div>
            </div>
        </div>
    `;

    // Restore chat history
    const area = document.getElementById('chatMessages');
    if (chatHistory.length === 0) {
        area.innerHTML = '<div class="empty-state" style="padding:30px"><p>Type a message or use commands like /browse, /inbox, /help</p></div>';
    } else {
        chatHistory.forEach(msg => {
            const div = document.createElement('div');
            div.className = `chat-msg chat-msg-${msg.type}`;
            div.innerHTML = msg.html;
            area.appendChild(div);
        });
        area.scrollTop = area.scrollHeight;
    }

    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');
    const chatVoice = document.getElementById('chatVoice');

    // Restore draft text
    if (chatInputDraft) {
        chatInput.value = chatInputDraft;
        chatSend.classList.add('send-active');
    }

    chatSend.addEventListener('click', sendChat);
    chatInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } });
    chatInput.addEventListener('input', () => {
        chatSend.classList.toggle('send-active', !!chatInput.value.trim());
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 100) + 'px';
        chatInputDraft = chatInput.value;
    });

    // Voice
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recog = new SR();
        recog.continuous = false; recog.interimResults = false; recog.lang = 'en-US';
        let recording = false;
        recog.onresult = e => { chatInput.value += e.results[0][0].transcript; chatInput.dispatchEvent(new Event('input')); };
        recog.onend = () => { recording = false; chatVoice.classList.remove('recording'); };
        chatVoice.addEventListener('click', () => { if (recording) recog.stop(); else { recog.start(); recording = true; chatVoice.classList.add('recording'); }});
    }
}

function sendChat() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text || !ws) return;

    addChatMsg(text, 'user');
    ws.send(JSON.stringify({ type: 'message', content: text }));
    input.value = '';
    chatInputDraft = '';
    input.style.height = 'auto';
    document.getElementById('chatSend').classList.remove('send-active');
}

// Auto-refresh: reload current page data when server pushes changes
let lastRefresh = 0;
function handleAutoRefresh() {
    const now = Date.now();
    if (now - lastRefresh < 2000) return; // Debounce: max 1 refresh per 2s
    lastRefresh = now;

    const main = document.getElementById('mainContent');
    if (!main) return;

    const pages = {
        dashboard: renderDashboard, clients: renderClients, content: renderContent,
        tasks: renderTasks, leads: renderLeads, pipeline: renderPipeline,
        media: renderMediaLibrary,
    };
    const fn = pages[currentPage];
    if (fn) fn(main);
}

function handleWSMessage(data) {
    // Auto-refresh UI when data changes
    if (data.type === 'refresh') {
        handleAutoRefresh();
        return;
    }

    // Route agent/meeting events to the office chat handler
    if (data.type === 'agent_reply' || data.type === 'meeting_reply' ||
        data.type === 'agent_typing' || data.type === 'meeting_typing') {
        handleAgentReply(data);
        return;
    }

    removeChatTyping();
    if (data.type === 'reply') addChatMsg(data.content, 'agent');
    else if (data.type === 'error') addChatMsg(data.content, 'error');
    else if (data.type === 'status') addChatMsg(data.content, 'status');
    else if (data.type === 'typing') showChatTyping();
    else if (data.type === 'confirm') addChatMsg(data.content, 'agent');
}

function addChatMsg(content, type) {
    const html = type === 'user' ? escapeHTML(content) : formatMD(content);

    // Always save to history (so it persists across page switches)
    if (type !== 'status') {
        chatHistory.push({ content, type, html });
    }

    // Only render if chat page is visible
    const area = document.getElementById('chatMessages');
    if (!area) return;
    const empty = area.querySelector('.empty-state');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = `chat-msg chat-msg-${type}`;
    div.innerHTML = html;
    area.appendChild(div);
    area.scrollTop = area.scrollHeight;
}

function showChatTyping() {
    const area = document.getElementById('chatMessages');
    if (!area || area.querySelector('.chat-typing')) return;
    const div = document.createElement('div');
    div.className = 'chat-typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    area.appendChild(div);
    area.scrollTop = area.scrollHeight;
}

function removeChatTyping() {
    const t = document.querySelector('.chat-typing');
    if (t) t.remove();
}

// ---- Design Studio ----
function renderDesignStudio(el) {
    el.innerHTML = `
        <div class="page-header">
            <div><h2>Design Studio</h2><div class="subtitle">AI-powered image & visual generation</div></div>
        </div>

        <div class="stat-card" style="margin-bottom:20px">
            <div class="section-title" style="margin-bottom:12px">Generate Image</div>
            <div class="form-group">
                <label>Prompt</label>
                <textarea id="imgPrompt" rows="3" placeholder="Describe the image you want... e.g. 'Luxury Dubai penthouse with panoramic skyline view, golden hour lighting, modern interior design, cinematic photography'"></textarea>
            </div>
            <div style="display:flex;gap:10px;margin-bottom:14px">
                <div class="form-group" style="flex:1">
                    <label>Size</label>
                    <select id="imgSize">
                        <option value="1024x1024">Square (Instagram Post)</option>
                        <option value="1024x1792">Portrait (Stories/Reels)</option>
                        <option value="1792x1024">Landscape (Facebook/YouTube)</option>
                    </select>
                </div>
                <div class="form-group" style="flex:1">
                    <label>Style</label>
                    <select id="imgStyle">
                        <option value="vivid">Vivid (Dramatic)</option>
                        <option value="natural">Natural (Realistic)</option>
                    </select>
                </div>
                <div class="form-group" style="flex:1">
                    <label>Link to Content</label>
                    <select id="imgContentId"><option value="">None</option></select>
                </div>
            </div>
            <button class="btn btn-primary" id="generateBtn" onclick="generateImage()">Generate Image</button>
            <div id="generateStatus" style="margin-top:12px"></div>
        </div>

        <div class="section">
            <div class="section-title">Generated Images</div>
            <div id="generatedGallery" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px">Loading...</div>
        </div>
    `;
    loadDesignData();
}

async function loadDesignData() {
    // Load content for linking dropdown
    try {
        const content = await (await fetch('/api/content')).json();
        const sel = document.getElementById('imgContentId');
        if (sel && content.length) {
            sel.innerHTML = '<option value="">None</option>' + content.map(c =>
                `<option value="${c.id}">[${c.platform}] ${(c.caption||'').substring(0,40)}...</option>`
            ).join('');
        }
    } catch(e) {}

    // Load generated images from agent logs
    try {
        const logs = await (await fetch('/api/agent-logs?agent=designer&limit=20')).json();
        const gallery = document.getElementById('generatedGallery');
        if (!gallery) return;

        const imgLogs = logs.filter(l => l.action === 'generate_image');
        if (!imgLogs.length) {
            gallery.innerHTML = '<div class="empty-state"><p>No images generated yet. Use the form above or ask the agent in chat.</p></div>';
            return;
        }

        gallery.innerHTML = imgLogs.map(log => {
            let imgPath = '';
            let prompt = '';
            try {
                const details = log.details || '';
                const resultMatch = details.match(/Result: ({.*})/s);
                if (resultMatch) {
                    const result = JSON.parse(resultMatch[1]);
                    imgPath = result.local_path || '';
                    prompt = result.revised_prompt || '';
                }
                const argsMatch = details.match(/Args: ({.*?})\n/s);
                if (argsMatch && !prompt) {
                    const args = JSON.parse(argsMatch[1]);
                    prompt = args.prompt || '';
                }
            } catch(e) {}

            if (!imgPath) return '';

            return `
                <div class="stat-card" style="padding:0;overflow:hidden">
                    <img src="${imgPath}" style="width:100%;height:200px;object-fit:cover" onerror="this.style.display='none'">
                    <div style="padding:12px">
                        <div style="font-size:12px;color:var(--text-secondary);line-height:1.4">${escapeHTML((prompt||'').substring(0,100))}...</div>
                        <div style="font-size:11px;color:var(--text-muted);margin-top:6px">${new Date(log.created_at).toLocaleString()}</div>
                    </div>
                </div>
            `;
        }).filter(Boolean).join('') || '<div class="empty-state"><p>No images yet.</p></div>';
    } catch(e) {
        console.error(e);
    }
}

async function generateImage() {
    const prompt = document.getElementById('imgPrompt').value.trim();
    if (!prompt) return;

    const size = document.getElementById('imgSize').value;
    const style = document.getElementById('imgStyle').value;
    const contentId = document.getElementById('imgContentId').value;

    const btn = document.getElementById('generateBtn');
    const status = document.getElementById('generateStatus');
    btn.disabled = true;
    btn.textContent = 'Generating...';
    status.innerHTML = '<span style="color:var(--accent)">AI is creating your image... this may take 10-20 seconds</span>';

    try {
        // Send through chat brain so it gets logged properly
        const msg = contentId
            ? `Generate an image for content ID ${contentId}: "${prompt}" — size: ${size}, style: ${style}`
            : `Generate an image: "${prompt}" — size: ${size}, style: ${style}`;

        ws.send(JSON.stringify({ type: 'message', content: msg }));

        // Wait for response
        const origHandler = ws.onmessage;
        ws.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.type === 'reply') {
                status.innerHTML = `<span style="color:var(--success)">Image generated!</span>`;
                btn.disabled = false;
                btn.textContent = 'Generate Image';
                loadDesignData(); // Refresh gallery
                ws.onmessage = origHandler;
            } else if (data.type === 'error') {
                status.innerHTML = `<span style="color:var(--danger)">${data.content}</span>`;
                btn.disabled = false;
                btn.textContent = 'Generate Image';
                ws.onmessage = origHandler;
            }
        };
    } catch(e) {
        status.innerHTML = `<span style="color:var(--danger)">Error: ${e.message}</span>`;
        btn.disabled = false;
        btn.textContent = 'Generate Image';
    }
}

// ---- Video Studio ----
let vsTab = 'create';
let currentProject = null; // { video, voiceover, subtitles, clips:[], script, prompt }

// ---- Timeline Editor State ----
const TL = {
    clips: [],           // [{id, filename, path, duration, startTime, thumbUrl, type:'video'|'image'}]
    voiceover: null,     // {filename, path, duration}
    music: null,         // {filename, path, duration}
    totalDuration: 0,
    playheadTime: 0,
    playing: false,
    zoom: 1,             // px per second
    selectedClipIdx: -1,
    cutMode: false,
    draggingClip: null,
    format: '9:16',      // '9:16' | '16:9' | '1:1'
    pixelsPerSec: 80,
    scrollLeft: 0,
    animFrame: null,
    videoEl: null,
    activeClipIdx: 0,
    clipStartedAt: 0,    // performance.now() when clip play started
};

function tlFormatDims() {
    if (TL.format === '9:16') return { w: 1080, h: 1920, label: 'Reel 9:16' };
    if (TL.format === '16:9') return { w: 1920, h: 1080, label: 'YouTube 16:9' };
    return { w: 1080, h: 1080, label: 'Square 1:1' };
}

function tlFmt(s) {
    if (!s || isNaN(s)) s = 0;
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = Math.floor(s % 60);
    const ms = Math.floor((s % 1) * 100);
    if (h > 0) return `${h}:${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;
    return `${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}.${ms.toString().padStart(2,'0')}`;
}

function tlRecalc() {
    let t = 0;
    TL.clips.forEach(c => { c.startTime = t; t += c.duration; });
    TL.totalDuration = t;
}

async function tlProbeFile(filename) {
    const r = await fetch('/api/video/probe', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ filename })
    });
    return r.json();
}

async function tlGetThumb(filename) {
    const r = await fetch('/api/video/thumbnail', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ filename })
    });
    const d = await r.json();
    return d.path || '';
}

function renderVideoStudio(el) {
    el.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
            <div><h2 style="font-size:22px">Video Studio</h2></div>
            <div style="display:flex;gap:4px;background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:3px">
                <button class="vs-tab" data-tab="editor" onclick="switchVsTab('editor')">Editor</button>
                <button class="vs-tab" data-tab="create" onclick="switchVsTab('create')">AI Generate</button>
                <button class="vs-tab" data-tab="voiceover" onclick="switchVsTab('voiceover')">Voiceover</button>
                <button class="vs-tab" data-tab="projects" onclick="switchVsTab('projects')">My Projects</button>
            </div>
        </div>
        <div id="vsContent"></div>
    `;
    switchVsTab('editor');
}

function switchVsTab(tab) {
    vsTab = tab;
    document.querySelectorAll('.vs-tab').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.vs-tab[data-tab="${tab}"]`);
    if (btn) btn.classList.add('active');

    const el = document.getElementById('vsContent');

    // Migrate old currentProject clips (string paths) to TL format when opening editor
    if (tab === 'editor' && currentProject) {
        const oldClips = currentProject.clips || [];
        const hasOldClips = oldClips.length > 0 && typeof oldClips[0] === 'string';
        const hasVideo = currentProject.video && TL.clips.length === 0;

        if (hasOldClips && TL.clips.length === 0) {
            (async () => {
                for (const path of oldClips) {
                    const filename = path.replace('/uploads/', '');
                    const isVid = path.endsWith('.mp4') || path.endsWith('.mov');
                    const clip = {
                        id: Date.now() + Math.random(),
                        filename, path,
                        duration: isVid ? 0 : 5,
                        startTime: 0,
                        thumbUrl: isVid ? '' : path,
                        type: isVid ? 'video' : 'image',
                    };
                    if (isVid) {
                        const info = await tlProbeFile(filename);
                        clip.duration = info.duration || 5;
                        const th = await tlGetThumb(filename);
                        clip.thumbUrl = th;
                    }
                    TL.clips.push(clip);
                }
                tlRecalc();
                ve2RenderMediaBin();
                ve2RenderTracks();
                ve2DrawRuler();
                if (TL.clips.length) ve2PreviewClip(0);
            })();
        } else if (hasVideo && !hasOldClips) {
            const filename = currentProject.video.replace('/uploads/', '');
            (async () => {
                const info = await tlProbeFile(filename);
                const th = await tlGetThumb(filename);
                TL.clips = [{
                    id: Date.now(),
                    filename, path: currentProject.video,
                    duration: info.duration || 10,
                    startTime: 0,
                    thumbUrl: th,
                    type: 'video',
                }];
                tlRecalc();
                ve2RenderMediaBin();
                ve2RenderTracks();
                ve2DrawRuler();
                ve2PreviewClip(0);
            })();
        }

        // Migrate voiceover
        if (currentProject.voiceover && !TL.voiceover) {
            const voFilename = currentProject.voiceover.replace('/uploads/', '');
            tlProbeFile(voFilename).then(info => {
                TL.voiceover = { filename: voFilename, path: currentProject.voiceover, duration: info.duration || 10 };
                ve2RenderTracks();
            });
        }
    }

    if (tab === 'create') renderVsCreate(el);
    else if (tab === 'editor') renderVsEditor(el);
    else if (tab === 'voiceover') renderVsVoiceover(el);
    else if (tab === 'projects') renderVsProjects(el);
}

function renderVsCreate(el) {
    el.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div>
                <div class="stat-card">
                    <div class="form-group">
                        <label>What should the video show?</label>
                        <textarea id="vidPrompt" rows="3" placeholder="Luxury Dubai penthouse tour, aerial shots of Palm Jumeirah, yacht at sunset..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Voiceover script</label>
                        <textarea id="vidScript" rows="3" placeholder="Welcome to the most exclusive lifestyle in Dubai..."></textarea>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
                        <div class="form-group">
                            <label>Duration</label>
                            <select id="vidClips">
                                <option value="3">15s</option><option value="4">20s</option>
                                <option value="5">25s</option><option value="6" selected>30s</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Format</label>
                            <select id="vidRatio">
                                <option value="9:16" selected>Reel 9:16</option>
                                <option value="16:9">YouTube 16:9</option>
                                <option value="1:1">Square 1:1</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Voice</label>
                            <select id="vidVoice">
                                <option value="onyx">Onyx (Male)</option><option value="nova">Nova (Female)</option>
                                <option value="alloy">Alloy (Neutral)</option><option value="shimmer">Shimmer (Soft)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Import video/image</label>
                            <input type="file" id="vidImport" accept="video/*,image/*" style="font-size:12px">
                        </div>
                    </div>
                    <button class="btn btn-primary" style="width:100%;padding:12px;font-size:14px" id="vidGenBtn" onclick="generateVideo()">Generate Video</button>
                    <div id="vidStatus" style="margin-top:10px"></div>
                </div>
            </div>
            <div>
                <div class="stat-card" style="min-height:400px;display:flex;flex-direction:column;align-items:center;justify-content:center" id="vidPreview">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
                    <div style="color:var(--text-muted);font-size:13px;margin-top:12px">Video preview will appear here</div>
                </div>
            </div>
        </div>
    `;
}

// ========================
// CAPCUT-STYLE VIDEO EDITOR
// ========================

function renderVsEditor(el) {
    if (!currentProject) {
        currentProject = { video: null, clips: [], voiceover: null, subtitles: null, script: '', prompt: '', caption: '', music: null };
    }

    const dims = tlFormatDims();
    const previewRatio = TL.format === '16:9' ? '56.25%' : (TL.format === '1:1' ? '100%' : '177.78%');
    const previewMaxH = TL.format === '16:9' ? '340px' : (TL.format === '1:1' ? '340px' : '420px');
    const previewMaxW = TL.format === '16:9' ? '100%' : (TL.format === '1:1' ? '340px' : '236px');

    el.innerHTML = `
        <!-- Top: Editor Layout -->
        <div class="ve2-top">
            <!-- Left: Media bin + tools -->
            <div class="ve2-sidebar">
                <div class="ve2-sidebar-tabs">
                    <button class="ve2-stab active" data-panel="ve2Media" onclick="ve2PanelTab(this)">Media</button>
                    <button class="ve2-stab" data-panel="ve2Audio" onclick="ve2PanelTab(this)">Audio</button>
                    <button class="ve2-stab" data-panel="ve2Text" onclick="ve2PanelTab(this)">Text</button>
                </div>

                <div class="ve2-panel" id="ve2Media">
                    <div style="display:flex;gap:4px;margin-bottom:8px">
                        <button class="btn btn-primary btn-sm" style="flex:1;font-size:10px" onclick="ve2ImportFiles()">+ Import</button>
                        <button class="btn btn-secondary btn-sm" style="flex:1;font-size:10px" onclick="ve2ImportFromLibrary()">Library</button>
                    </div>
                    <div class="ve2-media-grid" id="ve2MediaGrid"></div>
                </div>

                <div class="ve2-panel" id="ve2Audio" style="display:none">
                    <div class="ve-section-title">Voiceover</div>
                    ${TL.voiceover ? `<audio controls style="width:100%;height:28px;margin-bottom:6px"><source src="${TL.voiceover.path}" type="audio/mpeg"></audio>` : ''}
                    <textarea id="ve2Script" rows="3" class="ve2-textarea" placeholder="Voiceover script...">${escapeHTML(currentProject.script||'')}</textarea>
                    <div style="display:flex;gap:4px;margin-top:4px">
                        <select id="ve2Voice" class="ve2-select">
                            <option value="onyx">Onyx</option><option value="nova">Nova</option><option value="alloy">Alloy</option><option value="shimmer">Shimmer</option>
                        </select>
                        <button class="btn btn-primary btn-sm" style="font-size:10px" onclick="ve2GenVoiceover()">Generate</button>
                    </div>
                    <div class="ve-section-title" style="margin-top:14px">Music</div>
                    <div style="border:2px dashed var(--border);border-radius:6px;padding:10px;text-align:center;cursor:pointer;position:relative">
                        <div style="color:var(--text-muted);font-size:11px">${TL.music ? TL.music.filename : 'Drop or click to add music'}</div>
                        <input type="file" id="ve2MusicFile" accept="audio/*" style="position:absolute;inset:0;opacity:0;cursor:pointer">
                    </div>
                </div>

                <div class="ve2-panel" id="ve2Text" style="display:none">
                    <div class="ve-section-title">Caption</div>
                    <textarea id="ve2Caption" rows="5" class="ve2-textarea" placeholder="Write caption with hashtags...">${escapeHTML(currentProject.caption||'')}</textarea>
                    <button class="btn btn-secondary" style="width:100%;margin-top:6px;font-size:11px" onclick="ve2AiCaption()">AI Write Caption</button>
                </div>
            </div>

            <!-- Center: Preview Monitor -->
            <div class="ve2-monitor">
                <div class="ve2-format-bar">
                    <select id="ve2FormatSel" class="ve2-format-select" onchange="ve2ChangeFormat(this.value)">
                        <option value="9:16" ${TL.format==='9:16'?'selected':''}>Reel 9:16</option>
                        <option value="16:9" ${TL.format==='16:9'?'selected':''}>YouTube 16:9</option>
                        <option value="1:1" ${TL.format==='1:1'?'selected':''}>Square 1:1</option>
                    </select>
                    <span class="ve2-format-label">${dims.w}x${dims.h}</span>
                </div>
                <div class="ve2-preview-wrap" style="max-width:${previewMaxW};max-height:${previewMaxH}">
                    <div class="ve2-preview-container" id="ve2Preview" style="aspect-ratio:${dims.w}/${dims.h}">
                        <div class="ve2-preview-empty" id="ve2PreviewEmpty">
                            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
                            <div>Import media to start editing</div>
                        </div>
                        <video id="ve2Video" style="display:none;width:100%;height:100%;object-fit:contain" playsinline preload="auto"></video>
                        <img id="ve2Img" style="display:none;width:100%;height:100%;object-fit:contain">
                    </div>
                </div>
                <!-- Transport controls -->
                <div class="ve2-transport">
                    <button class="ve2-tbtn" onclick="ve2SkipBack()" title="Back 5s">&#9198;</button>
                    <button class="ve2-tbtn ve2-play-btn" id="ve2PlayBtn" onclick="ve2TogglePlay()" title="Play / Pause">&#9654;</button>
                    <button class="ve2-tbtn" onclick="ve2SkipFwd()" title="Forward 5s">&#9197;</button>
                    <div class="ve2-time" id="ve2TimeDisplay">${tlFmt(0)} / ${tlFmt(0)}</div>
                </div>
                <div class="ve2-action-bar">
                    <button class="btn btn-primary btn-sm" onclick="ve2ExportVideo()">Export / Render</button>
                    <button class="btn btn-secondary btn-sm" onclick="ve2Download()">Download</button>
                    <button class="btn btn-sm" style="background:var(--success);color:#fff" onclick="ve2SendPipeline()">Send to Pipeline</button>
                </div>
            </div>

            <!-- Right: Properties panel -->
            <div class="ve2-props" id="ve2Props">
                <div class="ve-section-title">Properties</div>
                <div id="ve2PropsContent" style="font-size:12px;color:var(--text-muted)">Select a clip to see properties</div>
            </div>
        </div>

        <!-- Resize handle between preview and timeline -->
        <div class="ve2-resizer" id="ve2Resizer" onmousedown="ve2ResizerStart(event)">
            <div class="ve2-resizer-grip"></div>
        </div>

        <!-- Bottom: Timeline -->
        <div class="ve2-timeline" id="ve2TimelinePanel">
            <!-- Timeline toolbar -->
            <div class="ve2-tl-toolbar">
                <div style="display:flex;gap:3px">
                    <button class="ve2-tool-btn ${TL.cutMode?'':'active'}" id="ve2SelectBtn" onclick="ve2SetSelectMode()" title="Select tool (V)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/></svg>
                    </button>
                    <button class="ve2-tool-btn ${TL.cutMode?'active':''}" id="ve2CutBtn" onclick="ve2ToggleCut()" title="Cut tool — click on a clip to split it (C)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>
                    </button>
                    <div style="width:1px;height:22px;background:var(--border);margin:0 2px"></div>
                    <button class="ve2-tool-btn" onclick="ve2SplitAtPlayhead()" title="Split at playhead position">Split</button>
                    <button class="ve2-tool-btn" onclick="ve2DeleteSelected()" title="Delete selected clip (Del)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                    <button class="ve2-tool-btn" onclick="ve2DuplicateSelected()" title="Duplicate selected clip">Dup</button>
                    <button class="ve2-tool-btn" onclick="ve2ReplaceSelected()" title="Replace selected clip">Replace</button>
                </div>
                <div style="width:1px;height:22px;background:var(--border);margin:0 2px"></div>
                <div id="ve2ToolStatus" style="font-size:10px;color:var(--text-muted)">${TL.cutMode ? 'Cut mode: click on clips to split' : 'Select mode'}</div>
                <div style="flex:1"></div>
                <div style="display:flex;align-items:center;gap:6px">
                    <button class="ve2-tool-btn" onclick="ve2ZoomOut()">-</button>
                    <input type="range" id="ve2Zoom" min="20" max="300" value="80" style="width:100px;accent-color:var(--accent)" oninput="ve2SetZoom(+this.value)">
                    <button class="ve2-tool-btn" onclick="ve2ZoomIn()">+</button>
                    <span style="font-size:10px;color:var(--text-muted);min-width:35px" id="ve2ZoomLabel">80px/s</span>
                </div>
            </div>

            <!-- Ruler + playhead -->
            <div class="ve2-tl-ruler-wrap" id="ve2RulerWrap">
                <div class="ve2-tl-label-spacer"></div>
                <div class="ve2-tl-ruler" id="ve2Ruler" onmousedown="ve2RulerMouseDown(event)">
                    <canvas id="ve2RulerCanvas" height="28"></canvas>
                    <div class="ve2-playhead" id="ve2Playhead">
                        <div class="ve2-playhead-head"></div>
                        <div class="ve2-playhead-line"></div>
                    </div>
                </div>
            </div>

            <!-- Tracks -->
            <div class="ve2-tl-body" id="ve2TlBody">
                <div class="ve2-tl-row">
                    <div class="ve2-tl-label">&#127909; Video</div>
                    <div class="ve2-tl-track" id="ve2VideoTrack" data-track="video"></div>
                </div>
                <div class="ve2-tl-row">
                    <div class="ve2-tl-label">&#127908; Voice</div>
                    <div class="ve2-tl-track" id="ve2VoiceTrack" data-track="voice"></div>
                </div>
                <div class="ve2-tl-row">
                    <div class="ve2-tl-label">&#127925; Music</div>
                    <div class="ve2-tl-track" id="ve2MusicTrack" data-track="music"></div>
                </div>
            </div>
        </div>
    `;

    // Initialize
    setTimeout(() => {
        ve2RenderMediaBin();
        ve2RenderTracks();
        ve2DrawRuler();
        ve2SyncPlayhead();
        ve2SetupKeyboard();
        ve2SetupMusicInput();
        ve2SetupDragDrop();
    }, 50);
}

// -- Panel tab switching --
function ve2PanelTab(btn) {
    document.querySelectorAll('.ve2-stab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.ve2-panel').forEach(p => p.style.display = 'none');
    document.getElementById(btn.dataset.panel).style.display = 'block';
}

// -- Format change --
function ve2ChangeFormat(fmt) {
    TL.format = fmt;
    switchVsTab('editor');
}

// -- Media bin --
function ve2RenderMediaBin() {
    const grid = document.getElementById('ve2MediaGrid');
    if (!grid) return;
    const allMedia = [...TL.clips];
    if (!allMedia.length) {
        grid.innerHTML = '<div style="color:var(--text-muted);font-size:11px;padding:10px;text-align:center">No clips yet. Import media to start.</div>';
        return;
    }
    grid.innerHTML = allMedia.map((c, i) => {
        const isVid = c.type === 'video';
        const thumb = c.thumbUrl || c.path;
        return `<div class="ve2-media-item ${TL.selectedClipIdx===i?'selected':''}" onclick="ve2SelectClip(${i})" draggable="true" ondragstart="ve2ClipDragStart(event,${i})">
            ${isVid ? `<video src="${c.path}" style="width:100%;height:50px;object-fit:cover;border-radius:4px;pointer-events:none" preload="metadata"></video>` :
                      `<img src="${thumb}" style="width:100%;height:50px;object-fit:cover;border-radius:4px">`}
            <div class="ve2-media-dur">${tlFmt(c.duration)}</div>
            <div class="ve2-media-del" onclick="event.stopPropagation();ve2RemoveClip(${i})">x</div>
        </div>`;
    }).join('');
}

// -- Import files --
function ve2ImportFiles() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'video/*,image/*';
    input.multiple = true;
    input.onchange = async (e) => {
        for (const file of e.target.files) {
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch('/upload', { method: 'POST', body: formData });
            const data = await res.json();
            const isVid = file.type.startsWith('video/');
            const clip = {
                id: Date.now() + Math.random(),
                filename: data.filename,
                path: `/uploads/${data.filename}`,
                duration: isVid ? 0 : 5,
                startTime: 0,
                thumbUrl: '',
                type: isVid ? 'video' : 'image',
            };
            if (isVid) {
                const info = await tlProbeFile(data.filename);
                clip.duration = info.duration || 5;
                const th = await tlGetThumb(data.filename);
                clip.thumbUrl = th;
            } else {
                clip.thumbUrl = clip.path;
            }
            TL.clips.push(clip);
        }
        tlRecalc();
        ve2RenderMediaBin();
        ve2RenderTracks();
        ve2DrawRuler();
        ve2PreviewClip(0);
    };
    input.click();
}

async function ve2ImportFromLibrary() {
    const media = await (await fetch('/api/media')).json();
    const items = media.filter(f => f.type === 'video' || f.type === 'image');
    if (!items.length) { alert('No media in library'); return; }

    // Show a quick picker modal
    const modal = document.createElement('div');
    modal.className = 've2-modal-overlay';
    modal.innerHTML = `<div class="ve2-modal">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3 style="margin:0;font-size:16px">Import from Library</h3>
            <button onclick="this.closest('.ve2-modal-overlay').remove()" style="background:none;border:none;color:var(--text-secondary);font-size:18px;cursor:pointer">x</button>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px;max-height:400px;overflow-y:auto">
            ${items.map((f, i) => `
                <div class="ve2-lib-item" onclick="ve2AddFromLibrary('${f.name}','${f.type}');this.closest('.ve2-modal-overlay').remove()">
                    ${f.type === 'video' ?
                        `<video src="${f.path}" style="width:100%;height:80px;object-fit:cover;border-radius:4px;pointer-events:none" preload="metadata"></video>` :
                        `<img src="${f.path}" style="width:100%;height:80px;object-fit:cover;border-radius:4px">`}
                    <div style="font-size:10px;color:var(--text-muted);margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${f.name}</div>
                </div>`).join('')}
        </div>
    </div>`;
    document.body.appendChild(modal);
}

async function ve2AddFromLibrary(filename, type) {
    const isVid = type === 'video';
    const clip = {
        id: Date.now() + Math.random(),
        filename: filename,
        path: `/uploads/${filename}`,
        duration: isVid ? 0 : 5,
        startTime: 0,
        thumbUrl: '',
        type: isVid ? 'video' : 'image',
    };
    if (isVid) {
        const info = await tlProbeFile(filename);
        clip.duration = info.duration || 5;
        const th = await tlGetThumb(filename);
        clip.thumbUrl = th;
    } else {
        clip.thumbUrl = clip.path;
    }
    TL.clips.push(clip);
    tlRecalc();
    ve2RenderMediaBin();
    ve2RenderTracks();
    ve2DrawRuler();
    ve2PreviewClip(TL.clips.length - 1);
}

// -- Render timeline tracks --
function ve2RenderTracks() {
    const videoTrack = document.getElementById('ve2VideoTrack');
    const voiceTrack = document.getElementById('ve2VoiceTrack');
    const musicTrack = document.getElementById('ve2MusicTrack');
    if (!videoTrack) return;

    const pps = TL.pixelsPerSec;
    const totalW = Math.max(600, TL.totalDuration * pps + 100);

    // Video clips
    videoTrack.style.minWidth = totalW + 'px';
    videoTrack.onclick = ve2TrackClick;

    if (TL.clips.length === 0) {
        videoTrack.innerHTML = `<div class="ve2-tl-empty" style="width:${totalW}px" ondragover="event.preventDefault()" ondrop="ve2TrackDrop(event,'video')">Drop or import media to start editing</div>`;
    } else {
        videoTrack.innerHTML = TL.clips.map((c, i) => {
            const w = Math.max(20, c.duration * pps);
            const left = c.startTime * pps;
            const isVid = c.type === 'video';
            const sel = TL.selectedClipIdx === i ? 'selected' : '';
            const thumb = c.thumbUrl || c.path;
            // Repeat thumbnails to fill width
            const thumbCount = Math.max(1, Math.ceil(w / 50));
            const thumbs = Array.from({length: thumbCount}, () =>
                `<img src="${thumb}" class="ve2-clip-thumb">`
            ).join('');

            const borderColor = sel ? 'var(--accent)' : (isVid ? 'var(--info)' : '#27ae60');

            return `<div class="ve2-tl-clip ${sel}" data-idx="${i}"
                style="left:${left}px;width:${w}px;border-color:${borderColor}"
                onmousedown="ve2ClipMouseDown(event,${i})"
                ondragover="event.preventDefault()"
                ondrop="ve2ClipReorderDrop(event,${i})">
                <div class="ve2-clip-thumbs">${thumbs}</div>
                <div class="ve2-clip-label">${isVid ? '&#127909; ' : '&#128247; '}${c.filename.substring(0,18)}</div>
                <div class="ve2-clip-duration">${tlFmt(c.duration)}</div>
                ${sel ? '<div class="ve2-clip-sel-border"></div>' : ''}
                <div class="ve2-clip-handle ve2-clip-handle-l" onmousedown="ve2TrimStart(event,${i})" title="Trim start"></div>
                <div class="ve2-clip-handle ve2-clip-handle-r" onmousedown="ve2TrimEnd(event,${i})" title="Trim end"></div>
            </div>`;
        }).join('') + `<div style="width:100px;min-width:100px;flex-shrink:0"></div>`;
    }

    // Voiceover track
    if (TL.voiceover) {
        const w = TL.voiceover.duration * pps;
        voiceTrack.innerHTML = `<div class="ve2-tl-audio-block" style="width:${w}px;background:var(--accent)">${TL.voiceover.filename || 'Voiceover'}</div>`;
    } else {
        voiceTrack.innerHTML = '<div class="ve2-tl-empty-sm">No voiceover</div>';
    }

    // Music track
    if (TL.music) {
        const w = Math.min(TL.music.duration, TL.totalDuration || TL.music.duration) * pps;
        musicTrack.innerHTML = `<div class="ve2-tl-audio-block" style="width:${w}px;background:#9b59b6">${TL.music.filename || 'Music'}</div>`;
    } else {
        musicTrack.innerHTML = '<div class="ve2-tl-empty-sm">No music</div>';
    }

    // Update playhead line height
    ve2SyncPlayhead();
}

// -- Draw ruler with time marks --
function ve2DrawRuler() {
    const canvas = document.getElementById('ve2RulerCanvas');
    if (!canvas) return;
    const pps = TL.pixelsPerSec;
    const dur = Math.max(TL.totalDuration, 10);
    const totalW = dur * pps + 200;
    canvas.width = totalW;
    canvas.style.width = totalW + 'px';
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, totalW, 28);

    // Determine interval based on zoom
    let interval = 1;
    if (pps < 30) interval = 10;
    else if (pps < 60) interval = 5;
    else if (pps < 120) interval = 2;
    else interval = 1;

    ctx.fillStyle = '#888';
    ctx.font = '9px SF Mono, Monaco, monospace';
    ctx.textAlign = 'center';

    for (let t = 0; t <= dur + 5; t += interval) {
        const x = t * pps;
        ctx.fillStyle = '#555';
        ctx.fillRect(x, 18, 1, 10);
        ctx.fillStyle = '#999';
        ctx.fillText(tlFmt(t), x, 14);
    }
    // Sub-marks
    const subInterval = interval / (interval >= 5 ? 5 : 2);
    for (let t = 0; t <= dur + 5; t += subInterval) {
        const x = t * pps;
        ctx.fillStyle = '#333';
        ctx.fillRect(x, 22, 1, 6);
    }

    document.getElementById('ve2ZoomLabel').textContent = `${pps}px/s`;
}

// -- Playhead --
function ve2SyncPlayhead() {
    const ph = document.getElementById('ve2Playhead');
    if (!ph) return;
    const x = TL.playheadTime * TL.pixelsPerSec;
    ph.style.left = x + 'px';
    const timeEl = document.getElementById('ve2TimeDisplay');
    if (timeEl) timeEl.textContent = `${tlFmt(TL.playheadTime)} / ${tlFmt(TL.totalDuration)}`;
}

function ve2RulerMouseDown(e) {
    const ruler = document.getElementById('ve2Ruler');
    if (!ruler) return;

    // Pause playback while scrubbing
    const wasPlaying = TL.playing;
    if (wasPlaying) ve2StopPlay();

    const body = document.getElementById('ve2TlBody');
    const scrollLeft = body ? body.scrollLeft : 0;
    const rect = ruler.getBoundingClientRect();

    let lastPreviewTime = 0;
    const setTime = (ex) => {
        const x = ex - rect.left + scrollLeft;
        TL.playheadTime = Math.max(0, Math.min(TL.totalDuration, x / TL.pixelsPerSec));
        ve2SyncPlayhead();

        // Throttle preview updates to avoid hammering the video element
        const now = performance.now();
        if (now - lastPreviewTime > 80) {
            lastPreviewTime = now;
            ve2PreviewAtTime(TL.playheadTime);
        }
    };
    setTime(e.clientX);

    const onMove = (e2) => { e2.preventDefault(); setTime(e2.clientX); };
    const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        // Final preview at exact position
        ve2PreviewAtTime(TL.playheadTime);
        if (wasPlaying) ve2StartPlay();
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
}

// -- Preview --
// Track which source is currently loaded to avoid reloading
let ve2CurrentVideoSrc = '';

function ve2ShowVideo(vid, img, empty) {
    vid.style.display = 'block';
    img.style.display = 'none';
    if (empty) empty.style.display = 'none';
}

function ve2ShowImage(vid, img, empty, src) {
    vid.pause();
    vid.style.display = 'none';
    img.src = src;
    img.style.display = 'block';
    if (empty) empty.style.display = 'none';
}

function ve2LoadVideo(vid, src, seekTo, autoplay) {
    const encodedSrc = encodeURI(src);
    const fullSrc = encodedSrc.startsWith('http') ? encodedSrc : location.origin + encodedSrc;

    if (ve2CurrentVideoSrc === fullSrc && vid.readyState >= 1) {
        try { vid.currentTime = seekTo || 0; } catch(e) {}
        if (autoplay) vid.play().catch(() => { vid.muted = true; vid.play().catch(() => {}); });
        return;
    }

    ve2CurrentVideoSrc = fullSrc;
    vid.src = encodedSrc;
    vid.oncanplaythrough = () => {
        vid.oncanplaythrough = null;
        try { vid.currentTime = seekTo || 0; } catch(e) {}
        if (autoplay) vid.play().catch(() => { vid.muted = true; vid.play().catch(() => {}); });
    };
    vid.load();
}

function ve2PreviewClip(idx) {
    if (idx < 0 || idx >= TL.clips.length) return;
    const c = TL.clips[idx];
    const vid = document.getElementById('ve2Video');
    const img = document.getElementById('ve2Img');
    const empty = document.getElementById('ve2PreviewEmpty');
    if (!vid || !img) return;

    if (c.type === 'video') {
        ve2ShowVideo(vid, img, empty);
        vid.src = encodeURI(c.path);
        vid.load();
        ve2CurrentVideoSrc = location.origin + encodeURI(c.path);
    } else {
        ve2ShowImage(vid, img, empty, c.path);
    }
}

function ve2PreviewAtTime(t) {
    for (let i = 0; i < TL.clips.length; i++) {
        const c = TL.clips[i];
        if (t >= c.startTime && t < c.startTime + c.duration) {
            const vid = document.getElementById('ve2Video');
            const img = document.getElementById('ve2Img');
            const empty = document.getElementById('ve2PreviewEmpty');
            if (!vid || !img) return;

            if (c.type === 'video') {
                ve2ShowVideo(vid, img, empty);
                const encodedPath = encodeURI(c.path);
                const fullSrc = location.origin + encodedPath;
                const seekTo = t - c.startTime;

                if (ve2CurrentVideoSrc === fullSrc && vid.readyState >= 1) {
                    // Same source — just seek
                    try { vid.currentTime = seekTo; } catch(e) {}
                } else {
                    // Different source — load it then seek
                    ve2CurrentVideoSrc = fullSrc;
                    vid.src = encodedPath;
                    vid.onloadeddata = () => {
                        vid.onloadeddata = null;
                        try { vid.currentTime = seekTo; } catch(e) {}
                    };
                    vid.load();
                }
            } else {
                ve2ShowImage(vid, img, empty, c.path);
            }
            TL.activeClipIdx = i;
            return;
        }
    }
}

// -- Playback --
function ve2TogglePlay() {
    if (TL.playing) {
        ve2StopPlay();
    } else {
        ve2StartPlay();
    }
}

function ve2StartPlay() {
    if (TL.clips.length === 0) return;
    TL.playing = true;
    document.getElementById('ve2PlayBtn').innerHTML = '&#9646;&#9646;';

    if (TL.playheadTime >= TL.totalDuration) TL.playheadTime = 0;

    const vid = document.getElementById('ve2Video');
    const img = document.getElementById('ve2Img');
    const empty = document.getElementById('ve2PreviewEmpty');
    if (!vid) return;

    // Find starting clip
    let startIdx = TL.clips.findIndex(c => TL.playheadTime >= c.startTime && TL.playheadTime < c.startTime + c.duration);
    if (startIdx < 0) startIdx = 0;
    TL.activeClipIdx = startIdx;

    // Load and play the current clip, then start the tick loop
    ve2PlayClipAtIndex(startIdx, TL.playheadTime - TL.clips[startIdx].startTime, () => {
        TL.clipStartedAt = performance.now() - (TL.playheadTime * 1000);
        TL.animFrame = requestAnimationFrame(ve2PlayTick);
    });
}

// Load a specific clip into the preview and start playing it
function ve2PlayClipAtIndex(idx, seekTo, onReady) {
    const vid = document.getElementById('ve2Video');
    const img = document.getElementById('ve2Img');
    const empty = document.getElementById('ve2PreviewEmpty');
    if (!vid || idx < 0 || idx >= TL.clips.length) {
        if (onReady) onReady();
        return;
    }

    const c = TL.clips[idx];
    TL.activeClipIdx = idx;

    if (c.type !== 'video') {
        vid.pause();
        ve2ShowImage(vid, img, empty, c.path);
        if (onReady) onReady();
        return;
    }

    // Video clip — encode path for spaces/special chars
    const encodedPath = encodeURI(c.path);
    ve2ShowVideo(vid, img, empty);

    // Remove ALL old event listeners by cloning the element
    // This is the nuclear option but ensures no stale handlers
    const parent = vid.parentNode;
    const newVid = vid.cloneNode(false);
    newVid.id = 've2Video';
    newVid.style.cssText = 'width:100%;height:100%;object-fit:contain';
    newVid.playsinline = true;
    newVid.preload = 'auto';
    parent.replaceChild(newVid, vid);

    ve2CurrentVideoSrc = '';

    newVid.src = encodedPath;

    newVid.oncanplaythrough = () => {
        newVid.oncanplaythrough = null;
        newVid.onerror = null;
        try { newVid.currentTime = seekTo || 0; } catch(e) {}
        newVid.play().then(() => {
            if (onReady) onReady();
        }).catch(() => {
            newVid.muted = true;
            newVid.play().then(() => {
                if (onReady) onReady();
            }).catch(() => {
                if (onReady) onReady();
            });
        });
    };

    newVid.onerror = () => {
        console.error('[play] Failed to load video:', encodedPath);
        newVid.onerror = null;
        if (onReady) onReady();
    };

    newVid.load();

    // Safety timeout
    setTimeout(() => {
        if (newVid.oncanplaythrough) {
            newVid.oncanplaythrough = null;
            newVid.onerror = null;
            try { newVid.currentTime = seekTo || 0; } catch(e) {}
            newVid.play().catch(() => { newVid.muted = true; newVid.play().catch(() => {}); });
            if (onReady) onReady();
        }
    }, 3000);
}

// Main playback tick — uses real clock for timeline, syncs video position
function ve2PlayTick() {
    if (!TL.playing) return;

    const elapsed = (performance.now() - TL.clipStartedAt) / 1000;
    TL.playheadTime = elapsed;

    // End of timeline
    if (TL.playheadTime >= TL.totalDuration) {
        TL.playheadTime = TL.totalDuration;
        ve2StopPlay();
        ve2SyncPlayhead();
        return;
    }

    // Find which clip the playhead is on
    const curClipIdx = TL.clips.findIndex(c => TL.playheadTime >= c.startTime && TL.playheadTime < c.startTime + c.duration);

    // Need to switch to a new clip?
    if (curClipIdx >= 0 && curClipIdx !== TL.activeClipIdx) {
        ve2PlayClipAtIndex(curClipIdx, 0, null);
    }

    ve2SyncPlayhead();

    // Auto-scroll timeline
    const body = document.getElementById('ve2TlBody');
    const rulerWrap = document.getElementById('ve2RulerWrap');
    if (body) {
        const phX = TL.playheadTime * TL.pixelsPerSec;
        if (phX > body.scrollLeft + body.clientWidth - 100) {
            body.scrollLeft = phX - 100;
            if (rulerWrap) rulerWrap.scrollLeft = body.scrollLeft;
        }
    }

    TL.animFrame = requestAnimationFrame(ve2PlayTick);
}

function ve2StopPlay() {
    TL.playing = false;
    if (TL.animFrame) cancelAnimationFrame(TL.animFrame);
    const btn = document.getElementById('ve2PlayBtn');
    if (btn) btn.innerHTML = '&#9654;';
    const vid = document.getElementById('ve2Video');
    if (vid) {
        vid.pause();
        vid.oncanplaythrough = null;
        vid.oncanplay = null;
        vid.onloadeddata = null;
        vid.onerror = null;
    }
}

function ve2SkipBack() {
    TL.playheadTime = Math.max(0, TL.playheadTime - 5);
    ve2SyncPlayhead();
    ve2PreviewAtTime(TL.playheadTime);
    if (TL.playing) TL.clipStartedAt = performance.now() - (TL.playheadTime * 1000);
}

function ve2SkipFwd() {
    TL.playheadTime = Math.min(TL.totalDuration, TL.playheadTime + 5);
    ve2SyncPlayhead();
    ve2PreviewAtTime(TL.playheadTime);
    if (TL.playing) TL.clipStartedAt = performance.now() - (TL.playheadTime * 1000);
}

// -- Select / deselect clips --
function ve2SelectClip(idx) {
    const prev = TL.selectedClipIdx;
    TL.selectedClipIdx = idx;

    // Update selection visually without full re-render
    document.querySelectorAll('.ve2-tl-clip').forEach((el, i) => {
        if (i === idx) {
            el.classList.add('selected');
            el.style.borderColor = 'var(--accent)';
            // Add selection border if not present
            if (!el.querySelector('.ve2-clip-sel-border')) {
                const selBorder = document.createElement('div');
                selBorder.className = 've2-clip-sel-border';
                el.appendChild(selBorder);
            }
        } else {
            el.classList.remove('selected');
            const c = TL.clips[i];
            el.style.borderColor = c?.type === 'video' ? 'var(--info)' : '#27ae60';
            const sb = el.querySelector('.ve2-clip-sel-border');
            if (sb) sb.remove();
        }
    });

    // Update media bin selection
    document.querySelectorAll('.ve2-media-item').forEach((el, i) => {
        el.classList.toggle('selected', i === idx);
    });

    ve2PreviewClip(idx);
    ve2UpdateProps(idx);
}

function ve2UpdateProps(idx) {
    const el = document.getElementById('ve2PropsContent');
    if (!el || idx < 0 || idx >= TL.clips.length) {
        if (el) el.innerHTML = '<div style="color:var(--text-muted)">Select a clip to see properties</div>';
        return;
    }
    const c = TL.clips[idx];
    el.innerHTML = `
        <div style="margin-bottom:8px"><strong style="color:var(--text-primary)">${c.filename}</strong></div>
        <div style="display:grid;gap:6px">
            <div class="ve2-prop-row"><span>Type</span><span>${c.type}</span></div>
            <div class="ve2-prop-row"><span>Duration</span><span>${tlFmt(c.duration)}</span></div>
            <div class="ve2-prop-row"><span>Start</span><span>${tlFmt(c.startTime)}</span></div>
            <div class="ve2-prop-row"><span>Index</span><span>${idx + 1} of ${TL.clips.length}</span></div>
        </div>
        <div style="margin-top:10px">
            <label style="font-size:11px;color:var(--text-secondary)">Clip duration (sec)</label>
            <input type="number" value="${c.duration.toFixed(1)}" min="0.5" step="0.5" style="width:100%;margin-top:4px;padding:6px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:12px" onchange="ve2SetClipDuration(${idx},+this.value)">
        </div>
        <div style="margin-top:8px;display:flex;gap:4px">
            <button class="btn btn-secondary btn-sm" style="flex:1;font-size:10px" onclick="ve2MoveClip(${idx},-1)">Move Left</button>
            <button class="btn btn-secondary btn-sm" style="flex:1;font-size:10px" onclick="ve2MoveClip(${idx},1)">Move Right</button>
        </div>
        <button class="btn btn-sm" style="width:100%;margin-top:6px;font-size:10px;background:var(--danger);color:#fff" onclick="ve2RemoveClip(${idx})">Remove Clip</button>
    `;
}

function ve2SetClipDuration(idx, dur) {
    if (dur < 0.5) dur = 0.5;
    TL.clips[idx].duration = dur;
    tlRecalc();
    ve2RenderTracks();
    ve2DrawRuler();
    ve2UpdateProps(idx);
}

// -- Clip operations --
function ve2RemoveClip(idx) {
    TL.clips.splice(idx, 1);
    TL.selectedClipIdx = -1;
    tlRecalc();
    ve2RenderMediaBin();
    ve2RenderTracks();
    ve2DrawRuler();
    ve2UpdateProps(-1);
    if (TL.clips.length === 0) {
        document.getElementById('ve2PreviewEmpty').style.display = 'flex';
        document.getElementById('ve2Video').style.display = 'none';
        document.getElementById('ve2Img').style.display = 'none';
    }
}

function ve2DeleteSelected() {
    if (TL.selectedClipIdx >= 0) ve2RemoveClip(TL.selectedClipIdx);
}

function ve2DuplicateSelected() {
    const idx = TL.selectedClipIdx;
    if (idx < 0 || idx >= TL.clips.length) return;
    const clone = { ...TL.clips[idx], id: Date.now() + Math.random() };
    TL.clips.splice(idx + 1, 0, clone);
    tlRecalc();
    ve2RenderMediaBin();
    ve2RenderTracks();
    ve2DrawRuler();
}

function ve2ReplaceSelected() {
    const idx = TL.selectedClipIdx;
    if (idx < 0) return;
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'video/*,image/*';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        const isVid = file.type.startsWith('video/');
        TL.clips[idx].filename = data.filename;
        TL.clips[idx].path = `/uploads/${data.filename}`;
        TL.clips[idx].type = isVid ? 'video' : 'image';
        if (isVid) {
            const info = await tlProbeFile(data.filename);
            TL.clips[idx].duration = info.duration || TL.clips[idx].duration;
            const th = await tlGetThumb(data.filename);
            TL.clips[idx].thumbUrl = th;
        } else {
            TL.clips[idx].thumbUrl = TL.clips[idx].path;
        }
        tlRecalc();
        ve2RenderMediaBin();
        ve2RenderTracks();
        ve2DrawRuler();
        ve2PreviewClip(idx);
    };
    input.click();
}

function ve2MoveClip(idx, dir) {
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= TL.clips.length) return;
    const [clip] = TL.clips.splice(idx, 1);
    TL.clips.splice(newIdx, 0, clip);
    TL.selectedClipIdx = newIdx;
    tlRecalc();
    ve2RenderMediaBin();
    ve2RenderTracks();
    ve2UpdateProps(newIdx);
}

// -- Split at playhead (finds clip automatically) --
async function ve2SplitAtPlayhead() {
    if (TL.clips.length === 0) {
        console.warn('[split] No clips on timeline');
        return;
    }
    const t = TL.playheadTime;
    console.log('[split] Playhead at', t.toFixed(2), 'total:', TL.totalDuration.toFixed(2));

    // Find clip under playhead
    let idx = TL.clips.findIndex(c => t >= c.startTime && t < c.startTime + c.duration);
    // If exact end, try last clip
    if (idx < 0 && t > 0) {
        idx = TL.clips.findIndex(c => Math.abs(t - (c.startTime + c.duration)) < 0.1);
    }
    if (idx < 0) {
        console.warn('[split] No clip found at time', t, 'clips:', TL.clips.map(c => `${c.startTime.toFixed(1)}-${(c.startTime+c.duration).toFixed(1)}`));
        const statusEl = document.getElementById('ve2ToolStatus');
        if (statusEl) { statusEl.textContent = 'Move playhead onto a clip first'; setTimeout(() => statusEl.textContent = TL.cutMode ? 'Cut mode' : 'Select mode', 2000); }
        return;
    }
    const splitAt = t - TL.clips[idx].startTime;
    if (splitAt < 0.2 || splitAt > TL.clips[idx].duration - 0.2) {
        console.warn('[split] Too close to edge. splitAt:', splitAt.toFixed(2), 'dur:', TL.clips[idx].duration.toFixed(2));
        const statusEl = document.getElementById('ve2ToolStatus');
        if (statusEl) { statusEl.textContent = 'Move playhead away from clip edges'; setTimeout(() => statusEl.textContent = TL.cutMode ? 'Cut mode' : 'Select mode', 2000); }
        return;
    }

    await ve2SplitClipAt(idx, splitAt);
}

// -- Split a specific clip at a specific time within it --
async function ve2SplitClipAt(idx, splitAt) {
    if (idx < 0 || idx >= TL.clips.length) return;
    const c = TL.clips[idx];

    const statusEl = document.getElementById('ve2ToolStatus');
    if (statusEl) statusEl.textContent = 'Splitting...';

    try {
        if (c.type === 'video') {
            // Re-probe actual file duration (timeline may be out of sync)
            const realInfo = await tlProbeFile(c.filename);
            const realDur = realInfo.duration || c.duration;
            console.log('[split] Timeline dur:', c.duration.toFixed(2), 'Real file dur:', realDur.toFixed(2));

            // If timeline duration was wrong, fix it
            if (Math.abs(c.duration - realDur) > 0.5) {
                console.log('[split] Correcting clip duration from', c.duration, 'to', realDur);
                c.duration = realDur;
                tlRecalc();
            }

            // Clamp splitAt to real file duration
            if (splitAt >= realDur - 0.1) {
                splitAt = realDur / 2;  // Fall back to middle of clip
                console.log('[split] splitAt was past real duration, using midpoint:', splitAt.toFixed(2));
            }

            if (splitAt < 0.1 || splitAt > realDur - 0.1) {
                console.warn('[split] Cannot split: too short. splitAt:', splitAt, 'realDur:', realDur);
                if (statusEl) statusEl.textContent = 'Clip too short to split';
                setTimeout(() => { if (statusEl) statusEl.textContent = TL.cutMode ? 'Cut mode' : 'Select mode'; }, 2000);
                return;
            }

            // Server-side FFmpeg split
            console.log('[split] Sending to server:', { filename: c.filename, at: splitAt });
            let data;
            try {
                const res = await fetch('/api/video/split', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: c.filename, at: splitAt })
                });
                console.log('[split] Response status:', res.status);
                if (!res.ok) {
                    const errText = await res.text();
                    console.error('[split] Server error:', res.status, errText);
                    alert('Split server error ' + res.status + ': ' + errText.substring(0, 200));
                    if (statusEl) statusEl.textContent = 'Split failed';
                    return;
                }
                data = await res.json();
                console.log('[split] Server response:', JSON.stringify(data));
            } catch (fetchErr) {
                console.error('[split] Fetch error:', fetchErr);
                alert('Split network error: ' + fetchErr.message);
                if (statusEl) statusEl.textContent = 'Split failed';
                return;
            }

            if (data.error) {
                alert('Split failed: ' + data.error);
                if (statusEl) statusEl.textContent = 'Split failed';
                return;
            }

            if (!data.parts || !data.parts[0] || !data.parts[1]) {
                console.error('[split] Unexpected response format:', data);
                alert('Split failed: unexpected server response');
                if (statusEl) statusEl.textContent = 'Split failed';
                return;
            }

            // Get info for both parts in parallel
            const [infoA, infoB, thA, thB] = await Promise.all([
                tlProbeFile(data.parts[0].filename),
                tlProbeFile(data.parts[1].filename),
                tlGetThumb(data.parts[0].filename),
                tlGetThumb(data.parts[1].filename),
            ]);

            const clipA = {
                id: Date.now(),
                filename: data.parts[0].filename,
                path: data.parts[0].path,
                duration: infoA.duration || splitAt,
                startTime: 0,
                thumbUrl: thA,
                type: 'video',
            };
            const clipB = {
                id: Date.now() + 1,
                filename: data.parts[1].filename,
                path: data.parts[1].path,
                duration: infoB.duration || (c.duration - splitAt),
                startTime: 0,
                thumbUrl: thB,
                type: 'video',
            };
            TL.clips.splice(idx, 1, clipA, clipB);

        } else {
            // Image or non-video: instant client-side split
            if (splitAt < 0.1 || splitAt > c.duration - 0.1) {
                if (statusEl) statusEl.textContent = 'Clip too short to split';
                setTimeout(() => { if (statusEl) statusEl.textContent = TL.cutMode ? 'Cut mode' : 'Select mode'; }, 2000);
                return;
            }
            const clipA = { ...c, id: Date.now(), duration: splitAt };
            const clipB = { ...c, id: Date.now() + 1, duration: c.duration - splitAt };
            TL.clips.splice(idx, 1, clipA, clipB);
        }

        TL.selectedClipIdx = idx;
        // Reset video source cache so playback loads the new split files
        ve2CurrentVideoSrc = '';
        tlRecalc();
        ve2RenderMediaBin();
        ve2RenderTracks();
        ve2DrawRuler();
        ve2SyncPlayhead();
        // Load the first split part into preview
        ve2PreviewClip(idx);

        if (statusEl) statusEl.textContent = 'Split done!';
        setTimeout(() => {
            if (statusEl) statusEl.textContent = TL.cutMode ? 'Cut mode: click on clips to split' : 'Select mode';
        }, 1500);

    } catch (err) {
        console.error('[split] Error:', err);
        alert('Split error: ' + err.message);
        if (statusEl) statusEl.textContent = 'Split error';
    }
}

// -- Tool modes: Select / Cut --
function ve2SetSelectMode() {
    TL.cutMode = false;
    document.getElementById('ve2CutBtn')?.classList.remove('active');
    document.getElementById('ve2SelectBtn')?.classList.add('active');
    document.getElementById('ve2TlBody')?.classList.remove('cut-cursor');
    const status = document.getElementById('ve2ToolStatus');
    if (status) status.textContent = 'Select mode';
}

function ve2ToggleCut() {
    TL.cutMode = !TL.cutMode;
    document.getElementById('ve2CutBtn')?.classList.toggle('active', TL.cutMode);
    document.getElementById('ve2SelectBtn')?.classList.toggle('active', !TL.cutMode);
    document.getElementById('ve2TlBody')?.classList.toggle('cut-cursor', TL.cutMode);
    const status = document.getElementById('ve2ToolStatus');
    if (status) status.textContent = TL.cutMode ? 'Cut mode: click on clips to split' : 'Select mode';
}

// -- Zoom --
function ve2SetZoom(val) {
    TL.pixelsPerSec = Math.max(20, Math.min(300, val));
    document.getElementById('ve2Zoom').value = TL.pixelsPerSec;
    ve2RenderTracks();
    ve2DrawRuler();
    ve2SyncPlayhead();
}

function ve2ZoomIn() { ve2SetZoom(TL.pixelsPerSec + 20); }
function ve2ZoomOut() { ve2SetZoom(TL.pixelsPerSec - 20); }

// -- Clip drag reorder on timeline --
let ve2DragClipIdx = null;

function ve2ClipDragStart(e, idx) {
    ve2DragClipIdx = idx;
    e.dataTransfer.effectAllowed = 'move';
}

function ve2ClipReorderDrop(e, targetIdx) {
    e.preventDefault();
    if (ve2DragClipIdx === null || ve2DragClipIdx === targetIdx) return;
    const [moved] = TL.clips.splice(ve2DragClipIdx, 1);
    TL.clips.splice(targetIdx, 0, moved);
    ve2DragClipIdx = null;
    TL.selectedClipIdx = targetIdx;
    tlRecalc();
    ve2RenderMediaBin();
    ve2RenderTracks();
    ve2DrawRuler();
}

function ve2TrackDrop(e, track) {
    e.preventDefault();
    // Accept external file drop as well
}

// -- Click on empty area of video track to place playhead --
function ve2TrackClick(e) {
    const track = document.getElementById('ve2VideoTrack');
    if (!track) return;
    if (e.target !== track && !e.target.classList.contains('ve2-tl-empty')) return;
    const body = document.getElementById('ve2TlBody');
    const rect = track.getBoundingClientRect();
    const x = e.clientX - rect.left + (body ? body.scrollLeft : 0);
    const t = Math.max(0, Math.min(TL.totalDuration, x / TL.pixelsPerSec));
    TL.playheadTime = t;
    ve2SyncPlayhead();
    ve2PreviewAtTime(t);
}

// -- Clip mouse drag on timeline (move position) --
function ve2ClipMouseDown(e, idx) {
    e.preventDefault();
    e.stopPropagation();

    if (TL.cutMode) {
        // Cut at the exact click point within this clip
        const clipEl = e.currentTarget;
        const clipRect = clipEl.getBoundingClientRect();
        const xInClip = e.clientX - clipRect.left;
        const c = TL.clips[idx];
        const timeInClip = (xInClip / clipRect.width) * c.duration;

        // Minimum split margin 0.2s from edges
        if (timeInClip < 0.2 || timeInClip > c.duration - 0.2) return;

        TL.playheadTime = c.startTime + timeInClip;
        ve2SyncPlayhead();

        console.log('[cut] Cutting clip', idx, 'at', timeInClip.toFixed(2) + 's within clip');

        // Perform the split directly with known index and time
        ve2SplitClipAt(idx, timeInClip).then(() => {
            console.log('[cut] Split completed');
        }).catch(err => {
            console.error('[cut] Split failed:', err);
            alert('Cut failed: ' + err.message);
        });
        return;
    }

    // Select this clip
    ve2SelectClip(idx);

    // Drag to reorder
    const startX = e.clientX;
    let moved = false;
    let ghostEl = null;

    const onMove = (e2) => {
        const dx = e2.clientX - startX;
        if (Math.abs(dx) > 8 && !moved) {
            moved = true;
            // Create ghost
            const clipEl = document.querySelector(`.ve2-tl-clip[data-idx="${idx}"]`);
            if (clipEl) {
                ghostEl = clipEl.cloneNode(true);
                ghostEl.style.position = 'fixed';
                ghostEl.style.top = clipEl.getBoundingClientRect().top + 'px';
                ghostEl.style.width = clipEl.offsetWidth + 'px';
                ghostEl.style.height = clipEl.offsetHeight + 'px';
                ghostEl.style.opacity = '0.7';
                ghostEl.style.zIndex = '9999';
                ghostEl.style.pointerEvents = 'none';
                ghostEl.style.border = '2px solid var(--accent)';
                document.body.appendChild(ghostEl);
                clipEl.style.opacity = '0.3';
            }
        }
        if (ghostEl) {
            ghostEl.style.left = (e2.clientX - ghostEl.offsetWidth / 2) + 'px';
        }
    };

    const onUp = (e2) => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);

        // Restore clip opacity
        const clipEl = document.querySelector(`.ve2-tl-clip[data-idx="${idx}"]`);
        if (clipEl) clipEl.style.opacity = '1';
        if (ghostEl) ghostEl.remove();

        if (!moved) return;

        // Determine new position from drop point
        const track = document.getElementById('ve2VideoTrack');
        if (!track) return;
        const body = document.getElementById('ve2TlBody');
        const rect = track.getBoundingClientRect();
        const x = e2.clientX - rect.left + (body ? body.scrollLeft : 0);
        const t = x / TL.pixelsPerSec;

        // Find target index
        let newIdx = TL.clips.length - 1;
        for (let i = 0; i < TL.clips.length; i++) {
            if (i === idx) continue;
            if (t < TL.clips[i].startTime + TL.clips[i].duration / 2) {
                newIdx = i;
                break;
            }
        }
        if (newIdx !== idx) {
            const [clip] = TL.clips.splice(idx, 1);
            const insertAt = newIdx > idx ? newIdx - 1 : newIdx;
            TL.clips.splice(Math.max(0, insertAt), 0, clip);
            TL.selectedClipIdx = Math.max(0, insertAt);
            tlRecalc();
            ve2RenderMediaBin();
            ve2RenderTracks();
            ve2DrawRuler();
        }
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
}

// -- Resizer between preview and timeline --
function ve2ResizerStart(e) {
    e.preventDefault();
    const topEl = document.querySelector('.ve2-top');
    const tlEl = document.getElementById('ve2TimelinePanel');
    if (!topEl || !tlEl) return;

    const startY = e.clientY;
    const startTopH = topEl.offsetHeight;
    const startTlH = tlEl.offsetHeight;

    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';

    const onMove = (e2) => {
        const dy = e2.clientY - startY;
        const newTopH = Math.max(200, Math.min(window.innerHeight - 200, startTopH + dy));
        const newTlH = Math.max(120, startTlH - dy);
        topEl.style.height = newTopH + 'px';
        tlEl.style.height = newTlH + 'px';
        tlEl.style.maxHeight = newTlH + 'px';
    };

    const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
}

// -- Trim handles --
function ve2TrimStart(e, idx) {
    e.stopPropagation();
    e.preventDefault();
    const c = TL.clips[idx];
    const startX = e.clientX;
    const origDur = c.duration;

    const onMove = (e2) => {
        const dx = e2.clientX - startX;
        const dt = dx / TL.pixelsPerSec;
        c.duration = Math.max(0.5, origDur - dt);
        tlRecalc();
        ve2RenderTracks();
        ve2DrawRuler();
    };

    const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        ve2UpdateProps(idx);
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
}

function ve2TrimEnd(e, idx) {
    e.stopPropagation();
    e.preventDefault();
    const c = TL.clips[idx];
    const startX = e.clientX;
    const origDur = c.duration;

    const onMove = (e2) => {
        const dx = e2.clientX - startX;
        const dt = dx / TL.pixelsPerSec;
        c.duration = Math.max(0.5, origDur + dt);
        tlRecalc();
        ve2RenderTracks();
        ve2DrawRuler();
    };

    const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        ve2UpdateProps(idx);
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
}

// -- Keyboard shortcuts --
function ve2SetupKeyboard() {
    // Only listen when on editor tab
    document.onkeydown = (e) => {
        if (currentPage !== 'video' || vsTab !== 'editor') return;
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if (e.code === 'Space') { e.preventDefault(); ve2TogglePlay(); }
        if (e.code === 'KeyC' && !e.ctrlKey && !e.metaKey) {
            if (TL.cutMode) {
                ve2SplitAtPlayhead();
            } else {
                ve2ToggleCut(); // Switch to cut mode
            }
        }
        if (e.code === 'KeyV' && !e.ctrlKey && !e.metaKey) { ve2SetSelectMode(); }
        if (e.code === 'KeyS' && !e.ctrlKey && !e.metaKey) { ve2SplitAtPlayhead(); }
        if (e.code === 'Delete' || e.code === 'Backspace') { e.preventDefault(); ve2DeleteSelected(); }
        if (e.code === 'ArrowLeft') { e.preventDefault(); TL.playheadTime = Math.max(0, TL.playheadTime - 1); ve2SyncPlayhead(); ve2PreviewAtTime(TL.playheadTime); }
        if (e.code === 'ArrowRight') { e.preventDefault(); TL.playheadTime = Math.min(TL.totalDuration, TL.playheadTime + 1); ve2SyncPlayhead(); ve2PreviewAtTime(TL.playheadTime); }
        if (e.code === 'KeyD' && !e.ctrlKey && !e.metaKey) { ve2DuplicateSelected(); }
    };
}

// -- Music file input --
function ve2SetupMusicInput() {
    document.getElementById('ve2MusicFile')?.addEventListener('change', async (e) => {
        const file = e.target.files[0]; if (!file) return;
        const formData = new FormData(); formData.append('file', file);
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        const info = await tlProbeFile(data.filename);
        TL.music = { filename: data.filename, path: `/uploads/${data.filename}`, duration: info.duration || 30 };
        ve2RenderTracks();
    });
}

// -- Drag & drop on timeline body --
function ve2SetupDragDrop() {
    const body = document.getElementById('ve2TlBody');
    const rulerWrap = document.getElementById('ve2RulerWrap');
    if (body && rulerWrap) {
        // Sync scroll between ruler and tracks
        body.addEventListener('scroll', () => {
            rulerWrap.scrollLeft = body.scrollLeft;
        });
    }
}

// -- Voiceover generation --
async function ve2GenVoiceover() {
    const script = document.getElementById('ve2Script')?.value.trim();
    const voice = document.getElementById('ve2Voice')?.value || 'onyx';
    if (!script) return;
    currentProject.script = script;
    ws.send(JSON.stringify({ type: 'message', content: `Generate a voiceover: "${script}" with voice ${voice}` }));
}

// -- AI caption --
async function ve2AiCaption() {
    const script = document.getElementById('ve2Script')?.value || currentProject.script || '';
    const prompt = currentProject.prompt || '';
    ws.send(JSON.stringify({ type: 'message', content: `Write an engaging Instagram caption with hashtags. Context: "${prompt || script}". Just the caption, nothing else.` }));
    const orig = ws.onmessage;
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'reply') {
            const el = document.getElementById('ve2Caption');
            if (el) el.value = data.content;
            currentProject.caption = data.content;
            ws.onmessage = orig;
        } else if (data.type !== 'typing') { ws.onmessage = orig; }
    };
}

// -- Export / render --
async function ve2ExportVideo() {
    if (TL.clips.length === 0) { alert('Add clips first'); return; }

    const statusEl = document.getElementById('ve2ToolStatus');
    if (statusEl) statusEl.textContent = 'Exporting...';

    try {
        let data;
        if (TL.clips.length === 1 && TL.clips[0].type === 'video') {
            const dims = tlFormatDims();
            const res = await fetch('/api/video/resize', {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ filename: TL.clips[0].filename, width: dims.w, height: dims.h })
            });
            data = await res.json();
        } else {
            const filenames = TL.clips.map(c => c.filename);
            const res = await fetch('/api/video/concat', {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ files: filenames })
            });
            data = await res.json();
        }

        if (data.error) { alert('Export failed: ' + data.error); if (statusEl) statusEl.textContent = 'Export failed'; return; }

        currentProject.video = data.path;

        // Clean up temp files after successful export
        await fetch('/api/video/temp', { method: 'DELETE' });

        if (statusEl) statusEl.textContent = 'Exported!';
        alert('Exported to library! ' + data.filename);
    } catch (err) {
        alert('Export error: ' + err.message);
        if (statusEl) statusEl.textContent = 'Export failed';
    }
}

function ve2Download() {
    if (currentProject?.video) {
        const a = document.createElement('a');
        a.href = currentProject.video;
        a.download = '';
        a.click();
    } else {
        alert('Export first, then download');
    }
}

async function ve2SendPipeline() {
    const caption = document.getElementById('ve2Caption')?.value || '';
    const mediaUrl = currentProject?.video || (TL.clips.length ? TL.clips[0].path : '');
    const status = currentProject?.video ? 'video_ready' : (TL.clips.length ? 'designed' : 'draft');
    const msg = `Create a content piece for the pipeline: platform instagram, type reel, caption "${caption || 'Needs caption'}", status ${status}${mediaUrl ? `, media_url ${mediaUrl}` : ''}. Then create a task to write the final caption and prepare for publishing.`;
    ws.send(JSON.stringify({ type: 'message', content: msg }));
    alert('Sent to pipeline!');
}

// Load project from media library
function openProjectInEditor(videoPath) {
    const filename = videoPath.replace('/uploads/', '');
    currentProject = { video: videoPath, clips: [], voiceover: null, subtitles: null, script: '', prompt: '', caption: '' };

    // Add as a clip to timeline
    tlProbeFile(filename).then(info => {
        tlGetThumb(filename).then(th => {
            TL.clips = [{
                id: Date.now(),
                filename: filename,
                path: videoPath,
                duration: info.duration || 10,
                startTime: 0,
                thumbUrl: th,
                type: 'video',
            }];
            tlRecalc();
            navigateTo('video');
            setTimeout(() => switchVsTab('editor'), 100);
        });
    });
}

// Keep old functions as aliases for compatibility
function importMainVideo() { ve2ImportFiles(); }
function addScene() { ve2ImportFiles(); }
function removeScene(i) { ve2RemoveClip(i); }
function replaceScene(i) { TL.selectedClipIdx = i; ve2ReplaceSelected(); }
function previewClip(src) { /* handled by ve2 now */ }
function regenVoiceover() { ve2GenVoiceover(); }
function sendToPipeline() { ve2SendPipeline(); }
function aiWriteCaption() { ve2AiCaption(); }
function reRenderVideo() { ve2ExportVideo(); }

function renderVsVoiceover(el) {
    el.innerHTML = `
        <div style="max-width:600px">
            <div class="stat-card">
                <div class="form-group">
                    <label>Text to speak</label>
                    <textarea id="voText" rows="4" placeholder="Type or paste the script here..."></textarea>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
                    <div class="form-group">
                        <label>Voice</label>
                        <select id="voVoice">
                            <option value="onyx">Onyx (Deep Male)</option>
                            <option value="nova">Nova (Female)</option>
                            <option value="alloy">Alloy (Neutral)</option>
                            <option value="echo">Echo (Male)</option>
                            <option value="fable">Fable (British)</option>
                            <option value="shimmer">Shimmer (Soft Female)</option>
                        </select>
                    </div>
                    <div class="form-group" style="display:flex;align-items:flex-end">
                        <button class="btn btn-primary" style="width:100%" onclick="genVoiceover()">Generate Voiceover</button>
                    </div>
                </div>
                <div id="voStatus" style="margin-top:10px"></div>
                <div id="voResult" style="margin-top:10px"></div>
            </div>
        </div>
    `;
}

async function genVoiceover() {
    const text = document.getElementById('voText').value.trim();
    if (!text) return;
    const voice = document.getElementById('voVoice').value;
    const status = document.getElementById('voStatus');
    status.innerHTML = '<span style="color:var(--accent)">Generating voiceover...</span>';

    ws.send(JSON.stringify({ type: 'message', content: `Generate a voiceover: "${text}" with voice ${voice}` }));

    const orig = ws.onmessage;
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'reply') {
            status.innerHTML = '<span style="color:var(--success)">Done!</span>';
            document.getElementById('voResult').innerHTML = formatMD(data.content);
            ws.onmessage = orig;
        } else if (data.type === 'error') {
            status.innerHTML = `<span style="color:var(--danger)">${data.content}</span>`;
            ws.onmessage = orig;
        }
    };
}

async function renderVsProjects(el) {
    const media = await (await fetch('/api/media')).json();
    const videos = media.filter(f => f.type === 'video');
    const audios = media.filter(f => f.type === 'audio');

    if (!videos.length && !audios.length) {
        el.innerHTML = '<div class="empty-state"><p>No projects yet. Create a video or voiceover to get started.</p></div>';
        return;
    }

    el.innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px">
            ${videos.map(v => `
                <div class="stat-card" style="padding:0;overflow:hidden">
                    <video controls preload="metadata" style="width:100%;height:200px;object-fit:cover;background:#000"><source src="${v.path}" type="video/mp4"></video>
                    <div style="padding:12px">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                            <span class="badge badge-scheduled">VIDEO</span>
                            <span style="font-size:11px;color:var(--text-muted)">${v.size_mb} MB</span>
                        </div>
                        <div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px">${v.name}</div>
                        <div style="display:flex;gap:6px">
                            <button class="btn btn-primary btn-sm" onclick="openProjectInEditor('${v.path}')">Edit</button>
                            <a href="${v.path}" download class="btn btn-secondary btn-sm" style="text-decoration:none">Download</a>
                            <button class="btn btn-danger btn-sm" onclick="deleteMedia('${v.name}');setTimeout(()=>switchVsTab('projects'),500)">Delete</button>
                        </div>
                    </div>
                </div>
            `).join('')}
            ${audios.map(a => `
                <div class="stat-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                        <span class="badge badge-active">VOICEOVER</span>
                        <span style="font-size:11px;color:var(--text-muted)">${a.size_mb} MB</span>
                    </div>
                    <audio controls style="width:100%;margin-bottom:8px"><source src="${a.path}" type="audio/mpeg"></audio>
                    <div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px">${a.name}</div>
                    <div style="display:flex;gap:6px">
                        <a href="${a.path}" download class="btn btn-secondary btn-sm" style="text-decoration:none">Download</a>
                        <button class="btn btn-danger btn-sm" onclick="deleteMedia('${a.name}');setTimeout(()=>switchVsTab('projects'),500)">Delete</button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

async function generateVideo() {
    const prompt = document.getElementById('vidPrompt').value.trim();
    const script = document.getElementById('vidScript').value.trim();
    if (!prompt || !script) { alert('Fill in the visual prompt and voiceover script'); return; }

    const numClips = document.getElementById('vidClips').value;
    const ratio = document.getElementById('vidRatio').value;
    const voice = document.getElementById('vidVoice').value;

    const btn = document.getElementById('vidGenBtn');
    const status = document.getElementById('vidStatus');
    const preview = document.getElementById('vidPreview');
    btn.disabled = true;
    btn.textContent = 'Generating...';
    status.innerHTML = '<span style="color:var(--accent)">Creating your video... ~1-2 min</span>';
    preview.innerHTML = '<div style="color:var(--accent);font-size:14px">Generating...</div><div class="chat-typing" style="justify-content:center;padding:20px"><span></span><span></span><span></span></div>';

    const msg = `Create a video: visual prompt="${prompt}", voiceover script="${script}", ${numClips} clips, aspect ratio ${ratio}, voice ${voice}`;
    ws.send(JSON.stringify({ type: 'message', content: msg }));

    const orig = ws.onmessage;
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'reply') {
            status.innerHTML = '<span style="color:var(--success)">Done!</span>';
            btn.disabled = false;
            btn.textContent = 'Generate Video';
            // Parse result and open editor
            const vidMatch = data.content.match(/\/uploads\/final_[^\s"]+\.mp4/);
            const clipMatches = data.content.match(/\/uploads\/scene_[^\s"]+\.png/g) || [];
            const voMatch = data.content.match(/\/uploads\/voiceover_[^\s"]+\.mp3/);
            const subMatch = data.content.match(/\/uploads\/subtitles_[^\s"]+\.srt/);

            currentProject = {
                video: vidMatch ? vidMatch[0] : null,
                clips: clipMatches,
                voiceover: voMatch ? voMatch[0] : null,
                subtitles: subMatch ? subMatch[0] : null,
                script: script,
                prompt: prompt,
            };

            if (currentProject.video || currentProject.clips.length) {
                preview.innerHTML = `
                    <div style="text-align:center">
                        ${currentProject.video ? `<video controls autoplay style="width:100%;max-height:350px;border-radius:8px;background:#000"><source src="${currentProject.video}" type="video/mp4"></video>` : '<div style="color:var(--accent);padding:20px">Video components ready</div>'}
                        <button class="btn btn-primary" style="margin-top:12px" onclick="switchVsTab('editor')">Open in Editor</button>
                    </div>`;
            } else {
                preview.innerHTML = `<div style="padding:16px;font-size:13px;line-height:1.5">${formatMD(data.content)}</div>`;
            }
            ws.onmessage = orig;
        } else if (data.type === 'error') {
            status.innerHTML = `<span style="color:var(--danger)">${data.content}</span>`;
            btn.disabled = false;
            btn.textContent = 'Generate Video';
            preview.innerHTML = `<div style="color:var(--danger);padding:16px">${data.content}</div>`;
            ws.onmessage = orig;
        }
    };
}

// ---- Media Library ----
async function renderMediaLibrary(el) {
    el.innerHTML = `
        <div class="page-header">
            <div><h2>Media Library</h2><div class="subtitle">All generated images, videos, and voiceovers</div></div>
            <div style="display:flex;gap:6px">
                <button class="btn btn-secondary btn-sm mediaFilter active" data-filter="all" onclick="filterMedia('all')">All</button>
                <button class="btn btn-secondary btn-sm mediaFilter" data-filter="image" onclick="filterMedia('image')">Images</button>
                <button class="btn btn-secondary btn-sm mediaFilter" data-filter="video" onclick="filterMedia('video')">Videos</button>
                <button class="btn btn-secondary btn-sm mediaFilter" data-filter="audio" onclick="filterMedia('audio')">Voiceovers</button>
            </div>
        </div>
        <div id="mediaStats" style="margin-bottom:16px"></div>
        <div id="mediaGrid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px">Loading...</div>
    `;
    await loadMediaLibrary();
}

let allMediaFiles = [];

async function loadMediaLibrary(typeFilter) {
    try {
        const url = typeFilter && typeFilter !== 'all' ? `/api/media?media_type=${typeFilter}` : '/api/media';
        const res = await fetch(url);
        const files = await res.json();
        allMediaFiles = files;

        // Stats
        const statsEl = document.getElementById('mediaStats');
        if (statsEl && !typeFilter) {
            const allFiles = await (await fetch('/api/media')).json();
            const images = allFiles.filter(f => f.type === 'image').length;
            const videos = allFiles.filter(f => f.type === 'video').length;
            const audio = allFiles.filter(f => f.type === 'audio').length;
            const totalSize = allFiles.reduce((s, f) => s + f.size_mb, 0).toFixed(1);

            statsEl.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-label">Total Files</div><div class="stat-value">${allFiles.length}</div></div>
                    <div class="stat-card"><div class="stat-label">Images</div><div class="stat-value gold">${images}</div></div>
                    <div class="stat-card"><div class="stat-label">Videos</div><div class="stat-value blue">${videos}</div></div>
                    <div class="stat-card"><div class="stat-label">Voiceovers</div><div class="stat-value green">${audio}</div></div>
                    <div class="stat-card"><div class="stat-label">Total Size</div><div class="stat-value">${totalSize} MB</div></div>
                </div>
            `;
        }

        const grid = document.getElementById('mediaGrid');
        if (!grid) return;

        if (!files.length) {
            grid.innerHTML = '<div class="empty-state"><p>No media files yet. Generate images or videos from the Design Studio, Video Studio, or Agent Chat.</p></div>';
            return;
        }

        grid.innerHTML = files.map(f => {
            const time = new Date(f.created_at).toLocaleString();
            let preview = '';

            if (f.type === 'image') {
                preview = `<img src="${f.path}" style="width:100%;height:200px;object-fit:cover;border-radius:8px 8px 0 0" loading="lazy">`;
            } else if (f.type === 'video') {
                preview = `<video controls preload="metadata" style="width:100%;height:200px;object-fit:cover;border-radius:8px 8px 0 0;background:#000"><source src="${f.path}" type="video/mp4"></video>`;
            } else if (f.type === 'audio') {
                preview = `
                    <div style="height:100px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--bg-input),var(--bg-card));border-radius:8px 8px 0 0">
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="1.5"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
                    </div>
                    <audio controls style="width:100%;padding:0 12px" preload="metadata"><source src="${f.path}" type="audio/mpeg"></audio>
                `;
            }

            const typeColors = { image: 'var(--accent)', video: 'var(--info)', audio: 'var(--success)' };
            const typeLabels = { image: 'IMAGE', video: 'VIDEO', audio: 'VOICEOVER' };

            return `
                <div class="stat-card" style="padding:0;overflow:hidden">
                    ${preview}
                    <div style="padding:12px">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                            <span class="badge" style="background:${typeColors[f.type]}20;color:${typeColors[f.type]}">${typeLabels[f.type] || f.type.toUpperCase()}</span>
                            <span style="font-size:11px;color:var(--text-muted)">${f.size_mb} MB</span>
                        </div>
                        <div style="font-size:12px;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${f.name}">${f.name}</div>
                        <div style="font-size:11px;color:var(--text-muted);margin-top:4px">${time}</div>
                        <div style="display:flex;gap:6px;margin-top:8px">
                            <a href="${f.path}" download="${f.name}" class="btn btn-secondary btn-sm" style="text-decoration:none">Download</a>
                            <button class="btn btn-danger btn-sm" onclick="deleteMedia('${f.name}')">Delete</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch(e) {
        console.error('Media library error:', e);
        const grid = document.getElementById('mediaGrid');
        if (grid) grid.innerHTML = '<div class="empty-state"><p>Error loading media</p></div>';
    }
}

function filterMedia(type) {
    document.querySelectorAll('.mediaFilter').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.mediaFilter[data-filter="${type}"]`);
    if (btn) btn.classList.add('active');
    loadMediaLibrary(type === 'all' ? null : type);
}

async function deleteMedia(filename) {
    if (!confirm(`Delete ${filename}?`)) return;
    await fetch(`/api/media/${filename}`, { method: 'DELETE' });
    await loadMediaLibrary();
}

// ---- Pipeline ----
// ---- AGENCY WORKFLOW PIPELINE ----
// Two tracks: Content Pipeline + Task Pipeline (all agents)

const CONTENT_STAGES = [
    { key: 'draft', label: 'Draft', color: '#3498db', agent: 'marcus', icon: '✍️' },
    { key: 'designed', label: 'Designed', color: '#9b59b6', agent: 'zara', icon: '🎨' },
    { key: 'video_ready', label: 'Video Ready', color: '#e67e22', agent: 'zara', icon: '🎬' },
    { key: 'scheduled', label: 'Scheduled', color: '#c9a44e', agent: 'sarah', icon: '📅' },
    { key: 'published', label: 'Published', color: '#2ecc71', agent: 'alex', icon: '✅' },
];

const TASK_STAGES = [
    { key: 'pending', label: 'Queued', color: '#3498db' },
    { key: 'in_progress', label: 'Working', color: '#c9a44e' },
    { key: 'completed', label: 'Done', color: '#2ecc71' },
    { key: 'failed', label: 'Failed', color: '#e74c3c' },
];

let pipelineData = [];
let pipelineTaskData = [];
let pipelineClientFilter = '';
let pipelineView = 'all'; // 'all' | 'content' | 'tasks'

async function renderPipeline(el) {
    const [clients, content, tasks, logs] = await Promise.all([
        fetch('/api/clients').then(r=>r.json()),
        fetch('/api/content').then(r=>r.json()),
        fetch('/api/tasks').then(r=>r.json()),
        fetch('/api/agent-logs?limit=20').then(r=>r.json()),
    ]);

    pipelineData = content;
    pipelineTaskData = tasks;

    // Stats
    const totalContent = content.length;
    const totalTasks = tasks.length;
    const activeTasks = tasks.filter(t=>t.status==='in_progress').length;
    const doneTasks = tasks.filter(t=>t.status==='completed').length;
    const doneContent = content.filter(c=>c.status==='published').length;

    // Per-agent workload
    const agentLoad = {};
    tasks.forEach(t => {
        const ak = Object.keys(OFFICE_AGENTS).find(k => OFFICE_AGENTS[k].role === t.assigned_agent);
        if (ak) {
            if (!agentLoad[ak]) agentLoad[ak] = { pending: 0, active: 0, done: 0 };
            if (t.status === 'pending') agentLoad[ak].pending++;
            else if (t.status === 'in_progress') agentLoad[ak].active++;
            else agentLoad[ak].done++;
        }
    });

    el.innerHTML = `
        <div class="page-header">
            <div><h2>Agency Workflow</h2><div class="subtitle">Full pipeline — all agents, all work</div></div>
            <div style="display:flex;gap:6px;align-items:center">
                <button class="btn btn-sm pp-view-btn ${pipelineView==='all'?'active':''}" onclick="pipelineView='all';renderPipeline(document.getElementById('mainContent'))">All</button>
                <button class="btn btn-sm pp-view-btn ${pipelineView==='tasks'?'active':''}" onclick="pipelineView='tasks';renderPipeline(document.getElementById('mainContent'))">Tasks</button>
                <button class="btn btn-sm pp-view-btn ${pipelineView==='content'?'active':''}" onclick="pipelineView='content';renderPipeline(document.getElementById('mainContent'))">Content</button>
                <select id="pipeClientFilter" onchange="pipelineClientFilter=this.value;renderPipeline(document.getElementById('mainContent'))" style="background:var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:8px;padding:6px 10px;font-size:12px">
                    <option value="">All Clients</option>
                    ${clients.map(c => `<option value="${c.id}" ${pipelineClientFilter==c.id?'selected':''}>${c.name}</option>`).join('')}
                </select>
                <button class="btn btn-primary btn-sm" onclick="ofGenerateReport()">📄 Report</button>
            </div>
        </div>

        <!-- Agent workload strip -->
        <div class="pp-agents-strip">
            ${Object.entries(OFFICE_AGENTS).map(([k, a]) => {
                const load = agentLoad[k] || { pending: 0, active: 0, done: 0 };
                const total = load.pending + load.active + load.done;
                const pct = total ? Math.round((load.done / total) * 100) : 0;
                return `<div class="pp-agent-load" style="--ac:${a.color}" onclick="openAgentChat('${k}')">
                    <img src="${a.avatar}" class="pp-agent-face">
                    <div class="pp-agent-info">
                        <strong>${a.name.split(' ')[0]}</strong>
                        <div class="pp-agent-bar">
                            <div class="pp-agent-bar-fill" style="width:${pct}%;background:${a.color}"></div>
                        </div>
                        <span>${load.active > 0 ? `${load.active} active` : load.pending > 0 ? `${load.pending} queued` : `${load.done} done`}</span>
                    </div>
                </div>`;
            }).join('')}
        </div>

        ${pipelineView !== 'content' ? `
        <!-- TASK PIPELINE -->
        <div class="pp-section">
            <div class="pp-section-title">Task Pipeline <span style="color:var(--text-muted);font-weight:400">${totalTasks} tasks</span></div>
            <div class="pp-kanban pp-kanban-4">
                ${TASK_STAGES.map(stage => {
                    let items = tasks.filter(t => t.status === stage.key);
                    if (pipelineClientFilter) items = items.filter(t => t.client_id == pipelineClientFilter);
                    return `<div class="pp-col">
                        <div class="pp-col-head" style="border-color:${stage.color}">
                            <span>${stage.label}</span>
                            <span class="pp-col-badge" style="background:${stage.color}22;color:${stage.color}">${items.length}</span>
                        </div>
                        <div class="pp-col-body">
                            ${items.length ? items.map(t => {
                                const ak = Object.keys(OFFICE_AGENTS).find(k => OFFICE_AGENTS[k].role === t.assigned_agent);
                                const a = ak ? OFFICE_AGENTS[ak] : null;
                                return `<div class="pp-task-card ${t.status==='in_progress'?'pp-card-active':''}">
                                    <div class="pp-card-top">
                                        ${a ? `<img src="${a.avatar}" class="pp-card-face" title="${a.name}">` : ''}
                                        <div class="pp-card-info">
                                            <div class="pp-card-title">${t.title}</div>
                                            ${t.description ? `<div class="pp-card-desc">${t.description.substring(0,60)}</div>` : ''}
                                        </div>
                                    </div>
                                    <div class="pp-card-bottom">
                                        <span class="pp-card-agent" style="color:${a?.color||'#888'}">${a?.name.split(' ')[0] || t.assigned_agent}</span>
                                        ${t.client_name ? `<span class="pp-card-client">${t.client_name}</span>` : ''}
                                        <span class="pp-card-pri pp-pri-${t.priority}"></span>
                                    </div>
                                    ${t.completed_at ? `<div class="pp-card-done">✓ ${tkTimeAgo(t.completed_at)}</div>` : ''}
                                </div>`;
                            }).join('') : '<div class="pp-col-empty">No tasks</div>'}
                        </div>
                    </div>`;
                }).join('')}
            </div>
        </div>` : ''}

        ${pipelineView !== 'tasks' ? `
        <!-- CONTENT PIPELINE -->
        <div class="pp-section">
            <div class="pp-section-title">Content Pipeline <span style="color:var(--text-muted);font-weight:400">${totalContent} pieces</span></div>
            <div class="pp-kanban pp-kanban-5">
                ${CONTENT_STAGES.map(stage => {
                    let items = content.filter(c => c.status === stage.key);
                    if (pipelineClientFilter) items = items.filter(c => c.client_id == pipelineClientFilter);
                    const a = OFFICE_AGENTS[stage.agent];
                    return `<div class="pp-col" data-stage="${stage.key}"
                        ondragover="event.preventDefault();this.classList.add('pp-col-hover')"
                        ondragleave="this.classList.remove('pp-col-hover')"
                        ondrop="pipeDrop(event,'${stage.key}');this.classList.remove('pp-col-hover')">
                        <div class="pp-col-head" style="border-color:${stage.color}">
                            <span>${stage.icon} ${stage.label}</span>
                            <span class="pp-col-badge" style="background:${stage.color}22;color:${stage.color}">${items.length}</span>
                        </div>
                        <div class="pp-col-body">
                            ${items.length ? items.map(c => {
                                const hasMedia = c.media_url && (c.media_url.endsWith('.mp4') || c.media_url.endsWith('.png') || c.media_url.endsWith('.jpg'));
                                return `<div class="pp-content-card" draggable="true" ondragstart="pipeDragStart(event,${c.id})" onclick="showPipeDetail(${c.id})">
                                    ${hasMedia ? `<div class="pp-card-thumb"><img src="${c.media_url}" onerror="this.parentElement.remove()"></div>` : ''}
                                    <div class="pp-card-platform">${c.platform} · ${c.content_type}</div>
                                    <div class="pp-card-caption">${escapeHTML((c.caption||'').substring(0,60))}</div>
                                    <div class="pp-card-bottom">
                                        <span class="pp-card-client">${c.client_name||'—'}</span>
                                        <span class="pp-card-time">${tkTimeAgo(c.created_at)}</span>
                                    </div>
                                </div>`;
                            }).join('') : '<div class="pp-col-empty">Empty</div>'}
                        </div>
                    </div>`;
                }).join('')}
            </div>
        </div>` : ''}

        <!-- Recent activity -->
        <div class="pp-section">
            <div class="pp-section-title">Recent Deliverables</div>
            <div class="pp-deliverables">
                ${logs.slice(0,8).map(l => {
                    const ak = Object.keys(OFFICE_AGENTS).find(k => OFFICE_AGENTS[k].role === l.agent);
                    const a = ak ? OFFICE_AGENTS[ak] : { name: l.agent, avatar: '', color: '#888' };
                    return `<div class="pp-delivery-item">
                        ${a.avatar ? `<img src="${a.avatar}" class="pp-delivery-face">` : `<span>${l.agent}</span>`}
                        <span style="color:${a.color};font-weight:600;min-width:60px">${a.name?.split(' ')[0]||l.agent}</span>
                        <span class="pp-delivery-action">${l.action.replace(/_/g,' ')}</span>
                        <span class="pp-delivery-time">${tkTimeAgo(l.created_at)}</span>
                    </div>`;
                }).join('')}
            </div>
        </div>

        <!-- Detail modal -->
        <div class="modal-overlay" id="pipeDetailModal">
            <div class="modal" style="width:560px" id="pipeDetailContent"></div>
        </div>
    `;
}

// Content detail modal
function showPipeDetail(contentId) {
    const c = pipelineData.find(x => x.id === contentId);
    if (!c) return;
    const stage = CONTENT_STAGES.find(s => s.key === c.status) || CONTENT_STAGES[0];
    let mediaEl = '';
    if (c.media_url) {
        if (c.media_url.endsWith('.mp4')) mediaEl = `<video controls style="width:100%;border-radius:8px;margin:12px 0;max-height:300px;background:#000"><source src="${c.media_url}" type="video/mp4"></video>`;
        else if (c.media_url.endsWith('.mp3')) mediaEl = `<audio controls style="width:100%;margin:12px 0"><source src="${c.media_url}" type="audio/mpeg"></audio>`;
        else mediaEl = `<img src="${c.media_url}" style="width:100%;border-radius:8px;margin:12px 0;max-height:300px;object-fit:cover">`;
    }
    document.getElementById('pipeDetailContent').innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:16px">
            <div>
                <span class="badge" style="background:${stage.color}22;color:${stage.color}">${stage.icon} ${stage.label}</span>
                <h3 style="margin-top:8px">${c.platform} ${c.content_type}</h3>
                <div style="font-size:12px;color:var(--text-muted)">${c.client_name||'No client'} · ${new Date(c.created_at).toLocaleDateString()}</div>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="closeModal('pipeDetailModal')">Close</button>
        </div>
        ${mediaEl}
        <div style="font-size:13px;line-height:1.6;padding:12px;background:var(--bg-input);border-radius:8px;white-space:pre-wrap;margin:12px 0">${escapeHTML(c.caption||'No caption')}</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
            ${c.status==='draft'?`<button class="btn btn-primary btn-sm" onclick="pipelineAction(${c.id},'design');closeModal('pipeDetailModal')">🎨 Generate Design</button>`:''}
            ${c.status==='designed'?`<button class="btn btn-primary btn-sm" onclick="pipelineAction(${c.id},'video');closeModal('pipeDetailModal')">🎬 Create Video</button>`:''}
            ${c.status==='video_ready'?`<button class="btn btn-primary btn-sm" onclick="pipelineAction(${c.id},'schedule');closeModal('pipeDetailModal')">📅 Schedule</button>`:''}
            ${c.status==='scheduled'?`<button class="btn btn-sm" style="background:var(--success);color:#fff" onclick="pipelineAction(${c.id},'publish');closeModal('pipeDetailModal')">✅ Publish</button>`:''}
            ${c.media_url?`<a href="${c.media_url}" download class="btn btn-secondary btn-sm" style="text-decoration:none">Download</a>`:''}
        </div>
    `;
    document.getElementById('pipeDetailModal').classList.add('active');
}

// Drag & Drop content between stages
let dragContentId = null;
function pipeDragStart(e, id) { dragContentId = id; e.dataTransfer.effectAllowed = 'move'; }
async function pipeDrop(e, newStage) {
    e.preventDefault();
    if (!dragContentId) return;
    const c = pipelineData.find(x => x.id === dragContentId);
    if (c && c.status !== newStage) {
        await fetch(`/api/content/${dragContentId}/status`, {
            method: 'PUT', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ status: newStage }),
        });
        renderPipeline(document.getElementById('mainContent'));
    }
    dragContentId = null;
}

async function pipelineAction(contentId, action) {
    const msgs = {
        design: `Generate a professional social media image for content ID ${contentId}. Look up the caption and create a matching visual.`,
        video: `Create a 15-second video for content ID ${contentId}. Look up the caption, write a voiceover, and generate the video.`,
        schedule: `Update content ID ${contentId} status to scheduled.`,
        publish: `Update content ID ${contentId} status to published.`,
    };
    if (ws?.readyState === WebSocket.OPEN && msgs[action]) {
        ws.send(JSON.stringify({ type: 'message', content: msgs[action] }));
        setTimeout(() => renderPipeline(document.getElementById('mainContent')), 3000);
    }
}

// ---- Settings ----
// ---- Research Vault (Project Folders) ----
let openProjectId = null;

async function renderLeads(el) {
    if (openProjectId) {
        await renderProjectDetail(el, openProjectId);
        return;
    }

    const projects = await (await fetch('/api/projects')).json();

    el.innerHTML = `
        <div class="page-header">
            <div><h2>Research Vault</h2><div class="subtitle">Project folders with contacts and data from agent research</div></div>
            <div style="display:flex;gap:6px">
                <button class="btn btn-secondary btn-sm" onclick="window.open('/api/leads/export/csv')">Export All CSV</button>
                <button class="btn btn-primary btn-sm" onclick="leadAskKai()">🔍 New Research</button>
                <button class="btn btn-sm" style="background:linear-gradient(135deg,#c9a44e,#e67e22);color:#fff;font-weight:600" onclick="showProspectingPanel()">🎯 Vibe Prospecting</button>
            </div>
        </div>

        <!-- Prospecting Campaign Panel -->
        <div class="vp-panel" id="vpPanel" style="display:none">
            <div class="vp-header">
                <div><strong>🎯 Vibe Prospecting</strong><div style="font-size:11px;color:var(--text-muted)">Auto-find companies → scrape contacts → qualify → generate proposals</div></div>
                <button class="of-close-btn" onclick="document.getElementById('vpPanel').style.display='none'">✕</button>
            </div>
            <div class="vp-body">
                <div class="vp-row">
                    <div class="form-group" style="flex:2"><label>Target Location</label><input id="vpLocation" placeholder="Dubai, Slovenia, Abu Dhabi..." value="Dubai"></div>
                    <div class="form-group" style="flex:1"><label>Target Count</label><input id="vpCount" type="number" value="50" min="10" max="200"></div>
                </div>
                <div class="form-group"><label>Project Name (optional)</label><input id="vpName" placeholder="Auto-generated if empty"></div>
                <div class="form-group"><label>Industries (leave empty for all 20 industries)</label><input id="vpIndustries" placeholder="restaurants, IT, fashion, real estate..."></div>
                <div style="display:flex;gap:8px;margin-top:8px">
                    <button class="btn btn-primary" style="flex:1;padding:10px;font-size:13px" onclick="runProspecting()" id="vpRunBtn">🎯 Start Prospecting</button>
                </div>
                <div id="vpStatus" style="margin-top:10px"></div>
            </div>
        </div>

        ${projects.length === 0 ? `
            <div class="empty-state">
                <div style="font-size:48px;margin-bottom:12px">📁</div>
                <p>No research projects yet. Ask Kai or Sarah to research companies.</p>
                <button class="btn btn-primary" onclick="leadAskKai()">Start a Research Project</button>
            </div>
        ` : `
            <div class="rv-grid">
                ${projects.map(p => `
                    <div class="rv-folder" onclick="openProjectId=${p.id};renderLeads(document.getElementById('mainContent'))">
                        <div class="rv-folder-icon">📁</div>
                        <div class="rv-folder-info">
                            <div class="rv-folder-name">${escapeHTML(p.name)}</div>
                            <div class="rv-folder-desc">${escapeHTML(p.description || '').substring(0,60)}</div>
                            <div class="rv-folder-stats">
                                <span>📋 ${p.lead_count || 0} contacts</span>
                                <span>📧 ${p.email_count || 0} emails</span>
                                <span>${tkTimeAgo(p.created_at)}</span>
                            </div>
                        </div>
                        <button class="btn btn-danger btn-sm" style="font-size:10px;padding:2px 8px;opacity:0.5" onclick="event.stopPropagation();deleteProject(${p.id})">x</button>
                    </div>
                `).join('')}
            </div>
        `}
    `;
}

async function renderProjectDetail(el, projectId) {
    const data = await (await fetch(`/api/projects/${projectId}/leads`)).json();
    const proj = data.project;
    const leads = data.leads;

    const withEmail = leads.filter(l => l.email).length;
    const withPhone = leads.filter(l => l.phone).length;

    el.innerHTML = `
        <div class="page-header">
            <div>
                <div style="display:flex;align-items:center;gap:8px">
                    <button class="btn btn-secondary btn-sm" onclick="openProjectId=null;renderLeads(document.getElementById('mainContent'))">← Back</button>
                    <h2>📁 ${escapeHTML(proj.name || 'Project')}</h2>
                </div>
                <div class="subtitle">${escapeHTML(proj.description || '')} — ${leads.length} contacts found</div>
            </div>
            <div style="display:flex;gap:6px">
                <button class="btn btn-secondary btn-sm" onclick="window.open('/api/leads/export/csv?project_id=${projectId}')">Export CSV</button>
                <button class="btn btn-primary btn-sm" onclick="leadGenProposal()">📄 Proposal</button>
                <button class="btn btn-primary btn-sm" onclick="leadResearchMore(${projectId},'${escapeHTML(proj.name)}')">🔍 Find More</button>
                <button class="btn btn-sm" style="background:var(--accent);color:#0c0c12" onclick="runAutoOutreach(${projectId})">📄 Auto-Outreach</button>
            </div>
        </div>

        <div class="tk-stats-row" style="margin-bottom:14px">
            <div class="tk-stat"><div class="tk-stat-num">${leads.length}</div><div class="tk-stat-label">Total</div></div>
            <div class="tk-stat"><div class="tk-stat-num">${withEmail}</div><div class="tk-stat-label">Have Email</div></div>
            <div class="tk-stat"><div class="tk-stat-num">${withPhone}</div><div class="tk-stat-label">Have Phone</div></div>
        </div>

        ${leads.length === 0 ? `
            <div class="empty-state"><p>No contacts yet. Kai is still researching or hasn't started.</p></div>
        ` : `
            <div class="rv-leads-grid">
                ${leads.map(l => `
                    <div class="rv-lead-card">
                        <div class="rv-lead-top">
                            <strong>${escapeHTML(l.company_name)}</strong>
                            <button class="btn btn-danger btn-sm" style="font-size:9px;padding:1px 6px" onclick="deleteLead(${l.id},${projectId})">x</button>
                        </div>
                        ${l.contact_name ? `<div class="rv-lead-row">👤 ${escapeHTML(l.contact_name)}</div>` : ''}
                        ${l.email ? `<div class="rv-lead-row">📧 <a href="mailto:${l.email}" style="color:var(--accent)">${l.email}</a></div>` : ''}
                        ${l.phone ? `<div class="rv-lead-row">📞 ${escapeHTML(l.phone)}</div>` : ''}
                        ${l.website ? `<div class="rv-lead-row">🌐 <a href="${l.website}" target="_blank" style="color:var(--accent);font-size:11px">${l.website}</a></div>` : ''}
                        ${l.industry ? `<div class="rv-lead-row rv-lead-tag">${escapeHTML(l.industry)}</div>` : ''}
                        ${l.location ? `<div class="rv-lead-row" style="font-size:10px;color:var(--text-muted)">📍 ${escapeHTML(l.location)}</div>` : ''}
                        ${l.notes ? `<div class="rv-lead-notes">${escapeHTML(l.notes)}</div>` : ''}
                        ${l.email ? `<button class="rv-proposal-btn" onclick="leadSendProposal('${escapeHTML(l.company_name)}','${escapeHTML(l.contact_name||l.company_name)}','${l.email}')">📄 Send Proposal</button>` : ''}
                    </div>
                `).join('')}
            </div>
        `}
    `;
}

async function deleteProject(id) {
    if (!confirm('Delete this project and all its contacts?')) return;
    await fetch(`/api/projects/${id}`, { method: 'DELETE' });
    renderLeads(document.getElementById('mainContent'));
}

async function deleteLead(id, projectId) {
    await fetch(`/api/leads/${id}`, { method: 'DELETE' });
    if (projectId) { openProjectId = projectId; }
    renderLeads(document.getElementById('mainContent'));
}

function showProspectingPanel() {
    const panel = document.getElementById('vpPanel');
    if (panel) panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

async function runProspecting() {
    const location = document.getElementById('vpLocation')?.value.trim();
    const count = parseInt(document.getElementById('vpCount')?.value) || 50;
    const name = document.getElementById('vpName')?.value.trim();
    const industriesRaw = document.getElementById('vpIndustries')?.value.trim() || '';
    const excludeRaw = document.getElementById('vpExclude')?.value.trim() || '';
    const industries = industriesRaw ? industriesRaw.split(',').map(s => s.trim()).filter(Boolean) : [];
    const exclude = excludeRaw ? excludeRaw.split(',').map(s => s.trim()).filter(Boolean) : [];
    const needEmail = document.getElementById('vpNeedEmail')?.checked ?? true;
    const needPhone = document.getElementById('vpNeedPhone')?.checked ?? false;
    const needWebsite = document.getElementById('vpNeedWebsite')?.checked ?? true;

    if (!location) { alert('Enter a target location'); return; }

    const btn = document.getElementById('vpRunBtn');
    const status = document.getElementById('vpStatus');
    btn.disabled = true;
    btn.textContent = '⏳ Prospecting...';
    status.innerHTML = `<div style="color:var(--accent)">🔍 Searching across ${industries.length || 20} industries in ${location}... This takes 30-60 seconds.</div>`;

    try {
        const res = await fetch('/api/prospect/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                location, target_count: count,
                project_name: name || undefined,
                industries: industries.length ? industries : undefined,
                exclude_industries: exclude.length ? exclude : undefined,
                require_email: needEmail,
                require_phone: needPhone,
                require_website: needWebsite,
            }),
        });
        const data = await res.json();

        if (data.error) {
            status.innerHTML = `<div style="color:var(--danger)">Error: ${data.error}</div>`;
        } else {
            status.innerHTML = `
                <div style="color:var(--success);font-weight:600;margin-bottom:8px">✅ Campaign complete!</div>
                <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:12px">
                    <span>📋 ${data.total_found} companies found</span>
                    <span>⭐ ${data.qualified} qualified</span>
                    <span>📧 ${data.with_email} with email</span>
                    <span>📞 ${data.with_phone} with phone</span>
                    <span>🔍 ${data.searches_run} searches run</span>
                </div>
                <div style="display:flex;gap:6px;margin-top:10px">
                    <button class="btn btn-primary btn-sm" onclick="openProjectId=${data.project_id};renderLeads(document.getElementById('mainContent'))">View Results</button>
                    <button class="btn btn-sm" style="background:var(--accent);color:#0c0c12" onclick="runAutoOutreach(${data.project_id})">📄 Auto-Generate Proposals</button>
                </div>
            `;
        }
    } catch (e) {
        status.innerHTML = `<div style="color:var(--danger)">Error: ${e.message}</div>`;
    }
    btn.disabled = false;
    btn.textContent = '🎯 Start Prospecting';
}

async function runAutoOutreach(projectId) {
    if (!confirm('Generate proposals for all qualified leads with emails?')) return;
    const res = await fetch(`/api/prospect/outreach/${projectId}?max_sends=10`, { method: 'POST' });
    const data = await res.json();
    alert(`Processed ${data.processed || 0} leads. Check Media Library for PDFs.`);
    renderLeads(document.getElementById('mainContent'));
}

function leadAskKai() {
    openAgentChat('kai');
    setTimeout(() => {
        const input = document.getElementById('ofChatInput');
        if (input) {
            input.value = 'Create a new research project and find 10 companies that need social media marketing. Save each one with company name, website, email, phone, and industry.';
            input.focus();
        }
    }, 300);
}

function leadResearchMore(projectId, projectName) {
    openAgentChat('kai');
    setTimeout(() => {
        const input = document.getElementById('ofChatInput');
        if (input) {
            input.value = `Find 10 more companies for the "${projectName}" project (ID: ${projectId}). Save each contact to that project with full details.`;
            input.focus();
        }
    }, 300);
}

function leadGenProposal() {
    const name = prompt('Client name for the proposal:');
    if (!name) return;
    const company = prompt('Company name (optional):') || '';
    openAgentChat('elena');
    setTimeout(() => {
        const input = document.getElementById('ofChatInput');
        if (input) {
            input.value = `Generate a marketing proposal PDF for ${name}${company ? ' from ' + company : ''}. Include all our services.`;
            ofSendChat();
        }
    }, 300);
}

function leadSendProposal(company, contact, email) {
    openAgentChat('elena');
    setTimeout(() => {
        const input = document.getElementById('ofChatInput');
        if (input) {
            input.value = `Generate a proposal PDF for ${contact} from ${company}, then send it to ${email} with a professional intro email.`;
            ofSendChat();
        }
    }, 300);
}

// ============================================================
// SOCIAL MEDIA WORKSPACE — WORKFLOW ENGINE
// ============================================================

const WF_STAGE_ICONS = { research: '🔍', strategy: '🧠', copywriting: '✍️', creative: '🎨', publishing: '📱', voiceover: '🎙️', music: '🎵', audio_mix: '🎧' };
const WF_STAGE_COLORS = { research: '#1abc9c', strategy: '#c9a44e', copywriting: '#3498db', creative: '#9b59b6', publishing: '#2ecc71', voiceover: '#e67e22', music: '#e91e63', audio_mix: '#ff5722' };
const WF_STATUS_LABELS = {
    new: 'New', in_research: '🔍 Researching', in_strategy: '🧠 Planning', in_copywriting: '✍️ Writing',
    in_creative: '🎨 Designing', in_publishing: '📱 Preparing', completed: '✅ Delivered',
    ready_for_approval: 'Review', ready_to_publish: 'Approved', published: 'Published',
};

async function renderSocialWorkspace(el) {
    const workflows = await fetch('/api/workflows').then(r => r.json());

    el.innerHTML = `
        <div class="page-header">
            <div><h2>Social Media</h2><div class="subtitle">Content workflow engine — auto-pipeline from brief to publish</div></div>
            <button class="btn btn-primary" onclick="showNewWorkflow()">+ New Content Brief</button>
        </div>

        <!-- New workflow form -->
        <div class="wf-new-panel" id="wfNewPanel" style="display:none">
            <div class="vp-header"><strong>📝 New Content Brief</strong><button class="of-close-btn" onclick="document.getElementById('wfNewPanel').style.display='none'">✕</button></div>
            <div class="vp-body">
                <div class="form-group"><label>What do you want to create?</label>
                    <textarea id="wfCommand" rows="3" placeholder="Create 3 reels about the impact of war on Dubai real estate. Make them strong, reassuring, investor-focused."></textarea>
                </div>
                <button class="btn btn-primary" style="width:100%;padding:10px" onclick="startNewWorkflow()" id="wfStartBtn">🚀 Start Workflow</button>
                <div id="wfStatus" style="margin-top:8px"></div>
            </div>
        </div>

        <!-- Workflows as horizontal flows -->
        ${workflows.length ? workflows.map(w => renderWorkflowFlow(w)).join('') : `
            <div class="empty-state">
                <div style="font-size:48px;margin-bottom:12px">📝</div>
                <p>No workflows yet. Create a content brief to start the pipeline.</p>
                <button class="btn btn-primary" onclick="showNewWorkflow()">+ New Content Brief</button>
            </div>
        `}

        <div class="modal-overlay" id="wfStageModal">
            <div class="modal" style="width:650px;max-height:80vh;overflow-y:auto" id="wfStageContent"></div>
        </div>
    `;

    // Load full stage data for each workflow
    for (const w of workflows) {
        const full = await fetch(`/api/workflows/${w.id}`).then(r => r.json());
        if (full.stages) renderWorkflowStages(w.id, full);
    }
}

function renderWorkflowFlow(w) {
    const statusLabel = WF_STATUS_LABELS[w.status] || w.status;
    const pct = w.stage_count ? Math.round(((w.stages_done||0) / w.stage_count) * 100) : 0;

    return `
    <div class="wf2-flow" id="wf2Flow${w.id}">
        <div class="wf2-header">
            <div class="wf2-title">${escapeHTML(w.title)}</div>
            <div class="wf2-meta">
                <span class="wf-status-badge wf-status-${w.status.replace(/_/g,'-')}">${statusLabel}</span>
                ${w.status === 'ready_for_approval' ? `<button class="btn btn-sm" style="background:var(--success);color:#fff;font-size:10px;padding:2px 10px" onclick="approveWorkflow(${w.id})">✓ Approve</button>` : ''}
            </div>
        </div>
        <div class="wf2-progress"><div class="wf2-progress-fill" style="width:${pct}%"></div></div>
        <div class="wf2-stages" id="wf2Stages${w.id}">
            <div style="padding:20px;color:var(--text-muted);font-size:12px">Loading stages...</div>
        </div>
    </div>`;
}

function renderWorkflowStages(wfId, wf) {
    const container = document.getElementById(`wf2Stages${wfId}`);
    if (!container) return;
    const stages = wf.stages || [];
    const hasCopywriting = stages.some(s => s.stage_name === 'copywriting' && s.status === 'completed');
    const hasVoiceover = stages.some(s => s.stage_name === 'voiceover');

    let html = stages.map((s, i) => {
        const icon = WF_STAGE_ICONS[s.stage_name] || '⚙️';
        const color = WF_STAGE_COLORS[s.stage_name] || '#888';
        const isDone = s.status === 'completed';
        const isActive = s.status === 'in_progress';
        const isWaiting = s.status === 'waiting';
        const label = s.stage_name.charAt(0).toUpperCase() + s.stage_name.slice(1);

        // Audio mix stage — voiceover + music combined
        if (s.stage_name === 'audio_mix') {
            return `
                ${i > 0 ? '<div class="wf2-arrow">→</div>' : ''}
                <div class="wf2-stage wf2-vo-stage ${isDone ? 'wf2-done' : ''} ${isActive ? 'wf2-active' : ''}" style="--sc:${color};min-width:200px;max-width:280px">
                    <div class="wf2-stage-icon">🎧</div>
                    <div class="wf2-stage-name">Final Audio</div>
                    ${isDone && s.output_data?.startsWith('/uploads/') ? `
                        <audio controls style="width:100%;height:28px;margin:6px 0"><source src="${s.output_data}" type="audio/mpeg"></audio>
                        <div style="display:flex;gap:4px;justify-content:center">
                            <a href="${s.output_data}" download class="btn btn-secondary btn-sm" style="text-decoration:none;font-size:9px;padding:2px 6px">Download</a>
                        </div>
                    ` : isDone ? `<div style="font-size:9px;color:var(--success)">✅ Mixed</div>`
                    : isActive ? `<div class="wf2-stage-status"><span class="tk-pulse" style="margin:0"></span></div><div style="font-size:9px;color:var(--text-muted)">Mixing...</div>`
                    : `<div style="font-size:9px;color:var(--text-muted)">⏸ Waiting</div>`}
                </div>`;
        }

        // Music stage — show library picker
        if (s.stage_name === 'music') {
            return `
                ${i > 0 ? '<div class="wf2-arrow">→</div>' : ''}
                <div class="wf2-stage wf2-vo-stage ${isDone ? 'wf2-done' : ''}" style="--sc:${color};min-width:200px;max-width:280px">
                    <div class="wf2-stage-icon">🎵</div>
                    <div class="wf2-stage-name">Music</div>
                    ${isDone && s.output_data ? `
                        <audio controls style="width:100%;height:28px;margin:6px 0"><source src="${s.output_data}" type="audio/mpeg"></audio>
                        <div style="display:flex;gap:4px;justify-content:center">
                            <a href="${s.output_data}" download class="btn btn-secondary btn-sm" style="text-decoration:none;font-size:9px;padding:2px 6px">Download</a>
                            <button class="btn btn-sm" style="font-size:9px;padding:2px 6px;background:#e91e63;color:#fff" onclick="event.stopPropagation();showMusicPicker(${wfId},${s.id})">Change Track</button>
                        </div>
                    ` : `<button class="btn btn-sm" style="font-size:10px;padding:4px 10px;background:#e91e63;color:#fff;margin-top:4px" onclick="event.stopPropagation();showMusicPicker(${wfId},${s.id})">Browse Music</button>`}
                </div>`;
        }

        // Voiceover stage gets special rendering
        if (s.stage_name === 'voiceover') {
            return `
                ${i > 0 ? '<div class="wf2-arrow">→</div>' : ''}
                <div class="wf2-stage wf2-vo-stage ${isDone ? 'wf2-done' : ''}" style="--sc:${color};min-width:200px;max-width:280px">
                    <div class="wf2-stage-icon">🎙️</div>
                    <div class="wf2-stage-name">Voiceover</div>
                    ${isDone && s.output_data ? `
                        <audio controls style="width:100%;height:28px;margin:6px 0"><source src="${s.output_data}" type="audio/mpeg"></audio>
                        <div style="display:flex;gap:4px;justify-content:center">
                            <a href="${s.output_data}" download class="btn btn-secondary btn-sm" style="text-decoration:none;font-size:9px;padding:2px 6px">Download</a>
                            <button class="btn btn-sm" style="font-size:9px;padding:2px 6px;background:var(--accent);color:#0c0c12" onclick="event.stopPropagation();showVoicePicker(${wfId})">Change Voice</button>
                        </div>
                    ` : isActive ? `<div class="wf2-stage-status"><span class="tk-pulse" style="margin:0"></span></div><div style="font-size:9px;color:var(--text-muted)">Generating...</div>`
                    : `<div id="wf2VoPicker${wfId}"></div><button class="btn btn-sm" style="font-size:10px;padding:4px 10px;background:var(--accent);color:#0c0c12;margin-top:4px" onclick="event.stopPropagation();showVoicePicker(${wfId})">Pick Voice</button>`}
                </div>`;
        }

        return `
            ${i > 0 ? '<div class="wf2-arrow">→</div>' : ''}
            <div class="wf2-stage ${isDone ? 'wf2-done' : ''} ${isActive ? 'wf2-active' : ''} ${isWaiting ? 'wf2-waiting' : ''}"
                 style="--sc:${color}" onclick="${isDone ? `openStageDetail(${wfId},${s.id})` : ''}">
                <div class="wf2-stage-icon">${icon}</div>
                <div class="wf2-stage-name">${label}</div>
                <div class="wf2-stage-status">
                    ${isDone ? '✅' : isActive ? '<span class="tk-pulse" style="margin:0"></span>' : '⏸'}
                </div>
                ${isDone ? '<div class="wf2-stage-click">Click to view</div>' : ''}
                ${isWaiting ? `<div class="wf2-stage-click" style="opacity:1;cursor:pointer" onclick="event.stopPropagation();retryStage(${wfId},${s.id})">▶ Start</div>` : ''}
                ${isActive ? `<div class="wf2-stage-click" style="opacity:1;font-size:8px;color:var(--text-muted)">Working...</div>` : ''}
            </div>`;
    }).join('');

    container.innerHTML = html;
}

async function addVoiceoverStage(wfId) {
    // Add voiceover stage to the workflow in the database
    await fetch(`/api/workflows/${wfId}/add-voiceover`, { method: 'POST' });
    // Reload
    const full = await fetch(`/api/workflows/${wfId}`).then(r => r.json());
    if (full.stages) renderWorkflowStages(wfId, full);
}

async function showVoicePicker(wfId) {
    // Show voice picker as a modal
    let voices = { elevenlabs: [], openai: [] };
    try { voices = await fetch('/api/voices').then(r => r.json()); } catch(e) {}

    const elVoices = voices.elevenlabs || [];
    const oaVoices = voices.openai || [];

    const modal = document.createElement('div');
    modal.className = 've2-modal-overlay';
    modal.innerHTML = `<div class="ve2-modal" style="max-width:500px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3 style="margin:0">🎙️ Select Voice</h3>
            <button onclick="this.closest('.ve2-modal-overlay').remove()" style="background:none;border:none;color:var(--text-secondary);font-size:18px;cursor:pointer">✕</button>
        </div>
        ${elVoices.length ? `
            <div class="vo-group-label">ElevenLabs</div>
            <div class="vo-grid">
                ${elVoices.map(v => `
                    <button class="vo-voice-btn" onclick="this.closest('.ve2-modal-overlay').remove();doVoiceoverStage(${wfId},'${escapeHTML(v.name)}')">
                        <span class="vo-voice-icon">${v.category === 'cloned' ? '⭐' : '🎤'}</span>
                        <span class="vo-voice-name">${v.name.split(' - ')[0]}</span>
                    </button>
                `).join('')}
            </div>
        ` : ''}
        <div class="vo-group-label">OpenAI</div>
        <div class="vo-grid">
            ${oaVoices.map(v => `
                <button class="vo-voice-btn" onclick="this.closest('.ve2-modal-overlay').remove();doVoiceoverStage(${wfId},'${v.id}')">
                    <span class="vo-voice-icon">🔊</span>
                    <span class="vo-voice-name">${v.name}</span>
                </button>
            `).join('')}
        </div>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">
            <div class="vo-group-label">Preview</div>
            <div style="font-size:11px;color:var(--text-muted)">Click a voice to generate. You can change it after.</div>
        </div>
    </div>`;
    document.body.appendChild(modal);
}

async function doVoiceoverStage(wfId, voice) {
    // Generate voiceover and save to the voiceover stage
    const full = await fetch(`/api/workflows/${wfId}`).then(r => r.json());
    const voStage = (full.stages || []).find(s => s.stage_name === 'voiceover');
    const copyStage = (full.stages || []).find(s => s.stage_name === 'copywriting');
    if (!voStage) return;

    // Mark as in_progress and refresh
    renderWorkflowStages(wfId, {...full, stages: full.stages.map(s =>
        s.id === voStage.id ? {...s, status: 'in_progress'} : s
    )});

    const res = await fetch(`/api/workflows/${wfId}/voiceover`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ voice, stage_id: copyStage?.id }),
    });
    const data = await res.json();

    if (data.path) {
        // Save to the voiceover stage
        await fetch(`/api/workflows/${wfId}/stages/${voStage.id}/output`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ output: data.path }),
        });
    }
    // Reload
    const updated = await fetch(`/api/workflows/${wfId}`).then(r => r.json());
    if (updated.stages) renderWorkflowStages(wfId, updated);
}

async function openStageDetail(wfId, stageId) {
    const wf = await fetch(`/api/workflows/${wfId}`).then(r => r.json());
    const stage = (wf.stages || []).find(s => s.id === stageId);
    if (!stage) return;

    const icon = WF_STAGE_ICONS[stage.stage_name] || '⚙️';
    const label = stage.stage_name.charAt(0).toUpperCase() + stage.stage_name.slice(1);

    const isCopywriting = stage.stage_name === 'copywriting';

    document.getElementById('wfStageContent').innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <div>
                <h3 style="margin:0">${icon} Stage ${stage.stage_number}: ${label}</h3>
                <div style="font-size:11px;color:var(--text-muted);margin-top:4px">${wf.title}</div>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="closeModal('wfStageModal')">Close</button>
        </div>

        <div class="wf2-deliverable">
            ${stage.output_data ? formatMD(stage.output_data) : '<div style="color:var(--text-muted)">No output yet.</div>'}
        </div>

        <!-- Actions -->
        <div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--border);display:flex;gap:8px;flex-wrap:wrap">
            <button class="btn btn-secondary btn-sm" onclick="requestRevision(${wfId},${stageId},'${label}')">✏️ Request Changes</button>
            ${isCopywriting ? `<button class="btn btn-primary btn-sm" onclick="generateVoiceover(${wfId},${stageId})">🎙️ Generate Voiceover</button>` : ''}
            <button class="btn btn-secondary btn-sm" onclick="copyStageOutput(this)" data-text="${escapeHTML((stage.output_data||'').replace(/"/g,'&quot;'))}">📋 Copy Text</button>
        </div>

        ${isCopywriting ? '<div id="wfVoiceoverResult" style="margin-top:10px"></div>' : ''}
    `;
    document.getElementById('wfStageModal').classList.add('active');
}

function showNewWorkflow() {
    document.getElementById('wfNewPanel').style.display = 'block';
    document.getElementById('wfCommand')?.focus();
}

async function startNewWorkflow() {
    const command = document.getElementById('wfCommand').value.trim();
    if (!command) return;

    const btn = document.getElementById('wfStartBtn');
    const status = document.getElementById('wfStatus');
    btn.disabled = true;
    btn.textContent = '⏳ Starting...';

    try {
        const res = await fetch('/api/workflows', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ command }),
        });
        const data = await res.json();
        status.innerHTML = `<div style="color:var(--success)">✅ Workflow started! ${data.stages?.length || 0} stages will execute automatically.</div>`;
        document.getElementById('wfCommand').value = '';
        setTimeout(() => renderSocialWorkspace(document.getElementById('mainContent')), 2000);
    } catch (e) {
        status.innerHTML = `<div style="color:var(--danger)">Error: ${e.message}</div>`;
    }
    btn.disabled = false;
    btn.textContent = '🚀 Start Workflow';
}

async function approveWorkflow(wfId) {
    await fetch(`/api/workflows/${wfId}/approve`, { method: 'POST' });
    renderSocialWorkspace(document.getElementById('mainContent'));
}

async function requestRevision(wfId, stageId, stageName) {
    const feedback = prompt(`What changes do you want for ${stageName}?`);
    if (!feedback) return;

    closeModal('wfStageModal');
    await fetch(`/api/workflows/${wfId}/stages/${stageId}/revise`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ feedback }),
    });
    // UI will auto-refresh when revision completes
    alert(`Revision started for ${stageName}. You'll be notified when done.`);
    renderSocialWorkspace(document.getElementById('mainContent'));
}

async function generateVoiceover(wfId, stageId) {
    const resultEl = document.getElementById('wfVoiceoverResult');
    if (!resultEl) return;

    // Show voice picker
    resultEl.innerHTML = '<div style="color:var(--accent)">Loading voices...</div>';

    let voices = { elevenlabs: [], openai: [] };
    try { voices = await fetch('/api/voices').then(r => r.json()); } catch(e) {}

    const elVoices = voices.elevenlabs || [];
    const oaVoices = voices.openai || [];

    resultEl.innerHTML = `
        <div class="vo-picker">
            <div class="vo-picker-title">🎙️ Choose a Voice</div>
            ${elVoices.length ? `
                <div class="vo-group-label">ElevenLabs${elVoices.some(v=>v.category==='cloned') ? ' (includes your cloned voices)' : ''}</div>
                <div class="vo-grid">
                    ${elVoices.map(v => `
                        <button class="vo-voice-btn" onclick="doGenerateVoiceover(${wfId},${stageId},'${escapeHTML(v.name)}')" title="${v.category}">
                            <span class="vo-voice-icon">${v.category === 'cloned' ? '⭐' : v.category === 'professional' ? '🎤' : '🔊'}</span>
                            <span class="vo-voice-name">${v.name.split(' - ')[0]}</span>
                        </button>
                    `).join('')}
                </div>
            ` : ''}
            <div class="vo-group-label">OpenAI</div>
            <div class="vo-grid">
                ${oaVoices.map(v => `
                    <button class="vo-voice-btn" onclick="doGenerateVoiceover(${wfId},${stageId},'${v.id}')">
                        <span class="vo-voice-icon">🔊</span>
                        <span class="vo-voice-name">${v.name}</span>
                    </button>
                `).join('')}
            </div>
        </div>
    `;
}

async function doGenerateVoiceover(wfId, stageId, voice) {
    const resultEl = document.getElementById('wfVoiceoverResult');
    if (resultEl) resultEl.innerHTML = `<div style="color:var(--accent)">🎙️ Generating with "${voice}"...</div>`;

    try {
        const res = await fetch(`/api/workflows/${wfId}/voiceover`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ voice, stage_id: stageId }),
        });
        const data = await res.json();

        if (data.path) {
            if (resultEl) resultEl.innerHTML = `
                <div style="color:var(--success);margin-bottom:8px">✅ Voiceover ready — ${voice}</div>
                <audio controls style="width:100%"><source src="${data.path}" type="audio/mpeg"></audio>
                <div style="margin-top:6px;display:flex;gap:6px">
                    <a href="${data.path}" download class="btn btn-secondary btn-sm" style="text-decoration:none">Download</a>
                    <button class="btn btn-primary btn-sm" onclick="generateVoiceover(${wfId},${stageId})">🎙️ Try Another Voice</button>
                </div>
            `;
        } else {
            if (resultEl) resultEl.innerHTML = `<div style="color:var(--danger)">Error: ${data.error}</div>`;
        }
    } catch (e) {
        if (resultEl) resultEl.innerHTML = `<div style="color:var(--danger)">Error: ${e.message}</div>`;
    }
}

function copyStageOutput(btn) {
    const text = btn.dataset.text?.replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
    if (text) {
        navigator.clipboard.writeText(text);
        btn.textContent = '✅ Copied!';
        setTimeout(() => btn.textContent = '📋 Copy Text', 2000);
    }
}

async function addMusicStage(wfId) {
    await fetch(`/api/workflows/${wfId}/add-voiceover`, { method: 'POST' }); // reuse endpoint but for music
    // Actually add music stage via dedicated endpoint
    const db_res = await fetch(`/api/workflows/${wfId}/add-music`, { method: 'POST' });
    const full = await fetch(`/api/workflows/${wfId}`).then(r => r.json());
    if (full.stages) renderWorkflowStages(wfId, full);
}

async function showMusicPicker(wfId, stageId) {
    // Load library tracks
    const tracks = await fetch('/api/music').then(r => r.json());

    const modal = document.createElement('div');
    modal.className = 've2-modal-overlay';
    modal.innerHTML = `<div class="ve2-modal" style="max-width:550px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3 style="margin:0">🎵 Music Library</h3>
            <button onclick="this.closest('.ve2-modal-overlay').remove()" style="background:none;border:none;color:var(--text-secondary);font-size:18px;cursor:pointer">✕</button>
        </div>

        <!-- Upload -->
        <div style="margin-bottom:14px;padding:12px;border:2px dashed var(--border);border-radius:8px;text-align:center;cursor:pointer;position:relative">
            <div style="font-size:13px;color:var(--text-muted)">📁 Drop or click to upload music (MP3, WAV)</div>
            <input type="file" accept="audio/*" style="position:absolute;inset:0;opacity:0;cursor:pointer"
                onchange="uploadMusicTrack(this.files[0],${wfId},${stageId})">
        </div>

        <!-- Library tracks -->
        ${tracks.length ? `
            <div class="vo-group-label">Your Library (${tracks.length} tracks)</div>
            <div style="max-height:300px;overflow-y:auto;display:flex;flex-direction:column;gap:6px">
                ${tracks.map(t => `
                    <div class="music-track-item">
                        <div style="flex:1;min-width:0">
                            <div style="font-size:12px;font-weight:600;color:var(--text-primary)">${escapeHTML(t.name)}</div>
                            <div style="font-size:10px;color:var(--text-muted)">${t.size_mb} MB · ${t.ext}</div>
                        </div>
                        <audio controls preload="none" style="height:28px;width:140px"><source src="${t.path}" type="audio/mpeg"></audio>
                        <button class="btn btn-sm" style="font-size:10px;padding:3px 8px;background:#e91e63;color:#fff" onclick="this.closest('.ve2-modal-overlay').remove();selectMusicTrack(${wfId},${stageId},'${t.path}')">Use</button>
                    </div>
                `).join('')}
            </div>
        ` : '<div style="color:var(--text-muted);font-size:12px;padding:10px;text-align:center">No tracks yet. Upload some music!</div>'}
    </div>`;
    document.body.appendChild(modal);
}

async function uploadMusicTrack(file, wfId, stageId) {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/music/upload', { method: 'POST', body: formData });
    const data = await res.json();
    // Close modal and reopen
    document.querySelector('.ve2-modal-overlay')?.remove();
    if (data.path) {
        selectMusicTrack(wfId, stageId, data.path);
    } else {
        showMusicPicker(wfId, stageId);
    }
}

async function selectMusicTrack(wfId, stageId, trackPath) {
    await fetch(`/api/workflows/${wfId}/stages/${stageId}/output`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ output: trackPath }),
    });
    const full = await fetch(`/api/workflows/${wfId}`).then(r => r.json());
    if (full.stages) renderWorkflowStages(wfId, full);
}

async function retryStage(wfId, stageId) {
    const res = await fetch(`/api/workflows/${wfId}/stages/${stageId}/run`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'started') {
        // Refresh to show active state
        renderSocialWorkspace(document.getElementById('mainContent'));
    } else {
        alert(data.error || 'Failed to start stage');
    }
}


// ============================================================
// RESEARCH & SALES WORKSPACE
// ============================================================
async function renderResearchWorkspace(el) {
    const [tasks, projects] = await Promise.all([
        fetch('/api/tasks').then(r => r.json()),
        fetch('/api/projects').then(r => r.json()),
    ]);

    // Only research-related tasks (browser + manager + email agents)
    const researchTasks = tasks.filter(t => ['browser', 'manager', 'email'].includes(t.assigned_agent));
    const activeTasks = researchTasks.filter(t => t.status === 'in_progress');
    const queuedTasks = researchTasks.filter(t => t.status === 'pending');
    const doneTasks = researchTasks.filter(t => t.status === 'completed').slice(0, 5);

    const totalLeads = projects.reduce((s, p) => s + (p.lead_count || 0), 0);
    const totalEmails = projects.reduce((s, p) => s + (p.email_count || 0), 0);

    el.innerHTML = `
        <div class="page-header">
            <div><h2>Research & Sales</h2><div class="subtitle">Market research, prospecting, outreach</div></div>
            <div style="display:flex;gap:6px">
                <button class="btn btn-sm" style="background:linear-gradient(135deg,#c9a44e,#e67e22);color:#fff;font-weight:600" onclick="showProspectingPanel()">🎯 Vibe Prospecting</button>
                <button class="btn btn-primary btn-sm" onclick="openAgentChat('kai')">🔍 Ask Kai</button>
                <button class="btn btn-primary btn-sm" onclick="openAgentChat('elena')">📧 Ask Elena</button>
            </div>
        </div>

        <!-- Prospecting Panel -->
        <div class="vp-panel" id="vpPanel" style="display:none">
            <div class="vp-header">
                <div><strong>🎯 Vibe Prospecting</strong><div style="font-size:11px;color:var(--text-muted)">Auto-discover → enrich → qualify → outreach</div></div>
                <button class="of-close-btn" onclick="document.getElementById('vpPanel').style.display='none'">✕</button>
            </div>
            <div class="vp-body">
                <div class="vp-row">
                    <div class="form-group" style="flex:2"><label>Location</label><input id="vpLocation" placeholder="Dubai, Slovenia..." value="Dubai"></div>
                    <div class="form-group" style="flex:1"><label>Count</label><input id="vpCount" type="number" value="50" min="10" max="200"></div>
                </div>
                <div class="form-group"><label>Project Name</label><input id="vpName" placeholder="Auto-generated if empty"></div>
                <div class="form-group"><label>Industries to INCLUDE (empty = all)</label><input id="vpIndustries" placeholder="restaurants, hotels, real estate, fashion, beauty..."></div>
                <div class="form-group"><label>Industries to EXCLUDE</label><input id="vpExclude" placeholder="IT, software, banks, government..."></div>
                <div class="form-group"><label>Requirements</label>
                    <div style="display:flex;gap:12px;flex-wrap:wrap;font-size:12px;margin-top:4px">
                        <label style="display:flex;align-items:center;gap:4px;cursor:pointer"><input type="checkbox" id="vpNeedEmail" checked> Must have email</label>
                        <label style="display:flex;align-items:center;gap:4px;cursor:pointer"><input type="checkbox" id="vpNeedPhone"> Must have phone</label>
                        <label style="display:flex;align-items:center;gap:4px;cursor:pointer"><input type="checkbox" id="vpNeedWebsite" checked> Must have website</label>
                    </div>
                </div>
                <button class="btn btn-primary" style="width:100%;padding:10px" onclick="runProspecting()" id="vpRunBtn">🎯 Start Prospecting</button>
                <div id="vpStatus" style="margin-top:8px"></div>
            </div>
        </div>

        <!-- Stats -->
        <div class="tk-stats-row" style="margin-bottom:12px">
            <div class="tk-stat"><div class="tk-stat-num">${projects.length}</div><div class="tk-stat-label">Projects</div></div>
            <div class="tk-stat"><div class="tk-stat-num">${totalLeads}</div><div class="tk-stat-label">Leads</div></div>
            <div class="tk-stat"><div class="tk-stat-num">${totalEmails}</div><div class="tk-stat-label">Emails</div></div>
            <div class="tk-stat tk-stat-active"><div class="tk-stat-num">${activeTasks.length}</div><div class="tk-stat-label">Active</div></div>
        </div>

        <!-- Active research -->
        ${activeTasks.length ? `
        <div class="ws-active">
            <div class="ws-active-title">🔍 Researching Now</div>
            ${activeTasks.map(t => {
                const a = AGENT_INFO[t.assigned_agent] || { icon: '⚙️', label: t.assigned_agent, color: '#888' };
                return `<div class="ws-active-item" style="border-left-color:${a.color}">
                    <span>${a.icon} <strong>${a.label}</strong></span>
                    <span>${t.title}</span>
                    <div style="display:flex;gap:3px">
                        <button class="tk-mini-btn tk-btn-done" onclick="event.stopPropagation();quickUpdateTask(${t.id},'completed')">✓</button>
                        <button class="tk-mini-btn tk-btn-stop" onclick="event.stopPropagation();cancelTask(${t.id})">■</button>
                    </div>
                </div>`;
            }).join('')}
        </div>` : ''}

        <!-- Queued -->
        ${queuedTasks.length ? `
        <div class="ws-queue">
            <div class="ws-queue-title">📋 Queued (${queuedTasks.length})</div>
            ${queuedTasks.map(t => `
                <div class="ws-queue-item">
                    <span>${t.title}</span>
                    <div style="display:flex;gap:4px">
                        <button class="tk-mini-btn tk-btn-start" onclick="startTask(${t.id})">▶</button>
                        <button class="tk-mini-btn tk-btn-del" onclick="deleteTask(${t.id})">×</button>
                    </div>
                </div>
            `).join('')}
        </div>` : ''}

        <!-- Research Projects -->
        <div style="margin-top:16px">
            <div class="pp-section-title">📁 Research Projects</div>
            ${projects.length ? `
            <div class="rv-grid">
                ${projects.map(p => `
                    <div class="rv-folder" onclick="openProjectId=${p.id};navigateTo('leads')">
                        <div class="rv-folder-icon">📁</div>
                        <div class="rv-folder-info">
                            <div class="rv-folder-name">${escapeHTML(p.name)}</div>
                            <div class="rv-folder-stats">
                                <span>📋 ${p.lead_count || 0}</span>
                                <span>📧 ${p.email_count || 0}</span>
                                <span>${tkTimeAgo(p.created_at)}</span>
                            </div>
                        </div>
                        <button class="btn btn-sm" style="font-size:9px;padding:2px 8px;background:var(--accent);color:#0c0c12" onclick="event.stopPropagation();runAutoOutreach(${p.id})">📄 Outreach</button>
                    </div>
                `).join('')}
            </div>` : '<div class="empty-state"><p>No research projects yet. Start a Vibe Prospecting campaign!</p></div>'}
        </div>

        <!-- Recent completed -->
        ${doneTasks.length ? `
        <div style="margin-top:16px">
            <div class="pp-section-title">✅ Recently Completed</div>
            <div class="pp-deliverables">
                ${doneTasks.map(t => `
                    <div class="pp-delivery-item">
                        <span style="color:var(--success)">✓</span>
                        <span>${t.title}</span>
                        <span class="pp-delivery-time">${tkTimeAgo(t.completed_at || t.created_at)}</span>
                    </div>
                `).join('')}
            </div>
        </div>` : ''}
    `;
}


async function renderSettings(el) {
    let notifConfig = {};
    try { notifConfig = await (await fetch('/api/notifications/config')).json(); } catch(e) {}

    el.innerHTML = `
        <div class="page-header"><div><h2>Settings</h2><div class="subtitle">Platform configuration</div></div></div>

        <!-- Notifications -->
        <div class="stat-card" style="max-width:600px;margin-bottom:16px">
            <div class="section-title">📱 Phone Notifications</div>
            <p style="font-size:13px;color:var(--text-secondary);line-height:1.8;margin-bottom:16px">
                Get notified on your phone when tasks complete, videos are ready, or reports are generated.
            </p>

            <!-- ntfy.sh -->
            <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <strong style="font-size:13px">Option 1: ntfy.sh (Easiest — Zero Setup)</strong>
                    <span class="badge ${notifConfig.ntfy_enabled ? 'badge-active' : 'badge-paused'}">${notifConfig.ntfy_enabled ? 'ON' : 'OFF'}</span>
                </div>
                <div style="font-size:12px;color:var(--text-secondary);line-height:1.6">
                    <strong>Steps:</strong><br>
                    1. On your iPhone/Android, open Safari/Chrome<br>
                    2. Go to: <code style="color:var(--accent);cursor:pointer" onclick="navigator.clipboard.writeText('${notifConfig.ntfy_url||'https://ntfy.sh/dubai-prod-agent'}');this.textContent='Copied!'">${notifConfig.ntfy_url || 'https://ntfy.sh/dubai-prod-agent'}</code> (tap to copy)<br>
                    3. Click "Subscribe" — done! You'll get push notifications<br>
                    <span style="color:var(--text-muted)">Or install the ntfy app from App Store / Play Store for better experience</span>
                </div>
            </div>

            <!-- Telegram -->
            <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <strong style="font-size:13px">Option 2: Telegram Bot</strong>
                    <span class="badge ${notifConfig.telegram_enabled ? 'badge-active' : 'badge-paused'}">${notifConfig.telegram_enabled ? 'ON' : 'OFF'}</span>
                </div>
                <div style="font-size:12px;color:var(--text-secondary);line-height:1.6">
                    <strong>Steps:</strong><br>
                    1. Open Telegram → search @BotFather → /newbot → get your token<br>
                    2. Message your bot, then get chat_id from <code style="color:var(--accent)">api.telegram.org/bot&lt;TOKEN&gt;/getUpdates</code><br>
                    3. Add to <code style="color:var(--accent)">.env</code>:<br>
                    <code style="color:var(--accent)">TELEGRAM_BOT_TOKEN=your_token</code><br>
                    <code style="color:var(--accent)">TELEGRAM_CHAT_ID=your_chat_id</code><br>
                    4. Restart the server
                </div>
            </div>

            <!-- Browser -->
            <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <strong style="font-size:13px">Option 3: Browser Notifications</strong>
                    <span class="badge" id="browserNotifBadge">checking...</span>
                </div>
                <div style="font-size:12px;color:var(--text-secondary);line-height:1.6">
                    Works when the browser tab is open. Click to enable:
                </div>
                <button class="btn btn-primary btn-sm" style="margin-top:8px" onclick="enableBrowserNotifications()">Enable Browser Notifications</button>
            </div>

            <button class="btn btn-secondary" style="width:100%" onclick="testNotification()">🔔 Send Test Notification</button>
        </div>

        <!-- Config -->
        <div class="stat-card" style="max-width:600px">
            <div class="section-title">Configuration</div>
            <p style="font-size:13px;color:var(--text-secondary);line-height:1.6">
                Edit <code style="color:var(--accent)">config/settings.yaml</code> for agent settings.<br>
                Edit <code style="color:var(--accent)">.env</code> for API keys and email credentials.
            </p>
        </div>
    `;

    // Check browser notification status
    const badge = document.getElementById('browserNotifBadge');
    if (badge) {
        if (!('Notification' in window)) badge.textContent = 'Not supported';
        else if (Notification.permission === 'granted') { badge.textContent = 'ON'; badge.className = 'badge badge-active'; }
        else if (Notification.permission === 'denied') { badge.textContent = 'Blocked'; badge.className = 'badge badge-paused'; }
        else { badge.textContent = 'OFF'; badge.className = 'badge badge-paused'; }
    }
}

function enableBrowserNotifications() {
    if (!('Notification' in window)) { alert('Browser notifications not supported'); return; }
    Notification.requestPermission().then(p => {
        if (p === 'granted') {
            new Notification('Dubai Prod Agent', { body: 'Notifications enabled! You will be notified when tasks complete.', icon: '/static/img/avatar_sarah.png' });
            renderSettings(document.getElementById('mainContent'));
        }
    });
}

async function testNotification() {
    // Server-side notification (ntfy + telegram)
    await fetch('/api/notifications/test', { method: 'POST' });

    // Browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Dubai Prod Agent 🔔', { body: 'Test notification — everything is working!', icon: '/static/img/avatar_sarah.png' });
    }

    alert('Test notification sent to all enabled channels!');
}

// Browser notification helper — call from anywhere
function browserNotify(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body, icon: '/static/img/avatar_sarah.png' });
    }
}

// ---- Helpers ----
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

function escapeHTML(text) {
    return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function formatMD(text) {
    let h = escapeHTML(text);
    h = h.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    h = h.replace(/`([^`]+)`/g, '<code style="color:var(--accent)">$1</code>');
    h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');
    h = h.replace(/\n/g, '<br>');
    h = h.replace(/<br><pre>/g, '<pre>').replace(/<\/pre><br>/g, '</pre>');
    return h;
}
