#!/usr/bin/env zsh
set -euo pipefail

FOUND=0
for PORT in {8501..8510}; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" || true)
  if [ "$CODE" = "200" ]; then
    FOUND=1
    echo "QuantLab running: http://localhost:$PORT"
    PIDS=$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
      echo "Process id: $PIDS"
    fi
  fi
done

if [ "$FOUND" = "0" ]; then
  echo "QuantLab is not running on ports 8501-8510."
fi
