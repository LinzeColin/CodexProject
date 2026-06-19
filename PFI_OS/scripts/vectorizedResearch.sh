#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/pfi_os-pycache}"
export PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

PYTHON_BIN="${PFI_PYTHON:-${PFI_PYTHON:-.venv/bin/python}}"
"$PYTHON_BIN" -m pfi_os.examples.vectorized_research "$@"
