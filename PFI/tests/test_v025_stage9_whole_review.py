from __future__ import annotations

import json
from pathlib import Path
import re

from pfi_os.application.analysis.stage9_reviewed_analysis import (
    COMPONENT_LABELS,
    build_stage9_reviewed_analysis_pack,
    validate_stage9_reviewed_analysis_pack,
)
from pfi_os.application.decisions.decision_review import validate_phase93_decision_pack


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
ANALYSIS_PATH = PFI_ROOT / "config/reports/v025_stage9_reviewed_analysis_snapshot.json"
DECISION_PATH = PFI_ROOT / "config/reports/v025_phase93_decision_snapshot.json"
MODEL_REPORT_PATH = (
    PFI_ROOT
    / "reports/pfi_v025/stage_9/whole_stage_review/model_validation_report.html"
)


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_reviewed_analysis_rebuilds_from_immutable_inputs_and_passes() -> None:
    snapshot = _json(ANALYSIS_PATH)
    rebuilt = build_stage9_reviewed_analysis_pack(
        PFI_ROOT, observed_at=str(snapshot["observed_at"])
    )

    assert snapshot == rebuilt
    assert validate_stage9_reviewed_analysis_pack(snapshot, pfi_root=PFI_ROOT) == {
        "schema": "PFIV025Stage9ReviewedAnalysisValidationV1",
        "phase_id": "V025-S9-WHOLE-REVIEW",
        "status": "pass",
        "errors": [],
        "report_count": 5,
        "component_count": 4,
        "cross_report_hashes_consistent": True,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }
    assert snapshot["status"] == "candidate_pass_pending_whole_stage_rereview"
    assert snapshot["phase_9_3_candidate_complete"] is True
    assert snapshot["stage_9_whole_stage_review_done"] is False
    assert snapshot["stage_10_started"] is False


def test_main_reports_are_truthful_and_four_consumption_components_are_visible() -> None:
    snapshot = _json(ANALYSIS_PATH)
    reports = {row["report_type"]: row for row in snapshot["report_set"]}

    assert set(reports) == {"net_worth", "cash", "investment", "consumption", "cashflow"}
    assert {key: row["status"] for key, row in reports.items()} == {
        "net_worth": "blocked",
        "cash": "blocked",
        "investment": "blocked",
        "consumption": "partial",
        "cashflow": "partial",
    }
    required = {
        "data_range",
        "sample_counts",
        "coverage",
        "report_as_of",
        "formula_ids",
        "parameter_ids",
        "hashes",
        "conclusions",
        "anomaly_ids",
        "limitations",
        "review_entry_ids",
    }
    assert all(required <= set(report) for report in reports.values())

    components = reports["consumption"]["component_cards"]
    assert [row["metric_id"] for row in components] == list(COMPONENT_LABELS)
    assert [row["label_zh"] for row in components] == list(COMPONENT_LABELS.values())
    assert all(row["status"] == "ready" for row in components)
    assert all(row["value_visibility"] == "private_runtime_only_not_persisted" for row in components)
    assert "不等于净资产损失" in components[0]["scope_zh"]


def test_current_decisions_and_all_four_exports_bind_the_reviewed_snapshot() -> None:
    analysis = _json(ANALYSIS_PATH)
    decision = _json(DECISION_PATH)

    assert validate_phase93_decision_pack(decision, pfi_root=PFI_ROOT)["status"] == "pass"
    assert decision["source_analysis_pack_hash"] == analysis["pack_hash"]
    consumption = next(
        row for row in decision["export_snapshot"]["reports"]
        if row["report_type"] == "consumption"
    )
    assert len(consumption["component_cards"]) == 4
    assert {row["source_snapshot_hash"] for row in decision["export_manifest"]["files"]} == {
        decision["export_snapshot_hash"]
    }
    assert decision["automatic_trading_allowed"] is False
    assert decision["trade_execution_available"] is False


def test_model_validation_report_is_current_complete_and_public_safe() -> None:
    analysis = _json(ANALYSIS_PATH)
    html = MODEL_REPORT_PATH.read_text(encoding="utf-8")

    assert str(analysis["pack_hash"]) in html
    for label in COMPONENT_LABELS.values():
        assert label in html
    for phrase in (
        "不变量",
        "变形验证",
        "历史/样本外",
        "敏感性与参数调整影响",
        "模型限制",
        "反方证据",
        "不提供自动交易或订单执行能力",
    ):
        assert phrase in html
    assert not re.search(r"\bCNY\s+-?[0-9]", html)
    assert "/Users/" not in html
    assert "place_order" not in html
    assert "execute_trade" not in html
