#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"
cd "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/data/cache"
LOG_FILE="$PROJECT_DIR/data/cache/quantlab_macos_app.log"
exec >> "$LOG_FILE" 2>&1
echo "==== EVA_OS launch $(date -u +"%Y-%m-%dT%H:%M:%SZ") pid=$$ ===="

open_existing_service() {
  for EXISTING_PORT in {8501..8510}; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$EXISTING_PORT/_stcore/health" | grep -q "200"; then
      EXISTING_URL="http://localhost:$EXISTING_PORT"
      echo "QuantLab is already running at $EXISTING_URL. Reusing the existing service."
      open "$EXISTING_URL" >/dev/null 2>&1
      return 0
    fi
  done
  return 1
}

wait_for_existing_service() {
  LOCK_WAIT_SECONDS="${QUANTLAB_LAUNCH_LOCK_WAIT_SECONDS:-30}"
  for _ in $(seq 1 "$LOCK_WAIT_SECONDS"); do
    if open_existing_service; then
      return 0
    fi
    sleep 1
  done
  return 1
}

close_launcher_terminal() {
  CURRENT_TTY="$(tty 2>/dev/null || true)"
  if [[ -z "$CURRENT_TTY" || "$CURRENT_TTY" != /dev/* ]]; then
    return
  fi
  (
    sleep 1
    osascript - "$CURRENT_TTY" <<'APPLESCRIPT'
on run argv
  set targetTty to item 1 of argv
  tell application "Terminal"
    set targetWindow to missing value
    repeat with w in windows
      repeat with t in tabs of w
        try
          if (tty of t as text) is targetTty then
            set targetWindow to w
          end if
        end try
      end repeat
    end repeat
    if targetWindow is not missing value then
      close targetWindow saving no
      delay 0.2
    end if
    if (count of windows) is 0 then
      quit
    end if
  end tell
end run
APPLESCRIPT
  ) >/dev/null 2>&1 &
}

LOCK_DIR="$PROJECT_DIR/data/cache/quantlab_launch.lockdir"
LOCK_PID_FILE="$LOCK_DIR/pid"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  EXISTING_LOCK_PID="$(cat "$LOCK_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$EXISTING_LOCK_PID" ]] && ! kill -0 "$EXISTING_LOCK_PID" >/dev/null 2>&1; then
    echo "Removing stale QuantLab launch lock for pid $EXISTING_LOCK_PID."
    rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true
  elif [[ -z "$EXISTING_LOCK_PID" ]]; then
    echo "Removing stale QuantLab launch lock without pid metadata."
    rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true
  fi
fi
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Another QuantLab launch is already starting. Waiting for the existing startup to finish."
  if wait_for_existing_service; then
    close_launcher_terminal
    exit 0
  fi
  rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "QuantLab launch lock is still active. Please wait a moment and try again."
    close_launcher_terminal
    exit 1
  fi
fi
printf "%s\n" "$$" > "$LOCK_PID_FILE"
trap 'rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true' EXIT

source "$PROJECT_DIR/scripts/quantlabRuntime.sh"

export PYTHONPATH="$PROJECT_DIR/src"
PYTHON_BIN="$(quantlab_ensure_app_python "$PROJECT_DIR")"

if open_existing_service; then
  close_launcher_terminal
  exit 0
fi

PORT=8501
while lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  PORT=$((PORT + 1))
done

HEARTBEAT_PORT=$((PORT + 1000))
while lsof -iTCP:"$HEARTBEAT_PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  HEARTBEAT_PORT=$((HEARTBEAT_PORT + 1))
done

URL="http://localhost:$PORT"
HEARTBEAT_TIMEOUT="${QUANTLAB_HEARTBEAT_TIMEOUT:-120}"
export QUANTLAB_HEARTBEAT_URL="http://127.0.0.1:$HEARTBEAT_PORT/heartbeat"
echo "Starting QuantLab at $URL"
echo "Research only. Live trading and real order submission are prohibited."
"$PYTHON_BIN" -m streamlit run src/quantlab/app/streamlit_app.py \
  --server.port "$PORT" \
  --server.address 127.0.0.1 \
  --server.headless true \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false &
STREAMLIT_PID=$!
CURRENT_TTY="$(tty 2>/dev/null || true)"
if [[ -n "$CURRENT_TTY" && "$CURRENT_TTY" != /dev/* ]]; then
  CURRENT_TTY=""
fi
"$PYTHON_BIN" -m quantlab.system.shutdown_monitor --port "$HEARTBEAT_PORT" --streamlit-pid "$STREAMLIT_PID" --terminal-tty "$CURRENT_TTY" --timeout "$HEARTBEAT_TIMEOUT" &
MONITOR_PID=$!

echo "Waiting for QuantLab to become ready..."
READY=0
for _ in {1..60}; do
  if ! kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; then
    echo "QuantLab failed to start. Check the messages above."
    close_launcher_terminal
    exit 1
  fi
  if curl -s -o /dev/null -w "%{http_code}" "$URL/_stcore/health" | grep -q "200"; then
    READY=1
    break
  fi
  sleep 1
done

if [ "$READY" != "1" ]; then
  echo "QuantLab did not become ready within 60 seconds. Stopping service."
  kill "$STREAMLIT_PID" >/dev/null 2>&1 || true
  kill "$MONITOR_PID" >/dev/null 2>&1 || true
  wait "$STREAMLIT_PID" >/dev/null 2>&1 || true
  close_launcher_terminal
  exit 1
fi

echo "QuantLab is ready. Opening $URL"
open "$URL" >/dev/null 2>&1

wait "$STREAMLIT_PID" >/dev/null 2>&1 || true
kill "$MONITOR_PID" >/dev/null 2>&1 || true
close_launcher_terminal
exit 0
