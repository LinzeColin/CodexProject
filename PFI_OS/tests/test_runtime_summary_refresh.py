from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pfi_os.executive import build_command_center, refresh_runtime_summary_latest


def test_refresh_runtime_summary_latest_writes_only_compact_public_safe_files(tmp_path: Path) -> None:
    payload = refresh_runtime_summary_latest(
        as_of="2026-06-16",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        monthly_investable_budget=1000,
    )

    assert payload["schema"] == "PFIOSRuntimeSummaryRefreshV1"
    assert payload["status"] == "Pass"
    assert payload["summary_count"] == 3
    assert payload["runtime_summary_only"] is True
    assert "no full entries" in payload["public_upload_safety"]

    expected = {
        "data/cashflow/CompanyCashFlowRuntimeSummary_latest.json": ("PFIOSCompanyCashFlowRuntimeSummaryV1", "entries"),
        "data/policy/PolicyIntelligenceRuntimeSummary_latest.json": ("PFIOSPolicyIntelligenceRuntimeSummaryV1", "opportunities"),
        "data/consumption/ConsumptionGuardRuntimeSummary_latest.json": ("PFIOSConsumptionGuardRuntimeSummaryV1", "events"),
    }
    for relative, (schema, forbidden_full_key) in expected.items():
        path = tmp_path / relative
        dated_path = tmp_path / relative.replace("_latest.json", "_16062026.json")
        assert path.exists()
        assert dated_path.exists()
        summary = json.loads(path.read_text(encoding="utf-8"))
        serialized = json.dumps(summary, ensure_ascii=False)
        assert summary["schema"] == schema
        assert forbidden_full_key not in summary
        assert str(tmp_path) not in serialized
        assert summary["outputs"]["latest_runtime_summary_json"] == relative


def test_refreshed_runtime_summaries_are_command_center_default_sources(tmp_path: Path) -> None:
    refresh_runtime_summary_latest(
        as_of="2026-06-16",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        monthly_investable_budget=1000,
    )

    latest_report = pd.DataFrame(
        [
            {
                "name": "BacktestReport_16062026.docx",
                "artifact_type": "Backtest Word Report",
                "date_folder": "2026-06-16",
                "size_kb": 12.0,
                "path": str(tmp_path / "reports" / "BacktestReport_16062026.docx"),
            }
        ]
    )
    payload = build_command_center(
        as_of="2026-06-16",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        daily_readiness_payload=_daily("NeedsReview"),
        integration_payload=_integration("Pass"),
        report_artifacts=latest_report,
    )

    assert {row["mode"] for row in payload["runtime_summary_sources"]} == {"runtime_summary"}
    schemas = {row["subsystem"]: row["schema"] for row in payload["runtime_summary_sources"]}
    assert schemas == {
        "Company CashFlow Command": "PFIOSCompanyCashFlowRuntimeSummaryV1",
        "Policy Intelligence Radar": "PFIOSPolicyIntelligenceRuntimeSummaryV1",
        "Consumption Guard": "PFIOSConsumptionGuardRuntimeSummaryV1",
    }


def _daily(status: str) -> dict:
    return {
        "schema": "PFIOSDailyReadinessV1",
        "readiness_status": status,
        "core_gates": [
            {"gate": "DataTrust", "status": "Review", "evidence": "audit_status=Review", "next_action": "Review data."},
            {"gate": "NoLiveTradingBoundary", "status": "Pass", "evidence": "No live orders.", "next_action": "Keep enforced."},
        ],
        "action_items": ["DataTrust: Review data."],
    }


def _integration(status: str) -> dict:
    return {
        "schema": "PFIOSIntegrationAuditV1",
        "status": status,
        "summary": {"pass": 1, "review": 0, "fail": 0},
        "items": [
            {"layer": "ResearchBusInterop", "status": "Pass", "summary": "Interop status.", "next_action": "Keep sync."},
        ],
    }
