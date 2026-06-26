// App state
let activeSessionId = null;
let activeWidgets = 0;

const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const btnSend = document.getElementById('btn-send');
const sandboxContent = document.getElementById('sandbox-content');
const emptyState = document.getElementById('empty-state');
const widgetBadge = document.getElementById('widget-badge');
const sessionsListContainer = document.getElementById('sessions-list');
const btnNewChat = document.getElementById('btn-new-chat');
const sandboxPane = document.querySelector('.sandbox-pane');
const sidebarPane = document.querySelector('.sidebar-pane');
const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');

const btnAttach = document.getElementById('btn-attach');
const btnMic = document.getElementById('btn-mic');
const fileInput = document.getElementById('file-upload-input');
const stagedFilesArea = document.getElementById('staged-files-area');
const voiceWaves = document.getElementById('voice-waves');
let stagedFiles = [];

function updateSandboxVisibility() {
    if (activeWidgets > 0) {
        sandboxPane.classList.remove('collapsed');
    } else {
        sandboxPane.classList.add('collapsed');
    }
}

function showTypingIndicator() {
    if (document.getElementById('typing-indicator')) return;
    
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message agent loading';
    msgDiv.id = 'typing-indicator';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar';
    avatarDiv.textContent = '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    
    const loaderDiv = document.createElement('div');
    loaderDiv.className = 'typing-loader';
    loaderDiv.innerHTML = '<span></span><span></span><span></span>';
    
    contentDiv.appendChild(loaderDiv);
    msgDiv.appendChild(avatarDiv);
    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Indicators
const indicators = {
    supervisor: document.getElementById('indicator-supervisor'),
    pricing: document.getElementById('indicator-pricing'),
    activate: document.getElementById('indicator-activate'),
    loyalty: document.getElementById('indicator-loyalty'),
    profile: document.getElementById('indicator-profile')
};

function setIndicator(activeName) {
    Object.keys(indicators).forEach(name => {
        if (name === activeName) {
            indicators[name].classList.add('active');
        } else {
            indicators[name].classList.remove('active');
        }
    });
}

function speakText(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const cleanText = text.replace(/[*_#`⚠️]/g, '').trim();
        const utterance = new SpeechSynthesisUtterance(cleanText);
        window.speechSynthesis.speak(utterance);
    } else {
        console.warn("Speech Synthesis not supported in this browser.");
    }
}

function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar';
    avatarDiv.textContent = role === 'user' ? '👤' : '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    contentDiv.textContent = text;
    contentDiv.style.whiteSpace = 'pre-wrap';
    
    if (role === 'agent') {
        const speakBtn = document.createElement('button');
        speakBtn.className = 'btn-speak';
        speakBtn.innerHTML = '🔊';
        speakBtn.title = 'Speak text';
        speakBtn.onclick = () => speakText(text);
        contentDiv.appendChild(speakBtn);
    }
    
    msgDiv.appendChild(avatarDiv);
    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return contentDiv;
}

function renderA2UIWidget(widget) {
    if (emptyState) {
        emptyState.style.display = 'none';
    }
    
    // Find the WebFrameSrcdoc components
    let htmlContent = "";
    let surfaceId = widget.surfaceId || "A2UI Widget";
    
    // Traversal function to find htmlContent recursively
    function findHtmlContent(node) {
        if (!node || typeof node !== 'object') return;
        if (node.WebFrameSrcdoc && node.WebFrameSrcdoc.htmlContent && node.WebFrameSrcdoc.htmlContent.literalString) {
            htmlContent = node.WebFrameSrcdoc.htmlContent.literalString;
            return;
        }
        for (let key in node) {
            if (node.hasOwnProperty(key)) {
                const val = node[key];
                if (Array.isArray(val)) {
                    val.forEach(findHtmlContent);
                } else if (typeof val === 'object') {
                    findHtmlContent(val);
                }
            }
        }
    }
    
    findHtmlContent(widget);
    
    if (!htmlContent) {
        console.warn("No htmlContent found in widget data:", widget);
        return;
    }
    
    activeWidgets++;
    widgetBadge.textContent = `${activeWidgets} Active Widget${activeWidgets > 1 ? 's' : ''}`;
    updateSandboxVisibility();
    
    const card = document.createElement('div');
    card.className = 'widget-card';
    
    const header = document.createElement('div');
    header.className = 'widget-card-header';
    header.style.cursor = 'pointer';
    
    const headerLeft = document.createElement('div');
    headerLeft.style.display = 'flex';
    headerLeft.style.alignItems = 'center';
    headerLeft.style.gap = '8px';
    
    const twistie = document.createElement('span');
    twistie.className = 'widget-twistie';
    twistie.textContent = '▼';
    twistie.style.fontSize = '10px';
    twistie.style.color = 'var(--text-primary)';
    
    const title = document.createElement('span');
    title.className = 'widget-title';
    title.textContent = surfaceId.replace(/-/g, ' ').toUpperCase();
    
    headerLeft.appendChild(twistie);
    headerLeft.appendChild(title);
    
    const badge = document.createElement('span');
    badge.className = 'widget-badge';
    badge.textContent = 'interactive';
    
    header.appendChild(headerLeft);
    header.appendChild(badge);
    
    const iframeContainer = document.createElement('div');
    iframeContainer.className = 'iframe-container';
    
    const isActivation = surfaceId.includes('activation') || htmlContent.includes('aud-tile') || htmlContent.includes('Scaled to a Complete');
    const defaultH = isActivation ? 700 : 450;
    iframeContainer.style.height = defaultH + 'px';
    
    header.onclick = () => {
        if (iframeContainer.style.display === 'none') {
            iframeContainer.style.display = 'block';
            twistie.textContent = '▼';
        } else {
            iframeContainer.style.display = 'none';
            twistie.textContent = '▶';
        }
    };
    
    const iframe = document.createElement('iframe');
    iframe.scrolling = 'yes';
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    
    iframeContainer.appendChild(iframe);
    card.appendChild(header);
    card.appendChild(iframeContainer);
    
    // Auto-collapse older widgets
    const oldWidgets = sandboxContent.querySelectorAll('.widget-card');
    oldWidgets.forEach(w => {
        const c = w.querySelector('.iframe-container');
        const t = w.querySelector('.widget-card-header span:last-child');
        if (c) c.style.display = 'none';
        if (t) t.textContent = '▶';
    });
    
    // Append to top of sandbox list before setting srcdoc
    sandboxContent.insertBefore(card, sandboxContent.firstChild);
    
    iframe.onload = () => {
        try {
            const win = iframe.contentWindow;
            const doc = win.document;
            const syncHeight = () => {
                const wrapper = doc.querySelector('.wrapper') || doc.body;
                const wrapperH = wrapper ? wrapper.scrollHeight : 0;
                const bodyH = doc.body ? doc.body.scrollHeight : 0;
                const docH = doc.documentElement ? doc.documentElement.scrollHeight : 0;
                const h = Math.max(bodyH, docH, wrapperH);
                if (h > 50 && h < 800) {
                    iframeContainer.style.height = (h + 40) + 'px';
                }
            };
            syncHeight();
            setTimeout(syncHeight, 100);
            setTimeout(syncHeight, 500);
            if (win.ResizeObserver && doc.body) {
                const ro = new win.ResizeObserver(syncHeight);
                ro.observe(doc.body);
            }
        } catch (e) {
            console.error("Dynamic iframe height sync:", e);
        }
    };
    
    iframe.srcdoc = htmlContent;
}

// Session Management REST Calls
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        if (!response.ok) throw new Error("Failed to list sessions");
        const sessions = await response.json();
        
        sessionsListContainer.innerHTML = '';
        if (sessions.length === 0) {
            sessionsListContainer.innerHTML = '<div class="session-loading">No conversations yet</div>';
            await createNewSession();
            return;
        }
        
        sessions.forEach(s => {
            const item = document.createElement('div');
            item.className = `session-item ${s.id === activeSessionId ? 'active' : ''}`;
            item.dataset.id = s.id;
            
            const details = document.createElement('div');
            details.className = 'session-details';
            details.onclick = () => selectSession(s.id);
            
            const name = document.createElement('span');
            name.className = 'session-name';
            name.textContent = `Session: ${s.id.substring(0, 8)}`;
            
            const time = document.createElement('span');
            time.className = 'session-time';
            if (s.create_time) {
                const date = new Date(s.create_time);
                time.textContent = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + " " + date.toLocaleDateString();
            } else {
                time.textContent = "unknown";
            }
            
            details.appendChild(name);
            details.appendChild(time);
            
            const btnDelete = document.createElement('button');
            btnDelete.className = 'btn-delete-session';
            btnDelete.innerHTML = '🗑️';
            btnDelete.onclick = (e) => {
                e.stopPropagation();
                deleteSession(s.id);
            };
            
            item.appendChild(details);
            item.appendChild(btnDelete);
            sessionsListContainer.appendChild(item);
        });
        
        if (!activeSessionId && sessions.length > 0) {
            selectSession(sessions[0].id);
        }
    } catch (err) {
        console.error("Load sessions error:", err);
        sessionsListContainer.innerHTML = '<div class="session-loading">Error loading conversations</div>';
    }
}

async function createNewSession() {
    try {
        const response = await fetch('/api/sessions', { method: 'POST' });
        if (!response.ok) throw new Error("Failed to create new session");
        const data = await response.json();
        activeSessionId = data.id;
        
        await loadSessions();
        selectSession(data.id);
    } catch (err) {
        console.error("Create session error:", err);
    }
}

async function deleteSession(id) {
    try {
        const response = await fetch(`/api/sessions/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error("Failed to delete session");
        
        if (activeSessionId === id) {
            activeSessionId = null;
        }
        await loadSessions();
    } catch (err) {
        console.error("Delete session error:", err);
    }
}

async function selectSession(id) {
    activeSessionId = id;
    document.getElementById('session-display').textContent = `Session ID: ${id.substring(0, 8)}`;
    
    // Highlight active sidebar item
    const items = document.querySelectorAll('.session-item');
    items.forEach(item => {
        if (item.dataset.id === id) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Clear chat panes & sandboxes
    chatMessages.innerHTML = '';
    sandboxContent.innerHTML = '';
    activeWidgets = 0;
    widgetBadge.textContent = '0 Active Widgets';
    updateSandboxVisibility();
    if (emptyState) {
        emptyState.style.display = 'flex';
    }
    
    // Show default initial welcome
    const welcome = document.createElement('div');
    welcome.className = 'message system';
    welcome.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="content">
            Welcome to the Circana Pilot multi-agent orchestrator. I can help coordinate your pricing analysis, cohort sizing, and campaign activations. Try asking:
            <div class="suggestions">
                <button onclick="suggest('Identify pricing opportunities with shopper attrition in the Soft Drinks category.')">🔍 Identify soft drink attrition opportunities</button>
            </div>
        </div>
    `;
    chatMessages.appendChild(welcome);
    
    try {
        const response = await fetch(`/api/sessions/${id}`);
        if (!response.ok) throw new Error("Failed to load history");
        const history = await response.json();
        
        if (history.length > 0) {
            chatMessages.innerHTML = ''; // wipe welcome message
            history.forEach(item => {
                // If it is a tech/action log like "Clicked action: ...", we can render it as system status or skip
                // Let's render as chat messages
                const role = item.role === 'model' || item.role === 'assistant' ? 'agent' : 'user';
                appendMessage(role, item.text);
                
                if (item.widgets && item.widgets.length > 0) {
                    item.widgets.forEach(renderA2UIWidget);
                }
            });
        }
    } catch (err) {
        console.error("Load history error:", err);
        appendMessage('system', `Error loading session history: ${err.message}`);
    }
}

// User text query input submission
async function submitUserMessage(message) {
    if (!message.trim() && stagedFiles.length === 0) return;
    if (!activeSessionId) return;
    
    let displayMessage = message;
    if (stagedFiles.length > 0) {
        displayMessage += "\n📎 Files attached: " + stagedFiles.map(f => f.filename).join(', ');
    }
    
    appendMessage('user', displayMessage);
    userInput.value = '';
    
    const attachments = stagedFiles.map(f => f.gcs_uri);
    
    // Clear staging area
    stagedFiles = [];
    stagedFilesArea.innerHTML = '';
    
    // Disable inputs
    userInput.disabled = true;
    btnSend.disabled = true;
    btnAttach.disabled = true;
    btnMic.disabled = true;
    setIndicator('supervisor');
    
    const msgLower = message.toLowerCase();
    if (msgLower.includes('pricing') || msgLower.includes('attrition') || msgLower.includes('soft drinks')) {
        setIndicator('pricing');
    } else if (msgLower.includes('loyalty') || msgLower.includes('campaign') || msgLower.includes('discount')) {
        setIndicator('loyalty');
    }
    
    showTypingIndicator();
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, session_id: activeSessionId, attachments: attachments })
        });
        
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            const errMsg = errData.detail || `Server returned HTTP ${response.status}`;
            throw new Error(errMsg);
        }
        
        const data = await response.json();
        setIndicator('supervisor');
        
        removeTypingIndicator();
        if (data.status === "Running" && data.job_id) {
            await handleJobPolling(data.job_id, data.message || "Queueing database job...");
            return;
        }
        if (data.text) {
            appendMessage('agent', data.text);
        }
        if (data.widgets && data.widgets.length > 0) {
            data.widgets.forEach(renderA2UIWidget);
        }
    } catch (err) {
        removeTypingIndicator();
        console.error("Chat Error:", err);
        appendMessage('system', `Error sending message: ${err.message}`);
        setIndicator('supervisor');
    } finally {
        removeTypingIndicator();
        userInput.disabled = false;
        btnSend.disabled = false;
        btnAttach.disabled = false;
        btnMic.disabled = false;
        userInput.focus();
    }
}

// Interactive callback payload submission
async function submitInteractiveAction(action) {
    if (!activeSessionId) return;
    
    let turnDescription = `User Action: ${action.actionId}`;
    let userPromptText = "";
    
    if (action.actionId === 'product_selected') {
        userPromptText = `Selected product: ${action.payload.product}`;
        setIndicator('activate');
    } else if (action.actionId === 'btn_activate') {
        const partners = action.payload.partners ? action.payload.partners.join(', ') : 'None';
        userPromptText = `Exporting cohort segment to: ${partners}`;
        setIndicator('activate');
    } else if (action.actionId === 'btn_launch_campaign') {
        userPromptText = `Launching personalized campaign for ${action.payload.product} (${action.payload.discount_pct}% discount, ${action.payload.points_mult}x multiplier)`;
        setIndicator('loyalty');
    } else if (action.actionId === 'profile_audience') {
        userPromptText = `Compiling demographic breakdown and audience profile...`;
        setIndicator('profile');
    } else {
        userPromptText = `Initiating A2UI callback action: ${action.actionId}`;
    }
    
    appendMessage('user', userPromptText);
    
    userInput.disabled = true;
    btnSend.disabled = true;
    
    showTypingIndicator();
    try {
        const response = await fetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action, session_id: activeSessionId })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned HTTP ${response.status}`);
        }
        
        const data = await response.json();
        setIndicator('supervisor');
        
        removeTypingIndicator();
        if (data.status === "Running" && data.job_id) {
            await handleJobPolling(data.job_id, data.message || "Queueing database job...");
            return;
        }
        if (data.text) {
            appendMessage('agent', data.text);
        }
        if (data.widgets && data.widgets.length > 0) {
            data.widgets.forEach(renderA2UIWidget);
        }
    } catch (err) {
        removeTypingIndicator();
        console.error("Action Callback Error:", err);
        appendMessage('system', `Error executing callback action: ${err.message}`);
        setIndicator('supervisor');
    } finally {
        removeTypingIndicator();
        userInput.disabled = false;
        btnSend.disabled = false;
    }
}

// Listen for iframe callbacks
window.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'USER_ACTION') {
        console.log("Captured USER_ACTION callback from widget:", event.data);
        submitInteractiveAction(event.data);
    }
});

// Input bindings
btnSend.addEventListener('click', () => submitUserMessage(userInput.value));
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        submitUserMessage(userInput.value);
    }
});

btnNewChat.addEventListener('click', createNewSession);

if (btnToggleSidebar && sidebarPane) {
    btnToggleSidebar.addEventListener('click', () => {
        sidebarPane.classList.toggle('collapsed');
    });
}

const sessionDisplay = document.getElementById('session-display');
if (sessionDisplay && sandboxPane) {
    sessionDisplay.addEventListener('click', () => {
        sandboxPane.classList.toggle('collapsed');
    });
}

// Suggestions shortcut
window.suggest = function(text) {
    userInput.value = text;
    submitUserMessage(text);
};

// File Attachment Event Listeners
if (btnAttach && fileInput) {
    btnAttach.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async () => {
        if (fileInput.files.length === 0) return;
        const file = fileInput.files[0];
        
        // Show uploading chip placeholder
        const chip = document.createElement('div');
        chip.className = 'staged-file-chip';
        chip.innerHTML = `<span>Uploading: ${file.name}...</span>`;
        stagedFilesArea.appendChild(chip);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) throw new Error("Upload failed");
            const resData = await response.json();
            
            // Add to staged list
            stagedFiles.push(resData);
            
            // Render completed chip with delete option
            chip.innerHTML = `
                <span>📎 ${file.name}</span>
                <button onclick="removeStagedFile('${resData.gcs_uri}', this)">×</button>
            `;
        } catch (err) {
            console.error("Upload error:", err);
            chip.innerHTML = `<span style="color: #ef4444;">Failed to upload: ${file.name}</span>`;
            setTimeout(() => chip.remove(), 3000);
        } finally {
            fileInput.value = '';
        }
    });
}

function removeStagedFile(gcsUri, buttonEl) {
    stagedFiles = stagedFiles.filter(f => f.gcs_uri !== gcsUri);
    buttonEl.parentElement.remove();
}
window.removeStagedFile = removeStagedFile;

// Voice Speech Recognition (STT) Bindings
let recognition = null;
let isRecording = false;

if (btnMic && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
        isRecording = true;
        btnMic.classList.add('recording');
        userInput.placeholder = "Listening...";
    };
    
    recognition.onresult = (event) => {
        const resultText = event.results[0][0].transcript;
        userInput.value = resultText;
    };
    
    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        voiceWaves.classList.add('hidden');
    };
    
    recognition.onend = () => {
        isRecording = false;
        btnMic.classList.remove('recording');
        voiceWaves.classList.add('hidden');
        userInput.placeholder = "Ask the coordinator a question or command...";
        
        // Auto-send the transcribed text if present
        const text = userInput.value.trim();
        if (text) {
            submitUserMessage(text);
        }
    };

    const startRecording = () => {
        if (!recognition || isRecording) return;
        userInput.value = "";
        
        // Position waves overlay directly over the user-input element
        const rect = userInput.getBoundingClientRect();
        const parentRect = userInput.parentElement.getBoundingClientRect();
        voiceWaves.style.left = `${rect.left - parentRect.left}px`;
        voiceWaves.style.width = `${rect.width}px`;
        voiceWaves.style.top = `${rect.top - parentRect.top}px`;
        voiceWaves.style.height = `${rect.height}px`;
        voiceWaves.classList.remove('hidden');

        try {
            recognition.start();
        } catch (e) {
            console.error("Speech recognition start failed:", e);
            voiceWaves.classList.add('hidden');
        }
    };

    const stopRecording = () => {
        if (!recognition || !isRecording) return;
        try {
            recognition.stop();
        } catch (e) {
            console.error("Speech recognition stop failed:", e);
        }
    };

    // Bind mousedown and touchstart to start recording (press-and-hold)
    btnMic.addEventListener('mousedown', (e) => {
        e.preventDefault();
        startRecording();
    });
    btnMic.addEventListener('touchstart', (e) => {
        e.preventDefault();
        startRecording();
    });

    // Bind mouseup, mouseleave, and touchend to stop recording (release)
    btnMic.addEventListener('mouseup', stopRecording);
    btnMic.addEventListener('mouseleave', stopRecording);
    btnMic.addEventListener('touchend', stopRecording);
} else if (btnMic) {
    btnMic.style.display = 'none';
}

async function handleJobPolling(jobId, initialMsg) {
    userInput.disabled = true;
    btnSend.disabled = true;
    btnAttach.disabled = true;
    btnMic.disabled = true;
    
    const loadingDiv = appendMessage('system', `🕒 [Job ${jobId}]: ${initialMsg} (0% complete)`);
    
    return new Promise((resolve, reject) => {
        const checkInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/jobs/${jobId}`);
                if (!res.ok) {
                    clearInterval(checkInterval);
                    loadingDiv.innerHTML = `❌ Job ${jobId} failed to check status.`;
                    userInput.disabled = false;
                    btnSend.disabled = false;
                    btnAttach.disabled = false;
                    btnMic.disabled = false;
                    reject(new Error("Failed to check status"));
                    return;
                }
                const job = await res.json();
                if (job.status === "Running") {
                    loadingDiv.innerHTML = `🕒 [Job ${jobId}]: ${job.message} (${job.progress}% complete)`;
                } else if (job.status === "Completed") {
                    clearInterval(checkInterval);
                    loadingDiv.innerHTML = `✅ Job ${jobId} completed successfully!`;
                    
                    if (job.result && job.result.message) {
                        appendMessage('agent', job.result.message);
                    }
                    
                    userInput.disabled = false;
                    btnSend.disabled = false;
                    btnAttach.disabled = false;
                    btnMic.disabled = false;
                    
                    if (job.result && job.result.audience_id) {
                        await submitChatMessage(`Calculate estimated match audience reach sizing metrics for isolation audience ID: ${job.result.audience_id}`);
                    }
                    resolve(job.result);
                } else {
                    clearInterval(checkInterval);
                    loadingDiv.innerHTML = `❌ Job ${jobId} failed: ${job.message || "Unknown error"}`;
                    userInput.disabled = false;
                    btnSend.disabled = false;
                    btnAttach.disabled = false;
                    btnMic.disabled = false;
                    reject(new Error(job.message || "Job failed"));
                }
            } catch (err) {
                clearInterval(checkInterval);
                loadingDiv.innerHTML = `❌ Connection error checking job ${jobId}.`;
                userInput.disabled = false;
                btnSend.disabled = false;
                btnAttach.disabled = false;
                btnMic.disabled = false;
                reject(err);
            }
        }, 2000);
    });
}

// Initial Load
loadSessions();
