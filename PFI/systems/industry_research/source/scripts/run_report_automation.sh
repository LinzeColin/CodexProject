#!/usr/bin/env bash
set -euo pipefail

REPORT_KIND="${1:-}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/data/report_artifacts/automation_logs"
TODAY="$(TZ=Australia/Sydney date +%F)"
STAMP="$(TZ=Australia/Sydney date +%Y-%m-%d_%H%M%S)"
AUTOMATION_ID="${AI_AUTOMATION_ID:-manual}"
LOG_FILE="$LOG_DIR/${AUTOMATION_ID}_${REPORT_KIND:-unknown}_${TODAY}_${STAMP}.log"

mkdir -p "$LOG_DIR"
exec >> "$LOG_FILE" 2>&1

cd "$ROOT_DIR"

export AI_RESEARCH_POLICY_REFRESH="${AI_RESEARCH_POLICY_REFRESH:-1}"
export AI_RESEARCH_POLICY_TIMEOUT_SECONDS="${AI_RESEARCH_POLICY_TIMEOUT_SECONDS:-240}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl-ai-research}"
mkdir -p "$MPLCONFIGDIR"

echo "automation_report_kind=$REPORT_KIND"
echo "automation_id=$AUTOMATION_ID"
echo "today=$TODAY"
echo "timezone=Australia/Sydney"
echo "root=$ROOT_DIR"
echo "log_file=$LOG_FILE"
echo "policy_refresh=$AI_RESEARCH_POLICY_REFRESH"
echo "policy_timeout_seconds=$AI_RESEARCH_POLICY_TIMEOUT_SECONDS"
echo "mplconfigdir=$MPLCONFIGDIR"

choose_python() {
  if [[ -n "${AI_RESEARCH_PYTHON:-}" ]]; then
    printf '%s\n' "$AI_RESEARCH_PYTHON"
    return 0
  fi
  local candidates=(
    "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
    "/usr/bin/python3"
    "python3"
  )
  local candidate
  for candidate in "${candidates[@]}"; do
    if ! command -v "$candidate" >/dev/null 2>&1 && [[ ! -x "$candidate" ]]; then
      continue
    fi
    if "$candidate" - <<'PY' >/dev/null 2>&1
import certifi
import matplotlib
import reportlab
PY
    then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(choose_python)"
echo "python=$PYTHON_BIN"
"$PYTHON_BIN" - <<'PY'
import certifi
import matplotlib
import reportlab
print("runtime_dependencies=ok")
PY

if command -v lsof >/dev/null 2>&1; then
  lsof -nP -iTCP:11111 -sTCP:LISTEN || true
fi

"$PYTHON_BIN" -m src.cli automation-health --date "$TODAY" --no-quality-check --preflight
"$PYTHON_BIN" -m src.cli alipay-update-status --start-date "$TODAY" --end-date "$TODAY"
"$PYTHON_BIN" -m src.cli pfi_os-refresh --date "$TODAY"

case "$REPORT_KIND" in
  monday_pre_open)
    "$PYTHON_BIN" -m src.cli generate-weekly --date "$TODAY" --session monday_pre_open
    ;;
  pre_open|midday|post_close)
    "$PYTHON_BIN" -m src.cli generate-daily --date "$TODAY" --session "$REPORT_KIND"
    ;;
  kline)
    "$PYTHON_BIN" -m src.cli generate-kline --date "$TODAY"
    ;;
  friday_post_close)
    "$PYTHON_BIN" -m src.cli generate-weekly --date "$TODAY" --session friday_post_close
    ;;
  *)
    echo "Unsupported report kind: $REPORT_KIND" >&2
    exit 2
    ;;
esac

"$PYTHON_BIN" -m src.cli generate-due-reports --date "$TODAY"
"$PYTHON_BIN" -m src.cli automation-health --date "$TODAY"
if "$PYTHON_BIN" -m src.cli automation-health --date "$TODAY" --no-quality-check --require-execution-ready; then
  echo "execution_readiness=ready"
else
  echo "execution_readiness=blocked"
fi
"$PYTHON_BIN" -m src.cli report-week-status --date "$TODAY"
