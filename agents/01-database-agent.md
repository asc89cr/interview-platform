# Build Agent 01 — Database Agent

## Mission
Design and implement the entire data layer: PostgreSQL schema, migrations,
and ORM models. All other agents depend on this agent completing first.

---

## Run Order
**Must complete before:** Backend API Agent, Auth Agent, AI Integration Agent

---

## Tech Stack
- PostgreSQL 16
- SQLAlchemy 2.x (async ORM)
- Alembic (migrations)
- Pydantic v2 (schema validation models)

---

## Owns These Files
```
backend/
├── db/
│   ├── base.py          # SQLAlchemy async engine + session factory
│   ├── models/
│   │   ├── user.py
│   │   ├── candidate_profile.py
│   │   ├── interviewer_profile.py
│   │   ├── session.py
│   │   ├── turn.py
│   │   ├── attached_file.py
│   │   └── analysis_report.py
│   └── migrations/      # Alembic migration files
└── schemas/             # Pydantic request/response schemas
    ├── user.py
    ├── session.py
    └── analysis.py
```

---

## Schema to Implement

```sql
-- Users
users (id, email, password_hash, name, subscription_tier,
       stripe_customer_id, stripe_subscription_id, created_at)

-- Candidate profiles (one per user)
candidate_profiles (id, user_id, resume_url, parsed_resume JSONB,
                    target_role, target_salary_usd, skills TEXT[],
                    weak_areas TEXT[], custom_notes, updated_at)

-- Interviewer profiles (many per user, reusable)
interviewer_profiles (id, user_id, name, company, role,
                      interview_style, known_questions TEXT[],
                      notes, created_at)

-- Interview sessions
sessions (id, user_id, candidate_profile_id, interviewer_profile_id,
          status, started_at, ended_at, created_at)

-- Files attached to a session
attached_files (id, session_id, label, file_url, file_type, uploaded_at)

-- Individual conversation turns
turns (id, session_id, speaker, text, generated_answer,
       timestamp, audio_url)

-- Post-interview analysis reports
analysis_reports (id, session_id, overall_score, category_scores JSONB,
                  strengths TEXT[], weaknesses TEXT[],
                  interviewer_intent_summary, recommended_practice TEXT[],
                  pdf_report_url, generated_at)
```

---

## Deliverables
- [ ] All SQLAlchemy async models created
- [ ] Alembic migration that creates all tables from scratch
- [ ] Pydantic schemas for all API request/response shapes
- [ ] `db/base.py` with async session factory and `get_db()` dependency
- [ ] Seed script for local development (sample user, profile, session)
- [ ] README section: how to run migrations locally

---

## Definition of Done
`alembic upgrade head` runs clean on a fresh PostgreSQL instance.
All models importable with no errors. Pydantic schemas validated with unit tests.
