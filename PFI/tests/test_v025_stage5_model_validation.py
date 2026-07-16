from __future__ import annotations

import json
from pathlib import Path
import zipfile

from jsonschema import Draft202012Validator
import pytest

from pfi_os.application.metrics.model_validation import (
    ACCEPTANCE_ID,
    CONTRACT_ID,
    PHASE_ID,
    TASK_IDS,
    build_phase53_contract,
    run_phase53_real_model_validation,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_5" / "phase_5_3"
CARD_SCHEMA_PATH = PFI_ROOT / "config" / "schemas" / "v025" / "model_validation_card.schema.json"
TASK_PACK = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
OBSERVED_AT = "2026-07-15T00:00:00Z"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


@pytest.fixture(scope="module")
def real_validation():
    return run_phase53_real_model_validation(REPO_ROOT, observed_at=OBSERVED_AT)


def test_phase53_contract_is_t3_read_only_and_stops_before_whole_stage_review() -> None:
    contract = build_phase53_contract()

    assert PHASE_ID == "V025-S5-P5.3"
    assert CONTRACT_ID == "PFI-V025-STAGE5-PHASE53-MODEL-VALIDATION"
    assert ACCEPTANCE_ID == "ACC-PFI-V025-S5-P53-MODEL-VALIDATION"
    assert TASK_IDS == ("S5-P3-T1", "S5-P3-T2", "S5-P3-T3", "S5-P3-T4")
    assert contract["risk_tier"] == "T3_FINANCIAL_MODEL_VALIDATION_PRIVACY"
    assert contract["real_data_read_only"] is True
    assert contract["financial_fixture_fallback_allowed"] is False
    assert contract["stage_5_whole_stage_review_started"] is False
    assert contract["finder_used"] is False
    assert contract["network_performed"] is False
    assert contract["push_performed"] is False
    assert contract["app_install_performed"] is False


def test_real_snapshot_is_immutable_cny_and_partition_complete(real_validation) -> None:
    source = real_validation.source_snapshot_attestation

    assert source["status"] == "pass"
    assert source["isolation_mode"] == "immutable_git_object_snapshot"
    assert source["input_record_count"] == 8815
    assert source["published_record_count"] == 6879
    assert source["review_queue_record_count"] == 1936
    assert source["silent_drop_count"] == 0
    assert source["adapted_financial_event_count"] == 6879
    assert source["currencies"] == ["CNY"]
    assert source["coverage_start"] == "2022-06-06"
    assert source["coverage_end"] == "2026-06-03"
    assert source["source_identity_before"] == source["source_identity_after"]
    assert source["source_mutation_performed"] is False
    assert source["financial_fixture_fallback_used"] is False


def test_real_dual_metrics_pass_invariants_and_metamorphic_tests(real_validation) -> None:
    invariant = real_validation.invariant_results

    assert invariant["status"] == "partial_pass_with_blocked_components"
    assert invariant["dual_metric_reconciliation"]["status"] == "pass"
    assert invariant["dual_metric_reconciliation"]["difference_is_exact_zero"] is True
    assert invariant["dual_metric_reconciliation"]["duplicate_economic_event_count"] == 0
    assert invariant["dual_metric_reconciliation"]["investment_activity_is_net_worth_loss"] is False
    assert invariant["cashflow_window_invariant"]["status"] == "pass"
    assert invariant["cashflow_window_invariant"]["window_record_counts_non_decreasing"] is True
    assert invariant["core_balance_invariants"]["status"] == "blocked_missing_required_sources"
    assert invariant["investment_return_xirr"]["status"] == "blocked_insufficient_chain"

    metamorphic = real_validation.metamorphic_results
    assert metamorphic["status"] == "pass"
    assert metamorphic["input_permutation_invariance"] == "pass"
    assert metamorphic["exact_duplicate_invariance"] == "pass"
    assert metamorphic["positive_scaling_invariance"] == "pass"
    assert metamorphic["date_translation_window_invariance"] == "pass"
    assert metamorphic["source_snapshot_mutated"] is False


def test_real_window_sensitivity_is_explainable_and_false_zero_safe(real_validation) -> None:
    sensitivity = real_validation.sensitivity_results

    assert sensitivity["status"] == "partial_pass_with_blocked_parameters"
    assert sensitivity["cashflow_window_days"] == [7, 21, 30, 60, 90, 180, 360]
    rows = sensitivity["cashflow_window_sensitivity"]
    assert [row["window_days"] for row in rows] == [7, 21, 30, 60, 90, 180, 360]
    counts = [row["record_count"] for row in rows]
    assert counts == sorted(counts)
    assert all(str(row["financial_value_fingerprint"]).startswith("sha256:") for row in rows)
    assert sensitivity["empty_window_boundary"]["status"] == "filtered_empty"
    assert sensitivity["empty_window_boundary"]["financial_values_are_null"] is True
    assert sensitivity["classification_threshold_sensitivity"]["status"] == "blocked_missing_scores"
    assert sensitivity["xirr_parameter_sensitivity"]["status"] == "blocked_insufficient_chain"


def test_model_card_is_schema_valid_partial_and_does_not_overstate(real_validation) -> None:
    card = real_validation.model_validation_card
    schema = _json(CARD_SCHEMA_PATH)

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(card)
    assert card["status"] == "partial_validated_with_blocked_components"
    formulas = {item["formula_id"]: item for item in card["formula_validation"]}
    assert formulas["FORM-PFI-015"]["status"] == "validated_real_snapshot"
    assert formulas["FORM-PFI-019"]["status"] == "validated_real_snapshot"
    assert formulas["FORM-PFI-016"]["status"] == "blocked_missing_required_sources"
    assert formulas["FORM-PFI-017"]["status"] == "blocked_missing_required_sources"
    assert formulas["FORM-PFI-018"]["status"] == "blocked_insufficient_chain"
    assert formulas["FORM-PFI-020"]["status"] == "validated_structure_only"
    assert card["historical_out_of_sample_validation"]["status"] == "blocked_insufficient_ground_truth"
    assert card["consumer_binding"]["same_payload_contract_validated"] is True
    assert card["consumer_binding"]["actual_ui_render_binding_completed"] is False
    assert card["consumer_binding"]["actual_report_render_binding_completed"] is False
    assert card["contains_private_values"] is False
    assert card["production_accepted"] is False


def test_public_validation_artifacts_emit_no_private_rows_or_financial_values(real_validation) -> None:
    public_payloads = (
        real_validation.source_snapshot_attestation,
        real_validation.invariant_results,
        real_validation.metamorphic_results,
        real_validation.sensitivity_results,
        real_validation.model_validation_card,
        real_validation.cross_surface_validation,
    )
    serialized = json.dumps(public_payloads, ensure_ascii=False, sort_keys=True)

    for forbidden in ("/Users/", "account_ref", "description", "raw_record_id", "normalized_transaction_id"):
        assert forbidden not in serialized
    assert '"contains_private_values": true' not in serialized.lower()
    assert real_validation.model_validation_card["financial_values_emitted"] == 0


def test_cross_surface_contract_is_real_snapshot_bound_but_render_binding_is_explicitly_open(real_validation) -> None:
    contract = real_validation.cross_surface_validation

    assert contract["status"] == "contract_pass_render_binding_open"
    assert contract["surface_ids"] == ["homepage", "consumption_page", "report"]
    assert contract["same_payload_hash"] is True
    assert contract["real_snapshot_bound"] is True
    assert contract["actual_ui_render_binding_completed"] is False
    assert contract["actual_report_render_binding_completed"] is False
    assert contract["financial_values_emitted"] == 0


def test_tracked_phase53_artifacts_match_replay_and_taskpack_schema() -> None:
    evidence = _json(REPORT_ROOT / "evidence.json")
    source = _json(REPORT_ROOT / "source_snapshot_attestation.json")
    replay = run_phase53_real_model_validation(
        REPO_ROOT,
        observed_at=str(evidence["observed_at"]),
        git_ref=str(source["resolved_commit"]),
    )

    assert source == replay.source_snapshot_attestation
    assert _json(REPORT_ROOT / "invariant_results.json") == replay.invariant_results
    assert _json(REPORT_ROOT / "metamorphic_results.json") == replay.metamorphic_results
    assert _json(REPORT_ROOT / "sensitivity_results.json") == replay.sensitivity_results
    assert _json(REPORT_ROOT / "model_validation_card.json") == replay.model_validation_card
    assert _json(REPORT_ROOT / "cross_surface_validation.json") == replay.cross_surface_validation
    assert evidence["status"] == "candidate_pass"
    assert evidence["stage_5_status"] == "in_progress"
    assert evidence["stage_5_phase_5_3_status"] == "candidate_pass"
    assert evidence["stage_5_whole_stage_review_status"] == "not_started"
    assert evidence["real_financial_data_read"] is True
    assert evidence["real_financial_data_mutated"] is False
    assert evidence["database_changed"] is False
    assert evidence["finder_used"] is False

    if TASK_PACK.is_file():
        with zipfile.ZipFile(TASK_PACK) as archive:
            schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(evidence)
