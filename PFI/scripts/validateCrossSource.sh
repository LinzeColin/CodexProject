#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

echo "Validating US cross-source data when enough providers are configured..."
if PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pfi_os.examples.validate_cross_source --market US --symbol AAPL --start 2024-01-01 --end 2024-01-31; then
  echo "US cross-source validation completed."
else
  exit_code=$?
  if [[ "$exit_code" == "3" ]]; then
    echo "US cross-source validation skipped because only one provider is configured."
  else
    exit "$exit_code"
  fi
fi

echo "Validating CN cross-source data when enough providers are configured..."
    if PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pfi_os.examples.validate_cross_source --market CN --symbol 600000 --start 2024-01-01 --end 2024-01-31; then
  echo "CN cross-source validation completed."
else
  exit_code=$?
  if [[ "$exit_code" == "3" ]]; then
    echo "CN cross-source validation skipped because only one provider is configured."
  else
    exit "$exit_code"
  fi
fi
