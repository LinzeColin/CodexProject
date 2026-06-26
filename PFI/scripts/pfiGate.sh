#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

MODE="${1:-target}"
export PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
source "$PROJECT_DIR/scripts/pfiRuntime.sh"
PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"

if ! "$PYTHON_BIN" -m pytest --version >/dev/null 2>&1; then
  echo "PFI gate dependency pytest is missing." >&2
  echo "Run scripts/installLockedEnv.sh once, then retry." >&2
  exit 67
fi

case "$MODE" in
  fast)
    "$PYTHON_BIN" -m compileall -q src
    "$PYTHON_BIN" -m pytest tests/test_pfi_product_contracts.py tests/contract/test_pfi_reproducible_env.py -q
    scripts/secretScan.sh
    ;;
  target)
    "$PYTHON_BIN" -m pytest \
      tests/test_pfi_product_contracts.py \
      tests/contract/test_pfi_reproducible_env.py \
      tests/contract/test_phase_a_homepage_ingestion.py \
      tests/contract/test_pfi_web_shell_contract.py \
      tests/contract/test_pfi005_gate2_shell_acceptance.py \
      tests/contract/test_pfi006_markets_vertical_acceptance.py \
      tests/contract/test_pfi007_research_policy_vertical_acceptance.py \
      tests/contract/test_pfi008_portfolio_vertical_acceptance.py \
      tests/contract/test_pfi009_strategy_vertical_acceptance.py \
      tests/contract/test_pfi010_minute_fast_path.py \
      tests/contract/test_pfi011_local_llm_deep_path.py \
      tests/contract/test_pfi012_mvp_release_gate.py \
      tests/e2e/test_pfi_web_shell_static_flow.py \
      -q
    scripts/secretScan.sh
    git diff --check
    ;;
  full)
    scripts/runTests.sh
    scripts/secretScan.sh
    ;;
  release)
    PFI_ALLOW_HEAVY_SMOKE="${PFI_ALLOW_HEAVY_SMOKE:-1}" scripts/finalAcceptanceCheck.sh
    scripts/secretScan.sh
    ;;
  *)
    echo "Usage: scripts/pfiGate.sh [fast|target|full|release]" >&2
    exit 64
    ;;
esac
