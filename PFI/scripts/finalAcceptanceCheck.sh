#!/usr/bin/env zsh
set -euo pipefail

if [[ "${1:-}" == "--allow-heavy-smoke" ]]; then
  export PFI_ALLOW_HEAVY_SMOKE=1
  shift
fi

if [[ "${PFI_ALLOW_HEAVY_SMOKE:-}" != "1" ]]; then
  cat >&2 <<'EOF'
PFI heavy SmokeTest is blocked by default.
Use scripts/devReadyCheck.sh --summary-json for normal development.
Run deliberately only for release gates:
  PFI_ALLOW_HEAVY_SMOKE=1 scripts/finalAcceptanceCheck.sh
EOF
  exit 64
fi

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
REPORT_DIR="${PFI_REPORT_DIR:-$HOME/Downloads/量化回测分析}"
APP_INSTALL_DIR="${PFI_APP_INSTALL_DIR:-/Applications}"
DOWNLOADS_DIR="${PFI_DOWNLOADS_DIR:-$HOME/Downloads}"
DESKTOP_DIR="${PFI_DESKTOP_DIR:-$HOME/Desktop}"
APP_BUNDLE_NAME="PFI"
APP_DISPLAY_NAME="PFI"
LEGACY_APP_NAME="量化回测系统"

cd "$PROJECT_DIR"

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf "PASS  %s\n" "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf "FAIL  %s\n" "$1"
}

check_file() {
  local path="$1"
  local label="$2"
  if [[ -f "$path" ]]; then
    pass "$label"
  else
    fail "$label missing: $path"
  fi
}

check_dir() {
  local path="$1"
  local label="$2"
  if [[ -d "$path" ]]; then
    pass "$label"
  else
    fail "$label missing: $path"
  fi
}

check_executable() {
  local path="$1"
  local label="$2"
  if [[ -x "$path" ]]; then
    pass "$label"
  else
    fail "$label not executable: $path"
  fi
}

check_app_signature() {
  local path="$1"
  local label="$2"
  if /usr/bin/codesign --verify --deep "$path" >/dev/null 2>&1; then
    pass "$label"
  else
    fail "$label signature invalid: $path"
  fi
}

check_plist_value() {
  local path="$1"
  local key="$2"
  local expected="$3"
  local label="$4"
  local actual
  actual="$(/usr/libexec/PlistBuddy -c "Print :$key" "$path/Contents/Info.plist" 2>/dev/null || true)"
  if [[ "$actual" == "$expected" ]]; then
    pass "$label"
  else
    fail "$label expected '$expected' but got '$actual'"
  fi
}

check_absent() {
  local path="$1"
  local label="$2"
  if [[ ! -e "$path" ]]; then
    pass "$label"
  else
    fail "$label still exists: $path"
  fi
}

check_text() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if /usr/bin/grep -q "$pattern" "$path"; then
    pass "$label"
  else
    fail "$label missing pattern '$pattern' in $path"
  fi
}

check_text_absent() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if /usr/bin/grep -q "$pattern" "$path"; then
    fail "$label unexpected pattern '$pattern' in $path"
  else
    pass "$label"
  fi
}

echo "PFI final acceptance check"
echo "Project: $PROJECT_DIR"
echo "Reports: $REPORT_DIR"
echo

check_dir "$PROJECT_DIR" "Project directory exists"
check_dir "$REPORT_DIR" "Report directory exists"

check_executable "$PROJECT_DIR/StartPFI.command" "Project double-click launcher is executable"
check_executable "$PROJECT_DIR/StopPFI.command" "Project stop launcher is executable"
check_dir "$DESKTOP_DIR/$APP_BUNDLE_NAME.app" "Desktop PFI app exists"
check_dir "$DOWNLOADS_DIR/$APP_BUNDLE_NAME.app" "Downloads PFI app exists"
check_dir "$APP_INSTALL_DIR/$APP_BUNDLE_NAME.app" "Applications PFI app exists"
check_executable "$DESKTOP_DIR/$APP_BUNDLE_NAME.app/Contents/MacOS/PFI" "Desktop PFI app launcher is executable"
check_executable "$DOWNLOADS_DIR/$APP_BUNDLE_NAME.app/Contents/MacOS/PFI" "Downloads PFI app launcher is executable"
check_executable "$APP_INSTALL_DIR/$APP_BUNDLE_NAME.app/Contents/MacOS/PFI" "Applications PFI app launcher is executable"
check_file "$PROJECT_DIR/macos/PFI.app/Contents/MacOS/PFI" "Source PFI app launcher exists"
check_file "$PROJECT_DIR/macos/PFI_launcher.c" "Source PFI native launcher source exists"
check_file "$DESKTOP_DIR/$APP_BUNDLE_NAME.app/Contents/Resources/PFI_PROJECT_ROOT" "Desktop PFI app local project binding exists"
check_file "$DOWNLOADS_DIR/$APP_BUNDLE_NAME.app/Contents/Resources/PFI_PROJECT_ROOT" "Downloads PFI app local project binding exists"
check_file "$APP_INSTALL_DIR/$APP_BUNDLE_NAME.app/Contents/Resources/PFI_PROJECT_ROOT" "Applications PFI app local project binding exists"
check_app_signature "$DESKTOP_DIR/$APP_BUNDLE_NAME.app" "Desktop PFI app signature is valid"
check_app_signature "$DOWNLOADS_DIR/$APP_BUNDLE_NAME.app" "Downloads PFI app signature is valid"
check_app_signature "$APP_INSTALL_DIR/$APP_BUNDLE_NAME.app" "Applications PFI app signature is valid"
check_plist_value "$DESKTOP_DIR/$APP_BUNDLE_NAME.app" "CFBundleDisplayName" "$APP_DISPLAY_NAME" "Desktop PFI display name is correct"
check_plist_value "$DOWNLOADS_DIR/$APP_BUNDLE_NAME.app" "CFBundleDisplayName" "$APP_DISPLAY_NAME" "Downloads PFI display name is correct"
check_plist_value "$APP_INSTALL_DIR/$APP_BUNDLE_NAME.app" "CFBundleDisplayName" "$APP_DISPLAY_NAME" "Applications PFI display name is correct"
check_file "$PROJECT_DIR/assets/PFIAppIconConfig.json" "macOS app icon config exists"
check_file "$PROJECT_DIR/assets/PFIAppIcon.icns" "macOS app icon exists"
check_file "$PROJECT_DIR/assets/PFIAppIconPreview.png" "macOS app icon preview exists"
check_absent "$DESKTOP_DIR/$LEGACY_APP_NAME.app" "Legacy Desktop app launcher removed"
check_absent "$DOWNLOADS_DIR/$LEGACY_APP_NAME.app" "Legacy Downloads app launcher removed"
check_absent "$APP_INSTALL_DIR/$LEGACY_APP_NAME.app" "Legacy Applications app launcher removed"
check_absent "$DESKTOP_DIR/$LEGACY_APP_NAME.command" "Old Desktop command launcher removed"
check_absent "$DOWNLOADS_DIR/$LEGACY_APP_NAME.command" "Old Downloads command launcher removed"
check_absent "$APP_INSTALL_DIR/$LEGACY_APP_NAME.command" "Old Applications command launcher removed"

check_executable "$PROJECT_DIR/scripts/startPFI.sh" "Start script is executable"
check_executable "$PROJECT_DIR/scripts/stopPFI.sh" "Stop script is executable"
check_executable "$PROJECT_DIR/scripts/installMacAppLaunchers.sh" "macOS app installer is executable"
check_executable "$PROJECT_DIR/scripts/statusPFI.sh" "Status script is executable"
check_executable "$PROJECT_DIR/scripts/macosAcceptance.sh" "macOS Acceptance Hub script is executable"
check_executable "$PROJECT_DIR/scripts/devReadyCheck.sh" "Development readiness check script is executable"
check_executable "$PROJECT_DIR/scripts/macosAppAcceptanceLite.sh" "macOS App Acceptance Lite script is executable"
check_executable "$PROJECT_DIR/scripts/macosLifecycleReadiness.sh" "macOS Lifecycle Readiness script is executable"
check_executable "$PROJECT_DIR/scripts/macosRuntimeAcceptance.sh" "macOS Runtime Acceptance script is executable"
check_executable "$PROJECT_DIR/scripts/macosPublicAcceptanceSummary.sh" "macOS Public Acceptance Summary script is executable"
check_executable "$PROJECT_DIR/scripts/dailyCheck.sh" "Daily check script is executable"
check_executable "$PROJECT_DIR/scripts/cashFlowReviewedInputRefresh.sh" "CashFlow reviewed input refresh script is executable"
check_executable "$PROJECT_DIR/scripts/policyReviewedInputRefresh.sh" "Policy reviewed input refresh script is executable"
check_executable "$PROJECT_DIR/scripts/consumptionReviewedInputRefresh.sh" "Consumption reviewed input refresh script is executable"
check_executable "$PROJECT_DIR/scripts/refreshRuntimeSummaries.sh" "Runtime Summary Refresh script is executable"
check_executable "$PROJECT_DIR/scripts/commandCenter.sh" "Executive Command Center script is executable"
check_executable "$PROJECT_DIR/scripts/reportValidation.sh" "Report Validation Hub script is executable"
check_executable "$PROJECT_DIR/scripts/reportDecisionSupport.sh" "Report Decision Support script is executable"
check_executable "$PROJECT_DIR/scripts/reportGapTasks.sh" "Report Evidence Gap Task script is executable"
check_executable "$PROJECT_DIR/scripts/validationPriorityPlan.sh" "Validation Priority Plan script is executable"
check_executable "$PROJECT_DIR/scripts/runValidationTask.sh" "Validation Task Execution script is executable"
check_executable "$PROJECT_DIR/scripts/vectorizedResearch.sh" "Vectorized Research script is executable"
check_executable "$PROJECT_DIR/scripts/hotspotRuntimeSummary.sh" "Hotspot Runtime Summary script is executable"
check_executable "$PROJECT_DIR/scripts/site52etfSnapshot.sh" "52ETF public snapshot script is executable"
check_executable "$PROJECT_DIR/scripts/verifyPFI.sh" "Verification script is executable"
check_executable "$PROJECT_DIR/scripts/checkMoomoo.sh" "Moomoo diagnostic script is executable"
check_executable "$PROJECT_DIR/scripts/validateCrossSource.sh" "Cross-source validation script is executable"

check_file "$PROJECT_DIR/README.md" "README exists"
check_file "$PROJECT_DIR/docs/Handbook.md" "Handbook exists"
check_file "$PROJECT_DIR/docs/ReportGuide.md" "Report guide exists"
check_file "$PROJECT_DIR/docs/DataSources.md" "Data sources guide exists"
check_file "$PROJECT_DIR/docs/OpenSourceReference.md" "Open-source reference exists"
check_file "$PROJECT_DIR/docs/AcceptanceChecklist.md" "Acceptance checklist exists"
check_file "$PROJECT_DIR/docs/Testing.md" "Testing guide exists"
check_file "$PROJECT_DIR/docs/MacOSAcceptanceHub.md" "macOS Acceptance Hub guide exists"
check_file "$PROJECT_DIR/docs/MacOSLifecycleReadiness.md" "macOS Lifecycle Readiness guide exists"
check_file "$PROJECT_DIR/docs/MacOSRuntimeAcceptance.md" "macOS Runtime Acceptance guide exists"
check_file "$PROJECT_DIR/docs/MacOSPublicAcceptanceSummary.md" "macOS Public Acceptance Summary guide exists"
check_file "$PROJECT_DIR/docs/evidence/MacOSAcceptancePublicSummary_latest.json" "macOS Public Acceptance latest JSON exists"
check_file "$PROJECT_DIR/docs/evidence/MacOSAcceptancePublicSummary_latest.md" "macOS Public Acceptance latest Markdown exists"
check_file "$PROJECT_DIR/docs/ExecutiveCommandCenter.md" "Executive Command Center guide exists"
check_file "$PROJECT_DIR/docs/ReportValidationHub.md" "Report Validation Hub guide exists"
check_file "$PROJECT_DIR/docs/ReportDecisionSupport.md" "Report Decision Support guide exists"
check_file "$PROJECT_DIR/docs/ReportEvidenceGapTasks.md" "Report Evidence Gap Tasks guide exists"
check_file "$PROJECT_DIR/docs/ValidationPriorityPlan.md" "Validation Priority Plan guide exists"
check_file "$PROJECT_DIR/docs/ValidationTaskExecution.md" "Validation Task Execution guide exists"
check_file "$PROJECT_DIR/docs/VectorizedResearchMode.md" "Vectorized Research Mode guide exists"

check_file "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "Streamlit workbench exists"
check_file "$PROJECT_DIR/src/pfi_os/system/macos_acceptance_hub.py" "macOS Acceptance Hub module exists"
check_file "$PROJECT_DIR/src/pfi_os/system/macos_acceptance.py" "macOS App Acceptance Lite module exists"
check_file "$PROJECT_DIR/src/pfi_os/system/dev_readiness.py" "Development readiness check module exists"
check_file "$PROJECT_DIR/src/pfi_os/system/macos_public_acceptance.py" "macOS Public Acceptance Summary module exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/macos_app_acceptance_lite.py" "macOS App Acceptance Lite CLI exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/macos_acceptance_hub.py" "macOS Acceptance Hub CLI exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/dev_ready_check.py" "Development readiness check CLI exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/macos_public_acceptance.py" "macOS Public Acceptance Summary CLI exists"
check_file "$PROJECT_DIR/src/pfi_os/system/macos_lifecycle.py" "macOS Lifecycle Readiness module exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/macos_lifecycle_readiness.py" "macOS Lifecycle Readiness CLI exists"
check_file "$PROJECT_DIR/src/pfi_os/system/macos_runtime_acceptance.py" "macOS Runtime Acceptance module exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/macos_runtime_acceptance.py" "macOS Runtime Acceptance CLI exists"
check_file "$PROJECT_DIR/src/pfi_os/reports/export.py" "Word report exporter exists"
check_file "$PROJECT_DIR/src/pfi_os/reports/catalog.py" "Report center catalog exists"
check_file "$PROJECT_DIR/src/pfi_os/risk/decision_quality.py" "Decision Quality module exists"
check_file "$PROJECT_DIR/src/pfi_os/research/reviews.py" "Trade review module exists"
check_file "$PROJECT_DIR/src/pfi_os/research/validation_queue.py" "Validation queue module exists"
check_file "$PROJECT_DIR/src/pfi_os/integrations/external_systems.py" "External systems integration module exists"
check_file "$PROJECT_DIR/src/pfi_os/integrations/holdings_book.py" "Holdings book module exists"
check_file "$PROJECT_DIR/docs/ResearchBusSchema.json" "Research bus schema contract exists"
check_file "$PROJECT_DIR/src/pfi_os/analysis/robustness.py" "Bootstrap robustness module exists"
check_file "$PROJECT_DIR/src/pfi_os/analysis/sentiment.py" "Sentiment analysis module exists"
check_file "$PROJECT_DIR/src/pfi_os/analysis/market_hotspots.py" "Market Hotspots module exists"
check_file "$PROJECT_DIR/src/pfi_os/analysis/strategy_diagnostics.py" "Strategy diagnostics module exists"
check_file "$PROJECT_DIR/src/pfi_os/executive/command_center.py" "Executive Command Center module exists"
check_file "$PROJECT_DIR/src/pfi_os/executive/runtime_summary_refresh.py" "Runtime Summary Refresh module exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/refresh_runtime_summaries.py" "Runtime Summary Refresh CLI exists"
check_file "$PROJECT_DIR/src/pfi_os/business/cashflow_reviewed_input.py" "CashFlow reviewed input refresh module exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/cashflow_reviewed_input_refresh.py" "CashFlow reviewed input refresh CLI exists"
check_file "$PROJECT_DIR/shared/schema/company_cashflow_reviewed_input.schema.json" "CashFlow reviewed input schema exists"
check_file "$PROJECT_DIR/data/cashflow/CompanyCashFlowReviewedInput.example.json" "CashFlow reviewed input public example exists"
check_file "$PROJECT_DIR/src/pfi_os/policy/reviewed_input.py" "Policy reviewed input refresh module exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/policy_reviewed_input_refresh.py" "Policy reviewed input refresh CLI exists"
check_file "$PROJECT_DIR/shared/schema/policy_reviewed_input.schema.json" "Policy reviewed input schema exists"
check_file "$PROJECT_DIR/data/policy/PolicyReviewedInput.example.json" "Policy reviewed input public example exists"
check_file "$PROJECT_DIR/src/pfi_os/consumption/reviewed_input.py" "Consumption reviewed input refresh module exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/consumption_reviewed_input_refresh.py" "Consumption reviewed input refresh CLI exists"
check_file "$PROJECT_DIR/shared/schema/consumption_guard_reviewed_input.schema.json" "Consumption reviewed input schema exists"
check_file "$PROJECT_DIR/data/consumption/ConsumptionGuardReviewedInput.example.json" "Consumption reviewed input public example exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/site52etf_snapshot.py" "52ETF public snapshot CLI exists"
check_file "$PROJECT_DIR/data/integrations/site52etf/.gitkeep" "52ETF public snapshot output directory placeholder exists"
check_file "$PROJECT_DIR/src/pfi_os/system/report_validation_hub.py" "Report Validation Hub module exists"
check_file "$PROJECT_DIR/src/pfi_os/examples/report_validation_hub.py" "Report Validation Hub CLI exists"
check_file "$PROJECT_DIR/src/pfi_os/reports/decision_support.py" "Report Decision Support module exists"
check_file "$PROJECT_DIR/src/pfi_os/research/report_gap_tasks.py" "Report Evidence Gap Task module exists"
check_file "$PROJECT_DIR/src/pfi_os/research/validation_priority.py" "Validation Priority Plan module exists"
check_file "$PROJECT_DIR/src/pfi_os/research/validation_execution.py" "Validation Task Execution module exists"
check_file "$PROJECT_DIR/src/pfi_os/research/vectorized.py" "Vectorized Research module exists"
check_file "$PROJECT_DIR/src/pfi_os/strategies/behavioral/alipay.py" "Buy Dips Sell Rallies strategy source exists"

check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "show_report_center_dashboard" "Report Center dashboard is wired"
check_text "$PROJECT_DIR/macos/PFI_launcher.c" "PFI_PROJECT_ROOT" "Source PFI app resolves local project root"
check_text "$PROJECT_DIR/macos/PFI_launcher.c" "PFI_APP_LAUNCH_DRY_RUN" "Source PFI app launch can be dry-run verified"
check_text "$PROJECT_DIR/macos/PFI_launcher.c" "./StartPFI.command" "Source PFI app opens local command launcher"
check_text "$PROJECT_DIR/macos/PFI_launcher.c" "mode=spawn-command" "Source PFI app uses direct command launch mode"
check_text "$PROJECT_DIR/macos/PFI_launcher.c" "posix_spawn" "Source PFI app uses native launcher process spawning"
check_text "$PROJECT_DIR/macos/PFI_launcher.c" "\"/bin/zsh\"" "Source PFI app invokes local command launcher through zsh without Terminal"
check_text_absent "$PROJECT_DIR/macos/PFI_launcher.c" "github.com/LinzeColin/CodexProject/PFI" "Source PFI app does not fall back to GitHub"
check_text_absent "$PROJECT_DIR/macos/PFI_launcher.c" "tell application \"Terminal\"" "Source PFI app does not require Terminal automation"
check_text_absent "$PROJECT_DIR/macos/PFI_launcher.c" "open_command_in_terminal" "Source PFI app does not route command launch through Terminal"
check_text_absent "$PROJECT_DIR/macos/PFI_launcher.c" "\"Terminal\"" "Source PFI app does not name Terminal"
check_text_absent "$DESKTOP_DIR/$APP_BUNDLE_NAME.app/Contents/MacOS/PFI" "github.com/LinzeColin/CodexProject/PFI" "Desktop PFI app does not fall back to GitHub"
check_text_absent "$DOWNLOADS_DIR/$APP_BUNDLE_NAME.app/Contents/MacOS/PFI" "github.com/LinzeColin/CodexProject/PFI" "Downloads PFI app does not fall back to GitHub"
check_text_absent "$APP_INSTALL_DIR/$APP_BUNDLE_NAME.app/Contents/MacOS/PFI" "github.com/LinzeColin/CodexProject/PFI" "Applications PFI app does not fall back to GitHub"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "sidebar_usage_guide" "Sidebar usage guide is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "render_macos_lifecycle_panel" "macOS lifecycle panel is wired into workspace shell"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "macos_runtime_evidence_summary" "macOS runtime evidence summary is wired into UI shell"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "MacOSRuntimeAcceptance_latest.json" "macOS runtime evidence reads latest JSON only"
check_text "$PROJECT_DIR/src/pfi_os/system/dev_readiness.py" "PFIOSDevReadyCheckV1" "Development readiness schema is present"
check_text "$PROJECT_DIR/src/pfi_os/system/dev_readiness.py" "runs_heavy_release_gates" "Development readiness documents release gate exclusion"
check_text "$PROJECT_DIR/src/pfi_os/examples/dev_ready_check.py" "summary-json" "Development readiness compact summary flag is present"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "macos_lifecycle_dev_ready" "Development readiness button is wired into macOS lifecycle panel"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "scripts/devReadyCheck.sh" "Development readiness script is allowlisted in UI shell"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "render_vectorized_research_panel" "Vectorized Research UI panel is wired into workspace shell"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "VectorizedResearch_latest.json" "Vectorized Research UI reads latest compact output"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "render_hotspot_runtime_summary" "Hotspot Runtime Summary UI panel is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "hotspot_runtime_cache_key" "Hotspot Runtime cache key is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "render_hotspot_cache_controls" "Hotspot cache controls are wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "render_hotspot_request_trace" "Hotspot per-symbol request trace UI is wired"
check_text "$PROJECT_DIR/src/pfi_os/analysis/market_hotspots.py" "PFIOSHotspotCacheStatusV1" "Hotspot cache status schema is present"
check_text "$PROJECT_DIR/src/pfi_os/analysis/market_hotspots.py" "PFIOSHotspotRequestTraceV1" "Hotspot request trace schema is present"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "render_site52etf_hotspot_comparison" "52ETF hotspot comparison UI panel is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "apply_research_chart_ux" "TradingView-like research chart UX helper is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "research_chart_config" "Research chart Plotly config is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "scrollZoom" "Research charts enable scroll zoom"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "LIFECYCLE_SCRIPT_ALLOWLIST" "macOS lifecycle actions use an allowlist"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "macos_lifecycle_acceptance_lite" "macOS lifecycle lite acceptance button is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "macosAppAcceptanceLite.sh" "macOS lifecycle lite acceptance script is allowlisted"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "macos_lifecycle_readiness" "macOS lifecycle readiness button is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "macosLifecycleReadiness.sh" "macOS lifecycle readiness script is allowlisted"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "build_cache_cleanup_report" "macOS lifecycle cache preview is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/dashboard.py" "macos_lifecycle_summary" "macOS lifecycle summary helper is present"
check_text "$PROJECT_DIR/src/pfi_os/app/dashboard.py" "MacOSRuntimeEvidenceSummaryV1" "macOS runtime evidence summary helper is present"
check_text "$PROJECT_DIR/src/pfi_os/app/dashboard.py" "Dev Ready Check" "Development readiness action is present"
check_text "$PROJECT_DIR/src/pfi_os/app/dashboard.py" "Lite Acceptance" "macOS lifecycle lite acceptance action is present"
check_text "$PROJECT_DIR/src/pfi_os/app/dashboard.py" "Lifecycle Readiness" "macOS lifecycle readiness action is present"
check_text "$PROJECT_DIR/src/pfi_os/app/dashboard.py" "Runtime Acceptance" "macOS runtime acceptance action is present"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_acceptance.py" "PFIOSMacOSAppAcceptanceLiteV1" "macOS App Acceptance Lite schema is present"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_acceptance.py" "finalAcceptanceCheck.sh" "macOS App Acceptance Lite does not run full final acceptance"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_acceptance.py" "PFI_APP_LAUNCH_DRY_RUN" "macOS App Acceptance Lite uses launcher dry-run"
check_text "$PROJECT_DIR/scripts/macosAppAcceptanceLite.sh" "macos_app_acceptance_lite" "macOS App Acceptance Lite shell entry is wired"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_lifecycle.py" "PFIOSMacOSLifecycleReadinessV1" "macOS Lifecycle Readiness schema is present"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_lifecycle.py" "pfi_os.system.shutdown_monitor" "macOS Lifecycle Readiness checks auto-shutdown monitor"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_lifecycle.py" "DevReadyScriptExecutable" "macOS Lifecycle Readiness checks development readiness entry"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_lifecycle.py" "build_cache_cleanup_report" "macOS Lifecycle Readiness checks cache cleanup dry-run"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_lifecycle.py" "finalAcceptanceCheck.sh" "macOS Lifecycle Readiness does not run final acceptance"
check_text "$PROJECT_DIR/scripts/macosLifecycleReadiness.sh" "macos_lifecycle_readiness" "macOS Lifecycle Readiness shell entry is wired"
check_text "$PROJECT_DIR/scripts/cleanCache.sh" "pfi_os_is_running" "Cache cleanup uses scoped running-service detection"
check_text "$PROJECT_DIR/scripts/cleanCache.sh" "process_cwd" "Cache cleanup checks running service cwd"
check_text "$PROJECT_DIR/scripts/cleanCache.sh" "cwd_path\" == \"\$PROJECT_DIR\"" "Cache cleanup only refuses this checkout's running service"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_runtime_acceptance.py" "PFIOSMacOSRuntimeAcceptanceV1" "macOS Runtime Acceptance schema is present"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_runtime_acceptance.py" "CleanCacheRefusesWhileRunning" "macOS Runtime Acceptance checks cache guard while running"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_runtime_acceptance.py" "NoPreExistingService" "macOS Runtime Acceptance avoids stopping existing sessions by default"
check_text "$PROJECT_DIR/src/pfi_os/system/macos_runtime_acceptance.py" "finalAcceptanceCheck.sh" "macOS Runtime Acceptance does not run final acceptance"
check_text "$PROJECT_DIR/scripts/macosRuntimeAcceptance.sh" "macos_runtime_acceptance" "macOS Runtime Acceptance shell entry is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/dashboard.py" "vectorized_research_shell_summary" "Vectorized Research shell summary helper is present"
check_text "$PROJECT_DIR/src/pfi_os/app/dashboard.py" "does not reload EventReplay records or rerun parameter scans" "Vectorized Research UI token policy is present"
check_text "$PROJECT_DIR/src/pfi_os/app/dashboard.py" "Lifecycle controls only manage the local PFI/PFIOS app process" "macOS lifecycle safety policy is present"
check_text "$PROJECT_DIR/src/pfi_os/system/cache_cleanup.py" "PFICacheCleanupReportV1" "Cache cleanup report schema is present"
check_text "$PROJECT_DIR/src/pfi_os/system/cache_cleanup.py" "market bar caches are not deleted" "Cache cleanup preserves market caches"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "executive_command_center_view" "Executive Command Center is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "show_report_decision_support_panel" "Report Decision Support is wired into Report Center"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "build_report_validation_hub" "Report Validation Hub is wired into Report Center"
check_text "$PROJECT_DIR/src/pfi_os/system/report_validation_hub.py" "PFIOSReportValidationHubV1" "Report Validation Hub schema is present"
check_text "$PROJECT_DIR/src/pfi_os/system/report_validation_hub.py" "does not include full report records" "Report Validation Hub token policy is present"
check_text "$PROJECT_DIR/src/pfi_os/examples/report_validation_hub.py" "summary-json" "Report Validation Hub compact summary flag is present"
check_text "$PROJECT_DIR/scripts/reportValidation.sh" "report_validation_hub" "Report Validation Hub shell entry is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "append_report_gap_validation_tasks" "Report Evidence Gap Tasks are wired into Validation Queue"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "write_validation_priority_plan" "Validation Priority Plan is wired into Validation Queue"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "write_validation_task_execution" "Validation Task Execution is wired into Validation Queue"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "parameter_scan_terms_panel" "Parameter scan term explanations are wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "built_in_strategy_order_editor" "Strategy order editor is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "built_in_strategy_parameter_editor" "Built-in strategy parameter editor is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "show_strategy_diagnostics" "Strategy diagnostics are wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "show_portfolio_risk_view" "Portfolio risk view is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "alipay_enhanced" "Buy Dips Sell Rallies Enhanced strategy is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "show_bootstrap_robustness" "Bootstrap robustness is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "show_decision_quality" "Decision Quality is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "show_trade_review_panel" "Trade review panel is wired into report center"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "show_validation_queue_panel" "Validation queue panel is wired into report center"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "industry_research_view" "Industry research view is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "research_bus_monitor_view" "Research bus monitor is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "big_data_simulation_view" "Big data simulation view is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "holdings_view" "Holdings view is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "sentiment_analysis_view" "Sentiment analysis view is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "personal_profile_view" "Personal profile view is wired into workbench"
check_text "$PROJECT_DIR/src/pfi_os/risk/decision_quality.py" "evaluate_decision_quality" "Decision Quality evaluator is present"
check_text "$PROJECT_DIR/src/pfi_os/research/reviews.py" "error_profile_frame" "Error attribution dashboard helper is present"
check_text "$PROJECT_DIR/src/pfi_os/research/validation_queue.py" "validation_task_frame" "Validation queue helper is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/external_systems.py" "collect_industry_reports" "Industry report connector is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/external_systems.py" "load_holdings_frame" "Holdings connector is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/external_systems.py" "build_personal_profile" "Personal profile analyzer is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/independent_validation.py" "run_independent_validation" "Independent validation runner is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/research_bus_api.py" "submit_chat_input" "Research bus chat input API is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/holdings_book.py" "sync_holdings_book" "Holdings sync helper is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/holdings_book.py" "load_pending_orders_frame" "Pending orders remain separated from holdings"
check_text "$PROJECT_DIR/src/pfi_os/analysis/sentiment.py" "sentiment_from_bars" "Sentiment analysis helper is present"
check_text "$PROJECT_DIR/scripts/refreshRuntimeSummaries.sh" "refresh_runtime_summaries" "Runtime Summary Refresh shell entry is wired"
check_text "$PROJECT_DIR/src/pfi_os/executive/runtime_summary_refresh.py" "PFIOSRuntimeSummaryRefreshV1" "Runtime Summary Refresh schema is present"
check_text "$PROJECT_DIR/src/pfi_os/executive/runtime_summary_refresh.py" "runtime_summary_only" "Runtime Summary Refresh writes compact outputs only"
check_text "$PROJECT_DIR/src/pfi_os/executive/runtime_summary_refresh.py" "no full entries" "Runtime Summary Refresh public safety boundary is present"
check_text "$PROJECT_DIR/src/pfi_os/executive/command_center.py" "PFICommandCenterV1" "Executive Command Center schema is present"
check_text "$PROJECT_DIR/src/pfi_os/executive/command_center.py" "不刷新行情" "Executive Command Center no-refresh boundary is present"
check_text "$PROJECT_DIR/src/pfi_os/executive/command_center.py" "runtime_summary_sources" "Executive Command Center runtime summary source table is present"
check_text "$PROJECT_DIR/src/pfi_os/executive/command_center.py" "CompanyCashFlowRuntimeSummary_latest.json" "Executive Command Center prefers CashFlow runtime summary"
check_text "$PROJECT_DIR/src/pfi_os/executive/command_center.py" "PolicyIntelligenceRuntimeSummary_latest.json" "Executive Command Center prefers Policy runtime summary"
check_text "$PROJECT_DIR/src/pfi_os/executive/command_center.py" "ConsumptionGuardRuntimeSummary_latest.json" "Executive Command Center prefers Consumption runtime summary"
check_file "$PROJECT_DIR/data/cashflow/CompanyCashFlowRuntimeSummary_latest.json" "CashFlow runtime summary latest artifact exists"
check_file "$PROJECT_DIR/data/policy/PolicyIntelligenceRuntimeSummary_latest.json" "Policy runtime summary latest artifact exists"
check_file "$PROJECT_DIR/data/consumption/ConsumptionGuardRuntimeSummary_latest.json" "Consumption runtime summary latest artifact exists"
check_text "$PROJECT_DIR/data/cashflow/CompanyCashFlowRuntimeSummary_latest.json" "PFIOSCompanyCashFlowRuntimeSummaryV1" "CashFlow runtime latest schema is correct"
check_text "$PROJECT_DIR/data/policy/PolicyIntelligenceRuntimeSummary_latest.json" "PFIOSPolicyIntelligenceRuntimeSummaryV1" "Policy runtime latest schema is correct"
check_text "$PROJECT_DIR/data/consumption/ConsumptionGuardRuntimeSummary_latest.json" "PFIOSConsumptionGuardRuntimeSummaryV1" "Consumption runtime latest schema is correct"
check_text "$PROJECT_DIR/src/pfi_os/business/cashflow.py" "PFIOSCompanyCashFlowCommandV1" "Company CashFlow Command schema is present"
check_text "$PROJECT_DIR/src/pfi_os/business/cashflow.py" "PFIOSCompanyCashFlowRuntimeSummaryV1" "Company CashFlow runtime summary schema is present"
check_text "$PROJECT_DIR/src/pfi_os/business/cashflow.py" "does not include full entries" "Company CashFlow compact summary token policy is present"
check_text "$PROJECT_DIR/src/pfi_os/examples/cashflow_command.py" "summary-json" "Company CashFlow low-token summary CLI flag is present"
check_text "$PROJECT_DIR/scripts/cashFlowReviewedInputRefresh.sh" "cashflow_reviewed_input_refresh" "Company CashFlow reviewed input shell entry is wired"
check_text "$PROJECT_DIR/src/pfi_os/business/cashflow_reviewed_input.py" "PFIOSCompanyCashFlowReviewedInputRefreshV1" "Company CashFlow reviewed input refresh schema is present"
check_text "$PROJECT_DIR/src/pfi_os/business/cashflow_reviewed_input.py" "data/private/cashflow/CompanyCashFlowReviewedInput.json" "Company CashFlow private reviewed input path is present"
check_text "$PROJECT_DIR/src/pfi_os/business/cashflow_reviewed_input.py" "Local reviewed JSON input only" "Company CashFlow reviewed input safety boundary is present"
check_text "$PROJECT_DIR/shared/schema/company_cashflow_reviewed_input.schema.json" "PFI Company CashFlow Reviewed Input" "Company CashFlow reviewed input JSON schema title is present"
check_text "$PROJECT_DIR/data/cashflow/CompanyCashFlowReviewedInput.example.json" "sample://cashflow" "Company CashFlow reviewed input public example is synthetic"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "build_cashflow_runtime_summary" "Company CashFlow runtime gate UI is wired"
check_text "$PROJECT_DIR/src/pfi_os/policy/radar.py" "PFIOSPolicyIntelligenceRuntimeSummaryV1" "Policy Intelligence runtime summary schema is present"
check_text "$PROJECT_DIR/src/pfi_os/policy/radar.py" "does not include full opportunities" "Policy Intelligence compact summary token policy is present"
check_text "$PROJECT_DIR/src/pfi_os/examples/policy_radar.py" "summary-json" "Policy Intelligence low-token summary CLI flag is present"
check_text "$PROJECT_DIR/scripts/policyReviewedInputRefresh.sh" "policy_reviewed_input_refresh" "Policy reviewed input shell entry is wired"
check_text "$PROJECT_DIR/src/pfi_os/policy/reviewed_input.py" "PFIOSPolicyReviewedInputRefreshV1" "Policy reviewed input refresh schema is present"
check_text "$PROJECT_DIR/src/pfi_os/policy/reviewed_input.py" "data/private/policy/PolicyReviewedInput.json" "Policy private reviewed input path is present"
check_text "$PROJECT_DIR/src/pfi_os/policy/reviewed_input.py" "Local reviewed JSON input only" "Policy reviewed input safety boundary is present"
check_text "$PROJECT_DIR/shared/schema/policy_reviewed_input.schema.json" "PFI Policy Reviewed Input" "Policy reviewed input JSON schema title is present"
check_text "$PROJECT_DIR/data/policy/PolicyReviewedInput.example.json" "https://example.gov" "Policy reviewed input public example is synthetic"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "build_policy_runtime_summary" "Policy Intelligence runtime gate UI is wired"
check_text "$PROJECT_DIR/src/pfi_os/consumption/guard.py" "PFIOSConsumptionGuardRuntimeSummaryV1" "Consumption Guard runtime summary schema is present"
check_text "$PROJECT_DIR/src/pfi_os/consumption/guard.py" "does not include full events" "Consumption Guard compact summary token policy is present"
check_text "$PROJECT_DIR/src/pfi_os/examples/consumption_guard.py" "summary-json" "Consumption Guard low-token summary CLI flag is present"
check_text "$PROJECT_DIR/scripts/consumptionReviewedInputRefresh.sh" "consumption_reviewed_input_refresh" "Consumption reviewed input shell entry is wired"
check_text "$PROJECT_DIR/src/pfi_os/consumption/reviewed_input.py" "PFIOSConsumptionGuardReviewedInputRefreshV1" "Consumption reviewed input refresh schema is present"
check_text "$PROJECT_DIR/src/pfi_os/consumption/reviewed_input.py" "data/private/consumption/ConsumptionGuardReviewedInput.json" "Consumption private reviewed input path is present"
check_text "$PROJECT_DIR/src/pfi_os/consumption/reviewed_input.py" "Local reviewed JSON input only" "Consumption reviewed input safety boundary is present"
check_text "$PROJECT_DIR/shared/schema/consumption_guard_reviewed_input.schema.json" "PFI Consumption Guard Reviewed Input" "Consumption reviewed input JSON schema title is present"
check_text "$PROJECT_DIR/data/consumption/ConsumptionGuardReviewedInput.example.json" "sample://consumption" "Consumption reviewed input public example is synthetic"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "build_consumption_runtime_summary" "Consumption Guard runtime gate UI is wired"
check_text "$PROJECT_DIR/src/pfi_os/reports/decision_support.py" "PFIOSReportDecisionSupportIndexV1" "Report Decision Support schema is present"
check_text "$PROJECT_DIR/src/pfi_os/reports/decision_support.py" "No live trading" "Report Decision Support no-live-trading boundary is present"
check_text "$PROJECT_DIR/src/pfi_os/research/report_gap_tasks.py" "PFIOSReportEvidenceGapTasksV1" "Report Evidence Gap Task schema is present"
check_text "$PROJECT_DIR/src/pfi_os/research/report_gap_tasks.py" "does not run validation" "Report Evidence Gap Task non-execution boundary is present"
check_text "$PROJECT_DIR/src/pfi_os/research/validation_priority.py" "PFIOSValidationTaskPriorityPlanV1" "Validation Priority Plan schema is present"
check_text "$PROJECT_DIR/src/pfi_os/research/validation_priority.py" "does not run validation" "Validation Priority Plan non-execution boundary is present"
check_text "$PROJECT_DIR/src/pfi_os/research/validation_execution.py" "PFIOSValidationTaskExecutionV1" "Validation Task Execution schema is present"
check_text "$PROJECT_DIR/src/pfi_os/research/validation_execution.py" "does not connect to live trading" "Validation Task Execution no-live-trading boundary is present"
check_text "$PROJECT_DIR/src/pfi_os/research/vectorized.py" "PFIOSVectorizedResearchBatchV1" "Vectorized Research schema is present"
check_text "$PROJECT_DIR/src/pfi_os/research/vectorized.py" "build_vectorized_research" "Vectorized Research builder is present"
check_text "$PROJECT_DIR/src/pfi_os/research/vectorized.py" "Read-only replay-to-DataFrame research adapter" "Vectorized Research no-live-trading boundary is present"
check_text "$PROJECT_DIR/src/pfi_os/analysis/market_hotspots.py" "PFIOSHotspotRuntimeSummaryV1" "Hotspot Runtime Summary schema is present"
check_text "$PROJECT_DIR/src/pfi_os/analysis/market_hotspots.py" "PFIOSHotspotPersistedCacheV1" "Hotspot Persisted Cache schema is present"
check_text "$PROJECT_DIR/src/pfi_os/analysis/market_hotspots.py" "hotspot_runtime_summary" "Hotspot Runtime Summary builder is present"
check_text "$PROJECT_DIR/src/pfi_os/analysis/market_hotspots.py" "write_hotspot_persisted_cache" "Hotspot Persisted Cache writer is present"
check_text "$PROJECT_DIR/src/pfi_os/analysis/market_hotspots.py" "does not retain raw price frames" "Hotspot Runtime Summary token policy is present"
check_text "$PROJECT_DIR/src/pfi_os/examples/hotspot_runtime_summary.py" "use-persisted-cache" "Hotspot persisted cache smoke flag is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/site52etf.py" "PFIOS52ETFHotspotComparisonV1" "52ETF hotspot comparison schema is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/site52etf.py" "PFIOS52ETFPublicSnapshotV1" "52ETF public snapshot schema is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/site52etf.py" "write_site52etf_public_snapshot" "52ETF public snapshot writer is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/site52etf.py" "load_site52etf_public_snapshot_latest" "52ETF public snapshot latest loader is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/site52etf.py" "raw HTML is not stored" "52ETF public snapshot token policy is present"
check_text "$PROJECT_DIR/src/pfi_os/integrations/site52etf.py" "build_site52etf_hotspot_comparison" "52ETF hotspot comparison builder is present"
check_text "$PROJECT_DIR/scripts/site52etfSnapshot.sh" "site52etf_snapshot" "52ETF public snapshot shell entry is wired"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "load_site52etf_public_snapshot_latest" "52ETF UI prefers local latest snapshot"
check_text "$PROJECT_DIR/src/pfi_os/app/streamlit_app.py" "snapshot_source" "52ETF UI labels local latest snapshot source"
check_text "$PROJECT_DIR/src/pfi_os/analysis/portfolio.py" "portfolio_stress_scenarios" "Portfolio stress scenarios are present"
check_text "$PROJECT_DIR/src/pfi_os/reports/export.py" "_add_strategy_diagnostics_section" "Word report includes strategy diagnostics"
check_text "$PROJECT_DIR/src/pfi_os/reports/export.py" "_add_bootstrap_robustness_section" "Word report includes Bootstrap robustness"
check_text "$PROJECT_DIR/src/pfi_os/reports/export.py" "_add_decision_quality_section" "Word report includes Decision Quality"
check_text "$PROJECT_DIR/src/pfi_os/reports/export.py" "_add_experiment_visuals" "Experiment report includes visuals"
check_text "$PROJECT_DIR/src/pfi_os/data/providers/moomoo_provider.py" "QuoteContext" "Moomoo quote-only provider is present"
check_text "$PROJECT_DIR/src/pfi_os/data/validation.py" "CrossSourceValidationResult" "Cross-source validation model is present"
check_text "$PROJECT_DIR/src/pfi_os/approvals/registry.py" "StrategyApprovalRegistry" "Strategy approval registry is present"
check_text "$PROJECT_DIR/docs/OpenSourceReference.md" "QuantStats" "Open-source reference includes QuantStats"
check_text "$PROJECT_DIR/docs/OpenSourceReference.md" "pyfolio" "Open-source reference includes pyfolio"
check_text "$PROJECT_DIR/docs/OpenSourceReference.md" "Qlib" "Open-source reference includes Qlib"
check_text "$PROJECT_DIR/docs/AcceptanceChecklist.md" "禁止实盘交易" "Research-only safety boundary is documented"

echo
echo "Running code verification..."
if "$PROJECT_DIR/scripts/verifyPFI.sh"; then
  pass "Full code verification passed"
else
  fail "Full code verification failed"
fi

echo
echo "Running non-network daily check..."
if "$PROJECT_DIR/scripts/dailyCheck.sh"; then
  pass "Daily check passed"
else
  fail "Daily check failed"
fi

echo
echo "Summary"
echo "PASS: $PASS_COUNT"
echo "FAIL: $FAIL_COUNT"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi

echo "PFI final acceptance check completed."
