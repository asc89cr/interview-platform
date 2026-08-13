'use strict';

/**
 * Renderer-side system-audio loopback capture (interviewer voice).
 *
 * Uses Electron's getDisplayMedia with audio: 'loopback' (granted in main.js)
 * to capture whatever plays to the active output device — i.e. the remote
 * interviewer's voice coming through the user's headset earpiece.
 *
 * Audio is downsampled to 16 kHz mono PCM16 and forwarded to the main process
 * (channel 'interviewer-audio'), which relays it to the backend WebSocket.
 *
 * Loaded as a plain <script> alongside overlay.js, so it runs inside an IIFE to
 * avoid clashing with overlay.js's top-level declarations (e.g. ipcRenderer).
 */

(function () {
const { ipcRenderer } = require('electron');

const TARGET_RATE = 16000;

let _ctx = null;
let _stream = null;
let _processor = null;
let _source = null;

function _floatToPCM16Downsampled(float32, inRate) {
  if (inRate === TARGET_RATE) {
    const out = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      const s = Math.max(-1, Math.min(1, float32[i]));
      out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return out;
  }
  const ratio = inRate / TARGET_RATE;
  const outLen = Math.floor(float32.length / ratio);
  const out = new Int16Array(outLen);
  for (let i = 0; i < outLen; i++) {
    const s = Math.max(-1, Math.min(1, float32[Math.floor(i * ratio)]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out;
}

function _rms(float32) {
  let sum = 0;
  for (let i = 0; i < float32.length; i++) sum += float32[i] * float32[i];
  return Math.sqrt(sum / float32.length);
}

async function startLoopbackCapture() {
  if (_ctx) return; // already running
  ipcRenderer.send('loopback-log', 'startLoopbackCapture called');
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: true,
      audio: true,
    });

    // We only want the audio track — stop and drop video immediately.
    stream.getVideoTracks().forEach((t) => t.stop());
    const audioTracks = stream.getAudioTracks();
    if (audioTracks.length === 0) {
      console.error('[Loopback] No system audio track — is loopback granted?');
      ipcRenderer.send('loopback-log', 'ERROR: no audio track (loopback not granted)');
      return;
    }
    _stream = new MediaStream([audioTracks[0]]);

    _ctx = new AudioContext();
    _source = _ctx.createMediaStreamSource(_stream);
    _processor = _ctx.createScriptProcessor(4096, 1, 1);

    let _blocks = 0;
    let _maxRms = 0;
    let _sent = 0;
    _processor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0);
      const r = _rms(input);
      _blocks++;
      if (r > _maxRms) _maxRms = r;
      if (_blocks % 40 === 0) {
        ipcRenderer.send('loopback-log', `blocks=${_blocks} maxRms=${_maxRms.toFixed(4)} sent=${_sent}`);
        _maxRms = 0;
      }
      // Stream continuously (including silence). Deepgram needs a live audio
      // timeline to detect end-of-utterance (endpointing/UtteranceEnd) and
      // finalize the last words — gating silence stalls the timeline and no
      // transcript is ever emitted.
      const pcm = _floatToPCM16Downsampled(input, _ctx.sampleRate);
      _sent++;
      // Transfer the underlying ArrayBuffer to main
      ipcRenderer.send('interviewer-audio', pcm.buffer);
    };

    // Route through a muted gain node so the ScriptProcessor fires without
    // playing the captured audio back out (which would cause a feedback loop).
    const mute = _ctx.createGain();
    mute.gain.value = 0;
    _source.connect(_processor);
    _processor.connect(mute);
    mute.connect(_ctx.destination);

    console.log(`[Loopback] Capturing interviewer audio @ ${_ctx.sampleRate}Hz → ${TARGET_RATE}Hz`);
    ipcRenderer.send('loopback-log', `capturing @ ${_ctx.sampleRate}Hz, track=${audioTracks[0].label || 'unlabeled'}`);
  } catch (err) {
    console.error('[Loopback] getDisplayMedia failed:', err.message);
    ipcRenderer.send('loopback-log', `ERROR getDisplayMedia: ${err.message}`);
  }
}

function stopLoopbackCapture() {
  if (_processor) { _processor.disconnect(); _processor.onaudioprocess = null; _processor = null; }
  if (_source) { _source.disconnect(); _source = null; }
  if (_ctx) { _ctx.close().catch(() => {}); _ctx = null; }
  if (_stream) { _stream.getTracks().forEach((t) => t.stop()); _stream = null; }
  console.log('[Loopback] Stopped');
}

ipcRenderer.on('start-loopback-capture', startLoopbackCapture);
ipcRenderer.on('stop-loopback-capture', stopLoopbackCapture);

window.__loopback = { startLoopbackCapture, stopLoopbackCapture };
})();
