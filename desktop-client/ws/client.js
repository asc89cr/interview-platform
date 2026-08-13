'use strict';

const WebSocket = require('ws');
const settings = require('../config/settings');

class WSClient {
  constructor({ sessionId, jwt, onMessage, onStatus }) {
    this._sessionId = sessionId;
    this._jwt = jwt;
    this._onMessage = onMessage;
    this._onStatus = onStatus;

    this._ws = null;
    this._destroyed = false;
    this._reconnectDelay = settings.reconnect.initialDelayMs;
    this._reconnectTimer = null;

    this._connect();
  }

  _url() {
    const token = encodeURIComponent(this._jwt);
    return `${settings.backendWsUrl}/ws/session/${this._sessionId}?token=${token}`;
  }

  _connect() {
    if (this._destroyed) return;

    this._onStatus('connecting');

    const ws = new WebSocket(this._url());

    ws.on('open', () => {
      this._ws = ws;
      this._reconnectDelay = settings.reconnect.initialDelayMs;
      this._onStatus('connected');
    });

    ws.on('message', (data) => {
      try {
        const msg = JSON.parse(data);
        this._onMessage(msg);
      } catch (err) {
        console.error('[WSClient] Failed to parse message:', err);
      }
    });

    ws.on('close', () => {
      this._ws = null;
      if (!this._destroyed) {
        this._onStatus('disconnected');
        this._scheduleReconnect();
      }
    });

    ws.on('error', (err) => {
      console.error('[WSClient] WebSocket error:', err.message);
    });
  }

  _scheduleReconnect() {
    const delay = this._reconnectDelay;
    const { maxDelayMs, multiplier } = settings.reconnect;
    this._reconnectDelay = Math.min(delay * multiplier, maxDelayMs);

    console.log(`[WSClient] Reconnecting in ${delay}ms...`);
    this._reconnectTimer = setTimeout(() => this._connect(), delay);
  }

  // Mic = candidate (no auto-answer), loopback = interviewer (auto-answer).
  // If only mic is available, user triggers answers manually via ⚡ button.
  sendAudioFrame(speaker, pcmBuffer) {
    if (!this._ws || this._ws.readyState !== WebSocket.OPEN) return;
    const prefix = Buffer.alloc(1);
    prefix[0] = speaker === 'interviewer' ? 0x00 : 0x01;
    this._ws.send(Buffer.concat([prefix, pcmBuffer]));
  }

  sendControl(payload) {
    if (!this._ws || this._ws.readyState !== WebSocket.OPEN) return;
    this._ws.send(JSON.stringify(payload));
  }

  destroy() {
    this._destroyed = true;
    clearTimeout(this._reconnectTimer);
    if (this._ws) {
      this._ws.terminate();
      this._ws = null;
    }
  }
}

module.exports = WSClient;