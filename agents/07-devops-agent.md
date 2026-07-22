# Build Agent 07 — DevOps Agent

## Mission
Set up the infrastructure, CI/CD pipelines, containerization, and deployment
so the backend runs reliably in production and the desktop client can be
distributed and auto-updated.

---

## Run Order
**Depends on:** All other agents having working code
**Runs last** — but can set up infrastructure and skeleton configs in parallel

---

## Tech Stack
- Docker + Docker Compose (local dev + production containers)
- GitHub Actions (CI/CD)
- Railway or Render (backend hosting — simpler than AWS for v1)
- Vercel (web dashboard hosting)
- AWS S3 (file storage — resume PDFs, session attachments, PDF reports)
- AWS CloudFront (CDN for S3 assets)
- Redis Cloud or Upstash (managed Redis for session state)
- Supabase or Neon (managed PostgreSQL — serverless, easy scaling)
- electron-builder + GitHub Releases (desktop client distribution)
- Sentry (error tracking for backend + desktop client)

---

## Owns These Files
```
/
├── docker-compose.yml           # Local dev: backend + postgres + redis
├── docker-compose.prod.yml      # Production overrides
├── backend/
│   └── Dockerfile
├── web-dashboard/
│   └── Dockerfile               # For self-hosted option
├── desktop-client/
│   ├── electron-builder.yml     # Build config: Windows + Mac installers
│   └── .github/workflows/
│       └── release.yml          # Build + publish installers on git tag
├── .github/workflows/
│   ├── backend-ci.yml           # Test + lint on PR
│   ├── dashboard-ci.yml         # Test + lint on PR
│   └── deploy.yml               # Deploy to Railway on merge to main
├── infra/
│   ├── s3-policy.json           # S3 bucket policy (least privilege)
│   └── env.example              # All required env vars documented
└── scripts/
    ├── setup-dev.sh             # One command local dev setup
    └── seed-db.sh               # Populate dev DB with sample data
```

---

## Infrastructure to Set Up

### Backend (Railway)
- Dockerfile: Python 3.12 slim, uvicorn, no unnecessary layers
- Environment variables via Railway dashboard (never committed to git)
- Health check endpoint: `GET /health` → `{"status": "ok"}`
- Auto-deploy on push to `main` branch
- Zero-downtime deploys

### Database (Neon / Supabase)
- Managed PostgreSQL — no server to maintain
- Connection pooling via PgBouncer (built into Neon/Supabase)
- Daily automated backups
- Alembic migrations run as part of deploy pipeline

### Redis (Upstash)
- Serverless Redis for session state
- TTL set to 60s for WebSocket reconnect hold

### S3 Bucket Setup
- Bucket: `interview-platform-files`
- Folders: `/resumes/`, `/session-files/`, `/reports/`
- Presigned URL expiry: 15 minutes (upload), 1 hour (download)
- CloudFront distribution for fast PDF report downloads

### Web Dashboard (Vercel)
- Auto-deploy on push to `main`
- Environment variables in Vercel dashboard
- Preview deployments on every PR

---

## CI/CD Pipelines

### `backend-ci.yml` — runs on every PR
```
1. Install dependencies
2. Run linter (ruff)
3. Run type checker (mypy)
4. Run unit tests (pytest)
5. Build Docker image (verify it builds)
```

### `dashboard-ci.yml` — runs on every PR
```
1. Install dependencies
2. Run linter (eslint)
3. Run type checker (tsc)
4. Run tests (jest)
5. Build Next.js (verify it builds)
```

### `deploy.yml` — runs on merge to main
```
1. Run full test suite
2. Run Alembic migrations against production DB
3. Deploy backend to Railway
4. Deploy dashboard to Vercel
```

### `release.yml` — runs on git tag `v*.*.*`
```
1. Build Windows installer (.exe) on windows-latest runner
2. Build Mac installer (.dmg) on macos-latest runner
3. Sign installers (code signing certificates)
4. Create GitHub Release with both installers attached
5. electron-updater picks up new release automatically
```

---

## Environment Variables (documented in env.example)
```
# Backend
DATABASE_URL=
REDIS_URL=
OPENAI_API_KEY=
DEEPGRAM_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
JWT_SECRET=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_NAME=
SENTRY_DSN=

# Desktop Client
VITE_API_BASE_URL=
VITE_SENTRY_DSN=
```

---

## Deliverables
- [ ] `docker-compose.yml` spins up full local stack with one command
- [ ] `scripts/setup-dev.sh` — one-command dev environment setup
- [ ] Backend Dockerfile production-ready (non-root user, slim image)
- [ ] GitHub Actions: CI runs on every PR (backend + dashboard)
- [ ] GitHub Actions: deploy to Railway + Vercel on merge to main
- [ ] GitHub Actions: build + publish desktop installers on version tag
- [ ] S3 bucket configured with correct IAM policy
- [ ] All environment variables documented in `env.example`
- [ ] Sentry error tracking integrated in backend + desktop client
- [ ] `GET /health` endpoint returning service status

---

## Definition of Done
`docker-compose up` starts the full stack locally in under 2 minutes.
Merging a PR to main automatically deploys the backend and dashboard.
Pushing a version tag produces signed Windows + Mac installers in GitHub Releases.
