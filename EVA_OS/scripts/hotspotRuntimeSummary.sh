#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/quantlab-pycache}"
export PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

PYTHON_BIN="${QUANTLAB_PYTHON:-${EVA_PYTHON:-.venv/bin/python}}"
"$PYTHON_BIN" -m quantlab.examples.hotspot_runtime_summary "$@"
