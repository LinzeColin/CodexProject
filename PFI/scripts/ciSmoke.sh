#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--allow-heavy-smoke" ]]; then
  export PFI_ALLOW_HEAVY_SMOKE=1
  shift
fi

if [[ "${PFI_ALLOW_HEAVY_SMOKE:-}" != "1" ]]; then
  cat >&2 <<'EOF'
PFI CI SmokeTest is blocked by default for local runs.
Use scripts/devReadyCheck.sh --summary-json for normal development.
Run deliberately only for CI or release gates:
  PFI_ALLOW_HEAVY_SMOKE=1 scripts/ciSmoke.sh
EOF
  exit 64
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [[ -n "${PYTHONPATH:-}" ]]; then
  export PYTHONPATH="$PROJECT_DIR/src:$PYTHONPATH"
else
  export PYTHONPATH="$PROJECT_DIR/src"
fi
export PYTHONDONTWRITEBYTECODE=1

PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

"$PYTHON_BIN" -m compileall -q src
"$PYTHON_BIN" -m pytest \
  tests/test_workspace_systems.py \
  tests/test_workspace_shell.py \
  tests/test_system_permissions.py \
  tests/test_system_orchestrator.py \
  tests/test_research_bus_audit.py \
  tests/test_research_bus_api.py \
  -q

"$PYTHON_BIN" -m compileall -q \
  systems/finance_ledger/source/src \
  systems/finance_ledger/source/scripts

PYTHONPATH="$PROJECT_DIR/systems/finance_ledger/source/src" \
"$PYTHON_BIN" -m pytest \
  systems/finance_ledger/source/tests/test_bill_import.py \
  systems/finance_ledger/source/tests/test_classifier.py \
  systems/finance_ledger/source/tests/test_reconciliation.py \
  -q

"$PYTHON_BIN" -m compileall -q \
  systems/industry_research/source/src \
  systems/industry_research/source/doctor.py

PYTHONPATH="$PROJECT_DIR/systems/industry_research/source" \
"$PYTHON_BIN" -m pytest \
  systems/industry_research/source/tests/test_advice_engine.py \
  systems/industry_research/source/tests/test_backtesting.py \
  systems/industry_research/source/tests/test_reconciliation.py \
  systems/industry_research/source/tests/test_workflow_layer.py \
  -q

PYTHONPATH="$PROJECT_DIR/systems/industry_research/source" \
"$PYTHON_BIN" -m src.cli --help >/dev/null

"$PYTHON_BIN" -m compileall -q \
  systems/policy_intelligence/source/src

bash -n systems/policy_intelligence/source/scripts/run_policy_report.sh

PYTHONPATH="$PROJECT_DIR/systems/policy_intelligence/source/src" \
"$PYTHON_BIN" -m pytest \
  systems/policy_intelligence/source/tests/test_registry.py \
  systems/policy_intelligence/source/tests/test_quality_gates.py \
  systems/policy_intelligence/source/tests/test_readiness.py \
  systems/policy_intelligence/source/tests/test_automation_readiness.py \
  -q

PYTHONPATH="$PROJECT_DIR/systems/policy_intelligence/source/src" \
"$PYTHON_BIN" -m source_registry --help >/dev/null
