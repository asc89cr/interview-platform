'use strict';

const { ipcRenderer } = require('electron');
const settings = require('../config/settings');

const form = document.getElementById('loginForm');
const emailEl = document.getElementById('email');
const passwordEl = document.getElementById('password');
const errorMsg = document.getElementById('errorMsg');
const submitBtn = document.getElementById('submitBtn');
const btnLabel = document.getElementById('btnLabel');
const spinner = document.getElementById('spinner');

// Deep links
document.getElementById('dashboardLink').addEventListener('click', () => {
  ipcRenderer.send('open-dashboard', '/');
});
document.getElementById('forgotLink').addEventListener('click', () => {
  ipcRenderer.send('open-dashboard', '/auth/forgot-password');
});

function setLoading(loading) {
  submitBtn.disabled = loading;
  btnLabel.style.display = loading ? 'none' : 'inline';
  spinner.style.display = loading ? 'block' : 'none';
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.style.display = 'block';
}

function clearError() {
  errorMsg.style.display = 'none';
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearError();
  setLoading(true);

  const email = emailEl.value.trim();
  const password = passwordEl.value;

  try {
    const res = await fetch(`${settings.apiBaseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const body = await res.json();

    if (!res.ok) {
      showError(body.detail || 'Invalid credentials');
      setLoading(false);
      return;
    }

    const { access_token, refresh_token } = body;

    // Ask main process to store credentials and open overlay
    ipcRenderer.send('login-success', {
      jwt: access_token,
      refreshToken: refresh_token,
      sessionId: null,
    });
  } catch (err) {
    showError('Network error — check your connection');
    setLoading(false);
  }
});
