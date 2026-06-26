#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p runtime

PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_PY=".venv/bin/python"
DASHBOARD_PID_FILE="runtime/alpha_dashboard.pid"
DASHBOARD_LOG_FILE="runtime/alpha_dashboard.log"
URL="http://127.0.0.1:8000/dashboard"

read_pid_file() {
  tr -d '[:space:]' < "$1"
}

valid_pid() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

process_is_active() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

process_matches_dashboard() {
  local pid="$1"
  local command_text
  command_text="$(ps -p "$pid" -o command= 2>/dev/null || ps -p "$pid" -o args= 2>/dev/null || true)"
  [[ "$command_text" == *"uvicorn"* && "$command_text" == *"backend.app.main:app"* ]]
}

archive_pid_file() {
  local pid_file="$1"
  local archived="${pid_file}.stale.$(date -u +%Y%m%dT%H%M%SZ)"
  mv -f "$pid_file" "$archived"
  echo "Archived stale Alpha dashboard PID file at $ROOT/$archived"
}

write_pid_file() {
  local pid="$1"
  local tmp="${DASHBOARD_PID_FILE}.$$"
  printf '%s\n' "$pid" > "$tmp"
  mv -f "$tmp" "$DASHBOARD_PID_FILE"
}

wait_for_exit() {
  local pid="$1"
  local attempts="$2"
  local attempt
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if ! process_is_active "$pid"; then
      return 0
    fi
    sleep 0.25
  done
  return 1
}

cleanup_started_process() {
  local pid="$1"
  if ! process_is_active "$pid"; then
    rm -f "$DASHBOARD_PID_FILE"
    return 0
  fi

  kill "$pid" 2>/dev/null || true
  if wait_for_exit "$pid" 20; then
    rm -f "$DASHBOARD_PID_FILE"
    return 0
  fi

  echo "Alpha dashboard process $pid did not stop after TERM; escalating to KILL."
  kill -KILL "$pid" 2>/dev/null || true
  if wait_for_exit "$pid" 20; then
    rm -f "$DASHBOARD_PID_FILE"
    return 0
  fi

  echo "Alpha dashboard process $pid is still active; preserving $ROOT/$DASHBOARD_PID_FILE."
  return 1
}

if [[ ! -x "$APP_PY" ]]; then
  "$PYTHON_BIN" -m venv .venv
  "$APP_PY" -m pip install -e .
fi

OPEN_BROWSER="${ALPHA_OPEN_BROWSER:-1}"

if [[ -f "$DASHBOARD_PID_FILE" ]]; then
  PID="$(read_pid_file "$DASHBOARD_PID_FILE")"
  if ! valid_pid "$PID"; then
    archive_pid_file "$DASHBOARD_PID_FILE"
  elif process_is_active "$PID" && process_matches_dashboard "$PID"; then
    echo "Alpha dashboard already running at $URL"
    if [[ "$OPEN_BROWSER" != "0" ]] && command -v open >/dev/null 2>&1; then
      open "$URL"
    fi
    exit 0
  else
    if process_is_active "$PID"; then
      echo "Alpha dashboard PID $PID points to a non-dashboard process."
    fi
    archive_pid_file "$DASHBOARD_PID_FILE"
  fi
fi

if HEALTH="$(curl -fsS "http://127.0.0.1:8000/health" 2>/dev/null)" && [[ "$HEALTH" == *"research_paper_order_intent_review"* ]]; then
  if command -v lsof >/dev/null 2>&1; then
    EXISTING_PID="$(lsof -tiTCP:8000 -sTCP:LISTEN | head -n 1 || true)"
    if [[ -n "$EXISTING_PID" ]]; then
      write_pid_file "$EXISTING_PID"
      echo "Alpha dashboard already running at $URL as process $EXISTING_PID"
    else
      echo "Alpha dashboard already running at $URL"
    fi
  else
    echo "Alpha dashboard already running at $URL"
  fi
  if [[ "$OPEN_BROWSER" != "0" ]] && command -v open >/dev/null 2>&1; then
    open "$URL"
  fi
  exit 0
fi

nohup "$APP_PY" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 >"$DASHBOARD_LOG_FILE" 2>&1 &
STARTED_PID="$!"
write_pid_file "$STARTED_PID"

echo "Alpha dashboard started at $URL"
echo "Alpha paper agent loop is managed by the dashboard app runtime."
echo "Dashboard log: $ROOT/$DASHBOARD_LOG_FILE"

READY=0
for _ in {1..60}; do
  if ! process_is_active "$STARTED_PID"; then
    echo "Alpha dashboard failed during startup."
    tail -n 80 "$DASHBOARD_LOG_FILE" || true
    rm -f "$DASHBOARD_PID_FILE"
    exit 1
  fi
  if curl -fsS "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
    echo "Alpha dashboard health check passed."
    READY=1
    break
  fi
  sleep 0.5
done

if [[ "$READY" != "1" ]]; then
  echo "Alpha dashboard did not become ready within 30 seconds."
  tail -n 80 "$DASHBOARD_LOG_FILE" || true
  cleanup_started_process "$STARTED_PID"
  exit 1
fi

if [[ "$OPEN_BROWSER" != "0" ]] && command -v open >/dev/null 2>&1; then
  open "$URL"
fi
