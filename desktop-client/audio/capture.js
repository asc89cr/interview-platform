'use strict';

/**
 * Audio capture module.
 *
 * Uses naudiodon (PortAudio bindings) for cross-platform mic capture.
 * On Windows, WASAPI loopback devices appear in the device list with
 * names containing "Loopback" — we auto-detect if no explicit deviceId is set.
 *
 * Emits Buffer objects (raw 16-bit signed PCM, 16 kHz, mono).
 */

const { EventEmitter } = require('events');
const settings = require('../config/settings');

// Lazy-loaded — avoids PortAudio crash on startup when no session is active
let portAudio = null;
function getPortAudio() {
  if (!portAudio) portAudio = require('naudiodon');
  return portAudio;
}

class AudioCapture extends EventEmitter {
  constructor() {
    super();
    this._micStream = null;
    this._loopbackStream = null;
    this._running = false;
  }

  /**
   * Returns a list of available audio devices.
   * @returns {Array<{id: number, name: string, maxInputChannels: number}>}
   */
  static listDevices() {
    return getPortAudio().getDevices().filter(d => d.maxInputChannels > 0);
  }

  /**
   * Finds the best loopback device on Windows (WASAPI loopback).
   * Returns null if none found.
   */
  static findLoopbackDevice() {
    const devices = getPortAudio().getDevices();
    const loopback = devices.find(
      d => d.maxInputChannels > 0 && /loopback|stereo mix|what u hear|wave out/i.test(d.name)
    );
    return loopback ? loopback.id : null;
  }

  /**
   * Start capturing audio from mic and (optionally) loopback.
   * @param {object} opts
   * @param {number|null} opts.micDeviceId
   * @param {number|null} opts.loopbackDeviceId
   */
  start({ micDeviceId = null, loopbackDeviceId = null, useLoopback = true } = {}) {
    if (this._running) return;
    this._running = true;

    const { sampleRate, channels, bitDepth } = settings.audio;

    this._micStream = this._openStream(micDeviceId, sampleRate, channels, bitDepth, 'candidate');

    if (useLoopback) {
      const resolvedLoopback = loopbackDeviceId ?? AudioCapture.findLoopbackDevice();
      if (resolvedLoopback !== null) {
        this._loopbackStream = this._openLoopbackStream(resolvedLoopback, sampleRate, channels, bitDepth);
      }
    }
  }

  stop() {
    this._running = false;
    if (this._micStream) {
      try { this._micStream.quit(); } catch (_) {}
      this._micStream = null;
    }
    if (this._loopbackStream) {
      try { this._loopbackStream.quit(); } catch (_) {}
      this._loopbackStream = null;
    }
  }

  _openLoopbackStream(deviceId, targetRate, channels, bitDepth) {
    const pa = getPortAudio();
    const nativeRates = [targetRate, 48000, 44100];

    for (const rate of nativeRates) {
      try {
        const options = {
          channelCount: channels,
          sampleFormat: bitDepth === 16 ? pa.SampleFormat16Bit : pa.SampleFormat32BitFloat,
          sampleRate: rate,
          deviceId: deviceId ?? -1,
          closeOnError: false,
        };

        const stream = new pa.AudioIO({ inOptions: options });
        const needsResample = rate !== targetRate;
        const ratio = rate / targetRate; // e.g. 44100/16000 ≈ 2.756

        stream.on('data', (chunk) => {
          const pcm = needsResample ? this._downsample(chunk, ratio) : chunk;
          this.emit('frame', { speaker: 'interviewer', data: pcm });
        });

        stream.on('error', (err) => {
          this.emit('error', { speaker: 'interviewer', err });
        });

        stream.start();
        console.log(`[Audio] Loopback opened at ${rate}Hz (device ${deviceId})${needsResample ? `, resampling → ${targetRate}Hz` : ''}`);
        return stream;
      } catch (err) {
        console.warn(`[Audio] Loopback @ ${rate}Hz failed: ${err.message}`);
      }
    }

    console.error('[Audio] Could not open loopback device at any supported sample rate');
    return null;
  }

  /** Linear downsample 16-bit PCM by a given ratio. */
  _downsample(buffer, ratio) {
    const inputSamples = buffer.length / 2;
    const outputSamples = Math.floor(inputSamples / ratio);
    const out = Buffer.alloc(outputSamples * 2);
    for (let i = 0; i < outputSamples; i++) {
      const srcIdx = Math.floor(i * ratio) * 2;
      out.writeInt16LE(buffer.readInt16LE(srcIdx), i * 2);
    }
    return out;
  }

  _openStream(deviceId, sampleRate, channels, bitDepth, speaker) {
    const pa = getPortAudio();
    const options = {
      channelCount: channels,
      sampleFormat: bitDepth === 16 ? pa.SampleFormat16Bit : pa.SampleFormat32BitFloat,
      sampleRate,
      deviceId: deviceId ?? -1,
      closeOnError: false,
    };

    const stream = new pa.AudioIO({ inOptions: options });

    stream.on('data', (chunk) => {
      this.emit('frame', { speaker, data: chunk });
    });

    stream.on('error', (err) => {
      this.emit('error', { speaker, err });
    });

    stream.start();
    return stream;
  }
}

module.exports = AudioCapture;
