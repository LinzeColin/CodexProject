from __future__ import annotations

import json
from pathlib import Path

from quantlab.research import append_report_gap_validation_tasks, build_report_gap_validation_tasks
from quantlab.research.validation_queue import load_validation_tasks


def test_report_gap_tasks_classify_missing_evidence_and_append_deduped_queue(tmp_path: Path) -> None:
    decision_payload = _decision_payload(tmp_path)
    queue_path = tmp_path / "ValidationTasks.json"

    preview = build_report_gap_validation_tasks(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        report_decision_payload=decision_payload,
    )
    first = append_report_gap_validation_tasks(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        queue_path=queue_path,
        output_dir=tmp_path / "reportDecision",
        max_records=50,
        report_decision_payload=decision_payload,
    )
    second = append_report_gap_validation_tasks(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        queue_path=queue_path,
        output_dir=tmp_path / "reportDecision",
        max_records=50,
        report_decision_payload=decision_payload,
    )
    tasks = load_validation_tasks(queue_path)

    assert preview["schema"] == "QuantLabReportEvidenceGapTasksV1"
    assert {row["evidence_gap"] for row in preview["tasks"]} >= {"DataQuality", "CrossSourceValidation", "WalkForwardValidation"}
    assert first["appended_task_count"] == len(tasks)
    assert first["pending_task_count"] == len(tasks)
    assert second["appended_task_count"] == 0
    assert second["skipped_existing_count"] >= first["appended_task_count"]
    assert all(task.status == "待验证" for task in tasks)
    assert (tmp_path / "reportDecision" / "ReportEvidenceGapTasks_07062026.json").exists()
    assert (tmp_path / "reportDecision" / "ReportEvidenceGapTasks_07062026.pdf").read_bytes().startswith(b"%PDF-1.4")


def test_report_gap_tasks_dry_run_does_not_write_queue(tmp_path: Path) -> None:
    report_root = _fixture_reports(tmp_path)
    queue_path = tmp_path / "ValidationTasks.json"

    payload = append_report_gap_validation_tasks(
        as_of="2026-06-07",
        project_root=tmp_path,
        report_root=report_root,
        queue_path=queue_path,
        output_dir=tmp_path / "reportDecision",
        dry_run=True,
    )

    assert payload["dry_run"] is True
    assert payload["appended_task_count"] == 0
    assert payload["pending_task_count"] > 0
    assert not queue_path.exists()
    assert (tmp_path / "reportDecision" / "ReportEvidenceGapTasks_07062026.json").exists()


def _decision_payload(tmp_path: Path) -> dict:
    report_path = tmp_path / "reports" / "2026-06-07" / "BacktestReport_07062026.docx"
    metadata_path = tmp_path / "reports" / "2026-06-07" / "RunMetadata_07062026.json"
    return {
        "schema": "QuantLabReportDecisionSupportIndexV1",
        "record_count": 1,
        "records": [
            {
                "run": "RunMetadata_07062026",
                "date_folder": "2026-06-07",
                "strategy_id": "ma_crossover",
                "symbol": "AAPL",
                "market": "US",
                "report_readiness": "NeedsMoreEvidence",
                "critical_missing_evidence": "数据质量状态; 多源交叉校验; walk-forward 验证",
                "metadata_path": str(metadata_path),
                "linked_report_path": str(report_path),
            }
        ],
    }


def _fixture_reports(tmp_path: Path) -> Path:
    report_root = tmp_path / "reports"
    day = report_root / "2026-06-07"
    day.mkdir(parents=True)
    (day / "BacktestReport_07062026.docx").write_bytes(b"docx")
    (day / "RunMetadata_07062026.json").write_text(
        json.dumps(
            {
                "metadata": {"strategy": {"strategy_id": "ma_crossover"}, "backtest": {"symbol": "AAPL", "market": "US"}},
                "metrics": {"total_return": 0.1, "ending_equity": 110000},
                "risk_gate": {"status": "NeedsMoreEvidence", "missing_evidence": ["walk-forward 验证"]},
                "decision_quality": {"status": "NeedsMoreEvidence", "missing_evidence": ["多源交叉校验"]},
                "report_evidence": {
                    "schema": "QuantLabReportEvidenceV1",
                    "evidence_status": "NeedsMoreEvidence",
                    "data_quality_status": "Missing",
                    "cross_validation_status": "Missing",
                    "missing_evidence": ["数据质量状态", "多源交叉校验"],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return report_root
