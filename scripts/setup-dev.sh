#!/usr/bin/env bash
# scripts/setup-dev.sh
# One-command local development environment setup.
# Usage: bash scripts/setup-dev.sh

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

info()  { echo -e "${GREEN}[setup]${RESET} $*"; }
warn()  { echo -e "${YELLOW}[warn]${RESET}  $*"; }
fatal() { echo -e "\033[0;31m[error]${RESET} $*" >&2; exit 1; }

# ── Prerequisites check ───────────────────────────────────────────────────────
command -v docker  >/dev/null 2>&1 || fatal "Docker is not installed. Install from https://docs.docker.com/get-docker/"
command -v python3 >/dev/null 2>&1 || fatal "Python 3 is required."

# ── .env file ─────────────────────────────────────────────────────────────────
if [[ ! -f .env ]]; then
  warn ".env not found — copying from infra/env.example"
  cp infra/env.example .env
  warn "Open .env and fill in any required values before running the app."
fi

# ── Python virtual environment ────────────────────────────────────────────────
if [[ ! -d .venv ]]; then
  info "Creating Python virtual environment (.venv)…"
  python3 -m venv .venv
fi

info "Activating venv and installing backend dependencies…"
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt

# ── Start containers ──────────────────────────────────────────────────────────
info "Starting Postgres + Redis via Docker Compose…"
docker compose up -d postgres redis

info "Waiting for Postgres to be healthy…"
until docker compose exec -T postgres pg_isready -U interview -d interview_platform >/dev/null 2>&1; do
  sleep 1
done

# ── Migrations ────────────────────────────────────────────────────────────────
info "Running Alembic migrations…"
alembic upgrade head

# ── Seed ──────────────────────────────────────────────────────────────────────
read -rp "Seed the database with sample data? [y/N] " seed
if [[ "$seed" =~ ^[Yy]$ ]]; then
  bash scripts/seed-db.sh
fi

echo ""
echo -e "${BOLD}✅  Setup complete!${RESET}"
echo ""
echo "  Start the full stack:"
echo "    docker compose up"
echo ""
echo "  Or run the backend only (hot-reload):"
echo "    source .venv/bin/activate"
echo "    uvicorn backend.main:app --reload"
echo ""
echo "  API docs: http://localhost:8000/docs"
echo "  Health:   http://localhost:8000/health"
