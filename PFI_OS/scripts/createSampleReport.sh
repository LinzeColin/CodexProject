#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pfi_os.examples.run_sample_backtest
