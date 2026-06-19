from __future__ import annotations

import csv
import json
from pathlib import Path

from quantlab.value import (
    append_manual_token_roi_entry,
    build_token_roi_ledger,
    build_token_roi_runtime_summary,
    create_manual_token_roi_entry,
    load_manual_token_roi_entries,
    write_token_roi_ledger,
)


def test_token_roi_ledger_records_outputs_without_fabricating_financial_value(tmp_path: Path) -> None:
    project_root = _fixture_project(tmp_path)
    report_root = _fixture_reports(tmp_path)

    payload = build_token_roi_ledger(
        as_of="2026-06-07",
        project_root=project_root,
        report_root=report_root,
    )

    assert payload["schema"] == "EVATokenROILedgerV1"
    assert payload["system"] == "EVA_OS"
    assert payload["subsystem"] == "Token ROI Ledger"
    assert payload["record_count"] >= 4
    assert payload["summary"]["quantified_records"] == 0
    assert payload["summary"]["financial_totals"] == {
        "ai_cost": 0.0,
        "human_time_cost": 0.0,
        "revenue_generated": 0.0,
        "cost_saved": 0.0,
        "loss_avoided": 0.0,
        "asset_reuse_value": 0.0,
    }
    assert payload["runtime_summary"]["schema"] == "EVATokenROIRuntimeSummaryV1"
    assert payload["runtime_summary"]["status"] == "NeedsReview"
    assert "records" not in payload["runtime_summary"]
    assert "does not include full records" in payload["runtime_summary"]["token_policy"]
    assert all(record["value_status"] == "Unquantified" for record in payload["records"])
    assert all(record["roi_score"] is None for record in payload["records"])
    assert any(record["artifact_type"] == "Daily Readiness" for record in payload["records"])
    assert any(record["artifact_type"] == "Executive Command Center" for record in payload["records"])
    assert any(record["artifact_type"] == "Report Decision Support Index" for record in payload["records"])
    assert any(record["artifact_type"] == "Validation Task Priority Plan" for record in payload["records"])
    assert any(record["artifact_type"] == "Validation Task Execution" for record in payload["records"])
    assert any(record["artifact_type"] == "Validation Task Queue" for record in payload["records"])
    assert any(record["artifact_type"] == "Backtest Word Report" for record in payload["records"])


def test_write_token_roi_ledger_outputs_json_csv_markdown_pdf_and_latest(tmp_path: Path) -> None:
    project_root = _fixture_project(tmp_path)
    report_root = _fixture_reports(tmp_path)
    output_dir = tmp_path / "value"

    payload = write_token_roi_ledger(
        as_of="2026-06-07",
        project_root=project_root,
        report_root=report_root,
        output_dir=output_dir,
    )

    outputs = payload["outputs"]
    json_path = Path(outputs["json"])
    csv_path = Path(outputs["csv"])
    markdown_path = Path(outputs["markdown"])
    pdf_path = Path(outputs["pdf"])
    latest_json = Path(outputs["latest_json"])
    latest_csv = Path(outputs["latest_csv"])
    latest_markdown = Path(outputs["latest_markdown"])
    latest_pdf = Path(outputs["latest_pdf"])
    runtime_summary_json = Path(outputs["runtime_summary_json"])
    latest_runtime_summary_json = Path(outputs["latest_runtime_summary_json"])

    saved = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_summary = json.loads(runtime_summary_json.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))

    assert json_path.name == "EVATokenROILedger_07062026.json"
    assert runtime_summary_json.name == "EVATokenROIRuntimeSummary_07062026.json"
    assert saved["schema"] == "EVATokenROILedgerV1"
    assert runtime_summary["schema"] == "EVATokenROIRuntimeSummaryV1"
    assert len(rows) == saved["record_count"]
    assert markdown_path.read_text(encoding="utf-8").startswith("# EVA_OS Token ROI Ledger")
    assert "## Runtime Evidence Gate" in markdown_path.read_text(encoding="utf-8")
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")
    assert latest_json.exists()
    assert latest_csv.exists()
    assert latest_markdown.exists()
    assert latest_pdf.exists()
    assert latest_runtime_summary_json.exists()


def test_reviewed_manual_value_entry_is_counted_as_quantified(tmp_path: Path) -> None:
    project_root = _fixture_project(tmp_path)
    report_root = _fixture_reports(tmp_path)
    manual_path = project_root / "data" / "value" / "TokenROIManualEntries.json"
    entry = create_manual_token_roi_entry(
        run_date="2026-06-07",
        task_goal="Reduce hotspot workbench latency",
        title="Hotspot latency reduction",
        subsystem="EVA_OS",
        value_contribution="System Reliability",
        evidence_link="docs/ReleaseNotes.md",
        token_estimate=12000,
        ai_cost=10.0,
        human_time_cost=90.0,
        cost_saved=1000.0,
        asset_reuse_value=200.0,
        time_saved_hours=2.5,
        reuse_count=3,
        review_status="Reviewed",
        notes="Reviewed against local report output.",
    )

    append_manual_token_roi_entry(entry, manual_path)
    loaded = load_manual_token_roi_entries(manual_path)
    payload = build_token_roi_ledger(project_root=project_root, report_root=report_root)
    manual_records = [record for record in payload["records"] if record.get("record_type") == "ManualValueEvidence"]

    assert len(loaded) == 1
    assert manual_records
    assert manual_records[0]["value_status"] == "Quantified"
    assert manual_records[0]["roi_score"] == 11.0
    assert payload["summary"]["quantified_records"] == 1
    assert payload["summary"]["financial_totals"]["ai_cost"] == 10.0
    assert payload["summary"]["financial_totals"]["human_time_cost"] == 90.0
    assert payload["summary"]["financial_totals"]["cost_saved"] == 1000.0
    assert payload["summary"]["financial_totals"]["asset_reuse_value"] == 200.0
    assert payload["runtime_summary"]["status"] == "Pass"
    assert payload["runtime_summary"]["financial_totals"]["benefit_total"] == 1200.0
    assert payload["runtime_summary"]["financial_totals"]["cost_total"] == 100.0
    assert payload["runtime_summary"]["financial_totals"]["aggregate_roi_score"] == 11.0


def test_pending_manual_value_entry_does_not_pollute_quantified_totals(tmp_path: Path) -> None:
    project_root = _fixture_project(tmp_path)
    report_root = _fixture_reports(tmp_path)
    manual_path = project_root / "data" / "value" / "TokenROIManualEntries.json"
    entry = create_manual_token_roi_entry(
        run_date="2026-06-07",
        task_goal="Draft value hypothesis before evidence exists",
        cost_saved=500.0,
        ai_cost=5.0,
        review_status="PendingReview",
    )

    append_manual_token_roi_entry(entry, manual_path)
    payload = build_token_roi_ledger(project_root=project_root, report_root=report_root)
    manual_record = next(record for record in payload["records"] if record.get("record_type") == "ManualValueEvidence")

    assert manual_record["value_status"] == "PendingReview"
    assert manual_record["roi_score"] is None
    assert payload["summary"]["quantified_records"] == 0
    assert payload["summary"]["financial_totals"]["ai_cost"] == 0.0
    assert payload["summary"]["financial_totals"]["cost_saved"] == 0.0
    assert payload["runtime_summary"]["pending_financial_hypothesis_count"] == 1
    assert any(gate["gate"] == "PendingValueReview" and gate["status"] == "Review" for gate in payload["runtime_summary"]["evidence_gate"])


def test_token_roi_runtime_summary_blocks_bad_schema_and_stays_compact(tmp_path: Path) -> None:
    project_root = _fixture_project(tmp_path)
    report_root = _fixture_reports(tmp_path)
    payload = build_token_roi_ledger(project_root=project_root, report_root=report_root)
    payload["schema"] = "UnexpectedSchema"

    summary = build_token_roi_runtime_summary(payload)

    assert summary["schema"] == "EVATokenROIRuntimeSummaryV1"
    assert summary["status"] == "Blocked"
    assert "records" not in summary
    assert any(gate["gate"] == "LedgerSchema" and gate["status"] == "Blocked" for gate in summary["evidence_gate"])


def _fixture_project(tmp_path: Path) -> Path:
    root = tmp_path / "CodexFinance"
    audit_dir = root / "data" / "systemAudit"
    audit_dir.mkdir(parents=True)
    (audit_dir / "QuantLabDailyReadiness_07062026.json").write_text("{}", encoding="utf-8")
    (audit_dir / "QuantLabIntegrationAudit_07062026.md").write_text("# Integration\n", encoding="utf-8")
    (audit_dir / "QuantLabDataTrustAudit_07062026.pdf").write_bytes(b"%PDF-1.4\n")
    command_dir = root / "data" / "commandCenter"
    command_dir.mkdir(parents=True)
    (command_dir / "EVACommandCenter_07062026.json").write_text('{"schema":"EVACommandCenterV1"}', encoding="utf-8")
    decision_dir = root / "data" / "reportDecision"
    decision_dir.mkdir(parents=True)
    (decision_dir / "ReportDecisionSupportIndex_07062026.json").write_text(
        '{"schema":"QuantLabReportDecisionSupportIndexV1"}',
        encoding="utf-8",
    )
    queue_dir = root / "data" / "validationQueue"
    queue_dir.mkdir(parents=True)
    (queue_dir / "ValidationTasks.json").write_text('[{"task_id":"task1","status":"待验证"}]', encoding="utf-8")
    (queue_dir / "ValidationTaskPriorityPlan_07062026.json").write_text(
        '{"schema":"QuantLabValidationTaskPriorityPlanV1"}',
        encoding="utf-8",
    )
    (queue_dir / "ValidationTaskExecution_07062026_demo.json").write_text(
        '{"schema":"QuantLabValidationTaskExecutionV1"}',
        encoding="utf-8",
    )
    return root


def _fixture_reports(tmp_path: Path) -> Path:
    root = tmp_path / "reports"
    day = root / "2026-06-07"
    day.mkdir(parents=True)
    (day / "BacktestReport_07062026.docx").write_bytes(b"docx")
    (day / "RunMetadata_07062026.json").write_text('{"schema":"RunMetadata"}', encoding="utf-8")
    (day / "DataQuality_sample_US_AAPL_20260607.json").write_text("{}", encoding="utf-8")
    return root
