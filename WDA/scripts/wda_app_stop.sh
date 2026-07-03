#!/usr/bin/env bash
set -euo pipefail

RUNTIME_ROOT="${WDA_R3_RUNTIME_ROOT:-/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime}"
PID_FILE="$RUNTIME_ROOT/state/service.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "WDA service pid file not found."
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [ -z "${PID:-}" ]; then
  rm -f "$PID_FILE"
  echo "WDA service pid file was empty."
  exit 0
fi

if kill -0 "$PID" >/dev/null 2>&1; then
  kill "$PID"
  echo "Stopped WDA service pid=$PID"
else
  echo "WDA service pid=$PID is not running."
fi

rm -f "$PID_FILE"
