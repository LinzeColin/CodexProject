#!/usr/bin/env python3
"""Generate and validate the fail-closed operator-input status manifest."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from validate_external_release_evidence_bundle import (
        DEFAULT_OPERATOR_INPUT_KIT_MANIFEST,
        REQUIRED_ACCEPTANCE_IDS,
        REQUIRED_TASK_IDS,
        display_path,
        read_json,
        sha256_file,
        write_json,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as scripts.*
    from scripts.validate_external_release_evidence_bundle import (
        DEFAULT_OPERATOR_INPUT_KIT_MANIFEST,
        REQUIRED_ACCEPTANCE_IDS,
        REQUIRED_TASK_IDS,
        display_path,
        read_json,
        sha256_file,
        write_json,
    )

ROOT = Path(__file__).resolve().parents[1]

STATUS_SCHEMA_VERSION = "eei-external-release-operator-input-status-v1"
DEFAULT_OUTPUT = ROOT / "artifacts/operator_inputs/operator_input_status.json"
VALIDATOR_CONTRACTS: dict[str, dict[str, Any]] = {
    "A202_source_license_passage_owner_legal_release": {
        "validator_id": "VAL-A202-SIGNED-INTAKE-PREFLIGHT",
        "validator_type": "signed_release_decision_intake",
        "expected_artifacts": [
            "artifacts/tests/a202/t1301_a202_signed_intake_preflight.json",
            "artifacts/tests/a202/t1301_a202_operator_intake_gap_packet.json",
        ],
        "success_statuses": ["A202_OPERATOR_INTAKE_READY_FOR_RELEASE_PREFLIGHT"],
    },
    "A210_brand_legal_market_clearance_or_risk_waiver": {
        "validator_id": "VAL-A210-BRAND-CLEARANCE",
        "validator_type": "brand_legal_market_clearance",
        "expected_artifacts": [
            "artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json",
        ],
        "success_statuses": ["READY_FOR_RELEASE_PREFLIGHT"],
    },
    "A026_entity_resolution_production_gold_set": {
        "validator_id": "VAL-A026-PRODUCTION-GOLD-ENTITY",
        "validator_type": "production_gold_quality",
        "expected_artifacts": [
            "artifacts/tests/a026/t904_entity_resolution_gold_evaluation_contract.json",
        ],
        "success_statuses": ["PRODUCTION_ENTITY_GOLD_READY"],
    },
    "A027_relationship_extraction_production_gold_set": {
        "validator_id": "VAL-A027-PRODUCTION-GOLD-RELATIONSHIP",
        "validator_type": "production_gold_quality",
        "expected_artifacts": [
            "artifacts/tests/a027/t904_relationship_gold_evaluation_contract.json",
        ],
        "success_statuses": ["PRODUCTION_RELATIONSHIP_GOLD_READY"],
    },
    "A209_clean_rerun_authorization": {
        "validator_id": "VAL-A209-CLEAN-RERUN-AUTHORIZATION",
        "validator_type": "operator_soak_recovery_authorization",
        "expected_artifacts": [
            "artifacts/tests/a209/t1307_operator_soak_recovery_authorization_packet.json",
        ],
        "success_statuses": ["A209_RECOVERY_AUTHORIZATION_READY"],
    },
    "A209_24h_operator_soak_finalization": {
        "validator_id": "VAL-A209-24H-SOAK-FINALIZATION",
        "validator_type": "operator_soak_finalization",
        "expected_artifacts": [
            "artifacts/tests/a209/t1307_operator_soak_evidence_validation.json",
            "artifacts/tests/a209/t1307_operator_soak_finalization_preflight.json",
            "artifacts/tests/a209/t1307_operator_soak_recovery_authorization_packet.json",
        ],
        "success_statuses": ["A209_FINALIZATION_READY_FOR_RELEASE_MANAGER"],
    },
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_repo_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return ROOT / path


def is_template_path(path_value: str) -> bool:
    normalized = Path(path_value).as_posix()
    return normalized.startswith("artifacts/operator_input_kit/")


def validator_contract_for(item: dict[str, Any]) -> dict[str, Any]:
    input_id = str(item.get("input_id", ""))
    command = str(item.get("validation_command", ""))
    base = VALIDATOR_CONTRACTS.get(input_id)
    if not base:
        raise ValueError(f"operator input status missing validator contract: {input_id}")
    if not command:
        raise ValueError(f"operator input status missing validation command: {input_id}")
    return {
        "validator_id": base["validator_id"],
        "validator_type": base["validator_type"],
        "command": command,
        "expected_artifacts": base["expected_artifacts"],
        "success_statuses": base["success_statuses"],
        "required_before_release_manager": True,
        "counts_as_release_ready_without_success": False,
    }


def validator_status_for(input_status: str) -> str:
    if input_status == "MISSING":
        return "NOT_RUN_INPUT_MISSING"
    if input_status.startswith("REJECTED_"):
        return "BLOCKED_REJECTED_INPUT"
    if input_status == "PRESENT_REQUIRES_VALIDATOR":
        return "PENDING_DEDICATED_VALIDATOR"
    return "UNKNOWN_OPERATOR_INPUT_STATUS"


def status_for_input(item: dict[str, Any]) -> dict[str, Any]:
    input_id = str(item.get("input_id", ""))
    acceptance_id = str(item.get("acceptance_id", ""))
    submission_target = str(item.get("submission_target", ""))
    target = resolve_repo_path(submission_target)
    target_exists = target.exists()
    target_display = display_path(target)
    target_sha256 = sha256_file(target) if target_exists and target.is_file() else ""
    kit_template_sha256 = str(item.get("kit_template_sha256", ""))
    kit_template_path = str(item.get("kit_template_path", ""))
    kit_template_display = display_path(resolve_repo_path(kit_template_path))

    if is_template_path(submission_target):
        status = "REJECTED_TEMPLATE_TARGET"
        reason = "submission target points at the template kit, not signed operator inputs"
    elif not target_exists:
        status = "MISSING"
        reason = "operator input target is missing"
    elif not target.is_file():
        status = "REJECTED_NON_FILE_TARGET"
        reason = "operator input target exists but is not a file"
    elif target_sha256 and target_sha256 == kit_template_sha256:
        status = "REJECTED_TEMPLATE_COPY"
        reason = "operator input target is byte-identical to the kit template"
    else:
        status = "PRESENT_REQUIRES_VALIDATOR"
        reason = "operator input target exists and must pass its dedicated validator"

    return {
        "input_id": input_id,
        "acceptance_id": acceptance_id,
        "status": status,
        "validator_status": validator_status_for(status),
        "reason": reason,
        "submission_target": submission_target,
        "submission_target_resolved": target_display,
        "submission_target_exists": target_exists,
        "submission_target_sha256": target_sha256,
        "kit_template_path": kit_template_display,
        "kit_template_sha256": kit_template_sha256,
        "template_counts_as_clearance": False,
        "release_gate_closure_allowed": False,
        "validation_command": item.get("validation_command"),
        "validator_contract": validator_contract_for(item),
        "completion_criteria": item.get("completion_criteria", []),
    }


def build_status(
    *,
    kit_manifest_path: Path = DEFAULT_OPERATOR_INPUT_KIT_MANIFEST,
    generated_at: str | None = None,
) -> dict[str, Any]:
    manifest = read_json(kit_manifest_path)
    kit_items = manifest.get("kit_items")
    if not isinstance(kit_items, list) or not kit_items:
        raise ValueError("operator input status requires non-empty kit_items")
    items = [
        status_for_input(item)
        for item in kit_items
        if isinstance(item, dict)
    ]
    if len(items) != len(kit_items):
        raise ValueError("operator input status kit_items must all be objects")

    missing_count = sum(1 for item in items if item["status"] == "MISSING")
    rejected_count = sum(1 for item in items if item["status"].startswith("REJECTED_"))
    present_requiring_validator_count = sum(
        1 for item in items if item["status"] == "PRESENT_REQUIRES_VALIDATOR"
    )
    blocked_validator_count = missing_count + rejected_count
    pending_dedicated_validator_count = present_requiring_validator_count

    if rejected_count:
        status = "OPERATOR_INPUTS_REJECTED"
    elif missing_count:
        status = "WAITING_FOR_OPERATOR_INPUTS"
    else:
        status = "OPERATOR_INPUTS_PRESENT_REQUIRING_VALIDATION"

    return {
        "schema_version": STATUS_SCHEMA_VERSION,
        "artifact_id": "t1303-external-release-operator-input-status",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_id": "T1303",
        "task_ids": REQUIRED_TASK_IDS,
        "acceptance_ids": REQUIRED_ACCEPTANCE_IDS,
        "status": status,
        "required_input_count": len(items),
        "missing_count": missing_count,
        "rejected_count": rejected_count,
        "present_requiring_validator_count": present_requiring_validator_count,
        "dedicated_validator_count": len(items),
        "blocked_validator_count": blocked_validator_count,
        "pending_dedicated_validator_count": pending_dedicated_validator_count,
        "dedicated_validators_ready_for_release_manager": False,
        "operator_inputs_ready_for_release_manager": False,
        "release_manager_preflight_refresh_allowed": False,
        "mvp_release_gate_refresh_allowed": False,
        "release_gate_closed_by_input_status": False,
        "source_files": {
            "operator_input_kit_manifest": {
                "path": display_path(kit_manifest_path),
                "sha256": sha256_file(kit_manifest_path),
            }
        },
        "input_statuses": items,
        "validation_policy": {
            "missing_inputs_block_release": True,
            "template_copies_rejected": True,
            "dedicated_validator_contract_required": True,
            "present_inputs_still_require_dedicated_validators": True,
            "dedicated_validators_must_pass_before_release_manager": True,
            "status_manifest_closes_release_gate": False,
        },
        "post_submission_commands": manifest.get("post_submission_commands", []),
        "non_claims": [
            "This status manifest does not certify any operator input.",
            "This status manifest does not convert templates into signed release evidence.",
            "This status manifest does not close A202, A209, A210, A026, "
            "A027, A204, A205 or MVP release.",
            "Release-manager refresh still requires every dedicated validator "
            "to pass on real operator inputs.",
        ],
    }


def validate_status(
    payload: dict[str, Any],
    *,
    kit_manifest_path: Path = DEFAULT_OPERATOR_INPUT_KIT_MANIFEST,
) -> None:
    expected = build_status(
        kit_manifest_path=kit_manifest_path,
        generated_at=payload.get("generated_at"),
    )
    checked_fields = (
        "schema_version",
        "artifact_id",
        "system_name",
        "task_id",
        "task_ids",
        "acceptance_ids",
        "status",
        "required_input_count",
        "missing_count",
        "rejected_count",
        "present_requiring_validator_count",
        "dedicated_validator_count",
        "blocked_validator_count",
        "pending_dedicated_validator_count",
        "dedicated_validators_ready_for_release_manager",
        "operator_inputs_ready_for_release_manager",
        "release_manager_preflight_refresh_allowed",
        "mvp_release_gate_refresh_allowed",
        "release_gate_closed_by_input_status",
        "source_files",
        "input_statuses",
        "validation_policy",
        "post_submission_commands",
        "non_claims",
    )
    for key in checked_fields:
        if payload.get(key) != expected.get(key):
            raise ValueError(f"operator input status drift: {key}")
    if payload.get("release_gate_closed_by_input_status") is not False:
        raise ValueError("operator input status must not close release gates")
    if payload.get("operator_inputs_ready_for_release_manager") is not False:
        raise ValueError("operator input status cannot certify release-manager readiness")
    for item in payload.get("input_statuses", []):
        if not isinstance(item, dict):
            raise ValueError("operator input status item must be an object")
        if item.get("template_counts_as_clearance") is not False:
            raise ValueError("operator input templates must not count as clearance")
        if item.get("release_gate_closure_allowed") is not False:
            raise ValueError("operator input status item must not close release gates")
        contract = item.get("validator_contract")
        if not isinstance(contract, dict):
            raise ValueError("operator input status item must include validator contract")
        if contract.get("required_before_release_manager") is not True:
            raise ValueError("operator input validators must be required before release manager")
        if contract.get("counts_as_release_ready_without_success") is not False:
            raise ValueError("operator input validators cannot count as ready without success")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"))
    parser.add_argument("--kit-manifest", type=Path, default=DEFAULT_OPERATOR_INPUT_KIT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "generate":
        payload = build_status(kit_manifest_path=args.kit_manifest)
        validate_status(payload, kit_manifest_path=args.kit_manifest)
        write_json(args.output, payload)
        if not args.quiet:
            print(json.dumps({"generated": True, "artifact": display_path(args.output)}))
    else:
        validate_status(read_json(args.output), kit_manifest_path=args.kit_manifest)
        if not args.quiet:
            print(json.dumps({"valid": True, "artifact": display_path(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
