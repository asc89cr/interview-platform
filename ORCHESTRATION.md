# Orchestration Guide — How to Run the Build Team

## The Golden Rule
> **No agent starts until every agent it depends on is Done.**
> "Done" means the Definition of Done in that agent's file is fully met —
> not just "mostly working."

---

## Build Phases

```
PHASE 1 ──────────────────────────────────────── (1 agent, ~1 day)
  [01] Database Agent
       No dependencies. Starts immediately.
       Delivers: schema, models, migrations, Pydantic schemas.

PHASE 2 ──────────────────────────────────────── (1 agent, ~1 day)
  [02] Auth & Payments Agent
       Starts when: Phase 1 done.
       Delivers: JWT auth, Stripe billing, tier enforcement.

PHASE 3 ──────────────────────────────────────── (2 agents in PARALLEL, ~2 days)
  [05] AI Integration Agent          [07] DevOps Agent (infra only)
       Starts when: Phase 2 done.         Starts when: Phase 1 done.
       Delivers: Deepgram, GPT,           Delivers: Docker, S3, DB hosted,
       analysis, resume parser.           Redis, env vars, CI skeletons.

PHASE 4 ──────────────────────────────────────── (1 agent, ~2 days)
  [03] Backend API Agent
       Starts when: Phase 2 + Phase 3 both done.
       Delivers: all REST endpoints + WebSocket session handler.

PHASE 5 ──────────────────────────────────────── (2 agents in PARALLEL, ~3 days)
  [04] Desktop Client Agent          [06] Web Dashboard Agent
       Starts when: Phase 4 done.         Starts when: Phase 4 done.
       Delivers: Electron app,            Delivers: Next.js dashboard,
       audio capture, overlay.            profile editor, reports.

PHASE 6 ──────────────────────────────────────── (1 agent, ~1 day)
  [07] DevOps Agent (final deployment)
       Starts when: Phase 5 done.
       Delivers: full CI/CD, deploy to Railway + Vercel, installers.
```

---

## Visual Timeline

```
Day  1   2   3   4   5   6   7   8   9  10
     │───────────────────────────────────────
[01] ████░
[02]     ████░
[05]         ████████░
[07-infra]   ████░
[03]                 ████████░
[04]                         ████████████░
[06]                         ████████████░
[07-deploy]                              ████░
     │───────────────────────────────────────
                                         SHIP
```

---

## How to Run Each Agent (Practical Steps)

Each agent file is a **prompt spec**. Hand it to an AI coding agent
(GitHub Copilot, Cursor, Claude, etc.) with this instruction:

```
You are a senior software engineer.
Read the agent spec below and implement everything described.
Follow the tech stack listed. Create all files in the "Owns" section.
Meet every item in the Deliverables checklist.
Do not move on until the Definition of Done is met.

[paste agent .md file here]
[paste README.md for overall context]
```

---

## Handoff Checklist Between Phases

Before starting the next phase, verify the previous agent delivered:

### Phase 1 → Phase 2
- [ ] `alembic upgrade head` runs clean on fresh PostgreSQL
- [ ] All models importable with no errors
- [ ] Pydantic schemas exist for all entities

### Phase 2 → Phase 3
- [ ] `POST /auth/register` returns JWT tokens
- [ ] `GET /protected` rejects request without valid token
- [ ] Stripe webhook updates subscription_tier in DB

### Phase 3 → Phase 4
- [ ] Deepgram streaming returns transcribed text from test audio
- [ ] `stream_answer()` yields tokens for a test question
- [ ] `analyze_session()` returns AnalysisReport from mock transcript
- [ ] Docker + S3 + Redis running locally

### Phase 4 → Phase 5
- [ ] All REST endpoints return correct responses with auth
- [ ] WebSocket connects and streams back mock answer tokens
- [ ] Session turns are persisted to DB during WebSocket session

### Phase 5 → Phase 6
- [ ] Desktop app captures audio and streams to backend
- [ ] Answer tokens appear in overlay within 2s of speech ending
- [ ] Web dashboard: user can register, create session, view report

---

## How to Handle Blockers

| Situation | Action |
|-----------|--------|
| Agent is blocked waiting on another agent | Do NOT start — document the blocker and wait |
| Agent delivers incomplete work | Do NOT advance phase — iterate with that agent first |
| Two parallel agents have a conflict | Resolve at the interface level (API contract or schema) |
| Agent makes a breaking change | Notify all agents that depend on it — they may need to update |

---

## Interface Contracts (Where Agents Must Agree)

These are the shared boundaries. Both agents on each side must agree
before building their side.

### Database ↔ Everyone
- SQLAlchemy model field names are the contract
- Any change to a model field requires re-running migrations AND
  updating all agents that reference that field

### Backend API ↔ Desktop Client
- WebSocket message format (defined in `03-backend-api-agent.md`)
- Any change must be reflected in both `session_handler.py` (backend)
  and `ws/client.js` (desktop)

### Backend API ↔ Web Dashboard
- REST endpoint paths and response shapes (Pydantic schemas)
- Dashboard uses TypeScript types generated from Pydantic schemas:
  `openapi-typescript` auto-generates them from `/openapi.json`

### AI Integration ↔ Backend API
- `stream_answer()` and `analyze_session()` function signatures
- Changes here require Backend API Agent to update its callers

---

## You as the Orchestrator

Your job during the build:

1. **Start Phase 1** — give Agent 01 its file + README
2. **Review the output** — run the Definition of Done checklist yourself
3. **Approve or send back** — if not done, tell the agent what's missing
4. **Advance the phase** — only when checklist passes
5. **Launch parallel agents** — give each their file + the outputs from dependencies
6. **Watch for interface conflicts** — you are the referee
7. **Keep a build log** — note what each agent delivered and any deviations

> Think of yourself as the **Tech Lead**:
> you don't write the code, but you decide when work is done
> and you resolve conflicts between agents.

---

## Quick Reference Card

```
START HERE → [01] Database
                  ↓
             [02] Auth & Payments
                  ↓
        ┌─── [05] AI Integration    ← also start [07] infra here
        │         ↓
        └──► [03] Backend API
                  ↓
        ┌─── [04] Desktop Client
        │    [06] Web Dashboard    ← both in parallel
        └─────────↓
             [07] DevOps (deploy)
                  ↓
               LAUNCH
```
