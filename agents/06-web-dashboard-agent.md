# Build Agent 06 — Web Dashboard Agent

## Mission
Build the candidate-facing web application where users manage their profiles,
upload resumes and session files, create interview sessions, view conversation
history, and read post-interview analysis reports.

---

## Run Order
**Depends on:** Auth Agent (02) endpoints, Backend API Agent (03) endpoints
**Runs in parallel with:** Desktop Client Agent (04)

---

## Tech Stack
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui (component library — clean, accessible, no bloat)
- React Query (TanStack) for data fetching + caching
- React Hook Form + Zod for form validation
- Stripe.js for checkout integration

---

## Owns These Files
```
web-dashboard/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── dashboard/
│   │   ├── page.tsx             # Home: recent sessions, quick stats
│   │   ├── profile/page.tsx     # Candidate profile editor
│   │   ├── interviewers/
│   │   │   ├── page.tsx         # List interviewer profiles
│   │   │   └── [id]/page.tsx    # Edit interviewer profile
│   │   ├── sessions/
│   │   │   ├── page.tsx         # Session history list
│   │   │   ├── new/page.tsx     # Create new session wizard
│   │   │   └── [id]/
│   │   │       ├── page.tsx     # Session detail + transcript
│   │   │       └── report/page.tsx # Analysis report view
│   │   └── billing/page.tsx     # Subscription management
│   └── layout.tsx
├── components/
│   ├── SessionCard.tsx
│   ├── AnalysisReport.tsx
│   ├── ResumeUpload.tsx
│   ├── InterviewerProfileForm.tsx
│   └── ScoreRadar.tsx           # Radar chart for category scores
└── lib/
    ├── api.ts                   # Typed API client (wraps fetch)
    └── auth.ts                  # JWT storage + refresh logic
```

---

## Pages to Implement

### Auth
- **Login** — email/password, redirect to dashboard on success
- **Register** — name, email, password, redirect to profile setup

### Dashboard Home
- Recent sessions (last 5) with status badges
- Quick stats: total sessions, avg score, improvement trend
- CTA: "Start New Session" button (opens session wizard)

### Candidate Profile
- Edit name, target role, salary range, notes
- Resume upload (drag & drop → presigned S3 URL)
- Resume parsing status indicator ("Analyzing your resume...")
- Skills list (editable tags)
- Weak areas (editable tags — used to focus coaching)

### Interviewer Profiles
- List of saved interviewer profiles with company + role
- Create / Edit form: name, company, role, interview style selector,
  known questions (add/remove list), notes
- Delete with confirmation

### New Session Wizard (3 steps)
1. Select candidate profile (auto-selected, can switch)
2. Select or create interviewer profile
3. Attach files: job description, company notes, other docs
   → "Start Session" → shows instructions to open desktop app

### Session History
- Filterable list: date, status (active/completed/analysed), score
- Click → Session Detail

### Session Detail
- Full conversation transcript (Interviewer / Candidate turns)
- AI-generated answers shown next to each Interviewer turn
- "Analysis Report" tab (shows when ready, "Generating..." if pending)

### Analysis Report
- Overall score (large number, color coded)
- Radar chart: technical / behavioral / communication / confidence
- Strengths section (with transcript quotes as evidence)
- Weaknesses section (with transcript quotes)
- Interviewer intent summary
- Recommended practice list
- Download PDF button (Pro/Teams only — blur + upgrade CTA for Free)

### Billing
- Current plan badge
- Upgrade button → Stripe Checkout
- "Manage subscription" → Stripe Customer Portal
- Usage stats (sessions this month vs limit)

---

## Deliverables
- [ ] All pages implemented and responsive (desktop + tablet)
- [ ] Auth flow: register, login, logout, token refresh
- [ ] Resume upload with S3 presigned URL + parsing status polling
- [ ] Session creation wizard
- [ ] Analysis report with radar chart and evidence quotes
- [ ] Stripe checkout + customer portal integration
- [ ] Tier-gated PDF download (blur overlay for free users)
- [ ] Loading states and error handling on all data fetches
- [ ] Deployed to Vercel (or Netlify)

---

## Definition of Done
A new user can register, upload their resume, create an interviewer profile,
start a session, and view a completed analysis report — all without
any technical guidance.
