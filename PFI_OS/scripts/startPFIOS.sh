#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

source "$PROJECT_DIR/scripts/pfiRuntime.sh"

export PYTHONPATH="$PROJECT_DIR/src"
export PFI_UI_V2="${PFI_UI_V2:-1}"
PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"
LOG_DIR="$PROJECT_DIR/data/cache"
LOG_FILE="$LOG_DIR/pfi_os_streamlit.log"
mkdir -p "$LOG_DIR"

process_cwd() {
  local pid="$1"
  lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | awk '/^n/ {sub(/^n/, ""); print; exit}'
}

service_url_if_current_project() {
  local port pids pid command cwd_path
  for port in {8501..8510}; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/_stcore/health" | grep -q "200"; then
      pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
      for pid in ${(f)pids}; do
        command="$(ps -p "$pid" -o command= 2>/dev/null || true)"
        cwd_path="$(process_cwd "$pid")"
        if [[ "$command" == *"src/pfi_os/app/streamlit_app.py"* && ( "$command" == *"$PROJECT_DIR"* || "$cwd_path" == "$PROJECT_DIR" ) ]]; then
          printf "http://localhost:%s\n" "$port"
          return 0
        fi
      done
    fi
  done
  return 1
}

if URL="$(service_url_if_current_project)"; then
  echo "PFI OS 已在运行：$URL"
  if [[ -t 1 && "${PFI_START_OPEN_BROWSER:-1}" == "1" ]]; then
    open "$URL" >/dev/null 2>&1 || true
  fi
  exit 0
fi

PORT=8501
while lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  PORT=$((PORT + 1))
done

URL="http://localhost:$PORT"
echo "正在启动 PFI OS：$URL"
echo "研究和回测专用；禁止实盘自动下单、券商提交、支付或无人值守执行。"

STREAMLIT_ARGS=(
  -m streamlit run src/pfi_os/app/streamlit_app.py
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

"$PYTHON_BIN" "${STREAMLIT_ARGS[@]}" > "$LOG_FILE" 2>&1 &
STREAMLIT_PID=$!

READY=0
for _ in {1..60}; do
  if ! kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; then
    echo "PFI OS 启动失败。日志：$LOG_FILE" >&2
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
  echo "PFI OS 在 60 秒内未就绪，已停止本次启动。日志：$LOG_FILE" >&2
  exit 1
fi

echo "PFI OS 已就绪：$URL"
echo "运行日志：$LOG_FILE"
if [[ -t 1 && "${PFI_START_OPEN_BROWSER:-1}" == "1" ]]; then
  open "$URL" >/dev/null 2>&1 || true
else
  echo "如需打开界面，请访问：$URL"
fi
