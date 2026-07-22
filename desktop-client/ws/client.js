'use strict';

/**
 * WebSocket client — connects to the backend session endpoint,
 * streams binary audio frames, and forwards server messages to the
 * Electron main process (via callback).
 *
 * Reconnect policy: exponential backoff up to maxDelayMs (60 s).
 * Server messages handled:
 *   { type: "status", ... }
 *   { type: "transcript", speaker, text }
 *   { type: "answer_token", token }
 *   { type: "answer_done" }
 *   { type: "error", message }
 */

const WebSocket = require('ws');
const settings = require('../config/settings');

class WSClient {
  /**
   * @param {object} opts
   * @param {string} opts.sessionId
   * @param {string} opts.jwt
   * @param {function(object): void} opts.onMessage  — called with parsed server message
   * @param {function(string): void} opts.onStatus   — 'connecting'|'connected'|'disconnected'
   */
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
    return `${settings.backendWsUrl}/ws/session/${this._sessionId}`;
  }

  _connect() {
    if (this._destroyed) return;

    this._onStatus('connecting');

    const ws = new WebSocket(this._url(), {
      headers: { Authorization: `Bearer ${this._jwt}` },
    });

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
      // 'close' will follow; reconnect is handled there
    });
  }

  _scheduleReconnect() {
    const delay = this._reconnectDelay;
    const { maxDelayMs, multiplier } = settings.reconnect;
    this._reconnectDelay = Math.min(delay * multiplier, maxDelayMs);

    console.log(`[WSClient] Reconnecting in ${delay}ms…`);
    this._reconnectTimer = setTimeout(() => this._connect(), delay);
  }

  /**
   * Send a 16kHz mono PCM audio frame.
   * @param {'candidate'|'interviewer'} speaker
   * @param {Buffer} pcmBuffer
   */
  sendAudioFrame(speaker, pcmBuffer) {
    if (!this._ws || this._ws.readyState !== WebSocket.OPEN) return;

    const msg = JSON.stringify({
      type: 'audio_frame',
      speaker,
      data: pcmBuffer.toString('base64'),
    });

    this._ws.send(msg);
  }

  /**
   * Send an arbitrary JSON control message.
   * @param {object} payload
   */
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
