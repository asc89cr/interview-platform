'use strict';

/**
 * Voice Activity Detection (VAD) — energy-based silence gate.
 *
 * Wraps an AudioCapture instance. Only forwards frames to the callback
 * when speech is detected, based on RMS energy threshold.
 *
 * State machine:
 *   SILENCE → SPEECH (when RMS > threshold for speechHoldMs)
 *   SPEECH → SILENCE (when RMS < threshold for silenceHoldMs)
 */

const settings = require('../config/settings');

class VAD {
  /**
   * @param {import('./capture').AudioCapture} capture
   * @param {function({ speaker: string, data: Buffer }): void} onSpeechFrame
   */
  constructor(capture, onSpeechFrame) {
    this._capture = capture;
    this._onSpeechFrame = onSpeechFrame;

    // Per-speaker state
    this._state = {};

    this._capture.on('frame', ({ speaker, data }) => {
      this._process(speaker, data);
    });
  }

  _getState(speaker) {
    if (!this._state[speaker]) {
      this._state[speaker] = {
        isSpeech: false,
        speechStartedAt: null,
        silenceStartedAt: null,
      };
    }
    return this._state[speaker];
  }

  _process(speaker, data) {
    const rms = this._rms(data);
    const now = Date.now();
    const { silenceThresholdRms, silenceHoldMs, speechHoldMs } = settings.vad;
    const state = this._getState(speaker);

    if (rms >= silenceThresholdRms) {
      // Energy detected
      state.silenceStartedAt = null;
      if (!state.isSpeech) {
        if (!state.speechStartedAt) state.speechStartedAt = now;
        if (now - state.speechStartedAt >= speechHoldMs) {
          state.isSpeech = true;
        }
      }
    } else {
      // Silence
      state.speechStartedAt = null;
      if (state.isSpeech) {
        if (!state.silenceStartedAt) state.silenceStartedAt = now;
        if (now - state.silenceStartedAt >= silenceHoldMs) {
          state.isSpeech = false;
          state.silenceStartedAt = null;
        }
      }
    }

    if (state.isSpeech) {
      this._onSpeechFrame({ speaker, data });
    }
  }

  /** Compute RMS energy of a 16-bit PCM buffer. */
  _rms(buffer) {
    let sum = 0;
    const samples = buffer.length / 2; // 16-bit = 2 bytes/sample
    for (let i = 0; i < buffer.length; i += 2) {
      const sample = buffer.readInt16LE(i);
      sum += sample * sample;
    }
    return Math.sqrt(sum / samples);
  }
}

module.exports = VAD;
