#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUNTIME_ROOT="${WDA_R3_RUNTIME_ROOT:-/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime}"
VENV_DIR="${WDA_R3_VENV_DIR:-$RUNTIME_ROOT/.venv}"
PYTHON_BOOTSTRAP="${PYTHON_BOOTSTRAP:-/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}"
HOST="${WDA_R3_HOST:-127.0.0.1}"
PORT="${WDA_R3_PORT:-18730}"
PID_FILE="$RUNTIME_ROOT/state/service.pid"
URL="http://$HOST:$PORT/"

mkdir -p "$RUNTIME_ROOT/logs" "$RUNTIME_ROOT/state"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  "$PYTHON_BOOTSTRAP" -m venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" - <<'PY' >/dev/null 2>&1
import fastapi
import uvicorn
PY
then
  "$VENV_DIR/bin/python" -m pip install -r "$PROJECT_DIR/requirements-v0_2_r3.txt"
fi

export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export WDA_R3_RUNTIME_ROOT="$RUNTIME_ROOT"

"$VENV_DIR/bin/python" -m WDA.app_api.cli init >/dev/null

if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "${PID:-}" ] && kill -0 "$PID" >/dev/null 2>&1; then
    open "$URL"
    echo "WDA already running: $URL"
    exit 0
  fi
fi

"$VENV_DIR/bin/python" -m WDA.app_api.cli start-background --host "$HOST" --port "$PORT"
sleep 2
open "$URL"
echo "WDA started: $URL"
