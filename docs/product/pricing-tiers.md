# Pricing & Tiers — Free / Pro / Teams

> Owned by the **Producer Agent (08)**, enforced by the **Auth & Payments Agent
> (02)**, presented by **Marketing (10)**. Any change to what a tier includes is a
> Producer decision. This supersedes the sketch in the root `README.md`.

_Last updated: 2026-08-13. Prices in USD. Subject to Marketing A/B testing._

---

## At a glance

| | **Free** | **Pro** | **Teams** |
|---|---|---|---|
| **Price** | $0 | **$29 / mo** (or $290/yr) | **$49 / user / mo** (min 3 seats) |
| **Target** | Try it, one-off interviews | Active job seekers | Bootcamps, universities, career-coaching & recruiting agencies |
| **Live sessions** | 3 / month | Unlimited | Unlimited |
| **Real-time AI answers** | ✅ (basic) | ✅ (advanced: tone, length, STAR mode) | ✅ advanced |
| **Session length cap** | 30 min | Unlimited | Unlimited |
| **Interviewer profiles** | 1 | Unlimited | Unlimited + **shared team library** |
| **Post-interview coaching report** | ❌ | ✅ | ✅ |
| **PDF report export** | ❌ | ✅ | ✅ + branded |
| **Transcript history** | last 3 sessions | Full history | Full history |
| **Audio retention (opt-in)** | ❌ | ✅ opt-in | ✅ opt-in, admin-controlled |
| **Resume-personalized answers** | ✅ | ✅ | ✅ |
| **Team admin console / seats** | — | — | ✅ |
| **Usage analytics** | — | Personal | Team-level |
| **Support** | Community | Priority email | Priority + onboarding |

> Pricing note: the README originally listed Pro $20 / Teams $50. Marketing's
> competitive analysis (see `docs/marketing/marketing-plan.md`) benchmarks
> competitors well above this; **$29 Pro / $49-per-seat Teams** is the current
> recommendation. Final numbers pending A/B tests — treat as a hypothesis.

---

## Why these gates

- **Free = acquisition + virality.** Enough to feel the magic (3 real sessions,
  basic real-time answers) but no coaching report and a session cap — the report
  and unlimited usage are the upgrade triggers.
- **Pro = the individual job seeker.** Unlimited sessions during an active search,
  advanced answers, full coaching reports + PDF, history, opt-in audio retention.
- **Teams = institutions.** Per-seat, shared interviewer library, admin console,
  team analytics, branded PDF exports. Highest LTV; sold via partnerships.

---

## Enforcement (owned by Auth & Payments Agent 02)
- Session count + length caps enforced server-side (not just UI).
- Report generation and PDF export gated by `subscription_tier`.
- Free users see a blurred report preview with an upgrade CTA (already speced in
  Agent 06).
- Stripe: one product, three prices; annual option for Pro; per-seat quantity for
  Teams; Customer Portal for self-serve management.

---

## Legal-linked tier rules (from Legal Advisor 09)
- **Audio not stored by default on any tier.** Retention is an explicit opt-in and
  only offered on Pro/Teams, with a stated retention window and one-click deletion.
- Consent acknowledgment gate applies to **all** tiers before a live session.

---

## Open questions for A/B testing (Marketing 10)
- Free at 3 sessions/mo vs. 1 session lifetime + then paywall?
- Pro monthly $29 vs $25 vs $19; annual discount depth.
- Teams minimum seat count (3 vs 5) and volume discounts.
- Whether "basic real-time answers" on Free is generous enough to convert without
  cannibalizing Pro.
