from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from src.monitoring.report_layer import (
    build_report_layer_audit,
    report_layer_quality_issues,
    report_layer_quality_issues_from_payload,
    write_report_layer_audit,
)
from src.reporting.quality_gate import _report_layer_issues


def test_report_layer_audit_caps_blocked_matrix_to_research_only(tmp_path: Path) -> None:
    root = tmp_path / "project"
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    _write_matrix(audit_dir / "evidence_decision_matrix_2026-06-06.json", audit_status="Blocked")

    audit = build_report_layer_audit("2026-06-06", root=root)

    assert audit["audit_status"] == "Blocked"
    assert audit["conclusion_ceiling"] == "ResearchOnlyBlocked"
    assert any("P0=2" in issue for issue in audit["quality_gate_issues"])
    assert any(row["gate_name"] == "Report Conclusion Ceiling" and row["decision_grade"] == "Reject" for row in audit["rows"])


def test_report_layer_missing_matrix_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "project"

    audit = build_report_layer_audit("2026-06-06", root=root)

    assert audit["audit_status"] == "Blocked"
    assert audit["conclusion_ceiling"] == "NoFormalResearchUse"
    assert audit["quality_gate_issues"] == ["Report Layer gate blocked: evidence decision matrix is missing or unreadable."]


def test_report_layer_quality_gate_uses_report_layer_before_matrix(tmp_path: Path) -> None:
    root = tmp_path / "project"
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    _write_matrix(audit_dir / "evidence_decision_matrix_2026-06-06.json", audit_status="Pass")
    report_layer_path = audit_dir / "report_layer_audit_2026-06-06.json"
    report_layer_path.write_text(
        json.dumps(
            {
                "schema": "AIResearchReportLayerAuditV1",
                "quality_gate_issues": ["Report Layer gate blocked: existing report-layer audit issue."],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    issues = report_layer_quality_issues("2026-06-06", root=root)

    assert issues == ["Report Layer gate blocked: existing report-layer audit issue."]


def test_report_layer_quality_gate_returns_empty_when_no_audit_exists(tmp_path: Path) -> None:
    assert report_layer_quality_issues("2026-01-01", root=tmp_path) == []


def test_quality_gate_delegates_to_report_layer_issues() -> None:
    with patch("src.reporting.quality_gate.report_layer_quality_issues", return_value=["blocked by report layer"]):
        assert _report_layer_issues("2026-06-06") == ["blocked by report layer"]


def test_report_layer_write_outputs(tmp_path: Path) -> None:
    root = tmp_path / "project"
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    _write_matrix(audit_dir / "evidence_decision_matrix_2026-06-06.json", audit_status="Review")

    audit = write_report_layer_audit("2026-06-06", root=root)

    assert Path(audit["outputs"]["json"]).exists()
    assert Path(audit["outputs"]["csv"]).exists()
    assert Path(audit["outputs"]["markdown"]).exists()
    assert Path(audit["outputs"]["pdf"]).exists()
    saved = json.loads(Path(audit["outputs"]["json"]).read_text(encoding="utf-8"))
    assert saved["schema"] == "AIResearchReportLayerAuditV1"
    assert saved["conclusion_ceiling"] == "ObservationOnly"


def test_report_layer_payload_issues_flag_weak_observations() -> None:
    payload = _matrix_payload(audit_status="Review")

    issues = report_layer_quality_issues_from_payload(payload)

    assert any("Watch/weak rows=3" in issue for issue in issues)
    assert any("OBSERVATION=7" in issue for issue in issues)


def _write_matrix(path: Path, *, audit_status: str) -> None:
    path.write_text(json.dumps(_matrix_payload(audit_status=audit_status), ensure_ascii=False, indent=2), encoding="utf-8")


def _matrix_payload(*, audit_status: str) -> dict[str, object]:
    if audit_status == "Pass":
        return {
            "schema": "AIResearchEvidenceDecisionMatrixV1",
            "audit_status": "Pass",
            "row_count": 3,
            "blocker_count": 0,
            "watch_count": 0,
            "user_confirmation_required_count": 0,
            "decision_counts": {"Actionable": 3},
            "evidence_counts": {"FACT": 3},
            "priority_counts": {"P2": 3},
        }
    if audit_status == "Review":
        return {
            "schema": "AIResearchEvidenceDecisionMatrixV1",
            "audit_status": "Review",
            "row_count": 10,
            "blocker_count": 0,
            "watch_count": 3,
            "user_confirmation_required_count": 1,
            "decision_counts": {"Actionable": 6, "Watch": 3, "Observe": 1},
            "evidence_counts": {"FACT": 3, "OBSERVATION": 7},
            "priority_counts": {"P1": 3, "P2": 7},
        }
    return {
        "schema": "AIResearchEvidenceDecisionMatrixV1",
        "audit_status": "Blocked",
        "row_count": 12,
        "blocker_count": 2,
        "watch_count": 6,
        "user_confirmation_required_count": 2,
        "decision_counts": {"Actionable": 4, "Reject": 2, "Watch": 6},
        "evidence_counts": {"FACT": 5, "OBSERVATION": 7},
        "priority_counts": {"P0": 2, "P1": 6, "P2": 4},
    }
