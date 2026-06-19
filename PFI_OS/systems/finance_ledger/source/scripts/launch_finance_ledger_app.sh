#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${FINANCE_LEDGER_HOME:-$(cd "$SCRIPT_DIR/.." && pwd)}"
REPORTS_DIR="${FINANCE_LEDGER_REPORTS_DIR:-$PROJECT_DIR/outputs/finance_ledger_20220605_20260603/reports}"
PYTHON_BIN="${FINANCE_LEDGER_PYTHON:-python3}"
LOG_DIR="$PROJECT_DIR/work/app_launcher"
mkdir -p "$LOG_DIR"
RUN_LOG="$LOG_DIR/launcher.log"
LOCK_DIR="$LOG_DIR/launcher.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  old_pid="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && /bin/kill -0 "$old_pid" 2>/dev/null; then
    sleep 0.8
  else
    rm -rf "$LOCK_DIR"
    mkdir "$LOCK_DIR" 2>/dev/null || true
  fi
fi
echo "$$" > "$LOCK_DIR/pid" 2>/dev/null || true
trap 'rm -rf "$LOCK_DIR" 2>/dev/null || true' EXIT
echo "$(date '+%Y-%m-%d %H:%M:%S') launch start" >> "$RUN_LOG"

page_matches() {
  local url="$1"
  /usr/bin/curl -fsS --max-time 2 "$url" 2>/dev/null | /usr/bin/grep -q "questionConsole" || return 1
  return 0
}

port_is_listening() {
  local port="$1"
  /usr/sbin/lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1 || return 1
  return 0
}

choose_url() {
  local port=8765
  local url="http://127.0.0.1:${port}/index.html"
  if [[ ! -f "$REPORTS_DIR/index.html" ]]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') missing reports index at $REPORTS_DIR/index.html" >> "$RUN_LOG"
    return 1
  fi
  if ! port_is_listening "$port"; then
    nohup "$PYTHON_BIN" -m http.server "$port" --bind 127.0.0.1 --directory "$REPORTS_DIR" > "$LOG_DIR/http_${port}.log" 2>&1 &
    echo $! > "$LOG_DIR/http_${port}.pid"
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      sleep 0.3
      if port_is_listening "$port"; then
        break
      fi
    done
  fi
  echo "$url"
  return 0
}

URL="$(choose_url || true)"
if [[ -z "$URL" ]]; then
  if [[ -f "$REPORTS_DIR/index.html" ]]; then
    URL="file://$REPORTS_DIR/index.html"
  else
    URL="file://$PROJECT_DIR/README.md"
  fi
fi
echo "$(date '+%Y-%m-%d %H:%M:%S') open $URL" >> "$RUN_LOG"
/usr/bin/open "$URL"
