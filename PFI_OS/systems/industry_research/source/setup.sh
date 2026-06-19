#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

REPORT_DATE="${1:-$(TZ=Australia/Sydney date +%F)}"

mkdir -p \
  data/report_artifacts/system_audit \
  data/report_artifacts/automation_logs \
  data/report_artifacts/automation_runtime/matplotlib

export MPLCONFIGDIR="${MPLCONFIGDIR:-$ROOT_DIR/data/report_artifacts/automation_runtime/matplotlib}"
mkdir -p "$MPLCONFIGDIR"

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
echo "root=$ROOT_DIR"
echo "date=$REPORT_DATE"
echo "python=$PYTHON_BIN"
echo "mplconfigdir=$MPLCONFIGDIR"

"$PYTHON_BIN" doctor.py --date "$REPORT_DATE" --json

cat <<'EOF'

Next commands:
  make doctor DATE=YYYY-MM-DD
  make audit-stack DATE=YYYY-MM-DD
  make test-monitoring
  make test

setup.sh is intentionally non-networked. It does not install packages, open apps, refresh data, or generate trading actions.
EOF
