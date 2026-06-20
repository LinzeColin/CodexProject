#!/usr/bin/env zsh
set -euo pipefail

FOUND=0
for PORT in {8501..8510}; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" || true)
  if [ "$CODE" = "200" ]; then
    FOUND=1
    echo "PFI OS 正在运行：http://localhost:$PORT"
    PIDS=$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
      echo "进程 id: $PIDS"
    fi
  fi
done

if [ "$FOUND" = "0" ]; then
  echo "PFI OS 未在端口 8501-8510 运行。"
fi
