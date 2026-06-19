from __future__ import annotations

import pandas as pd

from quantlab.app.dashboard import (
    macos_lifecycle_summary,
    macos_runtime_evidence_summary,
    vectorized_research_shell_summary,
    workspace_shell_summary,
)


def test_workspace_shell_summary_marks_canonical_systems_ready() -> None:
    payload = {
        "ready_count": 3,
        "systems": [
            _system("finance_ledger", "Finance Ledger"),
            _system("industry_research", "Industry Research"),
            _system("policy_intelligence", "Policy Intelligence"),
        ],
    }
    registry = pd.DataFrame(
        [
            {"system_name": "finance_ledger", "status": "Ready"},
            {"system_name": "industry_research", "status": "Ready"},
            {"system_name": "policy_intelligence", "status": "Ready"},
        ]
    )

    summary = workspace_shell_summary(payload, registry=registry)

    assert summary["schema"] == "WorkspaceShellSummaryV1"
    assert summary["status"] == "Ready"
    assert [card["value"] for card in summary["cards"]] == [3, 3, 3, 0]
    assert {row["系统"] for row in summary["rows"]} == {"finance_ledger", "industry_research", "policy_intelligence"}
    assert all(row["ResearchBus"] == "Ready" for row in summary["rows"])
    assert "/Users/" not in str(summary)


def test_workspace_shell_summary_flags_missing_research_bus_registration() -> None:
    payload = {"ready_count": 1, "systems": [_system("finance_ledger", "Finance Ledger")]}

    summary = workspace_shell_summary(payload, registry=pd.DataFrame())

    assert summary["status"] == "Review"
    assert summary["rows"][0]["ResearchBus"] == "NotRegistered"
    assert summary["cards"][-1]["value"] == 1


def test_macos_lifecycle_summary_disables_start_and_cache_when_running() -> None:
    summary = macos_lifecycle_summary(is_running=True)
    actions = {row["Action"]: row for row in summary["actions"]}

    assert summary["schema"] == "MacOSLifecycleSummaryV1"
    assert summary["status"] == "Running"
    assert actions["Daily Acceptance"]["enabled"] is True
    assert actions["Daily Acceptance"]["ui_mode"] == "UI"
    assert actions["Daily Acceptance"]["命令"] == "scripts/macosAcceptance.sh"
    assert actions["Status Check"]["enabled"] is True
    assert actions["Dev Ready Check"]["enabled"] is True
    assert actions["Dev Ready Check"]["ui_mode"] == "UI"
    assert actions["Dev Ready Check"]["命令"] == "scripts/devReadyCheck.sh"
    assert actions["Stop Service"]["enabled"] is True
    assert actions["Start Workbench"]["enabled"] is False
    assert actions["Clean Cache"]["enabled"] is False
    assert actions["Lite Acceptance"]["enabled"] is True
    assert actions["Lite Acceptance"]["ui_mode"] == "UI"
    assert actions["Lite Acceptance"]["命令"] == "scripts/macosAppAcceptanceLite.sh"
    assert actions["Lifecycle Readiness"]["enabled"] is True
    assert actions["Lifecycle Readiness"]["ui_mode"] == "UI"
    assert actions["Lifecycle Readiness"]["命令"] == "scripts/macosLifecycleReadiness.sh"
    assert actions["Runtime Acceptance"]["enabled"] is False
    assert actions["Runtime Acceptance"]["ui_mode"] == "Terminal"
    assert actions["Runtime Acceptance"]["禁用原因"] == "服务已在运行，避免误停当前会话"
    assert actions["App Open Acceptance"]["enabled"] is False
    assert actions["App Open Acceptance"]["ui_mode"] == "Terminal"
    assert actions["App Open Acceptance"]["禁用原因"] == "服务已在运行，避免误停当前会话"
    assert actions["Clean Cache"]["禁用原因"] == "先停止服务再清理缓存"
    assert actions["Final Acceptance"]["ui_mode"] == "Terminal"
    assert "/Users/" not in str(summary)


def test_macos_lifecycle_summary_allows_start_and_cache_when_stopped() -> None:
    summary = macos_lifecycle_summary(is_running=False)
    actions = {row["Action"]: row for row in summary["actions"]}

    assert summary["status"] == "Stopped"
    assert actions["Start Workbench"]["enabled"] is True
    assert actions["Clean Cache"]["enabled"] is True
    assert actions["Stop Service"]["enabled"] is False
    assert actions["Daily Acceptance"]["命令"] == "scripts/macosAcceptance.sh"
    assert actions["Status Check"]["命令"] == "scripts/statusQuantLab.sh"
    assert actions["Dev Ready Check"]["ui_mode"] == "UI"
    assert actions["Lite Acceptance"]["ui_mode"] == "UI"
    assert actions["Lifecycle Readiness"]["ui_mode"] == "UI"
    assert actions["Runtime Acceptance"]["enabled"] is True
    assert actions["Runtime Acceptance"]["命令"] == "scripts/macosRuntimeAcceptance.sh --summary-json"
    assert actions["App Open Acceptance"]["enabled"] is True
    assert actions["App Open Acceptance"]["命令"] == "scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/EVA_OS.app --summary-json"
    assert "~/Desktop/EVA_OS.app" in summary["app_paths"]
    assert "place orders" in summary["safety_policy"]


def test_vectorized_research_shell_summary_uses_compact_latest_payload() -> None:
    payload = {
        "schema": "EVAOSVectorizedResearchBatchV1",
        "status": "Pass",
        "replay_status": "Pass",
        "selected_symbol": "SPY",
        "strategy_id": "ma_crossover",
        "first_datetime": "2026-01-01T00:00:00",
        "last_datetime": "2026-01-09T00:00:00",
        "parameter_run_count": 4,
        "scan_run_count": 4,
        "best_run": {"run_id": "run_1", "sharpe": 1.234},
        "stability": {"stability_status": "Review", "parameter_coverage": 0.75},
        "summary_rows": [
            {
                "run_id": "run_1",
                "strategy_id": "ma_crossover",
                "param_short_window": 2,
                "param_long_window": 4,
                "total_return": 0.1234,
                "sharpe": 1.234,
                "max_drawdown": -0.0456,
                "trade_count": 3,
                "cost_total": 12.34,
            }
        ],
        "outputs": {"latest_json": "data/vectorized/VectorizedResearch_latest.json"},
        "safety_boundary": "Read-only replay-to-DataFrame research adapter; no live orders, broker calls, or market refresh.",
    }

    summary = vectorized_research_shell_summary(payload)

    assert summary["schema"] == "VectorizedResearchShellSummaryV1"
    assert summary["status"] == "Pass"
    assert summary["cards"][1]["value"] == "4/4"
    assert summary["rows"][0]["参数"] == "short_window=2, long_window=4"
    assert summary["rows"][0]["总收益%"] == 12.34
    assert summary["chart_rows"][0]["Sharpe"] == 1.23
    assert "does not reload EventReplay records or rerun parameter scans" in summary["token_policy"]
    assert "/Users/" not in str(summary)


def test_vectorized_research_shell_summary_fails_closed_when_missing() -> None:
    summary = vectorized_research_shell_summary(None)

    assert summary["status"] == "Missing"
    assert summary["rows"] == []
    assert summary["chart_rows"] == []
    assert "does not reload replay records or rerun scans" in summary["token_policy"]


def test_macos_runtime_evidence_summary_reads_latest_without_running_acceptance() -> None:
    payload = {
        "schema": "EVAOSMacOSRuntimeAcceptanceV1",
        "status": "Pass",
        "generated_at": "2026-06-16T12:00:00",
        "summary": {"pass": 10, "fail": 0, "info": 0, "total": 10},
        "started_by_acceptance": True,
        "launch_method": "app",
        "pre_existing_healthy_ports": [],
        "post_healthy_ports": [],
        "checks": [],
        "safety_boundary": "Controlled local acceptance; no broker calls, orders, or holdings mutation.",
        "next_action": "Optional visual UI verification.",
    }

    summary = macos_runtime_evidence_summary(payload)

    assert summary["schema"] == "MacOSRuntimeEvidenceSummaryV1"
    assert summary["status"] == "Pass"
    assert summary["cards"][1]["value"] == "10/10"
    assert summary["cards"][3]["value"] == "app"
    assert summary["rows"] == []
    assert "does not start or stop services" in summary["token_policy"]
    assert "scripts/macosRuntimeAcceptance.sh --summary-json" in summary["commands"]
    assert "/Users/" not in str(summary)


def test_macos_runtime_evidence_summary_fails_closed_when_missing() -> None:
    summary = macos_runtime_evidence_summary(None)

    assert summary["status"] == "Missing"
    assert summary["cards"][0]["value"] == "Missing"
    assert summary["rows"] == []
    assert "Terminal-only" in summary["safety_policy"]
    assert "scripts/macosRuntimeAcceptance.sh --summary-json" in summary["commands"]


def _system(system_id: str, display_name: str) -> dict:
    return {
        "system_id": system_id,
        "display_name": display_name,
        "adapter_status": "Ready",
        "migration_phase": "source_tests_docs_migrated",
        "sample_file_count": 3,
        "source_root": f"systems/{system_id}/source",
        "next_actions": ["Build UI acceptance"],
    }
