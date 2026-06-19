#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose up --build
  exit 0
fi

echo "Docker Compose 不可用，改用本地前后端启动。"
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
(
  cd backend
  PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!
(
  cd frontend
  npm install
  npm run dev -- --host 127.0.0.1
) &
FRONTEND_PID=$!

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' EXIT
wait

