from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_operator_input_status import (
    append_submission_receipt_to_ledger,
    build_status,
    build_submission_preflight,
    build_submission_receipt,
    empty_receipt_ledger,
    read_receipt_ledger,
    record_submission_receipt,
    validate_receipt_ledger,
    validate_status,
)


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def kit_manifest(tmp_path: Path, *, target: Path, template: Path) -> Path:
    return write_json(
        tmp_path / "operator_input_kit_manifest.json",
        {
            "post_submission_commands": ["make verify"],
            "kit_items": [
                {
                    "input_id": "A202_source_license_passage_owner_legal_release",
                    "acceptance_id": "A202",
                    "kit_template_path": template.as_posix(),
                    "kit_template_sha256": (
                        "REPLACED_BY_TEST"
                    ),
                    "submission_target": target.as_posix(),
                    "validation_command": (
                        "make generate-a202-signed-intake-preflight "
                        "validate-a202-signed-intake-preflight"
                    ),
                    "completion_criteria": [
                        "source-license reviews cover every required Golden Vertical source anchor"
                    ],
                }
            ],
        },
    )


def patch_manifest_template_sha(manifest_path: Path, template: Path) -> None:
    from scripts.validate_operator_input_status import sha256_file

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["kit_items"][0]["kit_template_sha256"] = sha256_file(template)
    manifest_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_status_reports_missing_operator_inputs(tmp_path: Path) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = tmp_path / "operator_inputs" / "a202" / "signed.json"
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)

    payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )

    assert payload["status"] == "WAITING_FOR_OPERATOR_INPUTS"
    assert payload["missing_count"] == 1
    assert payload["rejected_count"] == 0
    assert payload["dedicated_validator_count"] == 1
    assert payload["blocked_validator_count"] == 1
    assert payload["pending_dedicated_validator_count"] == 0
    assert payload["dedicated_validators_ready_for_release_manager"] is False
    assert payload["operator_inputs_ready_for_release_manager"] is False
    assert payload["release_gate_closed_by_input_status"] is False
    assert payload["input_statuses"][0]["status"] == "MISSING"
    assert payload["input_statuses"][0]["validator_status"] == "NOT_RUN_INPUT_MISSING"
    assert payload["input_statuses"][0]["validator_contract"] == {
        "validator_id": "VAL-A202-SIGNED-INTAKE-PREFLIGHT",
        "validator_type": "signed_release_decision_intake",
        "command": (
            "make generate-a202-signed-intake-preflight "
            "validate-a202-signed-intake-preflight"
        ),
        "expected_artifacts": [
            "artifacts/tests/a202/t1301_a202_signed_intake_preflight.json",
            "artifacts/tests/a202/t1301_a202_operator_intake_gap_packet.json",
        ],
        "success_statuses": ["A202_OPERATOR_INTAKE_READY_FOR_RELEASE_PREFLIGHT"],
        "required_before_release_manager": True,
        "counts_as_release_ready_without_success": False,
    }
    validate_status(payload, kit_manifest_path=manifest)


def test_status_rejects_template_copy_at_submission_target(tmp_path: Path) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = write_json(
        tmp_path / "operator_inputs" / "a202" / "signed.json",
        {"template_only": True},
    )
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)

    payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )

    assert payload["status"] == "OPERATOR_INPUTS_REJECTED"
    assert payload["missing_count"] == 0
    assert payload["rejected_count"] == 1
    assert payload["blocked_validator_count"] == 1
    assert payload["input_statuses"][0]["status"] == "REJECTED_TEMPLATE_COPY"
    assert payload["input_statuses"][0]["validator_status"] == "BLOCKED_REJECTED_INPUT"
    assert payload["input_statuses"][0]["template_counts_as_clearance"] is False
    validate_status(payload, kit_manifest_path=manifest)


def test_status_reports_present_inputs_as_requiring_validators(tmp_path: Path) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = write_json(
        tmp_path / "operator_inputs" / "a202" / "signed.json",
        {"signed_by": "operator", "template_only": False},
    )
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)

    payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )

    assert payload["status"] == "OPERATOR_INPUTS_PRESENT_REQUIRING_VALIDATION"
    assert payload["present_requiring_validator_count"] == 1
    assert payload["blocked_validator_count"] == 0
    assert payload["pending_dedicated_validator_count"] == 1
    assert payload["release_manager_preflight_refresh_allowed"] is False
    assert payload["input_statuses"][0]["status"] == "PRESENT_REQUIRES_VALIDATOR"
    assert payload["input_statuses"][0]["validator_status"] == "PENDING_DEDICATED_VALIDATOR"
    assert (
        payload["input_statuses"][0]["validator_contract"][
            "counts_as_release_ready_without_success"
        ]
        is False
    )
    validate_status(payload, kit_manifest_path=manifest)


def test_validation_detects_operator_input_status_drift(tmp_path: Path) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = tmp_path / "operator_inputs" / "a202" / "signed.json"
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )
    payload["release_gate_closed_by_input_status"] = True

    with pytest.raises(ValueError, match="operator input status drift"):
        validate_status(payload, kit_manifest_path=manifest)


def test_status_requires_known_validator_contract(tmp_path: Path) -> None:
    template = write_json(tmp_path / "kit" / "unknown.template.json", {"template_only": True})
    target = tmp_path / "operator_inputs" / "unknown" / "signed.json"
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["kit_items"][0]["input_id"] = "UNKNOWN_OPERATOR_INPUT"
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    with pytest.raises(ValueError, match="missing validator contract"):
        build_status(
            kit_manifest_path=manifest,
            generated_at="2026-06-27T00:00:00Z",
        )


def test_submission_preflight_reports_missing_target_as_not_dispatchable(
    tmp_path: Path,
) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = tmp_path / "operator_inputs" / "a202" / "signed.json"
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    status_payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )

    payload = build_submission_preflight(
        status_payload,
        input_id="A202_source_license_passage_owner_legal_release",
    )

    assert payload["schema_version"] == "eei-operator-input-submission-preflight-v1"
    assert payload["status"] == "SUBMISSION_TARGET_MISSING"
    assert payload["validator_dispatch_allowed"] is False
    assert payload["release_gate_closure_allowed"] is False
    assert payload["next_validation_command"] == (
        "make generate-a202-signed-intake-preflight validate-a202-signed-intake-preflight"
    )


def test_submission_preflight_allows_manual_validator_dispatch_for_present_target(
    tmp_path: Path,
) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = write_json(
        tmp_path / "operator_inputs" / "a202" / "signed.json",
        {"signed_by": "operator", "template_only": False},
    )
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    status_payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )
    observed_sha = status_payload["input_statuses"][0]["submission_target_sha256"]

    payload = build_submission_preflight(
        status_payload,
        input_id="A202_source_license_passage_owner_legal_release",
        submitted_sha256=observed_sha.upper(),
    )

    assert payload["status"] == "READY_FOR_DEDICATED_VALIDATOR_DISPATCH"
    assert payload["validator_dispatch_allowed"] is True
    assert payload["validator_dispatch_mode"] == "manual_command_only"
    assert payload["submitted_hash_matches_observed"] is True
    assert payload["validator_contract"]["validator_id"] == "VAL-A202-SIGNED-INTAKE-PREFLIGHT"
    assert payload["release_manager_preflight_refresh_allowed"] is False


def test_submission_preflight_blocks_hash_mismatch(tmp_path: Path) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = write_json(
        tmp_path / "operator_inputs" / "a202" / "signed.json",
        {"signed_by": "operator", "template_only": False},
    )
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    status_payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )

    payload = build_submission_preflight(
        status_payload,
        input_id="A202_source_license_passage_owner_legal_release",
        submitted_sha256="0" * 64,
    )

    assert payload["status"] == "SUBMISSION_HASH_MISMATCH"
    assert payload["validator_dispatch_allowed"] is False
    assert payload["submitted_hash_matches_observed"] is False


def test_submission_preflight_rejects_unknown_input_id(tmp_path: Path) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = tmp_path / "operator_inputs" / "a202" / "signed.json"
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    status_payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )

    payload = build_submission_preflight(status_payload, input_id="UNKNOWN_OPERATOR_INPUT")

    assert payload["status"] == "REJECTED_UNKNOWN_OPERATOR_INPUT"
    assert payload["validator_dispatch_allowed"] is False
    assert payload["validator_contract"] is None


def test_submission_receipt_records_present_target_pending_validator(
    tmp_path: Path,
) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = write_json(
        tmp_path / "operator_inputs" / "a202" / "signed.json",
        {"signed_by": "operator", "template_only": False},
    )
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    status_payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )
    observed_sha = status_payload["input_statuses"][0]["submission_target_sha256"]

    payload = build_submission_receipt(
        status_payload,
        input_id="A202_source_license_passage_owner_legal_release",
        submitted_sha256=observed_sha,
        submitted_by="release.operator",
        submission_note="source-license packet placed in approved operator-input path",
        generated_at="2026-06-27T00:01:00Z",
    )

    assert payload["schema_version"] == "eei-operator-input-submission-receipt-v1"
    assert payload["receipt_id"].startswith("sha256:")
    assert payload["status"] == "RECEIPT_RECORDED_PENDING_DEDICATED_VALIDATOR"
    assert payload["receipt_accepted"] is True
    assert payload["validator_dispatch_allowed"] is True
    assert payload["validator_dispatch_mode"] == "manual_command_only"
    assert payload["next_validation_command"] == (
        "make generate-a202-signed-intake-preflight validate-a202-signed-intake-preflight"
    )
    assert payload["release_gate_closure_allowed"] is False
    assert payload["release_manager_preflight_refresh_allowed"] is False
    assert payload["mvp_release_gate_refresh_allowed"] is False


def test_submission_receipt_rejects_hash_mismatch(tmp_path: Path) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = write_json(
        tmp_path / "operator_inputs" / "a202" / "signed.json",
        {"signed_by": "operator", "template_only": False},
    )
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    status_payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )

    payload = build_submission_receipt(
        status_payload,
        input_id="A202_source_license_passage_owner_legal_release",
        submitted_sha256="0" * 64,
        submitted_by="release.operator",
        generated_at="2026-06-27T00:01:00Z",
    )

    assert payload["status"] == "RECEIPT_REJECTED_HASH_MISMATCH"
    assert payload["receipt_accepted"] is False
    assert payload["validator_dispatch_allowed"] is False
    assert payload["next_validation_command"] == ""
    assert payload["expected_artifacts"] == []


def test_submission_receipt_ledger_records_and_validates_receipt(tmp_path: Path) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = write_json(
        tmp_path / "operator_inputs" / "a202" / "signed.json",
        {"signed_by": "operator", "template_only": False},
    )
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    status_payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )
    observed_sha = status_payload["input_statuses"][0]["submission_target_sha256"]
    receipt = build_submission_receipt(
        status_payload,
        input_id="A202_source_license_passage_owner_legal_release",
        submitted_sha256=observed_sha,
        submitted_by="release.operator",
        generated_at="2026-06-27T00:01:00Z",
    )

    ledger = append_submission_receipt_to_ledger(
        empty_receipt_ledger(generated_at="2026-06-27T00:00:00Z"),
        receipt,
        generated_at="2026-06-27T00:02:00Z",
    )

    assert ledger["schema_version"] == "eei-operator-input-submission-receipt-ledger-v1"
    assert ledger["receipt_count"] == 1
    assert ledger["accepted_receipt_count"] == 1
    assert ledger["rejected_receipt_count"] == 0
    assert ledger["latest_receipt_id"] == receipt["receipt_id"]
    assert ledger["receipt_recorded"] is True
    assert ledger["write_status"] == "RECEIPT_RECORDED"
    assert ledger["release_gate_closed_by_receipt_ledger"] is False
    validate_receipt_ledger(ledger)


def test_submission_receipt_ledger_replay_is_idempotent(tmp_path: Path) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = write_json(
        tmp_path / "operator_inputs" / "a202" / "signed.json",
        {"signed_by": "operator", "template_only": False},
    )
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    status_payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )
    observed_sha = status_payload["input_statuses"][0]["submission_target_sha256"]
    receipt = build_submission_receipt(
        status_payload,
        input_id="A202_source_license_passage_owner_legal_release",
        submitted_sha256=observed_sha,
        submitted_by="release.operator",
        generated_at="2026-06-27T00:01:00Z",
    )
    receipt_later = build_submission_receipt(
        status_payload,
        input_id="A202_source_license_passage_owner_legal_release",
        submitted_sha256=observed_sha,
        submitted_by="release.operator",
        generated_at="2026-06-27T00:05:00Z",
    )
    first = append_submission_receipt_to_ledger(empty_receipt_ledger(), receipt)

    replay = append_submission_receipt_to_ledger(first, receipt_later)

    assert receipt_later["receipt_id"] == receipt["receipt_id"]
    assert replay["receipt_count"] == 1
    assert replay["receipt_recorded"] is False
    assert replay["write_status"] == "IDEMPOTENT_RECEIPT_ALREADY_RECORDED"


def test_submission_receipt_ledger_blocks_previous_receipt_conflict(
    tmp_path: Path,
) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = write_json(
        tmp_path / "operator_inputs" / "a202" / "signed.json",
        {"signed_by": "operator", "template_only": False},
    )
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    status_payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )
    observed_sha = status_payload["input_statuses"][0]["submission_target_sha256"]
    receipt = build_submission_receipt(
        status_payload,
        input_id="A202_source_license_passage_owner_legal_release",
        submitted_sha256=observed_sha,
        submitted_by="release.operator",
        generated_at="2026-06-27T00:01:00Z",
    )

    with pytest.raises(ValueError, match="previous receipt conflict"):
        append_submission_receipt_to_ledger(
            empty_receipt_ledger(),
            receipt,
            expected_previous_receipt_id="sha256:" + "1" * 64,
        )


def test_record_submission_receipt_persists_ledger_without_changing_input(
    tmp_path: Path,
) -> None:
    template = write_json(tmp_path / "kit" / "a202.template.json", {"template_only": True})
    target = write_json(
        tmp_path / "operator_inputs" / "a202" / "signed.json",
        {"signed_by": "operator", "template_only": False},
    )
    before = target.read_text(encoding="utf-8")
    manifest = kit_manifest(tmp_path, target=target, template=template)
    patch_manifest_template_sha(manifest, template)
    status_payload = build_status(
        kit_manifest_path=manifest,
        generated_at="2026-06-27T00:00:00Z",
    )
    observed_sha = status_payload["input_statuses"][0]["submission_target_sha256"]
    ledger_path = tmp_path / "ledger" / "operator_input_submission_receipts.json"

    response = record_submission_receipt(
        status_payload,
        input_id="A202_source_license_passage_owner_legal_release",
        submitted_sha256=observed_sha,
        submitted_by="release.operator",
        ledger_path=ledger_path,
        generated_at="2026-06-27T00:01:00Z",
    )
    ledger = read_receipt_ledger(ledger_path)

    assert response["ledger_write_status"] == "RECEIPT_RECORDED"
    assert response["receipt_recorded"] is True
    assert response["ledger_receipt_count"] == 1
    assert ledger["receipt_count"] == 1
    assert target.read_text(encoding="utf-8") == before
