from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_operator_input_status import build_status, validate_status


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
    assert payload["operator_inputs_ready_for_release_manager"] is False
    assert payload["release_gate_closed_by_input_status"] is False
    assert payload["input_statuses"][0]["status"] == "MISSING"
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
    assert payload["input_statuses"][0]["status"] == "REJECTED_TEMPLATE_COPY"
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
    assert payload["release_manager_preflight_refresh_allowed"] is False
    assert payload["input_statuses"][0]["status"] == "PRESENT_REQUIRES_VALIDATOR"
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
