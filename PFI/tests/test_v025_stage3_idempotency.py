from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from pfi_os.application.stage3_reconciliation import (
    ACCEPTANCE_ID,
    CONTRACT_ID,
    PHASE_ID,
    TASK_IDS,
    build_phase33_contract,
    load_phase33_policy,
    run_phase33_real_reconciliation,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_3" / "phase_3_3"
POLICY_PATH = PFI_ROOT / "config" / "event_types" / "v025_phase_3_3_reconciliation_policy.json"
TASK_PACK = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
OBSERVED_AT = "2026-07-14T12:00:00Z"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


@pytest.fixture(scope="module")
def real_run():
    return run_phase33_real_reconciliation(REPO_ROOT, observed_at=OBSERVED_AT)


def test_phase_contract_is_exactly_stage3_phase33() -> None:
    contract = build_phase33_contract()

    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 3
    assert contract["phase_id"] == PHASE_ID == "V025-S3-P3.3"
    assert contract["contract_id"] == CONTRACT_ID == "PFI-V025-STAGE3-PHASE33-RECONCILIATION"
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-S3-P33-RECONCILIATION"
    assert contract["task_ids"] == list(TASK_IDS) == [
        "S3-P3-T1",
        "S3-P3-T2",
        "S3-P3-T3",
        "S3-P3-T4",
    ]
    assert contract["real_data_read_only"] is True
    assert contract["financial_fixture_fallback_allowed"] is False
    assert contract["database_changed"] is False
    assert contract["finder_used"] is False
    assert "Stage 3 whole-stage review" in contract["explicitly_not_done"]


def test_phase33_policy_is_fail_closed_and_has_no_source_name_or_amount_time_linking() -> None:
    policy = load_phase33_policy()

    assert policy["source_name_inference"] is False
    assert policy["amount_time_heuristic_grouping"] is False
    assert policy["unresolved_transfer_policy"] == "review_required_no_publication"
    assert policy["unresolved_refund_policy"] == "review_required_no_publication"
    assert policy["upstream_review_state_policy"] == "review_required_no_publication"
    assert policy["same_economic_event_per_metric_max_count"] == 1
    assert policy["read_model_hash_scope"] == "snapshot_not_page"
    assert policy["source_temporal_granularity"] == "date"
    assert policy["date_normalization"] == "utc_start_of_source_date_no_time_precision_claim"


def test_real_git_object_duplicate_import_publishes_zero_second_pass(real_run) -> None:
    result = real_run.idempotency_result

    assert result["status"] == "pass"
    assert result["isolation_mode"] == "immutable_git_object_snapshot"
    assert result["input_record_count"] == 8815
    assert result["first_import_candidate_count"] == 6879
    assert result["first_import_published_count"] == 6879
    assert result["second_import_candidate_count"] == 6879
    assert result["second_import_published_count"] == 0
    assert result["second_import_duplicate_count"] == 6879
    assert result["idempotency_key_collision_count"] == 0
    assert result["source_identity_before"] == result["source_identity_after"]
    assert result["source_mutation_performed"] is False
    assert result["financial_fixture_fallback_used"] is False
    assert result["raw_rows_emitted"] == 0
    assert result["financial_values_emitted"] == 0


def test_real_reconciliation_is_complete_or_locatable_without_silent_drop(real_run) -> None:
    reconciliation = real_run.reconciliation_summary
    queue = real_run.review_queue_summary

    assert reconciliation["status"] == "pass_with_review_queue"
    assert reconciliation["input_record_count"] == 8815
    assert reconciliation["published_record_count"] == 6879
    assert reconciliation["review_queue_record_count"] == 1936
    assert reconciliation["silent_drop_count"] == 0
    assert reconciliation["input_partition_complete"] is True
    assert reconciliation["published_investment_event_count"] == 3166
    assert reconciliation["published_transfer_without_explicit_link_or_role_count"] == 0
    assert reconciliation["published_refund_without_offset_count"] == 0
    assert reconciliation["transfer_chain_status"] == "pass_fail_closed_to_review"
    assert reconciliation["refund_chain_status"] == "pass_fail_closed_to_review"
    assert reconciliation["investment_chain_status"] == "pass"
    assert queue["status"] == "pass"
    assert queue["review_queue_record_count"] == 1936
    assert queue["reason_counts"] == {
        "refund_offset_missing": 249,
        "transfer_role_or_link_missing": 1250,
        "upstream_review_required": 406,
        "zero_amount": 31,
    }
    assert queue["private_identifiers_emitted"] == 0
    assert queue["financial_values_emitted"] == 0


def test_every_published_real_record_has_complete_redacted_lineage(real_run) -> None:
    lineage = real_run.lineage_samples_redacted

    assert lineage["status"] == "pass"
    assert lineage["published_record_count"] == 6879
    assert lineage["complete_lineage_count"] == 6879
    assert lineage["missing_lineage_count"] == 0
    assert lineage["lineage_order"] == [
        "raw_record_id_hash",
        "normalized_transaction_id",
        "interconnection_group_id",
        "economic_event_id",
        "ledger_event_id",
        "idempotency_key",
    ]
    assert lineage["financial_values_emitted"] == 0
    assert lineage["private_identifiers_emitted"] == 0
    serialized = json.dumps(lineage)
    for forbidden in ("amount", "account_ref", "/Users/", "description"):
        assert forbidden not in serialized


def test_tracked_phase33_artifacts_are_bound_to_runtime_contract() -> None:
    evidence = _json(REPORT_ROOT / "evidence.json")
    changed = (REPORT_ROOT / "changed_files.txt").read_text(encoding="utf-8").splitlines()
    tracked_idempotency = _json(REPORT_ROOT / "idempotency_result.json")
    tracked_reconciliation = _json(REPORT_ROOT / "reconciliation_summary.json")
    tracked_queue = _json(REPORT_ROOT / "review_queue_summary.json")

    run = run_phase33_real_reconciliation(
        REPO_ROOT,
        observed_at=str(evidence["observed_at"]),
        git_ref=str(tracked_idempotency["resolved_commit"]),
    )
    assert tracked_idempotency == run.idempotency_result
    assert tracked_reconciliation == run.reconciliation_summary
    assert tracked_queue == run.review_queue_summary
    assert evidence["status"] == "candidate_pass"
    assert evidence["phase_id"] == PHASE_ID
    assert evidence["task_ids"] == list(TASK_IDS)
    assert evidence["stage_3_status"] == "in_progress"
    assert evidence["stage_3_phase_3_3_status"] == "candidate_pass"
    assert evidence["stage_3_whole_stage_review_status"] == "not_started"
    assert evidence["real_financial_data_read"] is True
    assert evidence["real_financial_data_mutated"] is False
    assert evidence["database_changed"] is False
    assert evidence["finder_used"] is False
    assert changed == sorted(changed)
    assert len(changed) == len(set(changed))
    for relative, expected in evidence["artifact_hashes"].items():
        assert hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest() == expected


def test_phase_evidence_validates_against_taskpack_schema() -> None:
    if not TASK_PACK.is_file():
        return
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
    evidence = _json(REPORT_ROOT / "evidence.json")

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(evidence)
    assert evidence["git_commit"] == "SELF"
    assert evidence["requires_user_acceptance"] is True
