#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"

process_cwd() {
  local pid="$1"
  lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | awk '/^n/ {sub(/^n/, ""); print; exit}'
}

FOUND=0
for PORT in {8501..8510}; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/_stcore/health" || true)
  if [ "$CODE" = "200" ]; then
    PIDS=$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)
    for PID in ${(f)PIDS}; do
      COMMAND="$(ps -p "$PID" -o command= 2>/dev/null || true)"
      CWD_PATH="$(process_cwd "$PID")"
      if [[ "$COMMAND" == *"src/pfi_os/app/streamlit_app.py"* && ( "$COMMAND" == *"$PROJECT_DIR"* || "$CWD_PATH" == "$PROJECT_DIR" ) ]]; then
        FOUND=1
        echo "PFI 正在运行：http://localhost:$PORT"
        echo "进程 id: $PID"
      fi
    done
  fi
done

if [ "$FOUND" = "0" ]; then
  echo "PFI 未在端口 8501-8510 运行。"
fi
