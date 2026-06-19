#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

NETWORK_MODE=0
PY_ARGS=()
for arg in "$@"; do
  if [[ "$arg" == "--network" ]]; then
    NETWORK_MODE=1
  else
    PY_ARGS+=("$arg")
  fi
done

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pfi_os.examples.daily_check "${PY_ARGS[@]}"

if [[ "$NETWORK_MODE" == "1" ]]; then
  echo ""
  echo "Checking Moomoo quote-only environment..."
  scripts/checkMoomoo.sh || true

  echo ""
  echo "Running network validation..."
  if scripts/validateRealData.sh; then
    echo "Network validation completed."
  else
    echo "Network validation reported provider failures. Continuing daily check so other diagnostics can still run."
  fi

  echo ""
  echo "Running cross-source validation when enough providers are configured..."
  if scripts/validateCrossSource.sh; then
    echo "Cross-source validation completed."
  else
    echo "Cross-source validation reported provider failures or insufficient live sources. Review the output above."
  fi
fi
