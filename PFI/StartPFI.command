#!/bin/zsh
set -euo pipefail
setopt NO_BG_NICE

PROJECT_DIR="${0:A:h}"
cd "$PROJECT_DIR"
LOG_DIR="$PROJECT_DIR/data/cache"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/pfi_macos_app.log"
exec >> "$LOG_FILE" 2>&1
echo "==== PFI launch $(date -u +"%Y-%m-%dT%H:%M:%SZ") pid=$$ ===="
PFI_ACTIVE_BUILD_ID="pfi-v024-stage2-phase22"
PFI_ACTIVE_UI_CONTRACT="PFI-V024-STAGE2-ENTRY-CONSISTENCY"
PFI_VERSION_QUERY="pfi_app_version=0.2.3&pfi_build=pfi-v024-stage2-phase22&pfi_ui_contract=PFI-V024-STAGE2-ENTRY-CONSISTENCY"
PFI_ACTIVE_SERVICE_FILE="$LOG_DIR/pfi_active_service.env"

process_cwd() {
  local pid="$1"
  lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | awk '/^n/ {sub(/^n/, ""); print; exit}'
}

marker_value() {
  local key="$1"
  [[ -f "$PFI_ACTIVE_SERVICE_FILE" ]] || return 1
  awk -F= -v key="$key" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' "$PFI_ACTIVE_SERVICE_FILE"
}

active_service_url_if_current_build() {
  local marker_project marker_pid marker_port marker_url marker_build marker_contract command cwd_path
  marker_project="$(marker_value PFI_ACTIVE_PROJECT_DIR || true)"
  marker_pid="$(marker_value PFI_ACTIVE_PID || true)"
  marker_port="$(marker_value PFI_ACTIVE_PORT || true)"
  marker_url="$(marker_value PFI_ACTIVE_URL || true)"
  marker_build="$(marker_value PFI_ACTIVE_BUILD_ID || true)"
  marker_contract="$(marker_value PFI_ACTIVE_UI_CONTRACT || true)"
  [[ "$marker_project" == "$PROJECT_DIR" ]] || return 1
  [[ "$marker_build" == "$PFI_ACTIVE_BUILD_ID" ]] || return 1
  [[ "$marker_contract" == "$PFI_ACTIVE_UI_CONTRACT" ]] || return 1
  [[ -n "$marker_pid" && -n "$marker_port" && -n "$marker_url" ]] || return 1
  kill -0 "$marker_pid" >/dev/null 2>&1 || return 1
  curl -s -o /dev/null -w "%{http_code}" "$marker_url/_stcore/health" | grep -q "200" || return 1
  command="$(ps -p "$marker_pid" -o command= 2>/dev/null || true)"
  cwd_path="$(process_cwd "$marker_pid")"
  [[ "$command" == *"src/pfi_os/app/streamlit_app.py"* ]] || return 1
  [[ "$cwd_path" == "$PROJECT_DIR" || "$command" == *"$PROJECT_DIR"* ]] || return 1
  printf "%s\n" "$marker_url"
}

write_active_service_marker() {
  local pid="$1"
  local port="$2"
  local url="$3"
  {
    printf "PFI_ACTIVE_SCHEMA=PFIActiveServiceV1\n"
    printf "PFI_ACTIVE_PROJECT_DIR=%s\n" "$PROJECT_DIR"
    printf "PFI_ACTIVE_PID=%s\n" "$pid"
    printf "PFI_ACTIVE_PORT=%s\n" "$port"
    printf "PFI_ACTIVE_URL=%s\n" "$url"
    printf "PFI_ACTIVE_BUILD_ID=%s\n" "$PFI_ACTIVE_BUILD_ID"
    printf "PFI_ACTIVE_UI_CONTRACT=%s\n" "$PFI_ACTIVE_UI_CONTRACT"
    printf "PFI_ACTIVE_STARTED_AT=%s\n" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  } > "$PFI_ACTIVE_SERVICE_FILE"
}

open_existing_service() {
  local existing_url
  if existing_url="$(active_service_url_if_current_build)"; then
    OPEN_URL="$existing_url/?$PFI_VERSION_QUERY"
    echo "PFI 当前 build 服务已在运行：$existing_url。复用现有服务。"
    open "$OPEN_URL" >/dev/null 2>&1
    return 0
  fi
  echo "未找到当前 build 的 PFI 服务；将忽略同路径旧服务并启动新实例。"
  return 1
}

wait_for_existing_service() {
  LOCK_WAIT_SECONDS="${PFI_LAUNCH_LOCK_WAIT_SECONDS:-30}"
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

LOCK_DIR="$PROJECT_DIR/data/cache/pfi_launch.lockdir"
LOCK_PID_FILE="$LOCK_DIR/pid"
LOCK_ACQUIRED=0
if mkdir "$LOCK_DIR" 2>/dev/null; then
  LOCK_ACQUIRED=1
else
  EXISTING_LOCK_PID="$(cat "$LOCK_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$EXISTING_LOCK_PID" ]] && ! kill -0 "$EXISTING_LOCK_PID" >/dev/null 2>&1; then
    echo "正在清理过期 PFI 启动锁：pid $EXISTING_LOCK_PID。"
    rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true
  elif [[ -z "$EXISTING_LOCK_PID" ]]; then
    echo "正在清理缺少 pid 的过期 PFI 启动锁。"
    rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true
  fi
fi
if [[ "$LOCK_ACQUIRED" != "1" ]] && ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "另一个 PFI 启动流程正在进行，正在等待其完成。"
  if wait_for_existing_service; then
    close_launcher_terminal
    exit 0
  fi
  rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "PFI 启动锁仍在占用。请稍等后重试。"
    close_launcher_terminal
    exit 1
  fi
fi
printf "%s\n" "$$" > "$LOCK_PID_FILE"
trap 'rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true' EXIT

source "$PROJECT_DIR/scripts/pfiRuntime.sh"

export PYTHONPATH="$PROJECT_DIR/src"
export PFI_UI_V2="${PFI_UI_V2:-1}"
PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"

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
OPEN_URL="$URL/?$PFI_VERSION_QUERY"
HEARTBEAT_TIMEOUT="${PFI_HEARTBEAT_TIMEOUT:-120}"
export PFI_HEARTBEAT_URL="http://127.0.0.1:$HEARTBEAT_PORT/heartbeat"
echo "正在启动 PFI：$URL"
echo "研究和回测专用；禁止实盘自动下单、券商提交、支付或无人值守执行。"
"$PYTHON_BIN" -m streamlit run src/pfi_os/app/streamlit_app.py \
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
"$PYTHON_BIN" -m pfi_os.system.shutdown_monitor --port "$HEARTBEAT_PORT" --streamlit-pid "$STREAMLIT_PID" --terminal-tty "$CURRENT_TTY" --timeout "$HEARTBEAT_TIMEOUT" &
MONITOR_PID=$!

echo "正在等待 PFI 就绪..."
READY=0
for _ in {1..60}; do
  if ! kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; then
    echo "PFI 启动失败。请查看运行日志。"
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
  echo "PFI 在 60 秒内未就绪，正在停止本次启动。"
  kill "$STREAMLIT_PID" >/dev/null 2>&1 || true
  kill "$MONITOR_PID" >/dev/null 2>&1 || true
  wait "$STREAMLIT_PID" >/dev/null 2>&1 || true
  close_launcher_terminal
  exit 1
fi

echo "PFI 已就绪，正在打开：$OPEN_URL"
write_active_service_marker "$STREAMLIT_PID" "$PORT" "$URL"
open "$OPEN_URL" >/dev/null 2>&1

wait "$STREAMLIT_PID" >/dev/null 2>&1 || true
kill "$MONITOR_PID" >/dev/null 2>&1 || true
close_launcher_terminal
exit 0
