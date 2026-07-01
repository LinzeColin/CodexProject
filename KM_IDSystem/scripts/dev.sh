#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose up --build
  exit 0
fi

echo "Docker Compose 不可用，改用本地前后端启动。"
if [ ! -x ".venv/bin/uvicorn" ]; then
  echo "后端依赖未安装。请先运行: python3 -m venv .venv && .venv/bin/python -m pip install -r backend/requirements.txt" >&2
  exit 1
fi
if [ ! -d "frontend/node_modules" ]; then
  echo "前端依赖未安装。请先运行: cd frontend && npm install" >&2
  exit 1
fi
(
  cd backend
  PYTHONPATH=. ../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!
(
  cd frontend
  npm run dev -- --host 127.0.0.1
) &
FRONTEND_PID=$!

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' EXIT
wait
