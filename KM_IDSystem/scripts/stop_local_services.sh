#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${OPME_DATA_DIR:-$ROOT_DIR/data}"
LOG_FILE="$DATA_DIR/launcher.log"
mkdir -p "$DATA_DIR"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >>"$LOG_FILE"
}

pid_cmdline() {
  local pid="$1"
  if [ -r "/proc/$pid/cmdline" ]; then
    tr '\0' ' ' <"/proc/$pid/cmdline"
  else
    ps -p "$pid" -o command= 2>/dev/null || true
  fi
}

pid_cwd() {
  local pid="$1"
  if [ -e "/proc/$pid/cwd" ]; then
    (cd "/proc/$pid/cwd" 2>/dev/null && pwd -P) || true
  fi
}

process_exists() {
  local pid="$1"
  [ -r "/proc/$pid/cmdline" ] || ps -p "$pid" >/dev/null 2>&1
}

stop_pid_file() {
  local name="$1"
  local marker="$2"
  local pid_file="$DATA_DIR/$name.pid"
  local pid=""
  local cmdline=""
  local cwd=""

  if [ ! -f "$pid_file" ]; then
    log "$name pid file absent"
    return 0
  fi
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if ! [[ "$pid" =~ ^[0-9]+$ ]]; then
    log "$name pid file invalid; removing $pid_file"
    rm -f "$pid_file"
    return 0
  fi
  if ! process_exists "$pid"; then
    log "$name pid $pid is stale; removing $pid_file"
    rm -f "$pid_file"
    return 0
  fi

  cmdline="$(pid_cmdline "$pid")"
  cwd="$(pid_cwd "$pid")"
  if [[ "$cmdline" != *"$ROOT_DIR"* && "$cwd" != "$ROOT_DIR"* ]]; then
    log "$name pid $pid does not match IDS launcher ownership; leaving process running"
    return 1
  fi
  if [[ "$cmdline" != *"$marker"* ]]; then
    log "$name pid $pid does not match IDS launcher ownership; leaving process running"
    return 1
  fi

  log "Stopping $name pid $pid"
  kill "$pid" 2>/dev/null || true
  for _ in $(seq 1 10); do
    if ! process_exists "$pid"; then
      rm -f "$pid_file"
      return 0
    fi
    sleep 1
  done
  log "Escalating $name pid $pid"
  kill -TERM "$pid" 2>/dev/null || true
  sleep 1
  if process_exists "$pid"; then
    log "$name pid $pid still running after stop request"
    return 1
  fi
  rm -f "$pid_file"
}

stop_pid_file backend "uvicorn"
stop_pid_file frontend "npm"
log "Stop complete"
