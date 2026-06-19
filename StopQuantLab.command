#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"

stop_pid_if_quantlab() {
  local pid="$1"
  local command
  command="$(ps -p "$pid" -o command= 2>/dev/null || true)"
  if [[ "$command" == *"$PROJECT_DIR"* && "$command" == *"src/quantlab/app/streamlit_app.py"* ]]; then
    echo "Stopping QuantLab service pid $pid"
    kill "$pid" >/dev/null 2>&1 || true
  else
    echo "Skipping non-QuantLab process on monitored port: pid $pid"
  fi
}

for PORT in {8501..8510}; do
  PIDS=$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$PIDS" ]; then
    echo "Checking service on port $PORT"
    for PID in ${(f)PIDS}; do
      stop_pid_if_quantlab "$PID"
    done
  fi
done

echo "QuantLab stop command completed."
