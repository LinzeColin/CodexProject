#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

echo "Validating Yahoo Finance US daily data..."
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pfi_os.examples.fetch_real_data --provider "Yahoo Finance" --symbol AAPL --market US --interval 1d --start 2024-01-01 --end 2024-01-31

echo "Validating AKShare CN daily data..."
akshare_ok=0
for symbol in 600000 000001 000002; do
  for attempt in 1 2 3; do
    echo "AKShare attempt ${attempt}: ${symbol}"
    if PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pfi_os.examples.fetch_real_data --provider AKShare --symbol "$symbol" --market CN --interval 1d --start 2024-01-01 --end 2024-01-31; then
      akshare_ok=1
      break 2
    fi
    sleep 2
  done
done

if [[ "$akshare_ok" != "1" ]]; then
  echo "AKShare validation failed after retries. This usually means Eastmoney/AKShare is temporarily unreachable."
  exit 2
fi

echo "Real-data validation completed."
