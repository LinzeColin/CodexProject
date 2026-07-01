#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "后端依赖未安装。请先运行: python3 -m venv .venv && .venv/bin/python -m pip install -r backend/requirements.txt" >&2
  exit 1
fi
if [ ! -x ".venv/bin/pytest" ]; then
  echo "pytest 不存在。请先运行: .venv/bin/python -m pip install -r backend/requirements.txt" >&2
  exit 1
fi
PYTHONPATH=backend .venv/bin/pytest backend/tests

(
  cd frontend
  if [ ! -d "node_modules" ]; then
    echo "前端依赖未安装。请先运行: cd frontend && npm install" >&2
    exit 1
  fi
  npm run build
)

echo "Smoke tests passed."
