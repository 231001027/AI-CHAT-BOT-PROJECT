#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# start-dev.sh  —  Start both backends locally (no Docker) for development
# ──────────────────────────────────────────────────────────────────────────────
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── Colours ──────────────────────────────────────────────────────────────────
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${CYAN}[hearconnect]${NC} $*"; }
ok()   { echo -e "${GREEN}[ok]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }

# ── Cleanup on exit ───────────────────────────────────────────────────────────
PIDS=()
cleanup() {
  log "Shutting down..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  exit 0
}
trap cleanup INT TERM

# ── FastAPI ───────────────────────────────────────────────────────────────────
log "Starting FastAPI service on http://localhost:8000 ..."

FASTAPI_DIR="$ROOT/backend/fastapi"

# Create and activate a venv if one doesn't exist
if [ ! -d "$FASTAPI_DIR/.venv" ]; then
  warn "No .venv found — creating virtual environment..."
  python3 -m venv "$FASTAPI_DIR/.venv"
fi

source "$FASTAPI_DIR/.venv/bin/activate"

pip install -q -r "$FASTAPI_DIR/requirements.txt"

# Copy .env if missing
if [ ! -f "$FASTAPI_DIR/.env" ]; then
  cp "$FASTAPI_DIR/.env.example" "$FASTAPI_DIR/.env"
  warn "Created $FASTAPI_DIR/.env from example — review it before production use."
fi

(
  cd "$FASTAPI_DIR"
  set -a; [ -f .env ] && source .env; set +a
  uvicorn main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --reload
) &
PIDS+=($!)

ok "FastAPI started (PID $!)"

# ── Node.js Gateway ───────────────────────────────────────────────────────────
log "Starting Node.js gateway on http://localhost:3000 ..."

NODE_DIR="$ROOT/backend/node"

if [ ! -d "$NODE_DIR/node_modules" ]; then
  warn "node_modules not found — running npm install..."
  (cd "$NODE_DIR" && npm install)
fi

# Copy .env if missing
if [ ! -f "$NODE_DIR/.env" ]; then
  cp "$NODE_DIR/.env.example" "$NODE_DIR/.env"
  warn "Created $NODE_DIR/.env from example — review it before production use."
fi

(
  cd "$NODE_DIR"
  node server.js
) &
PIDS+=($!)

ok "Node.js gateway started (PID $!)"

# ── Frontend hint ─────────────────────────────────────────────────────────────
echo ""
log "Both backends are running."
echo -e "  FastAPI  → ${GREEN}http://localhost:8000${NC}  (API docs: http://localhost:8000/docs)"
echo -e "  Gateway  → ${GREEN}http://localhost:3000${NC}  (health:   http://localhost:3000/gateway/health)"
echo ""
log "Run the React frontend separately:"
echo -e "  ${YELLOW}cd $(basename $ROOT) && npm run dev${NC}"
echo ""
log "Press Ctrl+C to stop all services."

# Wait for all background processes
wait
