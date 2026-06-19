from pathlib import Path
import shutil
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_daily_check_network_mode_continues_after_provider_failures():
    script = (PROJECT_ROOT / "scripts" / "dailyCheck.sh").read_text(encoding="utf-8")

    assert "PY_ARGS=()" in script
    assert '"${PY_ARGS[@]}"' in script
    assert "if scripts/validateRealData.sh; then" in script
    assert "Continuing daily check so other diagnostics can still run." in script
    assert "if scripts/validateCrossSource.sh; then" in script
    assert "Review the output above." in script


def test_moomoo_check_script_is_quote_diagnostic_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "checkMoomoo.sh").read_text(encoding="utf-8")

    assert "quantlab.examples.validate_moomoo" in script


def test_verify_script_does_not_lower_bootstrap_simulation_count():
    script = (PROJECT_ROOT / "scripts" / "verifyQuantLab.sh").read_text(encoding="utf-8")

    assert "QUANTLAB_TEST_BOOTSTRAP_SIMULATIONS=300" not in script
    assert "scripts/finalAcceptanceCheck.sh" in script
    assert "-p no:cacheprovider" in script
    assert "src/quantlab/storage.py" in script
    assert "src/quantlab/approvals/registry.py" in script
    assert "src/quantlab/research/reviews.py" in script
    assert "src/quantlab/research/validation_queue.py" in script
    assert "src/quantlab/research/report_gap_tasks.py" in script
    assert "src/quantlab/reports/decision_support.py" in script
    assert "src/quantlab/examples/report_gap_tasks.py" in script
    assert "src/quantlab/examples/validation_priority_plan.py" in script
    assert "src/quantlab/examples/validation_task_execution.py" in script
    assert "scripts/reportGapTasks.sh" in script
    assert "scripts/validationPriorityPlan.sh" in script
    assert "scripts/runValidationTask.sh" in script
    assert "src/quantlab/research/validation_priority.py" in script
    assert "src/quantlab/research/validation_execution.py" in script
    assert "src/quantlab/strategies/custom_builder.py" in script
    assert "src/quantlab/strategies/profiles.py" in script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "QUANTLAB_REPORT_DIR" in script
    assert "/private/tmp/quantlab-report-test" in script
    assert "src/quantlab/system/eva_identity.py" in script
    assert "quantlab_ensure_app_python" in script
    assert "${PROJECT_DIR}[test]" in script
    assert "scripts/quantlabRuntime.sh" in script
    assert "MPLCONFIGDIR" in script


def test_heavy_smoke_scripts_require_explicit_confirmation():
    final_acceptance = (PROJECT_ROOT / "scripts" / "finalAcceptanceCheck.sh").read_text(encoding="utf-8")
    ci_smoke = (PROJECT_ROOT / "scripts" / "ciSmoke.sh").read_text(encoding="utf-8")
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")

    for script in (final_acceptance, ci_smoke):
        assert "EVA_OS_ALLOW_HEAVY_SMOKE" in script
        assert "scripts/devReadyCheck.sh --summary-json" in script
        assert "exit 64" in script

    assert 'EVA_OS_ALLOW_HEAVY_SMOKE: "1"' in workflow
    assert "workflow_dispatch:" in workflow
    assert "pull_request:" in workflow
    assert "\n  push:" not in workflow


def test_sensitive_holdings_paths_are_gitignored():
    patterns = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "data/holdings/*" in patterns
    assert "data/private/**" in patterns
    assert "data/external/**" in patterns
    assert "data/systemAudit/MacOSRuntimeAcceptance*.json" in patterns
    assert "data/systemAudit/UIVisualAcceptance*.json" in patterns
    assert "data/systemAudit/UIVisualAcceptance*.png" in patterns
    assert "!data/holdings/.gitkeep" in patterns


def test_shell_scripts_have_valid_zsh_syntax():
    zsh = shutil.which("zsh")
    if zsh is None:
        import pytest

        pytest.skip("zsh is not installed in this test environment")

    scripts = [
        "StartQuantLab.command",
        "StopQuantLab.command",
        "scripts/quantlabRuntime.sh",
        "scripts/startQuantLab.sh",
        "scripts/stopQuantLab.sh",
        "scripts/installMacAppLaunchers.sh",
        "scripts/statusQuantLab.sh",
        "scripts/devReadyCheck.sh",
        "scripts/macosAcceptance.sh",
        "scripts/macosAppAcceptanceLite.sh",
        "scripts/macosLifecycleReadiness.sh",
        "scripts/macosRuntimeAcceptance.sh",
        "scripts/uiVisualAcceptance.sh",
        "scripts/macosPublicAcceptanceSummary.sh",
        "scripts/verifyQuantLab.sh",
        "scripts/finalAcceptanceCheck.sh",
        "scripts/createSampleReport.sh",
        "scripts/setupEnv.sh",
        "scripts/validateRealData.sh",
        "scripts/validateCrossSource.sh",
        "scripts/checkMoomoo.sh",
        "scripts/dailyCheck.sh",
        "scripts/runTests.sh",
        "scripts/cleanCache.sh",
        "scripts/cleanReportJunk.sh",
        "scripts/openReports.sh",
        "scripts/researchBusApi.sh",
        "scripts/syncResearchBus.sh",
        "scripts/runIndependentValidation.sh",
        "scripts/watchResearchBus.sh",
        "scripts/syncResearchSystemsOnce.sh",
        "scripts/watchResearchSystems.sh",
        "scripts/installResearchBusLaunchAgent.sh",
        "scripts/researchBusWebhook.sh",
        "scripts/tokenRoiLedger.sh",
        "scripts/tokenRoiReviewedValueRefresh.sh",
        "scripts/cashFlowReviewedInputRefresh.sh",
        "scripts/policyReviewedInputRefresh.sh",
        "scripts/consumptionReviewedInputRefresh.sh",
        "scripts/refreshRuntimeSummaries.sh",
        "scripts/commandCenter.sh",
        "scripts/marketEventLayer.sh",
        "scripts/dataLakeManifest.sh",
        "scripts/eventReplay.sh",
        "scripts/vectorizedResearch.sh",
        "scripts/hotspotRuntimeSummary.sh",
        "scripts/site52etfSnapshot.sh",
        "scripts/reportValidation.sh",
        "scripts/reportDecisionSupport.sh",
        "scripts/reportGapTasks.sh",
        "scripts/validationPriorityPlan.sh",
        "scripts/runValidationTask.sh",
    ]

    for script in scripts:
        subprocess.run([zsh, "-n", str(PROJECT_ROOT / script)], check=True)


def test_double_click_launcher_refreshes_existing_streamlit_service():
    script = (PROJECT_ROOT / "StartQuantLab.command").read_text(encoding="utf-8")

    assert "Reusing the existing service" in script
    assert "_stcore/health" in script
    assert "quantlab_launch.lockdir" in script
    assert "LOCK_PID_FILE" in script
    assert "Removing stale QuantLab launch lock" in script
    assert "Another QuantLab launch is already starting" in script
    assert "QUANTLAB_HEARTBEAT_TIMEOUT:-120" in script
    assert "--server.address 127.0.0.1" in script
    assert "--server.fileWatcherType none" in script
    assert "--browser.gatherUsageStats false" in script
    assert "xargs kill" not in script
    assert "quantlab_ensure_app_python" in script
    assert ".[app,test,data]" not in script
    assert "codex-primary-runtime" not in script


def test_quiet_start_uses_stable_local_streamlit_settings():
    script = (PROJECT_ROOT / "scripts" / "startQuantLab.sh").read_text(encoding="utf-8")
    runtime = (PROJECT_ROOT / "scripts" / "quantlabRuntime.sh").read_text(encoding="utf-8")
    stop_script = (PROJECT_ROOT / "scripts" / "stopQuantLab.sh").read_text(encoding="utf-8")

    assert "--server.address 127.0.0.1" in script
    assert "--server.fileWatcherType none" in script
    assert "--browser.gatherUsageStats false" in script
    assert "_stcore/health" in script
    assert "quantlab_ensure_app_python" in script
    assert "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION" in runtime
    assert "QUANTLAB_PYTHON" in runtime
    assert "/opt/anaconda3/bin/python3.12" in runtime
    assert "pyarrow" in runtime
    assert ".quantlab_app_ready" in runtime
    assert "[app]" in runtime
    assert ".[app,test,data]" not in runtime
    assert "process_cwd" in stop_script
    assert 'cwd_path" == "$PROJECT_DIR"' in stop_script
    assert "src/quantlab/app/streamlit_app.py" in stop_script
    assert "quantlab_launch.lockdir" in stop_script
    assert 'pgrep -f "$PROJECT_DIR/StartQuantLab.command"' in stop_script
    assert "Stopping QuantLab launcher pid" in stop_script
    assert 'rm -rf "$LOCK_DIR"' in stop_script


def test_report_package_exports_are_lazy_for_light_ui_startup():
    reports_init = (PROJECT_ROOT / "src" / "quantlab" / "reports" / "__init__.py").read_text(encoding="utf-8")
    streamlit_app = (PROJECT_ROOT / "src" / "quantlab" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

    assert "__getattr__" in reports_init
    assert "_EXPORTS" in reports_init
    assert "from quantlab.reports.export import" not in reports_init
    assert "from quantlab.reports import export_backtest_docx" not in streamlit_app.split("from quantlab.reports.catalog", maxsplit=1)[0]


def test_streamlit_lifecycle_panel_uses_allowlisted_local_scripts_only():
    streamlit_app = (PROJECT_ROOT / "src" / "quantlab" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

    assert "render_macos_lifecycle_panel" in streamlit_app
    assert "macos_runtime_evidence_summary" in streamlit_app
    assert "MacOSRuntimeAcceptance_latest.json" in streamlit_app
    assert "render_vectorized_research_panel" in streamlit_app
    assert "vectorized_research_shell_summary(payload)" in streamlit_app
    assert "VectorizedResearch_latest.json" in streamlit_app
    assert "render_hotspot_runtime_summary" in streamlit_app
    assert "render_hotspot_preflight" in streamlit_app
    assert "hotspot_quick_preflight" in streamlit_app
    assert "EVAOSHotspotQuickPreflightV1" in streamlit_app
    assert "高级缓存与清理" in streamlit_app
    assert "hotspot_runtime_summary(" in streamlit_app
    assert "hotspot_runtime_cache_key" in streamlit_app
    assert "render_hotspot_cache_controls" in streamlit_app
    assert "render_hotspot_request_trace" in streamlit_app
    assert "invalidate_hotspot_persisted_cache" in streamlit_app
    assert "hotspot_cache_directory_summary" in streamlit_app
    assert "apply_research_chart_ux" in streamlit_app
    assert "research_chart_config" in streamlit_app
    assert "scrollZoom" in streamlit_app
    assert "render_parameter_scan_preflight" in streamlit_app
    assert "parameter_scan_preflight" in streamlit_app
    assert "EVAOSParameterScanPreflightV1" in streamlit_app
    assert "LIFECYCLE_SCRIPT_ALLOWLIST" in streamlit_app
    assert '"scripts/statusQuantLab.sh": 8' in streamlit_app
    assert '"scripts/stopQuantLab.sh": 20' in streamlit_app
    assert '"scripts/macosAcceptance.sh": 70' in streamlit_app
    assert '"scripts/devReadyCheck.sh": 45' in streamlit_app
    assert '"scripts/cleanCache.sh": 60' in streamlit_app
    assert '"scripts/macosAppAcceptanceLite.sh": 30' in streamlit_app
    assert '"scripts/macosLifecycleReadiness.sh": 40' in streamlit_app
    assert "macos_lifecycle_acceptance_lite" in streamlit_app
    assert "macos_lifecycle_daily_acceptance" in streamlit_app
    assert "macos_lifecycle_dev_ready" in streamlit_app
    assert "macos_lifecycle_readiness" in streamlit_app
    assert "macosRuntimeAcceptance.sh" not in streamlit_app
    assert "运行时验收证据" in streamlit_app
    assert "优先使用日常验收" in streamlit_app
    assert "高级单项验收" in streamlit_app
    assert "build_cache_cleanup_report(ROOT, dry_run=True)" in streamlit_app
    assert "缓存清理会在服务运行时自动拒绝" in streamlit_app
    assert "Lifecycle script not allowed" in streamlit_app
    assert "shell=True" not in streamlit_app


def test_final_acceptance_check_covers_product_artifacts_without_opening_browser():
    path = PROJECT_ROOT / "scripts" / "finalAcceptanceCheck.sh"
    script = path.read_text(encoding="utf-8")

    assert path.exists()
    assert "scripts/verifyQuantLab.sh" in script
    assert "scripts/dailyCheck.sh" in script
    assert "show_report_center_dashboard" in script
    assert "sidebar_usage_guide" in script
    assert "render_macos_lifecycle_panel" in script
    assert "LIFECYCLE_SCRIPT_ALLOWLIST" in script
    assert "macos_lifecycle_dev_ready" in script
    assert "scripts/devReadyCheck.sh" in script
    assert "Dev Ready Check" in script
    assert "build_cache_cleanup_report" in script
    assert "macos_lifecycle_summary" in script
    assert "macos_runtime_evidence_summary" in script
    assert "MacOSRuntimeAcceptance_latest.json" in script
    assert "render_vectorized_research_panel" in script
    assert "vectorized_research_shell_summary" in script
    assert "vectorizedResearch.sh" in script
    assert "hotspotRuntimeSummary.sh" in script
    assert "VectorizedResearchMode.md" in script
    assert "build_vectorized_research" in script
    assert "EVAOSVectorizedResearchBatchV1" in script
    assert "EVAOSHotspotRuntimeSummaryV1" in script
    assert "EVAOSHotspotCacheStatusV1" in script
    assert "EVAOSHotspotRequestTraceV1" in script
    assert "hotspot_runtime_summary" in script
    assert "render_hotspot_runtime_summary" in script
    assert "apply_research_chart_ux" in script
    assert "research_chart_config" in script
    assert "Lifecycle controls only manage the local EVA_OS/QuantLab app process" in script
    assert "show_strategy_diagnostics" in script
    assert "show_portfolio_risk_view" in script
    assert "show_decision_quality" in script
    assert "show_trade_review_panel" in script
    assert "show_validation_queue_panel" in script
    assert "show_report_decision_support_panel" in script
    assert "build_report_validation_hub" in script
    assert "append_report_gap_validation_tasks" in script
    assert "write_validation_priority_plan" in script
    assert "write_validation_task_execution" in script
    assert "industry_research_view" in script
    assert "research_bus_monitor_view" in script
    assert "holdings_view" in script
    assert "sentiment_analysis_view" in script
    assert "personal_profile_view" in script
    assert "built_in_strategy_order_editor" in script
    assert "built_in_strategy_parameter_editor" in script
    assert "alipay_enhanced" in script
    assert "OpenSourceReference.md" in script
    assert 'APP_BUNDLE_NAME="EVA_OS"' in script
    assert "$DESKTOP_DIR/$APP_BUNDLE_NAME.app" in script
    assert "$DOWNLOADS_DIR/$APP_BUNDLE_NAME.app" in script
    assert "$APP_INSTALL_DIR/$APP_BUNDLE_NAME.app" in script
    assert "EVA_OS" in script
    assert "QuantLabAppIcon.icns" in script
    assert "installMacAppLaunchers.sh" in script
    assert "macosAppAcceptanceLite.sh" in script
    assert "macosAcceptance.sh" in script
    assert "macosLifecycleReadiness.sh" in script
    assert "macosRuntimeAcceptance.sh" in script
    assert "macosPublicAcceptanceSummary.sh" in script
    assert "macos_acceptance.py" in script
    assert "macos_lifecycle.py" in script
    assert "macos_runtime_acceptance.py" in script
    assert "macos_public_acceptance.py" in script
    assert "macos_acceptance_hub.py" in script
    assert "EVAOSMacOSAppAcceptanceLiteV1" in script
    assert "EVAOSMacOSLifecycleReadinessV1" in script
    assert "DevReadyScriptExecutable" in script
    assert "EVAOSMacOSRuntimeAcceptanceV1" in script
    assert "MacOSAcceptancePublicSummary_latest.json" in script
    assert "MacOSPublicAcceptanceSummary.md" in script
    assert "Contents/MacOS/EVA_OS" in script
    assert "Contents/MacOS/applet" not in script
    assert "check_absent" in script
    assert "check_text_absent" in script
    assert "EVA_OS_PROJECT_ROOT" in script
    assert "EVA_OS_APP_LAUNCH_DRY_RUN" in script
    assert "does not fall back to GitHub" in script
    assert "check_app_signature" in script
    assert "decision_quality.py" in script
    assert "reviews.py" in script
    assert "validation_queue.py" in script
    assert "external_systems.py" in script
    assert "holdings_book.py" in script
    assert "sentiment.py" in script
    assert "value/token_roi.py" in script
    assert "tokenRoiLedger.sh" in script
    assert "EVATokenROIRuntimeSummaryV1" in script
    assert "does not include full records" in script
    assert "summary-json" in script
    assert "运行摘要与证据闸门" in script
    assert "EVAOSCompanyCashFlowRuntimeSummaryV1" in script
    assert "does not include full entries" in script
    assert "build_cashflow_runtime_summary" in script
    assert "EVAOSPolicyIntelligenceRuntimeSummaryV1" in script
    assert "does not include full opportunities" in script
    assert "build_policy_runtime_summary" in script
    assert "EVAOSConsumptionGuardRuntimeSummaryV1" in script
    assert "does not include full events" in script
    assert "build_consumption_runtime_summary" in script
    assert "runtime_summary_sources" in script
    assert "EVATokenROIRuntimeSummary_latest.json" in script
    assert "CompanyCashFlowRuntimeSummary_latest.json" in script
    assert "PolicyIntelligenceRuntimeSummary_latest.json" in script
    assert "ConsumptionGuardRuntimeSummary_latest.json" in script
    assert "refreshRuntimeSummaries.sh" in script
    assert "runtime_summary_refresh.py" in script
    assert "EVAOSRuntimeSummaryRefreshV1" in script
    assert "reportDecisionSupport.sh" in script
    assert "reportValidation.sh" in script
    assert "reportGapTasks.sh" in script
    assert "validationPriorityPlan.sh" in script
    assert "runValidationTask.sh" in script
    assert "report_validation_hub.py" in script
    assert "EVAOSReportValidationHubV1" in script
    assert "ReportDecisionSupport.md" in script
    assert "ReportValidationHub.md" in script
    assert "ReportEvidenceGapTasks.md" in script
    assert "ValidationPriorityPlan.md" in script
    assert "ValidationTaskExecution.md" in script
    assert "_add_decision_quality_section" in script
    assert "error_profile_frame" in script
    assert "validation_task_frame" in script
    assert "collect_industry_reports" in script
    assert "load_holdings_frame" in script
    assert "sync_holdings_book" in script
    assert "load_pending_orders_frame" in script
    assert "sentiment_from_bars" in script
    assert "build_personal_profile" in script
    assert "portfolio_stress_scenarios" in script
    assert "/usr/bin/grep" in script
    assert "open " not in script
    assert "--network" not in script


def test_report_validation_hub_is_default_low_token_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "reportValidation.sh").read_text(encoding="utf-8")
    module = (PROJECT_ROOT / "src" / "quantlab" / "system" / "report_validation_hub.py").read_text(encoding="utf-8")
    cli = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "report_validation_hub.py").read_text(encoding="utf-8")
    streamlit_app = (PROJECT_ROOT / "src" / "quantlab" / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    docs = (PROJECT_ROOT / "docs" / "ReportValidationHub.md").read_text(encoding="utf-8")

    assert "quantlab.examples.report_validation_hub" in script
    assert "set -- --mode daily --summary-json" in script
    assert "EVAOSReportValidationHubV1" in module
    assert "build_report_validation_hub" in cli
    assert "summary-json" in cli
    assert "does not include full report records" in module
    assert '"writes_files": False' in module
    assert '"mutates_validation_queue": False' in module
    assert '"executes_validation": False' in module
    assert "报告验证工作台" in streamlit_app
    assert "高级动作：入队、排序和执行" in streamlit_app
    assert "高级动作：写入报告证据索引产物" in streamlit_app
    assert "默认只读合并报告证据、补证据候选和验证优先级" in docs


def test_dev_ready_check_is_default_light_gate_without_heavy_release_steps():
    script = (PROJECT_ROOT / "scripts" / "devReadyCheck.sh").read_text(encoding="utf-8")
    module = (PROJECT_ROOT / "src" / "quantlab" / "system" / "dev_readiness.py").read_text(encoding="utf-8")
    cli = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "dev_ready_check.py").read_text(encoding="utf-8")

    assert "quantlab.examples.dev_ready_check" in script
    assert "EVAOSDevReadyCheckV1" in module
    assert "build_dev_ready_check" in cli
    assert "dirty_worktree_is_failure" in module
    assert "runs_heavy_release_gates" in module
    assert "scripts/uiVisualAcceptance.sh" in module
    for forbidden in (
        "finalAcceptanceCheck.sh",
        "ciSmoke.sh",
        "runTests.sh",
        "pytest",
        "run_strategy_smoke_test",
    ):
        assert forbidden not in script


def test_token_roi_ledger_script_is_value_layer_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "tokenRoiLedger.sh").read_text(encoding="utf-8")
    reviewed_script = (PROJECT_ROOT / "scripts" / "tokenRoiReviewedValueRefresh.sh").read_text(encoding="utf-8")
    example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "token_roi_ledger.py").read_text(encoding="utf-8")
    reviewed_example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "token_roi_reviewed_value_refresh.py").read_text(
        encoding="utf-8"
    )
    token_roi = (PROJECT_ROOT / "src" / "quantlab" / "value" / "token_roi.py").read_text(encoding="utf-8")
    reviewed = (PROJECT_ROOT / "src" / "quantlab" / "value" / "reviewed_input.py").read_text(encoding="utf-8")
    streamlit_app = (PROJECT_ROOT / "src" / "quantlab" / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    schema = (PROJECT_ROOT / "shared" / "schema" / "token_roi_reviewed_value_evidence.schema.json").read_text(
        encoding="utf-8"
    )

    assert "quantlab.examples.token_roi_ledger" in script
    assert "quantlab.examples.token_roi_reviewed_value_refresh" in reviewed_script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "summary-json" in example
    assert "manual-entry-path" in example
    assert "EVATokenROIReviewedValueEvidenceRefreshV1" in reviewed_example
    assert "data/private/value/TokenROIReviewedValueEvidence.json" in reviewed
    assert "TokenROIReviewedValueEvidence.example.json" in reviewed
    assert "Local reviewed JSON input only" in reviewed
    assert "EVA_OS Token ROI Reviewed Value Evidence" in schema
    assert "EVATokenROIRuntimeSummaryV1" in token_roi
    assert "build_token_roi_runtime_summary" in token_roi
    assert "does not include full records" in token_roi
    assert "运行摘要与证据闸门" in streamlit_app


def test_command_center_prefers_compact_runtime_summary_sources():
    command_center = (PROJECT_ROOT / "src" / "quantlab" / "executive" / "command_center.py").read_text(encoding="utf-8")

    assert "runtime_summary_sources" in command_center
    assert "EVATokenROIRuntimeSummary_latest.json" in command_center
    assert "CompanyCashFlowRuntimeSummary_latest.json" in command_center
    assert "PolicyIntelligenceRuntimeSummary_latest.json" in command_center
    assert "ConsumptionGuardRuntimeSummary_latest.json" in command_center


def test_cashflow_command_script_is_business_layer_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "cashFlowCommand.sh").read_text(encoding="utf-8")
    reviewed_script = (PROJECT_ROOT / "scripts" / "cashFlowReviewedInputRefresh.sh").read_text(encoding="utf-8")
    example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "cashflow_command.py").read_text(encoding="utf-8")
    reviewed_example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "cashflow_reviewed_input_refresh.py").read_text(encoding="utf-8")
    cashflow = (PROJECT_ROOT / "src" / "quantlab" / "business" / "cashflow.py").read_text(encoding="utf-8")
    reviewed = (PROJECT_ROOT / "src" / "quantlab" / "business" / "cashflow_reviewed_input.py").read_text(encoding="utf-8")
    streamlit_app = (PROJECT_ROOT / "src" / "quantlab" / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    schema = (PROJECT_ROOT / "shared" / "schema" / "company_cashflow_reviewed_input.schema.json").read_text(encoding="utf-8")

    assert "quantlab.examples.cashflow_command" in script
    assert "quantlab.examples.cashflow_reviewed_input_refresh" in reviewed_script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "QUANTLAB_PYTHON" in script
    assert "command -v python3" in script
    assert "summary-json" in example
    assert "EVAOSCompanyCashFlowReviewedInputRefreshV1" in reviewed_example
    assert "data/private/cashflow/CompanyCashFlowReviewedInput.json" in reviewed
    assert "CompanyCashFlowReviewedInput.example.json" in reviewed
    assert "Local reviewed JSON input only" in reviewed
    assert "Company CashFlow Reviewed Input" in schema
    assert "EVAOSCompanyCashFlowRuntimeSummaryV1" in cashflow
    assert "build_cashflow_runtime_summary" in cashflow
    assert "does not include full entries" in cashflow
    assert "build_cashflow_runtime_summary" in streamlit_app


def test_policy_radar_script_is_policy_layer_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "policyRadar.sh").read_text(encoding="utf-8")
    reviewed_script = (PROJECT_ROOT / "scripts" / "policyReviewedInputRefresh.sh").read_text(encoding="utf-8")
    example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "policy_radar.py").read_text(encoding="utf-8")
    reviewed_example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "policy_reviewed_input_refresh.py").read_text(
        encoding="utf-8"
    )
    policy = (PROJECT_ROOT / "src" / "quantlab" / "policy" / "radar.py").read_text(encoding="utf-8")
    reviewed = (PROJECT_ROOT / "src" / "quantlab" / "policy" / "reviewed_input.py").read_text(encoding="utf-8")
    streamlit_app = (PROJECT_ROOT / "src" / "quantlab" / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    schema = (PROJECT_ROOT / "shared" / "schema" / "policy_reviewed_input.schema.json").read_text(encoding="utf-8")

    assert "quantlab.examples.policy_radar" in script
    assert "quantlab.examples.policy_reviewed_input_refresh" in reviewed_script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "QUANTLAB_PYTHON" in script
    assert "command -v python3" in script
    assert "summary-json" in example
    assert "EVAOSPolicyReviewedInputRefreshV1" in reviewed_example
    assert "data/private/policy/PolicyReviewedInput.json" in reviewed
    assert "PolicyReviewedInput.example.json" in reviewed
    assert "Local reviewed JSON input only" in reviewed
    assert "EVA_OS Policy Reviewed Input" in schema
    assert "EVAOSPolicyIntelligenceRuntimeSummaryV1" in policy
    assert "build_policy_runtime_summary" in policy
    assert "does not include full opportunities" in policy
    assert "build_policy_runtime_summary" in streamlit_app


def test_consumption_guard_script_is_consumption_layer_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "consumptionGuard.sh").read_text(encoding="utf-8")
    reviewed_script = (PROJECT_ROOT / "scripts" / "consumptionReviewedInputRefresh.sh").read_text(encoding="utf-8")
    example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "consumption_guard.py").read_text(encoding="utf-8")
    reviewed_example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "consumption_reviewed_input_refresh.py").read_text(
        encoding="utf-8"
    )
    consumption = (PROJECT_ROOT / "src" / "quantlab" / "consumption" / "guard.py").read_text(encoding="utf-8")
    reviewed = (PROJECT_ROOT / "src" / "quantlab" / "consumption" / "reviewed_input.py").read_text(encoding="utf-8")
    streamlit_app = (PROJECT_ROOT / "src" / "quantlab" / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    schema = (PROJECT_ROOT / "shared" / "schema" / "consumption_guard_reviewed_input.schema.json").read_text(encoding="utf-8")

    assert "quantlab.examples.consumption_guard" in script
    assert "quantlab.examples.consumption_reviewed_input_refresh" in reviewed_script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "QUANTLAB_PYTHON" in script
    assert "command -v python3" in script
    assert "summary-json" in example
    assert "EVAOSConsumptionGuardReviewedInputRefreshV1" in reviewed_example
    assert "data/private/consumption/ConsumptionGuardReviewedInput.json" in reviewed
    assert "ConsumptionGuardReviewedInput.example.json" in reviewed
    assert "Local reviewed JSON input only" in reviewed
    assert "EVA_OS Consumption Guard Reviewed Input" in schema
    assert "EVAOSConsumptionGuardRuntimeSummaryV1" in consumption
    assert "build_consumption_runtime_summary" in consumption
    assert "does not include full events" in consumption
    assert "build_consumption_runtime_summary" in streamlit_app


def test_hotspot_runtime_summary_script_is_sample_only_smoke_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "hotspotRuntimeSummary.sh").read_text(encoding="utf-8")
    verify = (PROJECT_ROOT / "scripts" / "verifyQuantLab.sh").read_text(encoding="utf-8")
    example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "hotspot_runtime_summary.py").read_text(encoding="utf-8")

    assert "quantlab.examples.hotspot_runtime_summary" in script
    assert "--use-persisted-cache" in example
    assert "--cache-status" in example
    assert "--invalidate-cache" in example
    assert "elapsed_ms=" in example
    assert "request_trace" in example
    assert "data/cache/hotspots" in example
    assert "PYTHONPYCACHEPREFIX" in script
    assert "hotspotRuntimeSummary.sh" in verify
    assert "src/quantlab/examples/hotspot_runtime_summary.py" in verify


def test_site52etf_snapshot_script_is_read_only_reference_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "site52etfSnapshot.sh").read_text(encoding="utf-8")
    example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "site52etf_snapshot.py").read_text(encoding="utf-8")
    integration = (PROJECT_ROOT / "src" / "quantlab" / "integrations" / "site52etf.py").read_text(encoding="utf-8")
    streamlit_app = (PROJECT_ROOT / "src" / "quantlab" / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "quantlab.examples.site52etf_snapshot" in script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "EVAOS52ETFPublicSnapshotV1" in integration
    assert "write_site52etf_public_snapshot" in integration
    assert "load_site52etf_public_snapshot_latest" in integration
    assert "raw HTML is not stored" in integration
    assert "summary-json" in example
    assert "source-html" in example
    assert "load_site52etf_public_snapshot_latest" in streamlit_app
    assert "snapshot_source" in streamlit_app
    assert "data/integrations/site52etf/*" in gitignore


def test_macos_app_installer_builds_standard_app_bundle():
    launcher = (PROJECT_ROOT / "macos" / "EVA_OS_launcher.c").read_text(encoding="utf-8")
    wrapper = (PROJECT_ROOT / "scripts" / "installMacAppLaunchers.sh").read_text(encoding="utf-8")
    installer = (PROJECT_ROOT / "scripts" / "installEVAOSEntryApps.sh").read_text(encoding="utf-8")

    assert "EVA_OS_PROJECT_ROOT" in launcher
    assert "EVA_OS_APP_LAUNCH_DRY_RUN" in launcher
    assert "running_url" in launcher
    assert "./StartQuantLab.command" in launcher
    assert "mode=spawn-command" in launcher
    assert "posix_spawn" in launcher
    assert "spawn_command_direct" in launcher
    assert '"/bin/zsh"' in launcher
    assert '"-f"' in launcher
    assert "open_command_in_terminal" not in launcher
    assert '"Terminal"' not in launcher
    assert "_stcore/health" in launcher
    assert "--connect-timeout 0.15 --max-time 0.3" in launcher
    assert "http://127.0.0.1" in launcher
    assert "EVA_OS local project was not found" in launcher
    assert "github.com/LinzeColin/EVA_OS" not in launcher
    assert "tell application \"Terminal\"" not in launcher
    assert "installEVAOSEntryApps.sh" in wrapper
    assert 'LAUNCHER_SOURCE="$ROOT_DIR/macos/EVA_OS_launcher.c"' in installer
    assert 'clang -O2 -Wall -Wextra' in installer
    assert 'SOURCE_APP="$ROOT_DIR/macos/EVA_OS.app"' in installer
    assert 'DESKTOP_APP="$HOME/Desktop/EVA_OS.app"' in installer
    assert 'DOWNLOADS_APP="$HOME/Downloads/EVA_OS.app"' in installer
    assert 'APPLICATIONS_APP="/Applications/EVA_OS.app"' in installer
    assert 'mktemp -d "${TMPDIR:-/tmp}/eva_os_app.XXXXXX"' in installer
    assert '/usr/bin/ditto --norsrc --noextattr --noacl "$SOURCE_APP" "$staging/EVA_OS.app"' in installer
    assert '/usr/bin/codesign --verify --deep --strict "$staging/EVA_OS.app"' in installer
    assert '/usr/bin/ditto --norsrc --noextattr --noacl "$staging/EVA_OS.app" "$target"' in installer
    assert '/usr/bin/codesign --verify --deep --strict "$target"' in installer
    assert 'EVA_OS_PROJECT_ROOT' in installer
    assert 'chmod +x "$target/Contents/MacOS/EVA_OS"' in installer
    assert 'xattr -cr "$staging/EVA_OS.app"' in installer
    assert 'codesign --force --deep --sign - "$staging/EVA_OS.app"' in installer
    assert "EVA_OS_ENTRY_APPS: installed" in installer


def test_macos_app_acceptance_lite_script_is_read_only_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "macosAppAcceptanceLite.sh").read_text(encoding="utf-8")
    example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "macos_app_acceptance_lite.py").read_text(
        encoding="utf-8"
    )
    module = (PROJECT_ROOT / "src" / "quantlab" / "system" / "macos_acceptance.py").read_text(encoding="utf-8")
    dashboard = (PROJECT_ROOT / "src" / "quantlab" / "app" / "dashboard.py").read_text(encoding="utf-8")

    assert "quantlab.examples.macos_app_acceptance_lite" in script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "EVAOSMacOSAppAcceptanceLiteV1" in module
    assert "build_macos_app_acceptance_lite" in module
    assert "write_macos_app_acceptance_lite" in module
    assert "finalAcceptanceCheck.sh" in module
    assert "ciSmoke.sh" in module
    assert "EVA_OS_APP_LAUNCH_DRY_RUN" in module
    assert "github.com/LinzeColin/EVA_OS" in module
    assert "summary-json" in example
    assert "skip-codesign" in example
    assert "Lite Acceptance" in dashboard
    assert "Dev Ready Check" in dashboard
    assert "Daily Acceptance" in dashboard
    assert "scripts/macosAcceptance.sh" in dashboard
    assert "scripts/devReadyCheck.sh" in dashboard
    assert "scripts/macosAppAcceptanceLite.sh" in dashboard


def test_macos_lifecycle_readiness_script_is_read_only_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "macosLifecycleReadiness.sh").read_text(encoding="utf-8")
    example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "macos_lifecycle_readiness.py").read_text(
        encoding="utf-8"
    )
    module = (PROJECT_ROOT / "src" / "quantlab" / "system" / "macos_lifecycle.py").read_text(encoding="utf-8")
    dashboard = (PROJECT_ROOT / "src" / "quantlab" / "app" / "dashboard.py").read_text(encoding="utf-8")

    assert "quantlab.examples.macos_lifecycle_readiness" in script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "EVAOSMacOSLifecycleReadinessV1" in module
    assert "build_macos_lifecycle_readiness" in module
    assert "write_macos_lifecycle_readiness" in module
    assert "finalAcceptanceCheck.sh" in module
    assert "ciSmoke.sh" in module
    assert "quantlab.system.shutdown_monitor" in module
    assert "build_cache_cleanup_report" in module
    assert "macosAppAcceptanceLite.sh" in module
    assert "does not start, stop, clean" in module
    assert "summary-json" in example
    assert "skip-app-acceptance" in example
    assert "Lifecycle Readiness" in dashboard
    assert "scripts/macosLifecycleReadiness.sh" in dashboard


def test_macos_runtime_acceptance_script_is_controlled_terminal_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "macosRuntimeAcceptance.sh").read_text(encoding="utf-8")
    example = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "macos_runtime_acceptance.py").read_text(
        encoding="utf-8"
    )
    module = (PROJECT_ROOT / "src" / "quantlab" / "system" / "macos_runtime_acceptance.py").read_text(
        encoding="utf-8"
    )
    dashboard = (PROJECT_ROOT / "src" / "quantlab" / "app" / "dashboard.py").read_text(encoding="utf-8")
    streamlit_app = (PROJECT_ROOT / "src" / "quantlab" / "app" / "streamlit_app.py").read_text(encoding="utf-8")

    assert "quantlab.examples.macos_runtime_acceptance" in script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "EVAOSMacOSRuntimeAcceptanceV1" in module
    assert "run_macos_runtime_acceptance" in module
    assert "write_macos_runtime_acceptance" in module
    assert "scripts/startQuantLab.sh" in module
    assert "scripts/stopQuantLab.sh" in module
    assert "CleanCacheRefusesWhileRunning" in module
    assert "NoPreExistingService" in module
    assert "direct_fallback" in module
    assert "_app_launch_observed" in module
    assert "finalAcceptanceCheck.sh" in module
    assert "ciSmoke.sh" in module
    assert "does not open" in module
    assert "allow-existing-service" in example
    assert "launch-method" in example
    assert "app-path" in example
    assert "failed_checks" in example
    assert "start_timeout = 300" in example
    assert "default=45" in example
    assert "Runtime Acceptance" in dashboard
    assert "App Open Acceptance" in dashboard
    assert "scripts/macosRuntimeAcceptance.sh --summary-json" in dashboard
    assert "scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/EVA_OS.app --summary-json" in dashboard
    assert "scripts/macosRuntimeAcceptance.sh" not in streamlit_app


def test_ui_visual_acceptance_uses_browser_without_heavy_smoke():
    script = (PROJECT_ROOT / "scripts" / "uiVisualAcceptance.sh").read_text(encoding="utf-8")

    assert "EVAOSUIVisualAcceptanceV1" in script
    assert "playwright" in script
    assert "Google Chrome.app" in script
    assert "工作台状态" in script
    assert "macOS 生命周期" in script
    assert "运行时验收证据" in script
    assert "LifecycleButton" in script
    assert "scrollIntoViewIfNeeded" in script
    assert "scripts/startQuantLab.sh" in script
    assert "scripts/stopQuantLab.sh" in script
    assert "scripts/finalAcceptanceCheck.sh" in script
    assert "scripts/ciSmoke.sh" in script
    assert "full pytest" in script
    assert "market refresh" in script
    assert "broker connections" in script
    assert "orders" in script
    assert "open " not in script
    assert "EVA_OS_ALLOW_HEAVY_SMOKE" not in script


def test_macos_public_acceptance_summary_is_sanitized_and_lightweight():
    script = (PROJECT_ROOT / "scripts" / "macosPublicAcceptanceSummary.sh").read_text(encoding="utf-8")
    module = (PROJECT_ROOT / "src" / "quantlab" / "system" / "macos_public_acceptance.py").read_text(encoding="utf-8")
    docs = (PROJECT_ROOT / "docs" / "MacOSPublicAcceptanceSummary.md").read_text(encoding="utf-8")

    assert "EVAOSMacOSPublicAcceptanceSummaryV1" in module
    assert "MacOSRuntimeAcceptance_latest.json" in module
    assert "UIVisualAcceptance_latest.json" in module
    assert "docs/evidence" in script
    assert "finalAcceptanceCheck.sh" in module
    assert "ciSmoke.sh" in module
    assert "full pytest" in module
    assert "raw local evidence" in module
    assert "local-only details" in module
    assert "docs/evidence/MacOSAcceptancePublicSummary_latest.json" in docs
    assert "启动服务" in docs
    assert "open " not in script
    assert "EVA_OS_ALLOW_HEAVY_SMOKE" not in script


def test_macos_acceptance_hub_is_user_friendly_default_entry():
    script = (PROJECT_ROOT / "scripts" / "macosAcceptance.sh").read_text(encoding="utf-8")
    module = (PROJECT_ROOT / "src" / "quantlab" / "system" / "macos_acceptance_hub.py").read_text(encoding="utf-8")
    cli = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "macos_acceptance_hub.py").read_text(encoding="utf-8")
    docs = (PROJECT_ROOT / "docs" / "MacOSAcceptanceHub.md").read_text(encoding="utf-8")

    assert "EVAOSMacOSAcceptanceHubV1" in module
    assert "daily" in module
    assert "scripts/devReadyCheck.sh" in module
    assert "scripts/macosPublicAcceptanceSummary.sh" in module
    assert "scripts/macosRuntimeAcceptance.sh" in module
    assert "scripts/uiVisualAcceptance.sh" in module
    assert "set -- --mode daily --summary-json" in script
    assert "choices=[" in cli
    assert "底层脚本仍保留" in docs
    assert "finalAcceptanceCheck.sh" in module
    assert "ciSmoke.sh" in module
    assert "full pytest" in module
    assert "EVA_OS_ALLOW_HEAVY_SMOKE" not in script


def test_clean_cache_refuses_running_app_and_preserves_install_metadata():
    script = (PROJECT_ROOT / "scripts" / "cleanCache.sh").read_text(encoding="utf-8")

    assert "quantlab_is_running" in script
    assert "process_cwd" in script
    assert 'cwd_path" == "$PROJECT_DIR"' in script
    assert "lsof -tiTCP" in script
    assert "streamlit_app.py" in script
    assert "Stop it before cleaning cache" in script
    assert "PYTHONDONTWRITEBYTECODE=1" in script
    assert "PYTHONPYCACHEPREFIX" in script
    assert "exit 2" in script
    assert "pgrep -f" not in script
    assert "*.egg-info" not in script


def test_research_bus_background_scripts_are_headless_and_dropbox_aware():
    watch = (PROJECT_ROOT / "scripts" / "watchResearchBus.sh").read_text(encoding="utf-8")
    once = (PROJECT_ROOT / "scripts" / "syncResearchSystemsOnce.sh").read_text(encoding="utf-8")
    installer = (PROJECT_ROOT / "scripts" / "installResearchBusLaunchAgent.sh").read_text(encoding="utf-8")

    assert "process-dropbox" in watch
    assert "process-dropbox" in once
    assert "research-bus-sync" in once
    assert "StartInterval" in installer
    assert "researchBusSyncRunner.sh" in installer
    assert "Application Support/QuantLab" in installer
    assert "RUNNER_LOG_DIR" in installer
    assert "research_bus_launchd.err.log" in installer
    assert "RESEARCH_BUS_STEP_TIMEOUT_SECONDS" in installer
    assert "open " not in watch
    assert "open " not in once
    assert "open " not in installer


def test_research_bus_webhook_script_is_local_only_entrypoint():
    script = (PROJECT_ROOT / "scripts" / "researchBusWebhook.sh").read_text(encoding="utf-8")
    server = (PROJECT_ROOT / "src" / "quantlab" / "examples" / "research_bus_webhook.py").read_text(encoding="utf-8")

    assert "quantlab.examples.research_bus_webhook" in script
    assert "127.0.0.1" in server
    assert "ThreadingHTTPServer" in server
    assert "submit_webhook_payload" in server
