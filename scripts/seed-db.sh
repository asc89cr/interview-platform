#!/usr/bin/env bash
# scripts/seed-db.sh
# Populate the development database with sample data.
# Usage: bash scripts/seed-db.sh

set -euo pipefail

GREEN='\033[0;32m'
RESET='\033[0m'

info() { echo -e "${GREEN}[seed]${RESET} $*"; }

# Activate venv if present and not already active
if [[ -z "${VIRTUAL_ENV:-}" && -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

info "Running database seed script…"
python -m backend.seeds.seed

info "✅  Database seeded successfully."
info "   Login: dev@example.com  (subscription: pro)"
