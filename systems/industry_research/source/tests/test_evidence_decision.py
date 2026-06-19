from __future__ import annotations

import json
from pathlib import Path

from src.monitoring.evidence_decision import build_evidence_decision_matrix, write_evidence_decision_matrix


def test_evidence_decision_matrix_combines_audit_layers(tmp_path: Path) -> None:
    root = tmp_path / "project"
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    _seed_audits(audit_dir)

    audit = build_evidence_decision_matrix("2026-06-06", root=root)
    rows = audit["rows"]

    assert audit["audit_status"] == "Blocked"
    assert audit["source_layer_counts"]["DataTrust"] == 2
    assert audit["source_layer_counts"]["Reconciliation"] == 1
    assert audit["source_layer_counts"]["ManualReview"] == 1
    assert audit["source_layer_counts"]["EntityRegistry"] == 1
    assert audit["source_layer_counts"]["AliasMap"] == 1
    assert audit["decision_counts"]["Reject"] == 1
    assert audit["decision_counts"]["Watch"] >= 3
    assert audit["user_confirmation_required_count"] >= 1
    assert any(row["item_name"] == "current_positions.csv" and row["user_confirmation_required"] for row in rows)
    assert any(row["source_layer"] == "AliasMap" and row["decision_grade"] == "Watch" for row in rows)


def test_evidence_decision_missing_audits_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "project"

    audit = build_evidence_decision_matrix("2026-06-06", root=root)

    assert audit["audit_status"] == "Blocked"
    assert audit["priority_counts"]["P0"] == 4
    assert audit["decision_counts"]["Reject"] == 4


def test_evidence_decision_write_outputs(tmp_path: Path) -> None:
    root = tmp_path / "project"
    audit_dir = root / "data" / "report_artifacts" / "system_audit"
    audit_dir.mkdir(parents=True)
    _seed_audits(audit_dir)

    audit = write_evidence_decision_matrix("2026-06-06", root=root)

    assert Path(audit["outputs"]["json"]).exists()
    assert Path(audit["outputs"]["csv"]).exists()
    assert Path(audit["outputs"]["markdown"]).exists()
    assert Path(audit["outputs"]["pdf"]).exists()
    payload = json.loads(Path(audit["outputs"]["json"]).read_text(encoding="utf-8"))
    assert payload["schema"] == "AIResearchEvidenceDecisionMatrixV1"
    assert len(payload["rows"]) == audit["row_count"]


def _seed_audits(audit_dir: Path) -> None:
    _write_json(
        audit_dir / "data_trust_audit_2026-06-06.json",
        {
            "records": [
                {
                    "record_id": "dataTrust_ok",
                    "source_type": "report_source_log",
                    "source_name": "daily_sources.json",
                    "source_path": "/tmp/daily_sources.json",
                    "data_trust_status": "RECONCILED",
                    "evidence_classification": "FACT",
                    "decision_grade": "Actionable",
                    "issues": "",
                    "next_action": "可进入报告证据链。",
                },
                {
                    "record_id": "dataTrust_reject",
                    "source_type": "json_artifact",
                    "source_name": "automation_health_failed.json",
                    "source_path": "/tmp/automation_health_failed.json",
                    "data_trust_status": "REJECTED",
                    "evidence_classification": "FACT",
                    "decision_grade": "Reject",
                    "issues": "automation health failed",
                    "next_action": "修复健康检查后重跑。",
                },
            ]
        },
    )
    _write_json(
        audit_dir / "reconciliation_audit_2026-06-06.json",
        {
            "checks": [
                {
                    "check_id": "recon_pdf",
                    "domain": "report_chain",
                    "check_name": "source_log_pdf_pairing",
                    "status": "warn",
                    "severity": "P1",
                    "evidence_classification": "FACT",
                    "decision_grade": "Watch",
                    "issue": "missing historical pdf",
                    "next_action": "补齐正式 PDF。",
                    "source_paths": "/tmp/missing.pdf",
                }
            ]
        },
    )
    _write_json(
        audit_dir / "manual_review_queue_2026-06-06.json",
        {
            "items": [
                {
                    "review_id": "manualReview_alipay",
                    "queue_status": "Open",
                    "priority": "P1",
                    "source_layer": "DataTrust",
                    "source_domain": "csv_artifact",
                    "item_name": "current_positions.csv",
                    "item_status": "NEEDS_REVIEW",
                    "evidence_classification": "OBSERVATION",
                    "decision_grade": "Watch",
                    "user_confirmation_required": True,
                    "blocker_scope": "Account evidence requires user confirmation before use.",
                    "issue": "支付宝持仓需要确认。",
                    "next_action": "请用户确认。",
                    "source_paths": "/tmp/current_positions.csv",
                }
            ]
        },
    )
    _write_json(
        audit_dir / "entity_registry_2026-06-06.json",
        {
            "entities": [
                {
                    "entity_id": "entity_1",
                    "entity_type": "FinancialInstrument",
                    "canonical_name": "农业ETF天弘",
                    "evidence_classification": "FACT",
                    "decision_grade": "Actionable",
                    "issues": "",
                    "source_paths": "/tmp/watchlist.csv",
                }
            ],
            "conflicts": [
                {
                    "alias_id": "alias_1",
                    "entity_id": "entity_1",
                    "alias": "512620",
                    "normalized_alias": "512620",
                    "source_path": "/tmp/watchlist.csv",
                }
            ],
        },
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
