import json
from pathlib import Path

from quantlab.system import report_validation_hub as hub


def test_report_validation_hub_daily_merges_read_only_summaries(tmp_path: Path, monkeypatch) -> None:
    decision_payload = {
        "schema": "QuantLabReportDecisionSupportIndexV1",
        "record_count": 2,
        "summary": {
            "continue_research_count": 1,
            "needs_more_evidence_count": 1,
            "watch_only_count": 0,
            "do_not_use_count": 0,
            "average_evidence_score": 72,
        },
        "records": [{"metadata_path": "/private/report.json"}],
    }
    captured = {}

    def fake_decision(**kwargs):
        captured["decision_called"] = kwargs
        return decision_payload

    def fake_gaps(**kwargs):
        captured["gap_decision_payload"] = kwargs.get("report_decision_payload")
        return {
            "schema": "QuantLabReportEvidenceGapTasksV1",
            "source_record_count": 2,
            "task_count": 3,
            "gap_counts": [{"evidence_gap": "DataQuality", "count": 2}],
            "tasks": [{"metadata_path": "/private/full-task.json"}],
        }

    def fake_priority(**kwargs):
        return {
            "schema": "QuantLabValidationTaskPriorityPlanV1",
            "queue_record_count": 5,
            "candidate_record_count": 4,
            "prioritized_task_count": 2,
            "bucket_counts": [{"action_bucket": "RunFirst", "count": 1}],
            "top_tasks": [
                {
                    "priority_rank": 1,
                    "priority_score": 91,
                    "action_bucket": "RunFirst",
                    "evidence_gap": "CrossSourceValidation",
                    "symbol": "SPY",
                    "market": "US",
                    "blockers": "",
                    "source_report": "/private/report.docx",
                }
            ],
        }

    monkeypatch.setattr(hub, "build_report_decision_support_index", fake_decision)
    monkeypatch.setattr(hub, "build_report_gap_validation_tasks", fake_gaps)
    monkeypatch.setattr(hub, "build_validation_priority_plan", fake_priority)

    payload = hub.build_report_validation_hub(project_root=tmp_path, report_root=tmp_path / "reports")

    assert payload["schema"] == hub.REPORT_VALIDATION_HUB_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["mode"] == "daily"
    assert payload["summary"]["report_record_count"] == 2
    assert payload["summary"]["gap_candidate_task_count"] == 3
    assert payload["summary"]["prioritized_task_count"] == 2
    assert payload["mode_policy"]["read_only"] is True
    assert payload["mode_policy"]["writes_files"] is False
    assert payload["mode_policy"]["mutates_validation_queue"] is False
    assert payload["mode_policy"]["executes_validation"] is False
    assert captured["gap_decision_payload"] is decision_payload
    assert all("records" not in action.get("evidence", {}) for action in payload["actions"])
    assert all("tasks" not in action.get("evidence", {}) for action in payload["actions"])
    assert "/private/full-task.json" not in json.dumps(hub.report_validation_hub_summary(payload), ensure_ascii=False)


def test_report_validation_hub_mode_guide_keeps_advanced_writes_explicit() -> None:
    guide = hub.build_report_validation_mode_guide()

    assert guide["default_mode"] == "daily"
    assert any(item["mode"] == "daily" and item["read_only"] for item in guide["modes"])
    assert any(item["mutates_queue"] for item in guide["advanced_commands"])
    assert any(item["executes_validation"] for item in guide["advanced_commands"])


def test_report_validation_hub_blocks_failed_action_without_throwing(tmp_path: Path, monkeypatch) -> None:
    def boom(**kwargs):
        raise RuntimeError("decision index unavailable")

    monkeypatch.setattr(hub, "build_report_decision_support_index", boom)

    payload = hub.build_report_validation_hub(mode="decision", project_root=tmp_path, report_root=tmp_path / "reports")

    assert payload["status"] == "Blocked"
    assert payload["summary"]["fail"] == 1
    assert payload["actions"][0]["status"] == "Fail"
    assert payload["actions"][0]["evidence"]["error_type"] == "RuntimeError"
