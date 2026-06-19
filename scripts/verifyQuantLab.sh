#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/quantlab-pycache}"
export QUANTLAB_REPORT_DIR="${QUANTLAB_REPORT_DIR:-/private/tmp/quantlab-report-test}"
export MPLBACKEND="${MPLBACKEND:-Agg}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/private/tmp/quantlab-mplconfig}"
mkdir -p "$PYTHONPYCACHEPREFIX" "$QUANTLAB_REPORT_DIR" "$MPLCONFIGDIR"
source "$PROJECT_DIR/scripts/quantlabRuntime.sh"
PYTHON_BIN="$(quantlab_ensure_app_python "$PROJECT_DIR")"

ensure_test_deps() {
  if "$PYTHON_BIN" -m pytest --version >/dev/null 2>&1; then
    return
  fi
  echo "Installing verification test dependencies..."
  "$PYTHON_BIN" -m pip install -e "${PROJECT_DIR}[test]"
}

echo "Checking shell scripts..."
zsh -n StartQuantLab.command StopQuantLab.command scripts/quantlabRuntime.sh scripts/startQuantLab.sh scripts/stopQuantLab.sh scripts/installMacAppLaunchers.sh scripts/statusQuantLab.sh scripts/verifyQuantLab.sh scripts/finalAcceptanceCheck.sh scripts/createSampleReport.sh scripts/setupEnv.sh scripts/validateRealData.sh scripts/validateCrossSource.sh scripts/checkMoomoo.sh scripts/dailyCheck.sh scripts/runTests.sh scripts/cleanCache.sh scripts/cleanReportJunk.sh scripts/openReports.sh scripts/auditQuantLabIntegration.sh scripts/tokenRoiLedger.sh scripts/commandCenter.sh scripts/reportDecisionSupport.sh scripts/reportGapTasks.sh scripts/validationPriorityPlan.sh scripts/runValidationTask.sh scripts/vectorizedResearch.sh scripts/hotspotRuntimeSummary.sh

echo "Checking Python syntax..."
"$PYTHON_BIN" -m py_compile \
  src/quantlab/config.py \
  src/quantlab/storage.py \
  src/quantlab/analysis/market_hotspots.py \
  src/quantlab/analysis/portfolio.py \
  src/quantlab/app/dashboard.py \
  src/quantlab/app/streamlit_app.py \
  src/quantlab/approvals/registry.py \
  src/quantlab/data/provider_status.py \
  src/quantlab/data/moomoo_diagnostics.py \
  src/quantlab/data/providers/alpha_vantage.py \
  src/quantlab/data/providers/factory.py \
  src/quantlab/data/providers/moomoo_provider.py \
  src/quantlab/data/providers/polygon_provider.py \
  src/quantlab/data/providers/tushare_provider.py \
  src/quantlab/data/symbol_search.py \
  src/quantlab/data/validation.py \
  src/quantlab/examples/daily_check.py \
  src/quantlab/examples/command_center.py \
  src/quantlab/examples/report_decision_support.py \
  src/quantlab/examples/report_gap_tasks.py \
  src/quantlab/examples/validation_priority_plan.py \
  src/quantlab/examples/validation_task_execution.py \
  src/quantlab/examples/hotspot_runtime_summary.py \
  src/quantlab/examples/validate_moomoo.py \
  src/quantlab/examples/validate_cross_source.py \
  src/quantlab/examples/integration_audit.py \
  src/quantlab/examples/run_sample_backtest.py \
  src/quantlab/research/reviews.py \
  src/quantlab/research/report_gap_tasks.py \
  src/quantlab/research/validation_queue.py \
  src/quantlab/research/validation_priority.py \
  src/quantlab/research/validation_execution.py \
  src/quantlab/reports/catalog.py \
  src/quantlab/reports/decision_support.py \
  src/quantlab/reports/export.py \
  src/quantlab/executive/__init__.py \
  src/quantlab/executive/command_center.py \
  src/quantlab/strategies/custom_builder.py \
  src/quantlab/strategies/profiles.py \
  src/quantlab/strategies/mean_reversion/bollinger_reversion.py \
  src/quantlab/system/daily_readiness.py \
  src/quantlab/system/eva_identity.py \
  src/quantlab/system/health.py \
  src/quantlab/system/integration_audit.py \
  src/quantlab/system/shutdown_monitor.py \
  src/quantlab/value/token_roi.py \
  src/quantlab/examples/token_roi_ledger.py

echo "Running tests..."
ensure_test_deps
"$PYTHON_BIN" -m pytest -q -p no:cacheprovider

echo "Checking QuantLab runtime status, informational only..."
scripts/statusQuantLab.sh

echo "QuantLab verification completed."
