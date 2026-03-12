#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# dev.sh — start postgres, run migrations, start backend
# Usage: ./scripts/dev.sh [--no-frontend]
# ─────────────────────────────────────────────────────────────────
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"

# ── helpers ──────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[dev]${NC} $*"; }
warn()  { echo -e "${YELLOW}[dev]${NC} $*"; }
error() { echo -e "${RED}[dev]${NC} $*" >&2; }

# ── 1. postgres ───────────────────────────────────────────────────
info "Starting postgres..."
docker-compose -f "$ROOT/docker-compose.yml" up -d postgres

info "Waiting for postgres to be healthy..."
for i in $(seq 1 30); do
  if docker exec goti11_postgres pg_isready -U goti11_user -d goti11_db -q 2>/dev/null; then
    info "Postgres is ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    error "Postgres did not become ready in time."
    exit 1
  fi
  sleep 1
done

# ── 2. python venv + deps ─────────────────────────────────────────
cd "$BACKEND"

if [ ! -d ".venv" ]; then
  info "Creating virtualenv..."
  python3 -m venv .venv
fi

info "Installing dependencies..."
.venv/bin/pip install -q -r requirements.txt

# ── 3. alembic migrations ─────────────────────────────────────────
info "Running alembic migrations..."
.venv/bin/python -m alembic upgrade head

# ── 4. start uvicorn ─────────────────────────────────────────────
info "Starting backend at http://localhost:8000"
info "Docs: http://localhost:8000/docs"
exec .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
