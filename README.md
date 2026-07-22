# Interview Platform — Product & Architecture Overview

## Database Setup & Migrations

### Prerequisites
- PostgreSQL 16 running locally
- Python 3.11+ with dependencies installed

```bash
pip install -r backend/requirements.txt
```

### Environment

Create a `.env` file at the project root (or export variables):

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/interview_platform
```

### Run Migrations

```bash
# From the project root:
alembic upgrade head
```

To roll back:

```bash
alembic downgrade base
```

To generate a new migration after changing models:

```bash
alembic revision --autogenerate -m "describe your change"
```

### Seed Local Database

After running migrations, populate with sample data:

```bash
python -m backend.seeds.seed
```

This creates:
- User: `dev@example.com` (subscription: pro)
- Candidate profile with skills and target role
- Interviewer profile (Jane Smith @ Acme Corp, behavioral style)
- One completed interview session with turns and an analysis report

### Run Schema Tests

```bash
pytest backend/tests/test_schemas.py -v
```

---

## Vision

A cloud-based, real-time interview intelligence platform that helps candidates
perform their best during live interviews. The client app is lightweight (audio
capture + overlay display only). All AI processing runs in the cloud, making it
accessible to any laptop user with no technical setup required.

---

## Problem We Solve

- Candidates blank out under pressure — they know the answer but can't articulate it live
- Generic interview prep doesn't adapt to the specific company, role, or recruiter
- No tool today captures the full interview for structured post-session coaching

---

## How It Works

```
┌──────────────────────────────────────────────────────────┐
│                  WEB DASHBOARD                           │
│  Upload resume · Set interviewer profile · Attach files  │
│  View past sessions · Read analysis reports              │
└─────────────────────┬────────────────────────────────────┘
                      │ HTTPS / WebSocket
┌─────────────────────▼────────────────────────────────────┐
│              DESKTOP CLIENT (Windows / Mac)              │
│  Captures mic + system audio (loopback)                  │
│  Streams audio to cloud · Displays answer overlay        │
│  No GPU required · Any modern laptop                     │
└─────────────────────┬────────────────────────────────────┘
                      │ WebSocket (audio stream / token stream)
┌─────────────────────▼────────────────────────────────────┐
│                  CLOUD BACKEND (FastAPI)                  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │          SESSION ORCHESTRATOR AGENT             │    │
│  │  Coordinates all agents for a live session      │    │
│  └──┬──────────────┬──────────────────┬────────────┘    │
│     │              │                  │                  │
│  ┌──▼───┐    ┌─────▼──────┐    ┌─────▼──────┐          │
│  │ STT  │    │  CONTEXT   │    │  REAL-TIME │          │
│  │AGENT │    │  BUILDER   │    │   ANSWER   │          │
│  │      │    │   AGENT    │    │   AGENT    │          │
│  └──────┘    └────────────┘    └────────────┘          │
│                                                          │
│  ┌───────────────────┐   ┌──────────────────────────┐  │
│  │  PROFILE INGESTION│   │   POST-INTERVIEW ANALYSIS │  │
│  │      AGENT        │   │          AGENT            │  │
│  └───────────────────┘   └──────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │       INTERVIEWER INTELLIGENCE AGENT              │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Client (Desktop App)
| Component       | Technology                          |
|-----------------|-------------------------------------|
| UI framework    | Electron (cross-platform) or Tauri  |
| Audio capture   | PortAudio / WASAPI loopback (Win)   |
| Transport       | WebSocket (binary audio frames)     |
| Overlay display | HTML/CSS rendered in Electron       |

### Backend
| Component         | Technology                              |
|-------------------|-----------------------------------------|
| API framework     | FastAPI (Python)                        |
| Real-time comms   | WebSockets (native FastAPI support)     |
| STT               | Deepgram Streaming API                  |
| LLM               | OpenAI GPT-4o-mini (speed + cost)       |
| Analysis LLM      | GPT-4o or Claude Sonnet (deeper reasoning) |
| Database          | PostgreSQL (users, sessions, profiles)  |
| File storage      | AWS S3 (resumes, attachments)           |
| Auth              | JWT + refresh tokens                    |
| Payments          | Stripe subscriptions                    |
| Deployment        | AWS / Railway / Render                  |

### Web Dashboard
| Component   | Technology              |
|-------------|-------------------------|
| Frontend    | Next.js (React)         |
| Styling     | Tailwind CSS            |
| Auth UI     | NextAuth.js             |
| File upload | Presigned S3 URLs       |

---

## Data Model

```
User
├── id, email, name, subscription_tier, stripe_customer_id
│
├── CandidateProfile
│   ├── resume_url (S3)
│   ├── parsed_resume (JSON — extracted by Profile Ingestion Agent)
│   ├── target_role, target_salary
│   ├── skills[], weak_areas[]
│   └── custom_notes
│
├── InterviewerProfiles[]  (reusable across sessions)
│   ├── name, company, role
│   ├── interview_style (technical | behavioral | mixed | case)
│   ├── known_questions[]
│   └── notes
│
└── Sessions[]
    ├── candidate_profile_id
    ├── interviewer_profile_id
    ├── attached_files[] (job description, company research, etc.)
    ├── status (active | completed | analysing | analysed)
    ├── started_at, ended_at
    ├── Turns[]
    │   ├── speaker (Interviewer | Candidate)
    │   ├── text, timestamp, audio_url (optional)
    │   └── generated_answer (what the AI suggested)
    └── AnalysisReport
        ├── overall_score
        ├── category_scores (technical, behavioral, communication)
        ├── strengths[], weaknesses[]
        ├── interviewer_intent_summary
        ├── recommended_practice[]
        └── pdf_report_url
```

---

## Session Lifecycle

```
1. Pre-session (Web Dashboard)
   └── Candidate selects profile + interviewer profile + uploads files

2. Session Start (Desktop Client)
   └── Client connects via WebSocket → Orchestrator spins up session context

3. Live Session
   └── Audio streams → STT Agent → Orchestrator → Answer Agent → client overlay
   └── Every turn saved to database in real time

4. Session End
   └── Client disconnects → Orchestrator signals Analysis Agent
   └── Analysis Agent processes full transcript → generates report
   └── Report available in Web Dashboard within ~60 seconds
```

---

## Monetization

| Tier    | Price      | Sessions | Analysis Reports | Interviewer Profiles |
|---------|------------|----------|-----------------|----------------------|
| Free    | $0         | 3/month  | No              | 1                    |
| Pro     | $20/month  | Unlimited| Yes             | Unlimited            |
| Teams   | $50/month  | Unlimited| Yes + PDF export| Shared team library  |

Teams tier targets: coding bootcamps, universities, recruiting agencies.

---

## Build Agents

See the `/agents` folder for the full specification of each build agent.
Each file defines what to build, what files to own, dependencies, and
definition of done.

| File                          | Agent                  | Builds                                              |
|-------------------------------|------------------------|-----------------------------------------------------|
| `01-database-agent.md`        | Database Agent         | PostgreSQL schema, SQLAlchemy models, migrations    |
| `02-auth-payments-agent.md`   | Auth & Payments Agent  | JWT auth, Stripe subscriptions, tier enforcement    |
| `03-backend-api-agent.md`     | Backend API Agent      | FastAPI REST endpoints, WebSocket session handler   |
| `04-desktop-client-agent.md`  | Desktop Client Agent   | Electron app, audio capture, overlay UI             |
| `05-ai-integration-agent.md`  | AI Integration Agent   | Deepgram STT, GPT-4o-mini answers, analysis, resume parsing |
| `06-web-dashboard-agent.md`   | Web Dashboard Agent    | Next.js dashboard, profile editor, report viewer    |
| `07-devops-agent.md`          | DevOps Agent           | Docker, CI/CD, Railway/Vercel deploy, installers    |

### Recommended Build Order
```
01 Database ──► 02 Auth ──► 05 AI Integration ──► 03 Backend API
                                                         │
                                              ┌──────────┴──────────┐
                                         04 Desktop            06 Dashboard
                                              └──────────┬──────────┘
                                                    07 DevOps
```

---

## Competitive Edge

- **Fully personalized** — every answer adapts to the candidate's real resume AND the specific recruiter
- **Post-interview coaching** — the only tool that tells you how you actually did
- **Recruiter profiles reusable** — community-built library of known interviewers over time
- **Privacy first** — audio processed in real time, not stored by default (Pro opt-in)
- **No GPU, no setup** — install and go
