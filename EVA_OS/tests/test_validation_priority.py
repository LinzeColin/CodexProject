from __future__ import annotations

import json
from pathlib import Path

from quantlab.research import build_validation_priority_plan, validation_priority_frame, write_validation_priority_plan


def test_validation_priority_plan_ranks_foundational_evidence_first(tmp_path: Path) -> None:
    queue_path = tmp_path / "ValidationTasks.json"
    _write_queue(
        queue_path,
        [
            {
                "task_id": "manual_low",
                "created_at": "2026-06-01T09:00:00",
                "status": "待验证",
                "research_topic": "人工复核行业叙事",
                "signal_to_validate": "人工复核",
                "source_report": "report.docx",
            },
            {
                "task_id": "reportGapTask_data",
                "created_at": "2026-06-07T09:00:00",
                "status": "待验证",
                "evidence_gap": "DataQuality",
                "research_topic": "补齐报告证据：Run / DataQuality",
                "symbol": "AAPL",
                "market": "US",
                "source_report": "report.docx",
            },
            {
                "task_id": "reportGapTask_cross_missing",
                "created_at": "2026-06-07T09:00:00",
                "status": "待验证",
                "evidence_gap": "CrossSourceValidation",
                "research_topic": "补齐报告证据：Run / CrossSourceValidation",
                "source_report": "report.docx",
            },
            {
                "task_id": "done",
                "status": "已完成",
                "evidence_gap": "DataQuality",
                "research_topic": "已完成任务",
                "symbol": "MSFT",
                "market": "US",
            },
        ],
    )

    payload = build_validation_priority_plan(
        as_of="2026-06-07",
        project_root=tmp_path,
        queue_path=queue_path,
        max_tasks=10,
    )
    frame = validation_priority_frame(payload)

    assert payload["schema"] == "QuantLabValidationTaskPriorityPlanV1"
    assert payload["queue_record_count"] == 4
    assert payload["candidate_record_count"] == 3
    assert frame.iloc[0]["evidence_gap"] == "DataQuality"
    assert frame.iloc[0]["action_bucket"] == "RunFirst"
    missing = frame[frame["task_id"] == "reportGapTask_cross_missing"].iloc[0]
    assert missing["action_bucket"] == "PrepareInputs"
    assert "missing_symbol" in missing["blockers"]


def test_validation_priority_plan_writes_outputs_without_mutating_queue(tmp_path: Path) -> None:
    queue_path = tmp_path / "ValidationTasks.json"
    rows = [
        {
            "task_id": "reportGapTask_data",
            "created_at": "2026-06-07T09:00:00",
            "status": "待验证",
            "evidence_gap": "DataQuality",
            "research_topic": "补齐报告证据：Run / DataQuality",
            "symbol": "AAPL",
            "market": "US",
            "source_report": "report.docx",
        }
    ]
    _write_queue(queue_path, rows)

    payload = write_validation_priority_plan(
        as_of="2026-06-07",
        project_root=tmp_path,
        queue_path=queue_path,
        output_dir=tmp_path / "priority",
        max_tasks=5,
    )

    assert payload["prioritized_task_count"] == 1
    assert json.loads(queue_path.read_text(encoding="utf-8")) == rows
    assert (tmp_path / "priority" / "ValidationTaskPriorityPlan_07062026.json").exists()
    assert (tmp_path / "priority" / "ValidationTaskPriorityPlan_07062026.csv").exists()
    assert (tmp_path / "priority" / "ValidationTaskPriorityPlan_07062026.md").exists()
    assert (tmp_path / "priority" / "ValidationTaskPriorityPlan_07062026.pdf").read_bytes().startswith(b"%PDF-1.4")


def _write_queue(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
