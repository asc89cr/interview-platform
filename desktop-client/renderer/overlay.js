'use strict';

const { ipcRenderer } = require('electron');
const settings = require('../config/settings');

// ─── DOM refs ──────────────────────────────────────────────────────────────────
const statusDot    = document.getElementById('statusDot');
const statusLabel  = document.getElementById('statusLabel');
const transcriptEl = document.getElementById('transcript');
const answerEl     = document.getElementById('answer');
const spinner      = document.getElementById('spinner');
const sessionModal = document.getElementById('sessionModal');
const sessionSelect    = document.getElementById('sessionSelect');
const micSelect        = document.getElementById('micSelect');
const loopbackSelect   = document.getElementById('loopbackSelect');
const startSessionBtn  = document.getElementById('startSessionBtn');
const newSessionBtn    = document.getElementById('newSessionBtn');
const clearBtn         = document.getElementById('clearBtn');
const forceBtn         = document.getElementById('forceBtn');
const hideBtn          = document.getElementById('hideBtn');
const manualInput      = document.getElementById('manualInput');

// ─── State ─────────────────────────────────────────────────────────────────────
let answerBuffer = '';
let answerFlushTimer = null;

// ─── Token-batched answer rendering (50 ms flush) ─────────────────────────────
function appendAnswerToken(token) {
  answerBuffer += token;
  if (!answerFlushTimer) {
    answerFlushTimer = setTimeout(() => {
      answerEl.textContent = answerEl.textContent + answerBuffer;
      answerBuffer = '';
      answerFlushTimer = null;
      answerEl.scrollTop = answerEl.scrollHeight;
    }, 50);
  }
}

function flushAnswerBuffer() {
  if (answerFlushTimer) {
    clearTimeout(answerFlushTimer);
    answerFlushTimer = null;
  }
  if (answerBuffer) {
    answerEl.textContent = answerEl.textContent + answerBuffer;
    answerBuffer = '';
    answerEl.scrollTop = answerEl.scrollHeight;
  }
}

// ─── Transcript helpers ────────────────────────────────────────────────────────
function appendTranscript(speaker, text) {
  const label = speaker === 'interviewer' ? 'Interviewer' : 'You';
  // Each turn_saved is one complete utterance — give it its own line.
  const turn = document.createElement('div');
  turn.className = `turn ${speaker}`;
  turn.dataset.speaker = speaker;
  turn.innerHTML = `<span class="speaker">${label}</span><span class="turn-text">${escapeHtml(text)}</span>`;
  transcriptEl.appendChild(turn);
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function clearAll() {
  transcriptEl.innerHTML = '';
  answerEl.textContent = '';
  answerBuffer = '';
  clearTimeout(answerFlushTimer);
  answerFlushTimer = null;
}

// ─── Status indicator ──────────────────────────────────────────────────────────
function setStatus(s) {
  statusDot.className = `dot ${s}`;
  statusLabel.textContent = s.charAt(0).toUpperCase() + s.slice(1);
}

// ─── Spinner ───────────────────────────────────────────────────────────────────
function setSpinner(on) {
  spinner.classList.toggle('hidden', !on);
}

// ─── IPC: messages from main process ──────────────────────────────────────────
ipcRenderer.on('ws-status', (_e, status) => setStatus(status));

ipcRenderer.on('ws-message', (_e, msg) => {
  switch (msg.type) {
    case 'connected':
      setSpinner(msg.state === 'analyzing' || msg.state === 'generating');
      break;

    case 'turn_saved':
      appendTranscript(msg.speaker.toLowerCase(), msg.text);
      // Clear previous answer when a new interviewer turn arrives
      if (msg.speaker === 'Interviewer') {
        answerEl.textContent = '';
        answerBuffer = '';
        clearTimeout(answerFlushTimer);
        answerFlushTimer = null;
      }
      // Pulse the Answer button to prompt user
      forceBtn.classList.add('pulse');
      setTimeout(() => forceBtn.classList.remove('pulse'), 2000);
      break;

    case 'token':
      setSpinner(true);
      appendAnswerToken(msg.content);
      break;

    case 'answer_complete':
      flushAnswerBuffer();
      setSpinner(false);
      break;

    case 'error':
      answerEl.textContent = '[Error] ' + msg.message;
      setSpinner(false);
      break;
  }
});

ipcRenderer.on('force-answer', () => {
  setSpinner(true);
});

ipcRenderer.on('clear-conversation', () => clearAll());

ipcRenderer.on('audio-error', (_e, { speaker, message }) => {
  console.warn(`[Audio] ${speaker}: ${message}`);
});

// ─── Toolbar buttons ───────────────────────────────────────────────────────────
clearBtn.addEventListener('click', () => {
  ipcRenderer.send('clear-conversation-from-renderer');
  clearAll();
});

forceBtn.addEventListener('click', () => {
  ipcRenderer.send('force-answer-from-renderer');
  setSpinner(true);
});

hideBtn.addEventListener('click', () => {
  window.close();
});

// Manual question input — type question + Enter to get AI answer
manualInput.addEventListener('keydown', (e) => {
  if (e.key !== 'Enter') return;
  const text = manualInput.value.trim();
  if (!text) return;
  appendTranscript('interviewer', text);
  answerEl.textContent = '';
  ipcRenderer.send('manual-question', { text });
  manualInput.value = '';
});

// ─── Session modal ─────────────────────────────────────────────────────────────
async function initSessionModal() {
  // Populate audio devices
  const devices = await ipcRenderer.invoke('list-audio-devices');

  devices.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d.id;
    opt.textContent = d.name;

    if (/loopback|stereo mix|what u hear|wave out/i.test(d.name)) {
      loopbackSelect.appendChild(opt.cloneNode(true));
    } else {
      micSelect.appendChild(opt.cloneNode(true));
    }
  });

  // Populate sessions from backend (best-effort)
  const jwt = await ipcRenderer.invoke('get-stored-jwt');
  try {
    const res = await fetch(`${settings.apiBaseUrl}/sessions`, {
      headers: jwt ? { Authorization: `Bearer ${jwt}` } : {},
    });
    if (res.ok) {
      const items = await res.json();
      sessionSelect.innerHTML = '';
      if (items.length === 0) {
        sessionSelect.innerHTML = '<option value="">No sessions yet — create one below</option>';
      } else {
        items.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s.id;
          opt.textContent = `#${s.id.slice(0,8)} — ${s.status + ' (' + new Date(s.created_at).toLocaleDateString() + ')'}`;
          sessionSelect.appendChild(opt);
        });
      }
    }
  } catch (_) {
    sessionSelect.innerHTML = '<option value="">Unable to load sessions</option>';
  }

  sessionModal.classList.remove('hidden');
}

startSessionBtn.addEventListener('click', () => {
  const sessionId = sessionSelect.value;
  const micDeviceId = micSelect.value ? parseInt(micSelect.value, 10) : null;
  const loopbackDeviceId = loopbackSelect.value ? parseInt(loopbackSelect.value, 10) : null;

  if (!sessionId) return;

  ipcRenderer.send('start-session', { sessionId, micDeviceId, loopbackDeviceId });
  sessionModal.classList.add('hidden');
  setStatus('connecting');
});

newSessionBtn.addEventListener('click', async () => {
  const jwt = await ipcRenderer.invoke('get-stored-jwt');
  if (!jwt) return;
  try {
    newSessionBtn.disabled = true;
    newSessionBtn.textContent = 'Creating…';
    const res = await fetch(`${settings.apiBaseUrl}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${jwt}` },
      body: JSON.stringify({}),
    });
    if (res.ok) {
      const session = await res.json();
      const opt = document.createElement('option');
      opt.value = session.id;
      opt.textContent = `#${session.id.slice(0,8)} — New Session`;
      sessionSelect.innerHTML = '';
      sessionSelect.appendChild(opt);
    } else {
      alert('Failed to create session. Try again.');
    }
  } catch (err) {
    alert('Network error creating session.');
  } finally {
    newSessionBtn.disabled = false;
    newSessionBtn.textContent = '+ New session';
  }
});

// ─── Boot ──────────────────────────────────────────────────────────────────────
(async () => {
  const storedSession = await ipcRenderer.invoke('get-stored-session');
  if (storedSession) {
    // Auto-start last session
    ipcRenderer.send('start-session', { sessionId: storedSession, micDeviceId: null, loopbackDeviceId: null });
    setStatus('connecting');
  } else {
    await initSessionModal();
  }
})();
