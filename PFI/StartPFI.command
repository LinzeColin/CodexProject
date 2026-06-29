#!/bin/zsh
set -euo pipefail
setopt NO_BG_NICE

PROJECT_DIR="${0:A:h}"
cd "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/data/cache"
LOG_FILE="$PROJECT_DIR/data/cache/pfi_macos_app.log"
exec >> "$LOG_FILE" 2>&1
echo "==== PFI launch $(date -u +"%Y-%m-%dT%H:%M:%SZ") pid=$$ ===="
PFI_VERSION_QUERY="pfi_app_version=0.2.3&pfi_build=20260629-stage1&pfi_ui_contract=PFI-V023-STAGE1-APP-ENTRY-BUNDLE-CONSISTENCY"

process_cwd() {
  local pid="$1"
  lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | awk '/^n/ {sub(/^n/, ""); print; exit}'
}

open_existing_service() {
  local existing_port pids pid command cwd_path
  for EXISTING_PORT in {8501..8510}; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$EXISTING_PORT/_stcore/health" | grep -q "200"; then
      pids="$(lsof -tiTCP:"$EXISTING_PORT" -sTCP:LISTEN 2>/dev/null || true)"
      for pid in ${(f)pids}; do
        command="$(ps -p "$pid" -o command= 2>/dev/null || true)"
        cwd_path="$(process_cwd "$pid")"
        if [[ "$command" == *"src/pfi_os/app/streamlit_app.py"* && ( "$command" == *"$PROJECT_DIR"* || "$cwd_path" == "$PROJECT_DIR" ) ]]; then
          EXISTING_URL="http://localhost:$EXISTING_PORT"
          OPEN_URL="$EXISTING_URL/?$PFI_VERSION_QUERY"
          echo "PFI 当前项目服务已在运行：$EXISTING_URL。复用现有服务。"
          open "$OPEN_URL" >/dev/null 2>&1
          return 0
        fi
      done
      echo "端口 $EXISTING_PORT 上有其他健康服务，但不是当前 PFI 项目。已忽略。"
    fi
  done
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
open "$OPEN_URL" >/dev/null 2>&1

wait "$STREAMLIT_PID" >/dev/null 2>&1 || true
kill "$MONITOR_PID" >/dev/null 2>&1 || true
close_launcher_terminal
exit 0
