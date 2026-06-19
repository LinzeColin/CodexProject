from __future__ import annotations

import json
from pathlib import Path

from quantlab.reports import build_report_decision_support_index, report_decision_support_markdown, write_report_decision_support_index


def test_report_decision_support_classifies_evidence_status(tmp_path: Path) -> None:
    report_root = _fixture_reports(tmp_path)

    payload = build_report_decision_support_index(as_of="2026-06-07", project_root=tmp_path, report_root=report_root)

    assert payload["schema"] == "QuantLabReportDecisionSupportIndexV1"
    assert payload["system"] == "EVA_OS"
    assert payload["record_count"] == 3
    by_run = {row["run"]: row for row in payload["records"]}
    assert by_run["RunMetadataReady_07062026"]["report_readiness"] == "ContinueResearch"
    assert by_run["RunMetadataMissing_07062026"]["report_readiness"] == "NeedsMoreEvidence"
    assert by_run["RunMetadataReject_07062026"]["report_readiness"] == "DoNotUse"
    assert by_run["RunMetadataReady_07062026"]["evidence_score"] == 100
    assert "多源交叉校验" in by_run["RunMetadataMissing_07062026"]["critical_missing_evidence"]
    assert payload["summary"]["continue_research_count"] == 1
    assert payload["summary"]["needs_more_evidence_count"] == 1
    assert payload["summary"]["do_not_use_count"] == 1


def test_write_report_decision_support_outputs_json_csv_markdown_pdf_and_latest(tmp_path: Path) -> None:
    report_root = _fixture_reports(tmp_path)
    output_dir = tmp_path / "reportDecision"

    payload = write_report_decision_support_index(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=report_root,
        output_dir=output_dir,
    )

    outputs = payload["outputs"]
    json_path = Path(outputs["json"])
    csv_path = Path(outputs["csv"])
    markdown_path = Path(outputs["markdown"])
    pdf_path = Path(outputs["pdf"])
    saved = json.loads(json_path.read_text(encoding="utf-8"))

    assert json_path.name == "ReportDecisionSupportIndex_07062026.json"
    assert saved["schema"] == "QuantLabReportDecisionSupportIndexV1"
    assert csv_path.read_text(encoding="utf-8").startswith("decision_id,date_folder")
    assert markdown_path.read_text(encoding="utf-8").startswith("# Report Decision Support Index")
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")
    assert Path(outputs["latest_json"]).exists()
    assert Path(outputs["latest_csv"]).exists()
    assert Path(outputs["latest_markdown"]).exists()
    assert Path(outputs["latest_pdf"]).exists()


def test_report_decision_support_markdown_contains_missing_evidence_table(tmp_path: Path) -> None:
    payload = build_report_decision_support_index(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=_fixture_reports(tmp_path),
    )

    markdown = report_decision_support_markdown(payload)

    assert "## Readiness Counts" in markdown
    assert "## Top Missing Evidence" in markdown
    assert "NeedsMoreEvidence" in markdown


def _fixture_reports(tmp_path: Path) -> Path:
    report_root = tmp_path / "reports"
    day = report_root / "2026-06-07"
    day.mkdir(parents=True)
    (day / "BacktestReportReady_07062026.docx").write_bytes(b"docx")
    (day / "BacktestReportMissing_07062026.docx").write_bytes(b"docx")
    (day / "BacktestReportReject_07062026.docx").write_bytes(b"docx")
    _write_metadata(day / "RunMetadataReady_07062026.json", "ContinueResearch", missing=[])
    _write_metadata(day / "RunMetadataMissing_07062026.json", "NeedsMoreEvidence", missing=["多源交叉校验"])
    _write_metadata(day / "RunMetadataReject_07062026.json", "DoNotUse", missing=[])
    return report_root


def _write_metadata(path: Path, status: str, *, missing: list[str]) -> None:
    payload = {
        "metadata": {
            "strategy": {"strategy_id": "ma_crossover"},
            "backtest": {"initial_cash": 100000},
        },
        "metrics": {
            "total_return": 0.12,
            "annualized_return": 0.1,
            "sharpe": 1.1,
            "max_drawdown": -0.08,
            "cost_total": 100.0,
            "ending_equity": 112000.0,
            "trade_count": 12,
        },
        "risk_gate": {"status": status, "missing_evidence": missing},
        "decision_quality": {"status": status, "score": 82 if status == "ContinueResearch" else 62, "missing_evidence": missing},
        "report_evidence": {
            "schema": "QuantLabReportEvidenceV1",
            "evidence_status": status,
            "data_quality_status": "Pass",
            "cross_validation_status": "Pass" if not missing else "Missing",
            "risk_gate_status": status,
            "decision_quality_status": status,
            "missing_evidence": missing,
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
