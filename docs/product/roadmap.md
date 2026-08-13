# Product Roadmap

> Owned by the **Producer Agent (08)**. This is the single source of truth for
> what we build next and why. Format: **Now / Next / Later**. Every item names an
> owning build agent (01–07) and its Legal (09) / Marketing (10) dependencies.
>
> **Guardrail:** The desktop client, web dashboard, and backend are live and
> working. Items below are proposed changes with acceptance criteria — they are
> executed by the owning build agent, not ad-hoc. Prefer additive work.

_Last updated: 2026-08-13_

---

## Status of the core product (baseline — shipped & working)
- ✅ Desktop client: interviewer audio via system loopback → transcribed as
  **Interviewer** → auto-generated AI answer overlay. Mic (candidate) ignored.
- ✅ Backend: FastAPI + WebSocket, Deepgram STT (single connection, UtteranceEnd
  segmentation), GPT-4o-mini answers, PostgreSQL, deployed on Railway.
- ✅ Web dashboard: auth, profiles, sessions, reports (Next.js on Vercel).

The roadmap below is **net-new** work that does not regress the above.

---

## NOW (this cycle)
Focus: make the grey area defensible and get a public front door.

| Item | Owner | Tiers | Legal | Marketing |
|------|-------|-------|-------|-----------|
| **Public landing page** (standalone `landing/` site) | 10 + 07 (deploy) | all | claims review | ✅ lead |
| **Legal guardrails v1**: ToS, Privacy Policy, pre-session consent gate, "know your local laws" acknowledgment | 09 + 04 (client gate) + 06-adjacent | all | ✅ owner | — |
| **Tier enforcement audit**: confirm Free/Pro/Teams limits are actually enforced (session caps, report/PDF gating) | 02 | all | — | pricing page parity |
| **Audio-not-stored-by-default** confirmation + Pro opt-in retention toggle | 02/03 | Pro | ✅ required | privacy as a selling point |

**Release gate:** Legal sign-off on ToS/consent + Marketing sign-off on landing copy.

---

## NEXT (following cycle)
Focus: conversion + retention.

| Item | Owner | Tiers | Notes |
|------|-------|-------|-------|
| **macOS desktop build** (currently Windows loopback path) | 04 | all | expands TAM; loopback via ScreenCaptureKit/BlackHole guidance |
| **Post-interview coaching report polish** (scores, evidence quotes, PDF export) | 05 + 06 | Pro/Teams | PDF export is a paid gate |
| **Referral / affiliate program** | 02 + 10 | all | growth loop |
| **Onboarding flow** (resume upload → first session in <5 min) | 06 | Free | activation metric |
| **Answer quality controls** (tone, length, "STAR" behavioral mode) | 05 | Pro | reduces churn |
| **Multichannel STT** (interviewer ch0 + candidate ch1 on one connection) so the candidate's own answers appear in the transcript | 05/03 | Pro/Teams | optional, additive |

---

## LATER (backlog / bets)
- **Teams admin console** — shared interviewer library, seats, usage dashboard.
- **Browser-extension capture** as an install-free alternative to the desktop app.
- **Community interviewer library** — reusable recruiter/company profiles.
- **Localization** — non-native English speakers are a core ICP; multi-language STT + answers.
- **Live "practice mode"** — a safe, clearly-legal simulated interviewer (strong positioning for the prep/practice framing).
- **Mobile companion** (view reports, not live assist).

---

## Cross-cutting dependencies
- **Legal is a hard gate** for anything touching capture, storage, or public claims.
- **Marketing** needs the tier definitions frozen before finalizing the pricing page.
- **DevOps (07)** deploys the standalone landing site (separate from the dashboard).

---

## How to propose a feature
Open a one-pager using the template in `agents/08-producer-agent.md`, then the
Producer triages it into Now / Next / Later.
