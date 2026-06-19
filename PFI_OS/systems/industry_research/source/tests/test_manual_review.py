from __future__ import annotations

import json
from pathlib import Path

from src.monitoring.manual_review import build_manual_review_audit, write_manual_review_audit


def test_manual_review_builds_queue_from_data_trust_and_reconciliation(tmp_path: Path) -> None:
    root = tmp_path / "project"
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    _write_json(
        audit_dir / "data_trust_audit_2026-06-06.json",
        {
            "records": [
                {
                    "source_type": "csv_artifact",
                    "source_name": "current_positions.csv",
                    "source_path": str(root / "data/private/alipay/current_positions.csv"),
                    "data_trust_status": "NEEDS_REVIEW",
                    "evidence_classification": "OBSERVATION",
                    "decision_grade": "Watch",
                    "issues": "",
                    "next_action": "当前持仓含视频可见或延续口径，进入人工复核。",
                },
                {
                    "source_type": "json_artifact",
                    "source_name": "automation_health_2026-06-05_execution_ready_required.json",
                    "source_path": str(root / "data/report_artifacts/automation_logs/automation_health_2026-06-05_execution_ready_required.json"),
                    "data_trust_status": "REJECTED",
                    "evidence_classification": "FACT",
                    "decision_grade": "Reject",
                    "issues": "automation health failed",
                    "next_action": "先处理失败健康检查。",
                },
            ]
        },
    )
    _write_json(
        audit_dir / "reconciliation_audit_2026-06-06.json",
        {
            "checks": [
                {
                    "domain": "report_chain",
                    "check_name": "source_log_pdf_pairing",
                    "status": "fail",
                    "severity": "P1",
                    "evidence_classification": "FACT",
                    "decision_grade": "Watch",
                    "issue": "Some source logs do not have matching formal PDFs.",
                    "next_action": "补齐正式 PDF。",
                    "source_paths": "/tmp/missing.pdf",
                }
            ]
        },
    )

    audit = build_manual_review_audit("2026-06-06", root=root)

    assert audit["audit_status"] == "Blocked"
    assert audit["priority_counts"]["P0"] == 1
    assert audit["priority_counts"]["P1"] == 2
    user_items = [row for row in audit["items"] if row["user_confirmation_required"]]
    assert len(user_items) == 1
    assert user_items[0]["item_name"] == "current_positions.csv"


def test_manual_review_missing_audits_become_p0(tmp_path: Path) -> None:
    root = tmp_path / "project"

    audit = build_manual_review_audit("2026-06-06", root=root)

    assert audit["audit_status"] == "Blocked"
    assert audit["priority_counts"]["P0"] == 2
    assert {row["item_name"] for row in audit["items"]} == {"data_trust_audit_missing", "reconciliation_audit_missing"}


def test_manual_review_write_outputs(tmp_path: Path) -> None:
    root = tmp_path / "project"
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    _write_json(audit_dir / "data_trust_audit_2026-06-06.json", {"records": []})
    _write_json(audit_dir / "reconciliation_audit_2026-06-06.json", {"checks": []})

    audit = write_manual_review_audit("2026-06-06", root=root)

    assert audit["audit_status"] == "Pass"
    assert Path(audit["outputs"]["json"]).exists()
    assert Path(audit["outputs"]["csv"]).exists()
    assert Path(audit["outputs"]["markdown"]).exists()
    assert Path(audit["outputs"]["pdf"]).exists()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
