#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

export PYTHONPATH="$PROJECT_DIR/src"
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND="${MPLBACKEND:-Agg}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/private/tmp/pfi_os-mplconfig}"
mkdir -p "$MPLCONFIGDIR"
source "$PROJECT_DIR/scripts/pfiRuntime.sh"
PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"
if ! "$PYTHON_BIN" -m pytest --version >/dev/null 2>&1; then
  echo "PFI test dependency pytest is missing." >&2
  echo "Run scripts/installLockedEnv.sh once, then retry." >&2
  exit 67
fi
"$PYTHON_BIN" -m pytest -q -p no:cacheprovider
