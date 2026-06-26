#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/pfi_os-pycache}"
export PFI_REPORT_DIR="${PFI_REPORT_DIR:-/private/tmp/pfi_os-report-test}"
export MPLBACKEND="${MPLBACKEND:-Agg}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/private/tmp/pfi_os-mplconfig}"
mkdir -p "$PYTHONPYCACHEPREFIX" "$PFI_REPORT_DIR" "$MPLCONFIGDIR"
source "$PROJECT_DIR/scripts/pfiRuntime.sh"
PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"

ensure_test_deps() {
  if "$PYTHON_BIN" -m pytest --version >/dev/null 2>&1; then
    return
  fi
  echo "PFI test dependency pytest is missing." >&2
  echo "Run scripts/installLockedEnv.sh once, then retry." >&2
  exit 67
}

echo "Checking shell scripts..."
zsh -n StartPFI.command StopPFI.command scripts/pfiRuntime.sh scripts/startPFI.sh scripts/stopPFI.sh scripts/installMacAppLaunchers.sh scripts/statusPFI.sh scripts/pfiSupervisor.sh scripts/verifyPFI.sh scripts/finalAcceptanceCheck.sh scripts/createSampleReport.sh scripts/setupEnv.sh scripts/validateRealData.sh scripts/validateCrossSource.sh scripts/checkMoomoo.sh scripts/dailyCheck.sh scripts/runTests.sh scripts/cleanCache.sh scripts/cleanReportJunk.sh scripts/openReports.sh scripts/auditPFIIntegration.sh scripts/commandCenter.sh scripts/reportDecisionSupport.sh scripts/reportGapTasks.sh scripts/validationPriorityPlan.sh scripts/runValidationTask.sh scripts/vectorizedResearch.sh scripts/hotspotRuntimeSummary.sh

echo "Checking Python syntax..."
"$PYTHON_BIN" -m py_compile \
  src/pfi_os/config.py \
  src/pfi_os/storage.py \
  src/pfi_os/analysis/market_hotspots.py \
  src/pfi_os/analysis/portfolio.py \
  src/pfi_os/app/dashboard.py \
  src/pfi_os/app/streamlit_app.py \
  src/pfi_os/application/durable_jobs.py \
  src/pfi_os/examples/pfi_supervisor.py \
  src/pfi_os/approvals/registry.py \
  src/pfi_os/data/provider_status.py \
  src/pfi_os/data/moomoo_diagnostics.py \
  src/pfi_os/data/providers/alpha_vantage.py \
  src/pfi_os/data/providers/factory.py \
  src/pfi_os/data/providers/moomoo_provider.py \
  src/pfi_os/data/providers/polygon_provider.py \
  src/pfi_os/data/providers/tushare_provider.py \
  src/pfi_os/data/symbol_search.py \
  src/pfi_os/data/validation.py \
  src/pfi_os/examples/daily_check.py \
  src/pfi_os/examples/command_center.py \
  src/pfi_os/examples/report_decision_support.py \
  src/pfi_os/examples/report_gap_tasks.py \
  src/pfi_os/examples/validation_priority_plan.py \
  src/pfi_os/examples/validation_task_execution.py \
  src/pfi_os/examples/hotspot_runtime_summary.py \
  src/pfi_os/examples/validate_moomoo.py \
  src/pfi_os/examples/validate_cross_source.py \
  src/pfi_os/examples/integration_audit.py \
  src/pfi_os/examples/run_sample_backtest.py \
  src/pfi_os/research/reviews.py \
  src/pfi_os/research/report_gap_tasks.py \
  src/pfi_os/research/validation_queue.py \
  src/pfi_os/research/validation_priority.py \
  src/pfi_os/research/validation_execution.py \
  src/pfi_os/reports/catalog.py \
  src/pfi_os/reports/decision_support.py \
  src/pfi_os/reports/export.py \
  src/pfi_os/executive/__init__.py \
  src/pfi_os/executive/command_center.py \
  src/pfi_os/strategies/custom_builder.py \
  src/pfi_os/strategies/profiles.py \
  src/pfi_os/strategies/mean_reversion/bollinger_reversion.py \
  src/pfi_os/system/daily_readiness.py \
  src/pfi_os/system/pfi_identity.py \
  src/pfi_os/system/health.py \
  src/pfi_os/system/integration_audit.py \
  src/pfi_os/system/shutdown_monitor.py

echo "Running tests..."
ensure_test_deps
"$PYTHON_BIN" -m pytest -q -p no:cacheprovider

echo "Checking PFI runtime status, informational only..."
scripts/statusPFI.sh

echo "PFI verification completed."
