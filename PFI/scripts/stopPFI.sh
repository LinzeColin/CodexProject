#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
LOCK_DIR="$PROJECT_DIR/data/cache/pfi_launch.lockdir"

process_cwd() {
  local pid="$1"
  lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | awk '/^n/ {sub(/^n/, ""); print; exit}'
}

stop_pid_if_pfi() {
  local pid="$1"
  local command cwd_path
  command="$(ps -p "$pid" -o command= 2>/dev/null || true)"
  cwd_path="$(process_cwd "$pid")"
  if [[ "$command" == *"src/pfi_os/app/streamlit_app.py"* && ( "$command" == *"$PROJECT_DIR"* || "$cwd_path" == "$PROJECT_DIR" ) ]]; then
    echo "正在停止 PFI 服务 pid $pid"
    kill "$pid" >/dev/null 2>&1 || true
  else
    echo "已跳过监控端口上的非 PFI 进程：pid $pid"
  fi
}

for PORT in {8501..8510}; do
  PIDS=$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$PIDS" ]; then
    echo "Checking service on port $PORT"
    for PID in ${(f)PIDS}; do
      stop_pid_if_pfi "$PID"
    done
  fi
done

LAUNCHER_PIDS="$(pgrep -f "$PROJECT_DIR/StartPFI.command" 2>/dev/null || true)"
for PID in ${(f)LAUNCHER_PIDS}; do
  if [[ -n "$PID" && "$PID" != "$$" ]]; then
    echo "正在停止 PFI 启动器 pid $PID"
    kill "$PID" >/dev/null 2>&1 || true
  fi
done

rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true
echo "PFI 停止命令已完成。"
