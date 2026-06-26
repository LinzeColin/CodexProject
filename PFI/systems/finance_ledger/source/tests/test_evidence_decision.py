from __future__ import annotations

import json
from pathlib import Path

from econ_bleed_analyzer.evidence_decision import (
    build_evidence_decision_layer,
    evidence_decision_report_markdown,
    write_evidence_decision_outputs,
)


def test_evidence_decision_layer_unifies_core_audit_layers():
    layer = build_evidence_decision_layer(
        data_trust_rows=[
            {
                "review_key": "tx-1",
                "counterparty": "测试商户",
                "data_trust_status": "RECONCILED",
                "status_reason": "production matched",
            }
        ],
        reconciliation_rows=[{"check_id": "count_check", "status": "pass", "detail": "ok"}],
        manual_review_rows=[{"review_key": "review-1", "queue_status": "PENDING_REVIEW", "priority": "P1"}],
        entity_rows=[{"entity_id": "entity-1", "entity_type": "counterparty", "canonical_name": "测试商户"}],
        alias_rows=[{"alias_id": "alias-1", "alias_value": "测试商户", "collision_status": "unique"}],
        control_plan_rows=[{"focus_area": "平台便利", "priority": "P1", "recommended_action": "下期复核"}],
        source_platform_rows=[{"platform": "支付宝", "transaction_count": "10", "pending_review_count": "1"}],
        report_rows=[{"report_key": "monthly_pdf", "report_path": "/tmp/monthly_report.pdf", "status": "missing"}],
        question_answer_rows=[{"question": "本月最该优化哪类支出", "answer_policy": "local evidence only"}],
    )

    matrix = layer["evidence_decision_matrix"]
    summary = layer["evidence_decision_summary"]

    assert len(matrix) == 9
    assert summary
    assert {row["evidence_classification"] for row in matrix}.issubset({"FACT", "INFERENCE", "OPINION", "OBSERVATION"})
    assert {row["decision_grade"] for row in matrix}.issubset({"Actionable", "Watch", "Observe", "Reject"})
    assert any(row["layer"] == "ManualReview" and row["decision_grade"] == "Watch" for row in matrix)
    assert any(row["layer"] == "ReportLayer" and row["decision_grade"] == "Reject" for row in matrix)


def test_evidence_decision_outputs_include_machine_contract(tmp_path: Path):
    layer = build_evidence_decision_layer(
        data_trust_rows=[{"review_key": "tx-1", "counterparty": "测试商户", "data_trust_status": "RECONCILED"}]
    )

    paths = write_evidence_decision_outputs(layer, tmp_path)
    report = evidence_decision_report_markdown(layer)

    assert paths["evidence_decision_matrix_csv"].exists()
    assert paths["evidence_decision_matrix_json"].exists()
    assert paths["evidence_decision_summary_csv"].exists()
    assert paths["evidence_decision_matrix_report_md"].exists()
    assert "audit/evidence_decision_matrix.csv" in report
    assert "v_evidence_decision_watchlist" in report
    payload = json.loads(paths["evidence_decision_matrix_json"].read_text(encoding="utf-8"))
    assert payload[0]["schema_version"] == "evidence_decision_matrix.v1"
