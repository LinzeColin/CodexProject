#!/bin/zsh
set -euo pipefail
setopt NO_BG_NICE

PROJECT_DIR="${0:A:h}"
cd "$PROJECT_DIR"
source "$PROJECT_DIR/scripts/v025/stage1_phase13_candidate_env.sh"
pfi_stage1_candidate_configure "$PROJECT_DIR"
LOG_DIR="${PFI_RUNTIME_DIR:-$PROJECT_DIR/data/cache}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/pfi_macos_app.log"
exec >> "$LOG_FILE" 2>&1
echo "==== PFI launch $(date -u +"%Y-%m-%dT%H:%M:%SZ") pid=$$ ===="
source "$PROJECT_DIR/scripts/pfiReleaseIdentity.sh"
if ! pfi_release_identity_init "$PROJECT_DIR"; then
  pfi_release_show_conflict_dialog
  exit 1
fi
source "$PROJECT_DIR/scripts/pfiRuntime.sh"
export PYTHONPATH="$PROJECT_DIR/src"
export PFI_UI_V2="${PFI_UI_V2:-1}"
PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"
if ! pfi_release_cache_key_init "$PROJECT_DIR" "$PYTHON_BIN"; then
  pfi_release_show_conflict_dialog
  exit 1
fi
APP_ENTRY="src/pfi_os/app/streamlit_app.py"
MONITOR_ENTRY="$PROJECT_DIR/src/pfi_os/system/shutdown_monitor.py"
PFI_ACTIVE_SERVICE_FILE="$LOG_DIR/pfi_active_service.env"
CANDIDATE_PROCESS_GROUP_ID=""
if [[ "${PFI_STAGE1_CANDIDATE_MODE:-0}" == "1" ]]; then
  CANDIDATE_PROCESS_GROUP_ID="$(ps -p "$$" -o pgid= 2>/dev/null | awk '{$1=$1; print}')"
  if [[ "$CANDIDATE_PROCESS_GROUP_ID" != "$$" ]]; then
    echo "PFI isolated candidate launcher does not own a unique process group."
    exit 1
  fi
fi

candidate_finalization_in_progress() {
  [[ "${PFI_STAGE1_CANDIDATE_MODE:-0}" == "1" && -e "${PFI_STAGE1_FINALIZING_FILE:-}" ]]
}

pfi_open_url_if_enabled() {
  local url="$1"
  if [[ "${PFI_START_OPEN_BROWSER:-1}" == "0" ]]; then
    return 0
  fi
  open "$url" >/dev/null 2>&1
}

process_cwd() {
  local pid="$1"
  lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | awk '/^n/ {sub(/^n/, ""); print; exit}'
}

marker_value() {
  local key="$1"
  [[ -f "$PFI_ACTIVE_SERVICE_FILE" ]] || return 1
  awk -F= -v key="$key" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' "$PFI_ACTIVE_SERVICE_FILE"
}

candidate_runtime_api_port() {
  local streamlit_pid="$1"
  local marker="$PFI_RUNTIME_DIR/pfi_runtime_api.env"
  [[ "${PFI_STAGE1_CANDIDATE_MODE:-0}" == "1" ]] || return 1
  [[ -f "$marker" && ! -L "$marker" && -O "$marker" ]] || return 1
  [[ "$(stat -f %Lp "$marker" 2>/dev/null || true)" == "600" ]] || return 1
  [[ "$(awk -F= '$1 == "PFI_RUNTIME_API_SCHEMA" {print $2}' "$marker")" == "PFIV025Stage1OfficialCandidateRuntimeAPIV1" ]] || return 1
  local runtime_port
  runtime_port="$(awk -F= '$1 == "PFI_RUNTIME_API_PORT" {print $2}' "$marker")"
  [[ "$runtime_port" == <-> ]] || return 1
  (( runtime_port >= 1024 && runtime_port <= 65535 )) || return 1
  [[ "$runtime_port" != "$PORT" && "$runtime_port" != "$HEARTBEAT_PORT" && "$runtime_port" != "8501" && "$runtime_port" != "8502" && "$runtime_port" != "8766" ]] || return 1
  lsof -nP -a -p "$streamlit_pid" -iTCP:"$runtime_port" -sTCP:LISTEN 2>/dev/null | grep -q '127\.0\.0\.1:' || return 1
  curl -fsS "http://127.0.0.1:$runtime_port/health" >/dev/null || return 1
  printf "%s\n" "$runtime_port"
}

active_service_url_if_current_build() {
  local marker_project marker_pid marker_port marker_url marker_build marker_contract command cwd_path
  local marker_monitor_pid marker_heartbeat_port monitor_command monitor_cwd_path
  local marker_launcher_pid marker_process_group_id marker_runtime_api_port launcher_command launcher_cwd_path
  marker_project="$(marker_value PFI_ACTIVE_PROJECT_DIR || true)"
  marker_pid="$(marker_value PFI_ACTIVE_PID || true)"
  marker_port="$(marker_value PFI_ACTIVE_PORT || true)"
  marker_url="$(marker_value PFI_ACTIVE_URL || true)"
  marker_build="$(marker_value PFI_ACTIVE_BUILD_ID || true)"
  marker_contract="$(marker_value PFI_ACTIVE_UI_CONTRACT || true)"
  marker_monitor_pid="$(marker_value PFI_ACTIVE_MONITOR_PID || true)"
  marker_heartbeat_port="$(marker_value PFI_ACTIVE_HEARTBEAT_PORT || true)"
  marker_launcher_pid="$(marker_value PFI_ACTIVE_LAUNCHER_PID || true)"
  marker_process_group_id="$(marker_value PFI_ACTIVE_PROCESS_GROUP_ID || true)"
  marker_runtime_api_port="$(marker_value PFI_ACTIVE_RUNTIME_API_PORT || true)"
  [[ "$marker_project" == "$PROJECT_DIR" ]] || return 1
  [[ "$marker_build" == "$PFI_ACTIVE_BUILD_ID" ]] || return 1
  [[ "$marker_contract" == "$PFI_ACTIVE_UI_CONTRACT" ]] || return 1
  pfi_release_identity_marker_matches "$PFI_ACTIVE_SERVICE_FILE" || return 1
  pfi_stage1_candidate_active_marker_matches "$PFI_ACTIVE_SERVICE_FILE" || return 1
  [[ -n "$marker_pid" && -n "$marker_port" && -n "$marker_url" ]] || return 1
  kill -0 "$marker_pid" >/dev/null 2>&1 || return 1
  curl -s -o /dev/null -w "%{http_code}" "$marker_url/_stcore/health" | grep -q "200" || return 1
  command="$(ps -p "$marker_pid" -o command= 2>/dev/null || true)"
  cwd_path="$(process_cwd "$marker_pid")"
  [[ "$command" == *"$APP_ENTRY"* ]] || return 1
  [[ "$cwd_path" == "$PROJECT_DIR" || "$command" == *"$PROJECT_DIR"* ]] || return 1
  [[ "$marker_monitor_pid" == <-> && "$marker_heartbeat_port" == <-> ]] || return 1
  [[ "$marker_launcher_pid" == <-> ]] || return 1
  kill -0 "$marker_launcher_pid" >/dev/null 2>&1 || return 1
  launcher_command="$(ps -p "$marker_launcher_pid" -o command= 2>/dev/null || true)"
  launcher_cwd_path="$(process_cwd "$marker_launcher_pid")"
  [[ " $launcher_command " == *" $PROJECT_DIR/StartPFI.command "* ]] || return 1
  [[ "$launcher_cwd_path" == "$PROJECT_DIR" ]] || return 1
  if [[ "${PFI_STAGE1_CANDIDATE_MODE:-0}" == "1" ]]; then
    [[ "$marker_runtime_api_port" == <-> ]] || return 1
    [[ "$marker_process_group_id" == "$marker_launcher_pid" ]] || return 1
    [[ "$(ps -p "$marker_pid" -o pgid= 2>/dev/null | awk '{$1=$1; print}')" == "$marker_process_group_id" ]] || return 1
    [[ "$(ps -p "$marker_monitor_pid" -o pgid= 2>/dev/null | awk '{$1=$1; print}')" == "$marker_process_group_id" ]] || return 1
    lsof -nP -a -p "$marker_pid" -iTCP:"$marker_runtime_api_port" -sTCP:LISTEN 2>/dev/null | grep -q '127\.0\.0\.1:' || return 1
    curl -fsS "http://127.0.0.1:$marker_runtime_api_port/health" >/dev/null || return 1
  fi
  kill -0 "$marker_monitor_pid" >/dev/null 2>&1 || return 1
  monitor_command="$(ps -p "$marker_monitor_pid" -o command= 2>/dev/null || true)"
  monitor_cwd_path="$(process_cwd "$marker_monitor_pid")"
  [[ " $monitor_command " == *" $MONITOR_ENTRY "* ]] || return 1
  [[ " $monitor_command " == *" --port $marker_heartbeat_port "* ]] || return 1
  [[ " $monitor_command " == *" --streamlit-pid $marker_pid "* ]] || return 1
  [[ "$monitor_cwd_path" == "$PROJECT_DIR" || "$monitor_command" == *"$PROJECT_DIR"* ]] || return 1
  lsof -nP -a -p "$marker_monitor_pid" -iTCP:"$marker_heartbeat_port" -sTCP:LISTEN >/dev/null 2>&1 || return 1
  printf "%s\n" "$marker_url"
}

write_active_service_marker() {
  local pid="$1"
  local port="$2"
  local url="$3"
  local monitor_pid="$4"
  local heartbeat_port="$5"
  local runtime_api_port="${6:-}"
  local marker_tmp="${PFI_ACTIVE_SERVICE_FILE}.tmp.$$"
  if ! (
    umask 077
    {
      printf "PFI_ACTIVE_SCHEMA=PFIActiveServiceV1\n"
      printf "PFI_ACTIVE_PROJECT_DIR=%s\n" "$PROJECT_DIR"
      printf "PFI_ACTIVE_PID=%s\n" "$pid"
      printf "PFI_ACTIVE_PORT=%s\n" "$port"
      printf "PFI_ACTIVE_URL=%s\n" "$url"
      printf "PFI_ACTIVE_HEARTBEAT_PORT=%s\n" "$heartbeat_port"
      printf "PFI_ACTIVE_MONITOR_PID=%s\n" "$monitor_pid"
      printf "PFI_ACTIVE_LAUNCHER_PID=%s\n" "$$"
      if [[ "${PFI_STAGE1_CANDIDATE_MODE:-0}" == "1" ]]; then
        printf "PFI_ACTIVE_PROCESS_GROUP_ID=%s\n" "$CANDIDATE_PROCESS_GROUP_ID"
        printf "PFI_ACTIVE_RUNTIME_API_PORT=%s\n" "$runtime_api_port"
      fi
      printf "PFI_ACTIVE_CANDIDATE_MODE=%s\n" "${PFI_STAGE1_CANDIDATE_MODE:-0}"
      if [[ "${PFI_STAGE1_CANDIDATE_MODE:-0}" == "1" ]]; then
        printf "PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256=%s\n" "$PFI_CANDIDATE_APP_PATH_SHA256"
        printf "PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256=%s\n" "$PFI_CANDIDATE_EXECUTABLE_SHA256"
        printf "PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256=%s\n" "$PFI_CANDIDATE_BUNDLE_SHA256"
      fi
      pfi_release_identity_marker_lines
      printf "PFI_ACTIVE_STARTED_AT=%s\n" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    } > "$marker_tmp"
  ); then
    rm -f "$marker_tmp" >/dev/null 2>&1 || true
    return 1
  fi
  if ! chmod 0600 "$marker_tmp" || ! mv -f "$marker_tmp" "$PFI_ACTIVE_SERVICE_FILE"; then
    rm -f "$marker_tmp" >/dev/null 2>&1 || true
    return 1
  fi
}

monitor_service_ready() {
  local monitor_pid="$1"
  local streamlit_pid="$2"
  local heartbeat_port="$3"
  local command cwd_path
  kill -0 "$monitor_pid" >/dev/null 2>&1 || return 1
  command="$(ps -p "$monitor_pid" -o command= 2>/dev/null || true)"
  cwd_path="$(process_cwd "$monitor_pid")"
  [[ " $command " == *" $MONITOR_ENTRY "* ]] || return 1
  [[ " $command " == *" --port $heartbeat_port "* ]] || return 1
  [[ " $command " == *" --streamlit-pid $streamlit_pid "* ]] || return 1
  [[ "$cwd_path" == "$PROJECT_DIR" || "$command" == *"$PROJECT_DIR"* ]] || return 1
  lsof -nP -a -p "$monitor_pid" -iTCP:"$heartbeat_port" -sTCP:LISTEN >/dev/null 2>&1
}

open_existing_service() {
  local existing_url
  if existing_url="$(active_service_url_if_current_build)"; then
    OPEN_URL="$existing_url/?$PFI_VERSION_QUERY"
    echo "PFI 当前 build 服务已在运行：$existing_url。复用现有服务。"
    pfi_open_url_if_enabled "$OPEN_URL"
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

LOCK_DIR="$LOG_DIR/pfi_launch.lockdir"
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
STREAMLIT_PID=""
MONITOR_PID=""

stop_launcher_children() {
  if [[ "$STREAMLIT_PID" == <-> ]]; then
    kill "$STREAMLIT_PID" >/dev/null 2>&1 || true
  fi
  if [[ "$MONITOR_PID" == <-> ]]; then
    kill "$MONITOR_PID" >/dev/null 2>&1 || true
  fi
  if [[ "$STREAMLIT_PID" == <-> ]]; then
    wait "$STREAMLIT_PID" >/dev/null 2>&1 || true
  fi
  if [[ "$MONITOR_PID" == <-> ]]; then
    wait "$MONITOR_PID" >/dev/null 2>&1 || true
  fi
  STREAMLIT_PID=""
  MONITOR_PID=""
}

cleanup_launcher_on_exit() {
  local exit_status=$?
  trap - EXIT
  stop_launcher_children
  rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true
  exit "$exit_status"
}

trap cleanup_launcher_on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

if candidate_finalization_in_progress; then
  echo "PFI isolated candidate finalization is already in progress; refusing relaunch."
  close_launcher_terminal
  exit 1
fi

if open_existing_service; then
  close_launcher_terminal
  exit 0
fi

PORT="${PFI_STREAMLIT_PORT:-8501}"
HEARTBEAT_PORT="${PFI_HEARTBEAT_PORT:-$((PORT + 1000))}"
if [[ "${PFI_STAGE1_CANDIDATE_MODE:-0}" == "1" ]]; then
  if lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1 || \
    lsof -iTCP:"$HEARTBEAT_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "PFI isolated candidate port became occupied before launch; refusing to scan or reuse another port."
    close_launcher_terminal
    exit 1
  fi
else
  while lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; do
    PORT=$((PORT + 1))
  done
  HEARTBEAT_PORT=$((PORT + 1000))
  while lsof -iTCP:"$HEARTBEAT_PORT" -sTCP:LISTEN >/dev/null 2>&1; do
    HEARTBEAT_PORT=$((HEARTBEAT_PORT + 1))
  done
fi

URL="http://localhost:$PORT"
OPEN_URL="$URL/?$PFI_VERSION_QUERY"
HEARTBEAT_TIMEOUT="${PFI_HEARTBEAT_TIMEOUT:-120}"
export PFI_HEARTBEAT_URL="http://127.0.0.1:$HEARTBEAT_PORT/heartbeat"
export PFI_V021_RUNTIME_API_PORT=0
echo "正在启动 PFI：$URL"
echo "研究和回测专用；禁止实盘自动下单、券商提交、支付或无人值守执行。"
if candidate_finalization_in_progress; then
  echo "PFI isolated candidate finalization started before child launch; refusing launch."
  close_launcher_terminal
  exit 1
fi
"$PYTHON_BIN" "$PROJECT_DIR/scripts/v025/run_streamlit_with_release_cache.py" run "$APP_ENTRY" \
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
"$PYTHON_BIN" "$PROJECT_DIR/src/pfi_os/system/shutdown_monitor.py" --port "$HEARTBEAT_PORT" --streamlit-pid "$STREAMLIT_PID" --terminal-tty "$CURRENT_TTY" --timeout "$HEARTBEAT_TIMEOUT" &
MONITOR_PID=$!

MONITOR_READY=0
for _ in {1..50}; do
  if monitor_service_ready "$MONITOR_PID" "$STREAMLIT_PID" "$HEARTBEAT_PORT"; then
    MONITOR_READY=1
    break
  fi
  if ! kill -0 "$MONITOR_PID" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done
if [[ "$MONITOR_READY" != "1" ]]; then
  echo "PFI shutdown monitor failed to become ready; stopping this launch."
  stop_launcher_children
  close_launcher_terminal
  exit 1
fi
if candidate_finalization_in_progress; then
  echo "PFI isolated candidate finalization started during child launch; stopping this launch."
  stop_launcher_children
  close_launcher_terminal
  exit 1
fi

echo "正在等待 PFI 就绪..."
READY=0
for _ in {1..60}; do
  if ! kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; then
    echo "PFI 启动失败。请查看运行日志。"
    stop_launcher_children
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
  stop_launcher_children
  close_launcher_terminal
  exit 1
fi

echo "PFI 已就绪，正在打开：$OPEN_URL"
if candidate_finalization_in_progress; then
  echo "PFI isolated candidate finalization started before marker publication; stopping this launch."
  stop_launcher_children
  close_launcher_terminal
  exit 1
fi
RUNTIME_API_PORT=""
if [[ "${PFI_STAGE1_CANDIDATE_MODE:-0}" == "1" ]]; then
  for _ in {1..50}; do
    RUNTIME_API_PORT="$(candidate_runtime_api_port "$STREAMLIT_PID" || true)"
    [[ "$RUNTIME_API_PORT" == <-> ]] && break
    sleep 0.1
  done
  if [[ "$RUNTIME_API_PORT" != <-> ]]; then
    echo "PFI isolated candidate runtime API identity could not be proven; stopping this launch."
    stop_launcher_children
    close_launcher_terminal
    exit 1
  fi
fi
if ! write_active_service_marker "$STREAMLIT_PID" "$PORT" "$URL" "$MONITOR_PID" "$HEARTBEAT_PORT" "$RUNTIME_API_PORT"; then
  echo "PFI active marker could not be published; stopping this launch."
  stop_launcher_children
  close_launcher_terminal
  exit 1
fi
pfi_open_url_if_enabled "$OPEN_URL"

wait "$STREAMLIT_PID" >/dev/null 2>&1 || true
STREAMLIT_PID=""
if [[ "$MONITOR_PID" == <-> ]]; then
  kill "$MONITOR_PID" >/dev/null 2>&1 || true
  wait "$MONITOR_PID" >/dev/null 2>&1 || true
fi
MONITOR_PID=""
close_launcher_terminal
exit 0
