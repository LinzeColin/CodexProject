#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASHBOARD_PID_FILE="$ROOT/runtime/alpha_dashboard.pid"

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
  echo "Archived stale Alpha PID file at $archived"
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

stop_pid_file() {
  local name="$1"
  local pid_file="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "Alpha $name is not running."
    return
  fi

  local pid
  pid="$(read_pid_file "$pid_file")"
  if ! valid_pid "$pid"; then
    echo "Alpha $name PID file is invalid."
    archive_pid_file "$pid_file"
    return
  fi

  if ! process_is_active "$pid"; then
    echo "Alpha $name process $pid is not active."
    archive_pid_file "$pid_file"
    return
  fi

  if ! process_matches_dashboard "$pid"; then
    echo "Alpha $name PID $pid belongs to a non-dashboard process."
    archive_pid_file "$pid_file"
    return
  fi

  kill "$pid" 2>/dev/null || true
  if wait_for_exit "$pid" 20; then
    echo "Stopped Alpha $name process $pid."
    rm -f "$pid_file"
    return
  fi

  echo "Alpha $name process $pid did not stop after TERM; escalating to KILL."
  kill -KILL "$pid" 2>/dev/null || true
  if wait_for_exit "$pid" 20; then
    echo "Killed Alpha $name process $pid after TERM timeout."
    rm -f "$pid_file"
    return
  fi

  echo "Alpha $name process $pid is still active; preserving PID file $pid_file."
  return 1
}

stop_pid_file "dashboard" "$DASHBOARD_PID_FILE"
