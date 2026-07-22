# Build Agent 04 — Desktop Client Agent

## Mission
Build the lightweight desktop application that candidates install and run during
interviews. It captures microphone and system audio (loopback), streams audio
to the cloud backend via WebSocket, and displays AI-generated answers in a
floating overlay — with zero local AI processing required.

---

## Run Order
**Depends on:** Backend API Agent (03) WebSocket contract being finalized
**Runs in parallel with:** Web Dashboard Agent (06)

---

## Tech Stack
- **Electron** (cross-platform: Windows + Mac)
- **Node.js** for main process (audio capture, WebSocket client)
- **naudiodon** or **node-portaudio** for cross-platform audio capture
- **WebSocket** (ws npm package) for cloud connection
- **HTML/CSS/JS** for overlay renderer process (no framework needed — keep it light)

> Windows note: WASAPI loopback for system audio capture.
> Mac note: requires BlackHole or similar virtual audio device for loopback.

---

## Owns These Files
```
desktop-client/
├── package.json
├── main.js                  # Electron main process
├── audio/
│   ├── capture.js           # Mic + loopback audio capture
│   └── vad.js               # Voice activity detection (silence detection)
├── ws/
│   └── client.js            # WebSocket connection to backend, reconnect logic
├── renderer/
│   ├── overlay.html         # Floating answer overlay
│   ├── overlay.css
│   ├── overlay.js           # Token rendering, spinner, transcript display
│   ├── login.html           # Login screen (on first launch)
│   └── login.js
├── config/
│   └── settings.js          # Backend URL, audio device preferences
└── assets/
    └── icon.png
```

---

## Features to Implement

### Audio Capture
- Detect and list available audio input devices on startup
- Capture **microphone** (candidate voice)
- Capture **system audio loopback** (interviewer voice via Zoom/Teams/Meet)
- Voice Activity Detection — only send frames when speech is detected
- Convert to 16kHz mono PCM before sending

### WebSocket Client
- Authenticate using JWT stored in local secure storage (keytar)
- Connect to `wss://api.domain.com/ws/session/{session_id}`
- Send binary audio frames tagged with speaker label
- Receive and handle all server message types (status, transcript, answer tokens)
- Auto-reconnect with exponential backoff (up to 60s hold on server)

### Overlay Window
- Always-on-top, borderless, semi-transparent floating window
- Sections: conversation transcript + AI suggested answer
- Animated spinner during "Analyzing / Generating" states
- Token-batched rendering (50ms flush) — smooth text flow
- Draggable by header bar
- Global hotkeys:
  - `F9` — toggle overlay visibility
  - `F10` — force generate answer now
  - `F8` — clear conversation

### Login Screen
- Email + password form on first launch
- Saves JWT + refresh token to OS secure storage (keytar)
- Session picker: choose from existing sessions or create new (deep links to web dashboard)

---

## Audio Frame Format Sent to Server
```json
{
  "type": "audio_frame",
  "speaker": "interviewer",
  "data": "<base64 encoded 16kHz mono PCM, 20ms chunk>"
}
```

---

## Deliverables
- [ ] Electron app boots and shows login on first run
- [ ] Audio device picker on setup screen
- [ ] Mic + loopback capture working on Windows
- [ ] Mac loopback capture with BlackHole instructions in README
- [ ] WebSocket connects, authenticates, streams audio
- [ ] Overlay renders transcript + streaming answer tokens
- [ ] Auto-reconnect on network drop
- [ ] Global hotkeys registered
- [ ] App signed and packaged: `.exe` installer (Windows), `.dmg` (Mac)
- [ ] Auto-updater configured (electron-updater)

---

## Definition of Done
On Windows: install app, log in, start a session, speak into mic while playing
audio through headset — transcript appears and AI answer streams into overlay
within 2 seconds of speech ending.
