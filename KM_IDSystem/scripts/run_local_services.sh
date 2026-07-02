#!/bin/bash
set -euo pipefail

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/data"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/launcher.log"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >>"$LOG_FILE"
}

find_cmd() {
  local name="$1"
  command -v "$name" 2>/dev/null || true
}

notify_failure() {
  local message="$1"
  log "ERROR: $message"
  /usr/bin/osascript -e "display notification \"$message\" with title \"IDS / Industrial Data System\"" >/dev/null 2>&1 || true
}

fail() {
  notify_failure "$1"
  exit 1
}

PYTHON_BIN="$(find_cmd python3)"
NPM_BIN="$(find_cmd npm)"
LSOF_BIN="$(find_cmd lsof)"
OPEN_BIN="$(find_cmd open)"
CURL_BIN="$(find_cmd curl)"

[ -n "$PYTHON_BIN" ] || fail "找不到 python3，请安装 Python 3"
[ -n "$NPM_BIN" ] || fail "找不到 npm，请安装 Node.js/npm"
[ -n "$LSOF_BIN" ] || fail "找不到 lsof，无法检查端口"
[ -n "$CURL_BIN" ] || fail "找不到 curl，无法检查服务健康状态"

port_open() {
  local port="$1"
  "$LSOF_BIN" -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

http_get() {
  "$CURL_BIN" -fsS --max-time 2 "$1" 2>/dev/null || true
}

backend_healthy() {
  local port="$1"
  http_get "http://127.0.0.1:$port/api/health" | grep -q "ids-industrial-data-system"
}

frontend_healthy() {
  local port="$1"
  http_get "http://127.0.0.1:$port/" | grep -q "IDS / Industrial Data System"
}

first_free_port() {
  local start="$1"
  local end="$2"
  local port
  for port in $(seq "$start" "$end"); do
    if ! port_open "$port"; then
      echo "$port"
      return 0
    fi
  done
  return 1
}

select_backend_port() {
  local saved_port=""
  if [ -f "$LOG_DIR/backend_port" ]; then
    saved_port="$(cat "$LOG_DIR/backend_port" 2>/dev/null || true)"
  fi
  if [ -n "$saved_port" ] && backend_healthy "$saved_port"; then
    echo "$saved_port"
    return 0
  fi
  local port
  for port in $(seq 8000 8020); do
    if backend_healthy "$port"; then
      echo "$port"
      return 0
    fi
  done
  first_free_port 8000 8020
}

select_frontend_port() {
  local backend_port="$1"
  local saved_port=""
  local saved_proxy=""
  if [ -f "$LOG_DIR/frontend_port" ]; then
    saved_port="$(cat "$LOG_DIR/frontend_port" 2>/dev/null || true)"
  fi
  if [ -f "$LOG_DIR/frontend_proxy_port" ]; then
    saved_proxy="$(cat "$LOG_DIR/frontend_proxy_port" 2>/dev/null || true)"
  fi
  if [ -n "$saved_port" ] && [ "$saved_proxy" = "$backend_port" ] && frontend_healthy "$saved_port"; then
    echo "$saved_port"
    return 0
  fi
  first_free_port 5173 5190
}

wait_for_backend() {
  local port="$1"
  local attempt
  for attempt in $(seq 1 30); do
    if backend_healthy "$port"; then
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_for_frontend() {
  local port="$1"
  local attempt
  for attempt in $(seq 1 30); do
    if frontend_healthy "$port"; then
      return 0
    fi
    sleep 1
  done
  return 1
}

ensure_backend() {
  cd "$ROOT_DIR"
  log "Using python: $PYTHON_BIN"
  if [ ! -x ".venv/bin/python" ]; then
    fail "后端依赖未安装。请先运行: cd '$ROOT_DIR' && python3 -m venv .venv && .venv/bin/python -m pip install -r backend/requirements.txt"
  fi
  if [ ! -x ".venv/bin/uvicorn" ]; then
    fail "后端 uvicorn 不存在。请先运行: cd '$ROOT_DIR' && .venv/bin/python -m pip install -r backend/requirements.txt"
  fi

  BACKEND_PORT="$(select_backend_port || true)"
  [ -n "$BACKEND_PORT" ] || fail "8000-8020 均不可用，无法启动后端"
  if backend_healthy "$BACKEND_PORT"; then
    log "Backend already healthy on 127.0.0.1:$BACKEND_PORT"
  else
    log "Starting backend on 127.0.0.1:$BACKEND_PORT"
    (
      cd "$ROOT_DIR"
      nohup env PYTHONPATH="$ROOT_DIR/backend" "$ROOT_DIR/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port "$BACKEND_PORT" >>"$LOG_FILE" 2>&1 </dev/null &
      echo $! >"$LOG_DIR/backend.pid"
    )
    wait_for_backend "$BACKEND_PORT" || fail "后端启动失败，请查看 data/launcher.log"
  fi
  echo "$BACKEND_PORT" >"$LOG_DIR/backend_port"
}

ensure_frontend() {
  cd "$ROOT_DIR/frontend"
  log "Using npm: $NPM_BIN"
  if [ ! -d "node_modules" ]; then
    fail "前端依赖未安装。请先运行: cd '$ROOT_DIR/frontend' && npm install"
  fi
  FRONTEND_PORT="$(select_frontend_port "$BACKEND_PORT" || true)"
  [ -n "$FRONTEND_PORT" ] || fail "5173-5190 均不可用，无法启动前端"
  if frontend_healthy "$FRONTEND_PORT"; then
    log "Frontend already healthy on 127.0.0.1:$FRONTEND_PORT"
  else
    log "Starting frontend on 127.0.0.1:$FRONTEND_PORT with API proxy $BACKEND_PORT"
    (
      cd "$ROOT_DIR/frontend"
      nohup env VITE_API_PROXY="http://127.0.0.1:$BACKEND_PORT" "$NPM_BIN" run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort >>"$LOG_FILE" 2>&1 </dev/null &
      echo $! >"$LOG_DIR/frontend.pid"
    )
    wait_for_frontend "$FRONTEND_PORT" || fail "前端启动失败，请查看 data/launcher.log"
  fi
  echo "$FRONTEND_PORT" >"$LOG_DIR/frontend_port"
  echo "$BACKEND_PORT" >"$LOG_DIR/frontend_proxy_port"
}

ensure_backend
ensure_frontend
sleep 3
if [ "${OPEN_BROWSER:-1}" != "0" ]; then
  [ -n "$OPEN_BIN" ] || fail "找不到 open 命令，无法打开浏览器"
  "$OPEN_BIN" "http://127.0.0.1:$FRONTEND_PORT/"
fi
log "Launch complete: frontend=http://127.0.0.1:$FRONTEND_PORT backend=http://127.0.0.1:$BACKEND_PORT"

if [ "${KEEP_TERMINAL_OPEN:-0}" = "1" ]; then
  echo "IDS / Industrial Data System is running."
  echo "Frontend: http://127.0.0.1:$FRONTEND_PORT/"
  echo "Backend:  http://127.0.0.1:$BACKEND_PORT/api/health"
  echo "Keep this Terminal window open while using the system. Press Ctrl-C to stop watching."
  while true; do
    sleep 30
    if ! backend_healthy "$BACKEND_PORT"; then
      echo "Backend health check failed. See $LOG_FILE"
    fi
    if ! frontend_healthy "$FRONTEND_PORT"; then
      echo "Frontend health check failed. See $LOG_FILE"
    fi
  done
fi
