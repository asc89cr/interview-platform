'use strict';

/**
 * Electron main process.
 *
 * Responsibilities:
 *  - Create login window (first run) or overlay window (authenticated)
 *  - Manage audio capture pipeline: AudioCapture → VAD → WSClient
 *  - Register global hotkeys (F8 / F9 / F10)
 *  - Handle IPC from renderer processes
 */

const {
  app,
  BrowserWindow,
  globalShortcut,
  ipcMain,
  screen,
  shell,
} = require('electron');
const path = require('path');
const keytar = require('keytar');
const AudioCapture = require('./audio/capture');
const VAD = require('./audio/vad');
const WSClient = require('./ws/client');
const settings = require('./config/settings');

const KEYTAR_SERVICE = 'InterviewPlatformClient';
const KEYTAR_ACCOUNT_JWT = 'jwt';
const KEYTAR_ACCOUNT_REFRESH = 'refresh_token';
const KEYTAR_ACCOUNT_SESSION = 'session_id';

let loginWin = null;
let overlayWin = null;
let wsClient = null;
let audioCapture = null;
let vad = null;

// ─── Window helpers ────────────────────────────────────────────────────────────

function createLoginWindow() {
  loginWin = new BrowserWindow({
    width: 420,
    height: 540,
    resizable: false,
    center: true,
    autoHideMenuBar: true,
    title: 'Interview Platform — Sign In',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  loginWin.loadFile(path.join(__dirname, 'renderer', 'login.html'));
  loginWin.on('closed', () => { loginWin = null; });
}

function createOverlayWindow() {
  const { width, height, opacity } = settings.overlay;
  const display = screen.getPrimaryDisplay();
  const x = settings.overlay.x ?? display.workAreaSize.width - width - 20;
  const y = settings.overlay.y ?? 60;

  overlayWin = new BrowserWindow({
    width,
    height,
    x,
    y,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    hasShadow: false,
    opacity,
    title: 'Interview Overlay',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  overlayWin.loadFile(path.join(__dirname, 'renderer', 'overlay.html'));
  overlayWin.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  overlayWin.on('closed', () => { overlayWin = null; });
}

// ─── Global hotkeys ────────────────────────────────────────────────────────────

function registerHotkeys() {
  // F9 — toggle overlay visibility
  globalShortcut.register('F9', () => {
    if (!overlayWin) return;
    if (overlayWin.isVisible()) overlayWin.hide();
    else overlayWin.show();
  });

  // F10 — force generate answer now
  globalShortcut.register('F10', () => {
    if (wsClient) wsClient.sendControl({ type: 'force_answer' });
    if (overlayWin) overlayWin.webContents.send('force-answer');
  });

  // F8 — clear conversation
  globalShortcut.register('F8', () => {
    if (wsClient) wsClient.sendControl({ type: 'clear_conversation' });
    if (overlayWin) overlayWin.webContents.send('clear-conversation');
  });
}

// ─── Audio pipeline ────────────────────────────────────────────────────────────

function startAudioPipeline(micDeviceId, loopbackDeviceId) {
  audioCapture = new AudioCapture();

  audioCapture.on('error', ({ speaker, err }) => {
    console.error(`[Audio] Capture error (${speaker}):`, err.message);
    if (overlayWin) overlayWin.webContents.send('audio-error', { speaker, message: err.message });
  });

  vad = new VAD(audioCapture, ({ speaker, data }) => {
    if (wsClient) wsClient.sendAudioFrame(speaker, data);
  });

  audioCapture.start({ micDeviceId, loopbackDeviceId });
}

function stopAudioPipeline() {
  if (audioCapture) {
    audioCapture.stop();
    audioCapture = null;
    vad = null;
  }
}

// ─── WebSocket session ─────────────────────────────────────────────────────────

function startSession(jwt, sessionId, micDeviceId, loopbackDeviceId) {
  wsClient = new WSClient({
    sessionId,
    jwt,
    onMessage: (msg) => {
      if (overlayWin) overlayWin.webContents.send('ws-message', msg);
    },
    onStatus: (status) => {
      console.log(`[WS] Status: ${status}`);
      if (overlayWin) overlayWin.webContents.send('ws-status', status);
    },
  });

  startAudioPipeline(micDeviceId, loopbackDeviceId);
}

function endSession() {
  stopAudioPipeline();
  if (wsClient) {
    wsClient.destroy();
    wsClient = null;
  }
}

// ─── IPC handlers ──────────────────────────────────────────────────────────────

// Renderer → main: login succeeded, save credentials and open overlay
ipcMain.on('login-success', async (_event, { jwt, refreshToken, sessionId }) => {
  await keytar.setPassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_JWT, jwt);
  await keytar.setPassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_REFRESH, refreshToken);
  if (sessionId) {
    await keytar.setPassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_SESSION, sessionId);
  }

  if (loginWin) { loginWin.close(); loginWin = null; }
  createOverlayWindow();
});

// Renderer → main: start session (from overlay session picker or login)
ipcMain.on('start-session', async (_event, { sessionId, micDeviceId, loopbackDeviceId }) => {
  const jwt = await keytar.getPassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_JWT);
  if (!jwt) return;
  endSession();
  startSession(jwt, sessionId, micDeviceId ?? null, loopbackDeviceId ?? null);
});

// Renderer → main: end session
ipcMain.on('end-session', () => endSession());

// Renderer → main: open web dashboard (deep link)
ipcMain.on('open-dashboard', (_event, relPath = '') => {
  shell.openExternal(`https://app.interviewplatform.com${relPath}`);
});

// Renderer asks for audio device list
ipcMain.handle('list-audio-devices', () => {
  try {
    return require('./audio/capture').listDevices();
  } catch (err) {
    console.warn('[Audio] Could not enumerate devices:', err.message);
    return [];
  }
});

// Renderer asks for stored session id
ipcMain.handle('get-stored-session', async () => {
  return keytar.getPassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_SESSION);
});

// Renderer asks for stored JWT (for API calls from renderer)
ipcMain.handle('get-stored-jwt', async () => {
  return keytar.getPassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_JWT);
});

// Renderer signs out
ipcMain.on('logout', async () => {
  endSession();
  await keytar.deletePassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_JWT);
  await keytar.deletePassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_REFRESH);
  await keytar.deletePassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_SESSION);
  if (overlayWin) { overlayWin.close(); overlayWin = null; }
  createLoginWindow();
});

// ─── App lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  const jwt = await keytar.getPassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_JWT);

  if (jwt) {
    createOverlayWindow();
  } else {
    createLoginWindow();
  }

  registerHotkeys();
});

app.on('window-all-closed', () => {
  endSession();
  globalShortcut.unregisterAll();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', async () => {
  if (!loginWin && !overlayWin) {
    const jwt = await keytar.getPassword(KEYTAR_SERVICE, KEYTAR_ACCOUNT_JWT);
    if (jwt) createOverlayWindow();
    else createLoginWindow();
  }
});
