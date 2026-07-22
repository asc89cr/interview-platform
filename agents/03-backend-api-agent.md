# Build Agent 03 — Backend API Agent

## Mission
Build all REST API endpoints for managing profiles, sessions, files, and
reports. Also implements the WebSocket endpoint that the desktop client connects
to during a live session, orchestrating audio routing between agents.

---

## Run Order
**Depends on:** Database Agent (01), Auth Agent (02), AI Integration Agent (05)
**Must complete before:** Desktop Client Agent, Web Dashboard Agent

---

## Tech Stack
- FastAPI (async)
- WebSockets (native FastAPI)
- asyncio for concurrent audio/LLM streaming
- boto3 (S3 presigned URLs for file uploads)
- Redis (session state, reconnect support)

---

## Owns These Files
```
backend/
├── main.py                  # FastAPI app, routers, CORS, startup
├── routers/
│   ├── profiles.py          # Candidate + interviewer profile CRUD
│   ├── sessions.py          # Session create/list/get/end
│   ├── files.py             # File upload (presigned S3 URLs)
│   └── reports.py           # Fetch analysis report for a session
├── websocket/
│   ├── session_handler.py   # WebSocket endpoint + state machine
│   ├── audio_router.py      # Routes audio frames to STT
│   └── answer_router.py     # Routes transcribed turns to LLM, streams back
└── services/
    ├── s3.py                # Upload, presigned URL generation
    └── session_state.py     # Redis-backed session state
```

---

## REST Endpoints to Implement

### Candidate Profile
| Method | Path | Description |
|--------|------|-------------|
| GET | `/profile/candidate` | Get current user's candidate profile |
| PUT | `/profile/candidate` | Update profile fields |
| POST | `/profile/candidate/resume` | Get presigned S3 URL to upload resume PDF |

### Interviewer Profiles
| Method | Path | Description |
|--------|------|-------------|
| GET | `/profile/interviewers` | List all interviewer profiles for user |
| POST | `/profile/interviewers` | Create new interviewer profile |
| PUT | `/profile/interviewers/{id}` | Update interviewer profile |
| DELETE | `/profile/interviewers/{id}` | Delete interviewer profile |

### Sessions
| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions` | Create new session (links profiles, returns session_id) |
| GET | `/sessions` | List past sessions with status + scores |
| GET | `/sessions/{id}` | Get session detail + all turns |
| POST | `/sessions/{id}/files` | Attach file to session (presigned S3 URL) |
| DELETE | `/sessions/{id}` | Delete session and all related data |

### Reports
| Method | Path | Description |
|--------|------|-------------|
| GET | `/sessions/{id}/report` | Get analysis report (returns 404 if not ready) |
| GET | `/sessions/{id}/report/pdf` | Redirect to S3 PDF download URL |

---

## WebSocket Endpoint

```
WS /ws/session/{session_id}
```

### Lifecycle
1. Client connects → validate JWT from query param `?token=...`
2. Load session context from DB + Redis
3. Start audio routing loop (async):
   - Receive audio frames → forward to STT Agent
   - Receive transcribed Interviewer turns → forward to LLM Agent
   - Stream answer tokens back to client
4. Persist every turn to DB in real time
5. On disconnect → hold state in Redis 60s, allow reconnect
6. On `session_end` message → trigger Analysis Agent async task

### Message Protocol
See `README.md` WebSocket Protocol section.

---

## Deliverables
- [ ] All REST endpoints implemented with auth dependency
- [ ] WebSocket session handler with full state machine
- [ ] S3 presigned URL generation for resume + session file uploads
- [ ] Redis session state for reconnect support
- [ ] Background task trigger for Analysis Agent on session end
- [ ] Integration tests for all REST endpoints
- [ ] WebSocket integration test (mock STT + LLM)

---

## Definition of Done
All endpoints return correct responses with valid auth tokens.
WebSocket session can be started, receives audio, and streams back mocked answers.
