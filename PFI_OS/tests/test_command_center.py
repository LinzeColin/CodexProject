from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pfi_os.executive import build_command_center, command_center_markdown, write_command_center


def test_command_center_reports_ready_when_core_evidence_is_closed(tmp_path: Path) -> None:
    latest_report = pd.DataFrame(
        [
            {
                "name": "BacktestReport_07062026.docx",
                "artifact_type": "Backtest Word Report",
                "date_folder": "2026-06-07",
                "size_kb": 12.0,
                "path": str(tmp_path / "reports" / "BacktestReport_07062026.docx"),
            }
        ]
    )
    payload = build_command_center(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        daily_readiness_payload=_daily("ReadyForResearch"),
        integration_payload=_integration("Pass"),
        cashflow_payload=_cashflow("Stable"),
        policy_payload=_policy("Observe"),
        consumption_payload=_consumption("Stable"),
        report_artifacts=latest_report,
    )

    assert payload["schema"] == "PFICommandCenterV1"
    assert payload["system"] == "PFI_OS"
    assert payload["subsystem"] == "Executive Command Center"
    assert payload["command_status"] == "ReadyForResearch"
    assert payload["latest_report"]["artifact_type"] == "Backtest Word Report"
    assert any(row["metric"] == "Company CashFlow Command" for row in payload["scorecards"])
    assert any(row["source"] == "Company CashFlow Command" for row in payload["evidence_sources"])
    assert all("Value" not in row["owner"] for row in payload["action_queue"])
    assert payload["cashflow_summary"]["cashflow_status"] == "Stable"
    assert payload["policy_summary"]["policy_status"] == "Observe"
    assert payload["consumption_summary"]["guard_status"] == "Stable"
    assert "不刷新行情" in payload["assumptions"][0]


def test_command_center_downgrades_when_report_or_gate_is_missing(tmp_path: Path) -> None:
    payload = build_command_center(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        daily_readiness_payload=_daily("NeedsReview", gate_status="Review"),
        integration_payload=_integration("Review", item_status="Review"),
        report_artifacts=pd.DataFrame(),
    )

    assert payload["command_status"] == "NeedsReview"
    assert "LatestReport" in payload["status_reason"]
    assert any(row["priority"] == "P0" for row in payload["action_queue"])
    assert any(row["source"] == "Report Evidence" for row in payload["action_queue"])


def test_command_center_downgrades_when_business_subsystem_needs_review(tmp_path: Path) -> None:
    latest_report = pd.DataFrame(
        [
            {
                "name": "BacktestReport_07062026.docx",
                "artifact_type": "Backtest Word Report",
                "date_folder": "2026-06-07",
                "size_kb": 12.0,
                "path": str(tmp_path / "reports" / "BacktestReport_07062026.docx"),
            }
        ]
    )
    payload = build_command_center(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        daily_readiness_payload=_daily("ReadyForResearch"),
        integration_payload=_integration("Pass"),
        cashflow_payload=_cashflow("MissingBalance"),
        policy_payload=_policy("Observe"),
        consumption_payload=_consumption("Stable"),
        report_artifacts=latest_report,
    )

    assert payload["command_status"] == "NeedsReview"
    assert "Company CashFlow Command" in payload["status_reason"]
    assert any(row["source"].startswith("Company CashFlow Command") for row in payload["action_queue"])


def test_write_command_center_outputs_json_markdown_pdf_and_latest(tmp_path: Path) -> None:
    output_dir = tmp_path / "commandCenter"
    payload = write_command_center(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        output_dir=output_dir,
        daily_readiness_payload=_daily("NeedsReview", gate_status="Review"),
        integration_payload=_integration("Review", item_status="Review"),
        report_artifacts=pd.DataFrame(),
    )

    outputs = payload["outputs"]
    json_path = Path(outputs["json"])
    markdown_path = Path(outputs["markdown"])
    pdf_path = Path(outputs["pdf"])
    latest_json = Path(outputs["latest_json"])
    latest_markdown = Path(outputs["latest_markdown"])
    latest_pdf = Path(outputs["latest_pdf"])

    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_path.name == "PFICommandCenter_07062026.json"
    assert saved["schema"] == "PFICommandCenterV1"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert markdown.startswith("# PFI OS 总控报告")
    assert "## 总览" in markdown
    assert "## Scorecards" not in markdown
    assert "System:" not in markdown
    assert pdf_path.read_bytes().startswith(b"%PDF-")
    assert b"????" not in pdf_path.read_bytes()
    assert latest_json.exists()
    assert latest_markdown.exists()
    assert latest_pdf.exists()


def test_command_center_markdown_contains_key_tables(tmp_path: Path) -> None:
    payload = build_command_center(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        daily_readiness_payload=_daily("ReadyForResearch"),
        integration_payload=_integration("Pass"),
        cashflow_payload=_cashflow("Stable"),
        policy_payload=_policy("Observe"),
        consumption_payload=_consumption("Stable"),
        report_artifacts=pd.DataFrame(
            [
                {
                    "name": "BacktestReport_07062026.docx",
                    "artifact_type": "Backtest Word Report",
                    "date_folder": "2026-06-07",
                    "size_kb": 1.0,
                    "path": "BacktestReport_07062026.docx",
                }
            ]
        ),
    )

    markdown = command_center_markdown(payload)
    assert "## 核心状态" in markdown
    assert "## 风控闸门" in markdown
    assert "## 行动队列" in markdown
    assert "## 运行摘要来源" in markdown
    assert "## 业务子系统" in markdown
    assert "| 指标 | 数值 | 状态 | 证据 |" in markdown
    assert "可用于研究" in markdown


def test_command_center_prefers_compact_runtime_summaries_over_full_latest(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "data" / "cashflow" / "CompanyCashFlowRuntimeSummary_latest.json",
        {
            "schema": "PFIOSCompanyCashFlowRuntimeSummaryV1",
            "cashflow_status": "Stable",
            "status": "Pass",
            "latest_balance": 12345.0,
            "net_cashflow": 678.0,
            "runway_days": 120.0,
            "pending_review_records": 0,
            "reviewed_missing_evidence_records": 0,
            "top_actions": [{"priority": "P2", "status": "Open", "action": "保持现金流复核。", "source": "Runtime"}],
        },
    )
    _write_json(
        tmp_path / "data" / "cashflow" / "CompanyCashFlowCommand_latest.json",
        {"schema": "PFIOSCompanyCashFlowCommandV1", "cashflow_status": "MissingBalance", "summary": {"latest_balance": None}},
    )
    _write_json(
        tmp_path / "data" / "policy" / "PolicyIntelligenceRuntimeSummary_latest.json",
        {
            "schema": "PFIOSPolicyIntelligenceRuntimeSummaryV1",
            "policy_status": "Observe",
            "status": "Pass",
            "opportunity_count": 2,
            "actionable_count": 0,
            "watch_count": 1,
            "missing_evidence_count": 0,
            "pending_review_count": 0,
            "top_actions": [{"priority": "P2", "status": "Open", "action": "继续观察政策。", "source": "Runtime"}],
        },
    )
    _write_json(
        tmp_path / "data" / "policy" / "PolicyIntelligenceRadar_latest.json",
        {"schema": "PFIOSPolicyIntelligenceRadarV1", "policy_status": "MissingPolicyEvidence", "summary": {"total_records": 0}},
    )
    _write_json(
        tmp_path / "data" / "consumption" / "ConsumptionGuardRuntimeSummary_latest.json",
        {
            "schema": "PFIOSConsumptionGuardRuntimeSummaryV1",
            "guard_status": "Stable",
            "status": "Pass",
            "counted_spend": 88.0,
            "impulse_spend": 0.0,
            "fixed_cost": 20.0,
            "investable_cashflow_pressure": 0.12,
            "pending_review_records": 0,
            "reviewed_missing_evidence_records": 0,
            "top_actions": [{"priority": "P2", "status": "Open", "action": "继续登记消费证据。", "source": "Runtime"}],
        },
    )
    _write_json(
        tmp_path / "data" / "consumption" / "ConsumptionGuard_latest.json",
        {"schema": "PFIOSConsumptionGuardV1", "guard_status": "MissingConsumptionEvidence", "summary": {"total_records": 0}},
    )
    latest_report = pd.DataFrame(
        [
            {
                "name": "BacktestReport_07062026.docx",
                "artifact_type": "Backtest Word Report",
                "date_folder": "2026-06-07",
                "size_kb": 12.0,
                "path": str(tmp_path / "reports" / "BacktestReport_07062026.docx"),
            }
        ]
    )

    payload = build_command_center(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        daily_readiness_payload=_daily("ReadyForResearch"),
        integration_payload=_integration("Pass"),
        report_artifacts=latest_report,
    )

    assert payload["command_status"] == "ReadyForResearch"
    assert payload["cashflow_summary"]["latest_balance"] == 12345.0
    assert payload["policy_summary"]["opportunity_count"] == 2
    assert payload["consumption_summary"]["counted_spend"] == 88.0
    assert all(row["mode"] == "runtime_summary" for row in payload["runtime_summary_sources"])
    schemas = {row["source"]: row["schema"] for row in payload["evidence_sources"]}
    assert schemas["Company CashFlow Command"] == "PFIOSCompanyCashFlowRuntimeSummaryV1"
    assert schemas["Policy Intelligence Radar"] == "PFIOSPolicyIntelligenceRuntimeSummaryV1"
    assert schemas["Consumption Guard"] == "PFIOSConsumptionGuardRuntimeSummaryV1"


def _daily(status: str, *, gate_status: str = "Pass") -> dict:
    return {
        "schema": "PFIOSDailyReadinessV1",
        "readiness_status": status,
        "core_gates": [
            {"gate": "DataTrust", "status": gate_status, "evidence": "audit_status=Pass", "next_action": "Keep clean."},
            {"gate": "IntegrationAudit", "status": gate_status, "evidence": "summary={}", "next_action": "Run audit."},
            {"gate": "NoLiveTradingBoundary", "status": "Pass", "evidence": "No live orders.", "next_action": "Keep enforced."},
        ],
        "action_items": [] if status == "ReadyForResearch" else ["DataTrust: Keep evidence audit clean."],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _integration(status: str, *, item_status: str = "Pass") -> dict:
    return {
        "schema": "PFIOSIntegrationAuditV1",
        "status": status,
        "summary": {"pass": 6 if status == "Pass" else 5, "review": 0 if status == "Pass" else 1, "fail": 0},
        "items": [
            {"layer": "ReportEvidence", "status": item_status, "summary": "RunMetadata files=1.", "next_action": "Keep report evidence."},
            {"layer": "ResearchBusInterop", "status": item_status, "summary": "Interop status.", "next_action": "Keep sync."},
        ],
    }

def _cashflow(status: str) -> dict:
    latest_balance = 10000.0 if status != "MissingBalance" else None
    return {
        "schema": "PFIOSCompanyCashFlowCommandV1",
        "cashflow_status": status,
        "summary": {
            "cashflow_status": status,
            "latest_balance": latest_balance,
            "net_cashflow": 1200.0,
            "runway_days": 90.0 if latest_balance is not None else None,
            "pending_review_records": 0,
            "reviewed_missing_evidence_records": 0,
        },
        "action_queue": [
            {"priority": "P0", "status": "Open", "action": "录入并复核最新公司现金余额。", "source": "BalanceSnapshot"}
        ],
    }


def _policy(status: str) -> dict:
    return {
        "schema": "PFIOSPolicyIntelligenceRadarV1",
        "policy_status": status,
        "summary": {
            "policy_status": status,
            "total_records": 1,
            "actionable_count": 1 if status == "Actionable" else 0,
            "watch_count": 0,
            "missing_evidence_count": 0,
            "pending_review_count": 0,
        },
        "action_queue": [
            {"priority": "P1", "status": "Open", "action": "复核政策机会并确认下一步。", "source": "Policy Opportunity"}
        ],
    }


def _consumption(status: str) -> dict:
    return {
        "schema": "PFIOSConsumptionGuardV1",
        "guard_status": status,
        "summary": {
            "guard_status": status,
            "counted_spend": 150.0,
            "impulse_spend": 0.0,
            "fixed_cost": 40.0,
            "investable_cashflow_pressure": 0.2,
            "pending_review_records": 0,
            "reviewed_missing_evidence_records": 0,
        },
        "action_queue": [
            {"priority": "P1", "status": "Open", "action": "复盘高冲动消费事件。", "source": "Impulse Risk"}
        ],
    }
