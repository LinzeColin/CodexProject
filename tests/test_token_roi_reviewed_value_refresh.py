from __future__ import annotations

import json
from pathlib import Path

from quantlab.executive import refresh_runtime_summary_latest
from quantlab.value import refresh_token_roi_from_reviewed_input


def test_token_roi_reviewed_value_refresh_missing_input_blocks_without_outputs(tmp_path: Path) -> None:
    payload = refresh_token_roi_from_reviewed_input(
        as_of="2026-06-16",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
    )

    assert payload["schema"] == "EVATokenROIReviewedValueEvidenceRefreshV1"
    assert payload["status"] == "Blocked"
    assert payload["roi_status"] == "MissingReviewedInput"
    assert payload["input_status"] == "Missing"
    assert payload["outputs"] == {}
    assert payload["report_root"] == "reports"
    assert "/Users/" not in json.dumps(payload, ensure_ascii=False)
    assert payload["input_contract"]["default_private_input"] == "data/private/value/TokenROIReviewedValueEvidence.json"
    assert "No fabricated revenue" in payload["safety_boundary"]


def test_token_roi_reviewed_value_refresh_writes_quantified_outputs(tmp_path: Path) -> None:
    entry_path = _private_entries(tmp_path)
    output_dir = tmp_path / "value"

    payload = refresh_token_roi_from_reviewed_input(
        as_of="2026-06-16",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        entry_path=entry_path,
        output_dir=output_dir,
    )
    runtime = payload["runtime_summary"]

    assert payload["status"] == "Pass"
    assert payload["roi_status"] == "Quantified"
    assert payload["input_status"] == "Present"
    assert payload["input_path"] == "data/private/value/TokenROIReviewedValueEvidence.json"
    assert payload["summary"]["manual_record_count"] == 2
    assert payload["summary"]["quantified_records"] == 2
    assert payload["summary"]["financial_totals"]["benefit_total"] == 1420.0
    assert payload["summary"]["financial_totals"]["cost_total"] == 95.5
    assert runtime["schema"] == "EVATokenROIRuntimeSummaryV1"
    assert runtime["status"] == "Pass"
    assert "records" not in runtime
    assert (tmp_path / payload["outputs"]["json"]).is_file()
    assert (tmp_path / payload["outputs"]["runtime_summary_json"]).is_file()
    assert (tmp_path / payload["outputs"]["pdf"]).read_bytes().startswith(b"%PDF-1.4")


def test_runtime_summary_refresh_accepts_token_roi_reviewed_value_input(tmp_path: Path) -> None:
    entry_path = _private_entries(tmp_path)
    payload = refresh_runtime_summary_latest(
        as_of="2026-06-16",
        project_root=tmp_path,
        report_root=tmp_path / "reports",
        token_roi_entry_path=entry_path,
        monthly_investable_budget=1000,
    )

    summary_path = tmp_path / "data" / "value" / "EVATokenROIRuntimeSummary_latest.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert payload["schema"] == "EVAOSRuntimeSummaryRefreshV1"
    assert payload["status"] == "Pass"
    assert summary["schema"] == "EVATokenROIRuntimeSummaryV1"
    assert summary["status"] == "Pass"
    assert summary["quantified_records"] == 2
    assert summary["financial_totals"]["benefit_total"] == 1420.0
    assert "records" not in summary
    assert summary["outputs"]["latest_runtime_summary_json"] == "data/value/EVATokenROIRuntimeSummary_latest.json"


def test_token_roi_reviewed_value_public_example_is_synthetic_and_schema_linked() -> None:
    project_root = Path(__file__).resolve().parents[1]
    example = project_root / "data" / "value" / "TokenROIReviewedValueEvidence.example.json"
    schema = project_root / "shared" / "schema" / "token_roi_reviewed_value_evidence.schema.json"
    gitignore = project_root / ".gitignore"

    payload = json.loads(example.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, ensure_ascii=False)

    assert schema.exists()
    assert "EVA_OS Token ROI Reviewed Value Evidence" in schema.read_text(encoding="utf-8")
    assert payload
    assert all(str(row.get("evidence_link", "")).startswith("sample://token-roi/") for row in payload)
    assert "/Users/" not in serialized
    assert "linzezhang" not in serialized
    assert "api_key" not in serialized.lower()
    assert "password" not in serialized.lower()
    assert "TokenROIManualEntries.json" in gitignore.read_text(encoding="utf-8")


def _private_entries(root: Path) -> Path:
    path = root / "data" / "private" / "value" / "TokenROIReviewedValueEvidence.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            [
                {
                    "run_date": "2026-06-16",
                    "task_goal": "Productize reviewed-input refresh for Consumption Guard.",
                    "title": "Consumption Guard reviewed-input MVP",
                    "subsystem": "EVA_OS Consumption Guard",
                    "value_contribution": "System Reliability",
                    "evidence_link": "sample://token-roi/consumption-reviewed-input-2026-06-16",
                    "source_path": "sample://token-roi/consumption-reviewed-input-2026-06-16",
                    "token_estimate": 9000,
                    "ai_cost": 12.5,
                    "human_time_cost": 45.0,
                    "cost_saved": 520.0,
                    "asset_reuse_value": 180.0,
                    "time_saved_hours": 2.0,
                    "reuse_count": 2,
                    "review_status": "Reviewed",
                },
                {
                    "run_date": "2026-06-16",
                    "task_goal": "Reduce agent context cost with compact runtime summaries.",
                    "title": "Runtime summary low-token handoff",
                    "subsystem": "EVA_OS Executive Command Center",
                    "value_contribution": "Validation Efficiency",
                    "evidence_link": "sample://token-roi/runtime-summary-low-token-2026-06-16",
                    "source_path": "sample://token-roi/runtime-summary-low-token-2026-06-16",
                    "token_estimate": 6500,
                    "ai_cost": 8.0,
                    "human_time_cost": 30.0,
                    "cost_saved": 360.0,
                    "loss_avoided": 120.0,
                    "asset_reuse_value": 240.0,
                    "time_saved_hours": 1.5,
                    "reuse_count": 3,
                    "review_status": "Reviewed",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path
