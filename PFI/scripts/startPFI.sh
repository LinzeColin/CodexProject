#!/usr/bin/env zsh
set -euo pipefail
setopt NO_BG_NICE

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

source "$PROJECT_DIR/scripts/pfiRuntime.sh"

export PYTHONPATH="$PROJECT_DIR/src"
export PFI_UI_V2="${PFI_UI_V2:-1}"
PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"
LOG_DIR="$PROJECT_DIR/data/cache"
LOG_FILE="$LOG_DIR/pfi_streamlit.log"
mkdir -p "$LOG_DIR"
source "$PROJECT_DIR/scripts/pfiReleaseIdentity.sh"
pfi_release_identity_init "$PROJECT_DIR"
pfi_release_cache_key_init "$PROJECT_DIR" "$PYTHON_BIN"
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
  pfi_release_identity_marker_matches "$PFI_ACTIVE_SERVICE_FILE" || return 1
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
    pfi_release_identity_marker_lines
    printf "PFI_ACTIVE_STARTED_AT=%s\n" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  } > "$PFI_ACTIVE_SERVICE_FILE"
}

service_url_if_current_project() {
  if active_service_url_if_current_build; then
    return 0
  fi
  return 1
}

if URL="$(service_url_if_current_project)"; then
  OPEN_URL="$URL/?$PFI_VERSION_QUERY"
  echo "PFI 已在运行：$URL"
  if [[ -t 1 && "${PFI_START_OPEN_BROWSER:-1}" == "1" ]]; then
    open "$OPEN_URL" >/dev/null 2>&1 || true
  fi
  exit 0
fi

PORT=8501
while lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  PORT=$((PORT + 1))
done

URL="http://localhost:$PORT"
OPEN_URL="$URL/?$PFI_VERSION_QUERY"
echo "正在启动 PFI：$URL"
echo "研究和回测专用；禁止实盘自动下单、券商提交、支付或无人值守执行。"
export PFI_V021_RUNTIME_API_PORT=0

STREAMLIT_ARGS=(
  "$PROJECT_DIR/scripts/v025/run_streamlit_with_release_cache.py" run src/pfi_os/app/streamlit_app.py
  --server.port "$PORT" \
  --server.address 127.0.0.1 \
  --server.headless true \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false
)

if [[ "${PFI_START_FOREGROUND:-0}" == "1" ]]; then
  "$PYTHON_BIN" "${STREAMLIT_ARGS[@]}"
  exit $?
fi

STREAMLIT_PID="$("$PYTHON_BIN" - "$LOG_FILE" "${STREAMLIT_ARGS[@]}" <<'PY'
import os
import subprocess
import sys

log_path = sys.argv[1]
args = [sys.executable, *sys.argv[2:]]
log_file = open(log_path, "ab", buffering=0)
process = subprocess.Popen(
    args,
    cwd=os.getcwd(),
    stdin=subprocess.DEVNULL,
    stdout=log_file,
    stderr=subprocess.STDOUT,
    start_new_session=True,
    close_fds=True,
)
print(process.pid)
PY
)"

READY=0
for _ in {1..60}; do
  if ! kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; then
    echo "PFI 启动失败。日志：$LOG_FILE" >&2
    exit 1
  fi
  if curl -s -o /dev/null -w "%{http_code}" "$URL/_stcore/health" | grep -q "200"; then
    READY=1
    break
  fi
  sleep 1
done

if [[ "$READY" != "1" ]]; then
  kill "$STREAMLIT_PID" >/dev/null 2>&1 || true
  echo "PFI 在 60 秒内未就绪，已停止本次启动。日志：$LOG_FILE" >&2
  exit 1
fi

echo "PFI 已就绪：$URL"
echo "运行日志：$LOG_FILE"
write_active_service_marker "$STREAMLIT_PID" "$PORT" "$URL"
if [[ -t 1 && "${PFI_START_OPEN_BROWSER:-1}" == "1" ]]; then
  open "$OPEN_URL" >/dev/null 2>&1 || true
else
  echo "如需打开界面，请访问：$URL"
fi
