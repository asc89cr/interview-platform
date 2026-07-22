'use strict';

const settings = {
  // HTTP REST backend — override with INTERVIEW_PLATFORM_HTTP env var (no trailing slash)
  apiBaseUrl: process.env.INTERVIEW_PLATFORM_HTTP || 'https://api.interviewplatform.com',

  // WebSocket backend — override with INTERVIEW_PLATFORM_API env var
  backendWsUrl: process.env.INTERVIEW_PLATFORM_API || 'wss://api.interviewplatform.com',

  // Audio capture defaults
  audio: {
    sampleRate: 16000,      // 16 kHz required by STT agent
    channels: 1,            // mono
    bitDepth: 16,
    chunkMs: 20,            // 20 ms frames
    micDeviceId: null,      // null = system default mic
    loopbackDeviceId: null, // null = system default loopback (WASAPI on Windows)
  },

  // VAD thresholds
  vad: {
    silenceThresholdRms: 200,   // RMS below this is considered silence
    silenceHoldMs: 800,         // ms of silence before we stop sending
    speechHoldMs: 100,          // ms of speech before we start sending
  },

  // WebSocket reconnect policy
  reconnect: {
    initialDelayMs: 1000,
    maxDelayMs: 60000,
    multiplier: 2,
  },

  // Overlay window geometry defaults
  overlay: {
    width: 480,
    height: 340,
    x: null,  // null = centered
    y: null,
    opacity: 0.92,
  },
};

module.exports = settings;
