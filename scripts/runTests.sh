#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

export PYTHONPATH="$PROJECT_DIR/src"
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND="${MPLBACKEND:-Agg}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/private/tmp/quantlab-mplconfig}"
mkdir -p "$MPLCONFIGDIR"
source "$PROJECT_DIR/scripts/quantlabRuntime.sh"
PYTHON_BIN="$(quantlab_ensure_app_python "$PROJECT_DIR")"
if ! "$PYTHON_BIN" -m pytest --version >/dev/null 2>&1; then
  echo "Installing verification test dependencies..."
  "$PYTHON_BIN" -m pip install -e "${PROJECT_DIR}[test]"
fi
"$PYTHON_BIN" -m pytest -q -p no:cacheprovider
