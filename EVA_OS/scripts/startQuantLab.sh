#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

source "$PROJECT_DIR/scripts/quantlabRuntime.sh"

export PYTHONPATH="$PROJECT_DIR/src"
PYTHON_BIN="$(quantlab_ensure_app_python "$PROJECT_DIR")"

for EXISTING_PORT in {8501..8510}; do
  if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$EXISTING_PORT/_stcore/health" | grep -q "200"; then
    URL="http://localhost:$EXISTING_PORT"
    echo "QuantLab is already running at $URL"
    echo "No browser opened. Copy the URL above if needed."
    exit 0
  fi
done

PORT=8501
while lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  PORT=$((PORT + 1))
done

URL="http://localhost:$PORT"
echo "Starting QuantLab at $URL"
echo "Research only. Live trading and real order submission are prohibited."
echo "No browser opened. Copy the URL above if needed."
"$PYTHON_BIN" -m streamlit run src/quantlab/app/streamlit_app.py \
  --server.port "$PORT" \
  --server.address 127.0.0.1 \
  --server.headless true \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false
