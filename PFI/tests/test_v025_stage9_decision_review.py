from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from pfi_os.application.decisions.decision_review import (
    ACCEPTANCE_ID,
    PHASE_ID,
    REVIEW_OUTCOMES,
    TASK_IDS,
    apply_human_review,
    build_phase93_contract,
    build_phase93_core,
    canonical_hash,
    validate_phase93_decision_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SNAPSHOT_PATH = PFI_ROOT / "config/reports/v025_phase93_decision_snapshot.json"
REVIEWED_ANALYSIS_PATH = PFI_ROOT / "config/reports/v025_stage9_reviewed_analysis_snapshot.json"


def _snapshot() -> dict[str, object]:
    payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _resign_export_manifest(payload: dict[str, object]) -> None:
    manifest = payload["export_manifest"]
    manifest["manifest_hash"] = canonical_hash(
        {key: value for key, value in manifest.items() if key != "manifest_hash"}
    )
    payload["ui_contract"]["export_manifest_hash"] = manifest["manifest_hash"]
    payload["ui_contract"]["export_cards"] = deepcopy(manifest["files"])
    payload["pack_hash"] = canonical_hash(
        {key: value for key, value in payload.items() if key != "pack_hash"}
    )


def test_phase93_contract_is_t3_current_phase_only_and_has_no_trade_capability() -> None:
    contract = build_phase93_contract()

    assert contract["phase_id"] == PHASE_ID
    assert contract["task_ids"] == list(TASK_IDS)
    assert contract["acceptance_id"] == ACCEPTANCE_ID
    assert contract["risk_tier"] == "T3_FINANCIAL_DECISION_REVIEW_EXPORT"
    assert contract["current_phase_only"] is True
    assert contract["phase_9_2_candidate_required"] is True
    assert contract["review_outcomes"] == list(REVIEW_OUTCOMES)
    assert contract["export_formats"] == ["html", "pdf", "csv", "markdown"]
    assert contract["human_review_required"] is True
    assert contract["automatic_trading_allowed"] is False
    assert contract["trade_execution_available"] is False
    assert contract["stage_9_whole_stage_review_done"] is False
    assert contract["stage_10_started"] is False
    assert contract["database_read"] is False
    assert contract["finder_used"] is False
    assert contract["push_performed"] is False
    assert contract["app_install_performed"] is False


def test_decision_pack_rebuilds_from_current_phase92_truth_and_passes() -> None:
    snapshot = _snapshot()
    rebuilt = build_phase93_core(PFI_ROOT, observed_at=str(snapshot["observed_at"]))
    gate = validate_phase93_decision_pack(snapshot, pfi_root=PFI_ROOT)

    assert gate == {
        "schema": "PFIV025Stage9Phase93DecisionValidationV1",
        "phase_id": PHASE_ID,
        "status": "pass",
        "errors": [],
        "decision_count": 2,
        "counter_evidence_count": 4,
        "invalidation_condition_count": 4,
        "export_format_count": 4,
        "cross_format_same_snapshot": True,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }
    for key, value in rebuilt.items():
        if key == "schema":
            assert snapshot["core_schema"] == value
        else:
            assert snapshot[key] == value
    assert snapshot["status"] == "candidate_pass"
    reviewed_analysis = json.loads(REVIEWED_ANALYSIS_PATH.read_text(encoding="utf-8"))
    assert snapshot["source_analysis_pack_hash"] == reviewed_analysis["pack_hash"]
    assert snapshot["stage_9_whole_stage_review_done"] is False


def test_every_decision_has_required_evidence_countercase_invalidation_and_review() -> None:
    decisions = _snapshot()["decision_objects"]
    assert isinstance(decisions, list)
    assert {row["decision_id"] for row in decisions} == {
        "DEC-PFI-V025-REVIEW-QUEUE",
        "DEC-PFI-V025-SOURCE-COMPLETENESS",
    }
    for decision in decisions:
        assert decision["action"]
        assert decision["horizon"] == "next_human_review_session"
        assert decision["status"] == "awaiting_human_review"
        assert decision["confidence_dimensions"]
        assert decision["thesis"]["statement_zh"]
        assert decision["catalysts"]
        assert decision["evidence"]
        assert len(decision["counter_evidence"]) == 2
        assert len(decision["invalidation_conditions"]) == 2
        assert decision["risks"]
        assert decision["portfolio_effect"]["status"] == "not_calculable"
        assert decision["model_versions"]
        assert decision["source_ids"]
        assert decision["human_review_required"] is True
        assert decision["allowed_review_outcomes"] == list(REVIEW_OUTCOMES)
        assert decision["automatic_trading_allowed"] is False
        assert decision["trade_execution_available"] is False
        assert decision["review_route"].startswith("/")
        assert len(decision["review_history"]) == 1
        assert decision["review_history"][0]["event_type"] == "created"


def test_human_review_is_append_only_and_never_executes_the_action() -> None:
    decision = _snapshot()["decision_objects"][0]
    accepted = apply_human_review(
        decision,
        outcome="accepted",
        reviewer_ref="local_owner",
        reason_zh="接受复核任务，但不执行任何交易。",
        observed_at="2026-07-15T16:45:00+10:00",
    )

    assert decision["status"] == "awaiting_human_review"
    assert len(decision["review_history"]) == 1
    assert accepted["status"] == "accepted"
    assert len(accepted["review_history"]) == 2
    assert accepted["review_history"][1]["prior_event_hash"] == decision["review_history"][0]["event_hash"]
    assert accepted["review_history"][1]["event_hash"].startswith("sha256:")
    assert accepted["automatic_trading_allowed"] is False
    assert accepted["trade_execution_available"] is False
    with pytest.raises(ValueError, match="invalid review transition"):
        apply_human_review(
            accepted,
            outcome="rejected",
            reviewer_ref="local_owner",
            reason_zh="无效转换。",
            observed_at="2026-07-15T16:46:00+10:00",
        )


def test_validator_fails_closed_on_hash_trade_review_and_snapshot_tamper() -> None:
    original = _snapshot()

    event_tamper = deepcopy(original)
    event_tamper["decision_objects"][0]["review_history"][0]["reason_zh"] = "tampered"
    assert validate_phase93_decision_pack(event_tamper, pfi_root=PFI_ROOT)["status"] == "fail"

    trade_tamper = deepcopy(original)
    trade_tamper["decision_objects"][0]["trade_execution_available"] = True
    assert validate_phase93_decision_pack(trade_tamper, pfi_root=PFI_ROOT)["status"] == "fail"

    counter_tamper = deepcopy(original)
    counter_tamper["decision_objects"][0]["counter_evidence"] = []
    assert validate_phase93_decision_pack(counter_tamper, pfi_root=PFI_ROOT)["status"] == "fail"

    export_tamper = deepcopy(original)
    export_tamper["export_manifest"]["files"][0]["source_snapshot_hash"] = "sha256:" + "0" * 64
    assert validate_phase93_decision_pack(export_tamper, pfi_root=PFI_ROOT)["status"] == "fail"

    pack_hash_tamper = deepcopy(original)
    pack_hash_tamper["pack_hash"] = "sha256:" + "0" * 64
    assert validate_phase93_decision_pack(pack_hash_tamper, pfi_root=PFI_ROOT)["status"] == "fail"

    ui_tamper = deepcopy(original)
    ui_tamper["ui_contract"]["decision_cards"][0]["thesis"]["statement_zh"] = "tampered"
    ui_tamper["pack_hash"] = canonical_hash(
        {key: value for key, value in ui_tamper.items() if key != "pack_hash"}
    )
    assert validate_phase93_decision_pack(ui_tamper, pfi_root=PFI_ROOT)["status"] == "fail"

    manifest_metadata_tamper = deepcopy(original)
    manifest_metadata_tamper["export_manifest"]["files"][0]["filename"] = "drifted.html"
    _resign_export_manifest(manifest_metadata_tamper)
    assert validate_phase93_decision_pack(
        manifest_metadata_tamper, pfi_root=PFI_ROOT
    )["status"] == "fail"

    byte_size_tamper = deepcopy(original)
    byte_size_tamper["export_manifest"]["files"][0]["byte_size"] += 1
    _resign_export_manifest(byte_size_tamper)
    assert validate_phase93_decision_pack(
        byte_size_tamper, pfi_root=PFI_ROOT
    )["status"] == "fail"

    export_hash_tamper = deepcopy(original)
    export_hash_tamper["export_manifest"]["files"][0]["sha256"] = (
        "sha256:" + "0" * 64
    )
    _resign_export_manifest(export_hash_tamper)
    assert validate_phase93_decision_pack(
        export_hash_tamper, pfi_root=PFI_ROOT
    )["status"] == "fail"
