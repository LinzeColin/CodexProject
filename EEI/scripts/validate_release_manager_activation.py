#!/usr/bin/env python3
"""Generate and validate the EEI release-manager activation preflight.

The preflight is intentionally fail-closed. It aggregates the current release
decision, gold-quality, brand-clearance, and long-duration soak evidence and
keeps final release-manager activation blocked until the external gates are
real, current, and release-ready.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "eei-release-manager-activation-preflight-v1"
DEFAULT_RELEASE_DECISION_CONTRACT = (
    ROOT / "artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json"
)
DEFAULT_SIGNED_DECISION_BUNDLE = (
    ROOT
    / "tests/fixtures/release_decision_bundle/"
    "a202_a210_signed_decision_bundle_contract_test.json"
)
DEFAULT_OPERATOR_SOAK_EVIDENCE = (
    ROOT / "artifacts/tests/a209/t1307_operator_soak_evidence_validation.json"
)
DEFAULT_OPERATOR_SOAK_HEARTBEAT = (
    ROOT / "artifacts/tests/a209/t1307_operator_soak_background_progress.json"
)
DEFAULT_ENTITY_GOLD_EVALUATION = (
    ROOT / "artifacts/tests/a026/t904_entity_resolution_gold_evaluation_contract.json"
)
DEFAULT_RELATIONSHIP_GOLD_EVALUATION = (
    ROOT / "artifacts/tests/a027/t904_relationship_gold_evaluation_contract.json"
)
DEFAULT_BRAND_PREFLIGHT = (
    ROOT / "artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json"
)
DEFAULT_OUTPUT = ROOT / "artifacts/tests/a205/t1303_release_manager_activation_preflight.json"

REQUIRED_TASK_IDS = ["T1301", "T1303", "T1307", "T1309", "T904"]
REQUIRED_ACCEPTANCE_IDS = ["A202", "A204", "A205", "A209", "A210", "A026", "A027"]
REQUIRED_EXTERNAL_GATES = [
    "A202_source_license_reviews",
    "A202_passage_level_relationship_reviews",
    "A202_production_owner_signoffs",
    "A202_legal_release_clearance",
    "A210_brand_clearance_or_risk_waiver",
    "A026_entity_resolution_production_gold_set",
    "A027_relationship_extraction_production_gold_set",
    "A209_24h_operator_soak",
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def release_decision_status(
    contract: dict[str, Any],
    signed_bundle: dict[str, Any],
) -> dict[str, Any]:
    signed_summary = contract.get("signed_contract_test_summary") or {}
    validation_policy = contract.get("validation_policy") or {}
    signed_complete = (
        signed_bundle.get("bundle_status") == "SIGNED_DECISION_BUNDLE"
        and signed_bundle.get("release_gate_closure_allowed") is True
        and signed_summary.get("source_license_reviews", 0) > 0
        and signed_summary.get("passage_reviews", 0) > 0
        and signed_summary.get("owner_signoffs", 0) > 0
    )
    counts_as_clearance = validation_policy.get("signed_contract_test_counts_as_clearance") is True
    return {
        "signed_decision_complete": signed_complete,
        "signed_contract_test_counts_as_clearance": counts_as_clearance,
        "contract_status": contract.get("status"),
        "release_gate_closed_by_contract": contract.get("release_gate_closed_by_contract"),
        "relationship_publication_allowed": contract.get("relationship_publication_allowed"),
        "public_brand_launch_allowed": contract.get("public_brand_launch_allowed"),
    }


def soak_status(payload: dict[str, Any]) -> dict[str, Any]:
    results = {
        str(row.get("label")): str(row.get("status"))
        for row in payload.get("results", [])
        if isinstance(row, dict)
    }
    return {
        "status": payload.get("status"),
        "release_gate_closed_by_validator": payload.get("release_gate_closed_by_validator"),
        "operator_4h": results.get("operator_4h", "MISSING"),
        "operator_24h": results.get("operator_24h", "MISSING"),
    }


def soak_heartbeat_status(payload: dict[str, Any]) -> dict[str, Any]:
    progress = payload.get("progress") if isinstance(payload.get("progress"), dict) else {}
    latest = (
        progress.get("latest_successful_window")
        if isinstance(progress.get("latest_successful_window"), dict)
        else {}
    )
    contract = (
        payload.get("background_resolution_contract")
        if isinstance(payload.get("background_resolution_contract"), dict)
        else {}
    )
    return {
        "status": payload.get("status"),
        "progress_status": payload.get("progress_status"),
        "release_gate_closed_by_background_heartbeat": payload.get(
            "release_gate_closed_by_background_heartbeat"
        ),
        "counts_as_release_ready": False,
        "target_windows": progress.get("target_windows"),
        "windows_completed": progress.get("windows_completed"),
        "windows_failed": progress.get("windows_failed"),
        "windows_remaining": progress.get("windows_remaining"),
        "completion_percent": progress.get("completion_percent"),
        "latest_successful_window_index": latest.get("index"),
        "operator_process_status": contract.get("operator_process_status"),
        "watchdog_process_status": contract.get("watchdog_process_status"),
    }


def gold_status(payload: dict[str, Any], focus_id: str) -> dict[str, Any]:
    focus = payload.get("focus_quality_result") or {}
    metrics = focus.get("metrics") or {}
    return {
        "focus_acceptance_id": payload.get("focus_acceptance_id"),
        "expected_acceptance_id": focus_id,
        "status": focus.get("status"),
        "threshold_result": focus.get("threshold_result"),
        "release_gate_closure_allowed": focus.get("release_gate_closure_allowed"),
        "sample_count": metrics.get("sample_count"),
        "precision": metrics.get("precision"),
        "source_coverage_min": metrics.get("source_coverage_min"),
        "production_gold_set": (payload.get("fixture_policy") or {}).get("production_gold_set"),
    }


def brand_status(payload: dict[str, Any]) -> dict[str, Any]:
    release_gate = payload.get("release_gate") or {}
    current = payload.get("current_clearance_status") or {}
    return {
        "release_gate_status": release_gate.get("status"),
        "public_release_allowed": release_gate.get("public_release_allowed"),
        "formal_legal_clearance": current.get("formal_legal_clearance"),
        "market_clearance": current.get("market_clearance"),
        "signed_risk_waiver": current.get("signed_risk_waiver"),
        "owner_signoff": current.get("owner_signoff"),
        "a210_status": current.get("a210_status"),
    }


def missing_gates(
    *,
    release_decision: dict[str, Any],
    soak: dict[str, Any],
    soak_heartbeat: dict[str, Any],
    entity_gold: dict[str, Any],
    relationship_gold: dict[str, Any],
    brand: dict[str, Any],
) -> list[dict[str, str]]:
    gates: list[dict[str, str]] = []

    if not release_decision["signed_decision_complete"]:
        gates.append(
            {
                "gate_id": "A202_signed_decision_bundle",
                "reason": "signed source/license/passage/owner/legal inputs are incomplete",
            }
        )
    if not release_decision["signed_contract_test_counts_as_clearance"]:
        gates.extend(
            [
                {
                    "gate_id": "A202_source_license_reviews",
                    "reason": "repository signed fixture is not real source-license clearance",
                },
                {
                    "gate_id": "A202_passage_level_relationship_reviews",
                    "reason": "repository signed fixture is not real passage-level review",
                },
                {
                    "gate_id": "A202_production_owner_signoffs",
                    "reason": "repository signed fixture is not real production owner approval",
                },
                {
                    "gate_id": "A202_legal_release_clearance",
                    "reason": "repository signed fixture is not legal clearance or risk waiver",
                },
            ]
        )
    if brand["public_release_allowed"] is not True or brand["a210_status"] != "DONE":
        gates.append(
            {
                "gate_id": "A210_brand_clearance_or_risk_waiver",
                "reason": "formal brand/legal/market clearance or owner waiver is not complete",
            }
        )
    if entity_gold["release_gate_closure_allowed"] is not True:
        gates.append(
            {
                "gate_id": "A026_entity_resolution_production_gold_set",
                "reason": "entity-resolution production gold threshold is not met",
            }
        )
    if relationship_gold["release_gate_closure_allowed"] is not True:
        gates.append(
            {
                "gate_id": "A027_relationship_extraction_production_gold_set",
                "reason": "relationship extraction production gold threshold is not met",
            }
        )
    if soak["release_gate_closed_by_validator"] is not True or soak["operator_24h"] != "PASS":
        heartbeat_reason = ""
        if soak_heartbeat.get("windows_completed") is not None:
            heartbeat_reason = (
                "; background heartbeat reports "
                f"{soak_heartbeat.get('windows_completed')}/"
                f"{soak_heartbeat.get('target_windows')} windows, "
                f"{soak_heartbeat.get('windows_failed')} failed, "
                f"{soak_heartbeat.get('progress_status')}"
            )
        gates.append(
            {
                "gate_id": "A209_24h_operator_soak",
                "reason": (
                    "24h operator soak evidence is missing or not release-ready"
                    f"{heartbeat_reason}"
                ),
            }
        )
    return gates


def build_preflight(
    *,
    release_decision_contract_path: Path = DEFAULT_RELEASE_DECISION_CONTRACT,
    signed_decision_bundle_path: Path = DEFAULT_SIGNED_DECISION_BUNDLE,
    operator_soak_evidence_path: Path = DEFAULT_OPERATOR_SOAK_EVIDENCE,
    operator_soak_heartbeat_path: Path = DEFAULT_OPERATOR_SOAK_HEARTBEAT,
    entity_gold_evaluation_path: Path = DEFAULT_ENTITY_GOLD_EVALUATION,
    relationship_gold_evaluation_path: Path = DEFAULT_RELATIONSHIP_GOLD_EVALUATION,
    brand_preflight_path: Path = DEFAULT_BRAND_PREFLIGHT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    release_decision = release_decision_status(
        read_json(release_decision_contract_path),
        read_json(signed_decision_bundle_path),
    )
    soak = soak_status(read_json(operator_soak_evidence_path))
    soak_heartbeat = soak_heartbeat_status(read_json(operator_soak_heartbeat_path))
    entity_gold = gold_status(read_json(entity_gold_evaluation_path), "A026")
    relationship_gold = gold_status(read_json(relationship_gold_evaluation_path), "A027")
    brand = brand_status(read_json(brand_preflight_path))
    blockers = missing_gates(
        release_decision=release_decision,
        soak=soak,
        soak_heartbeat=soak_heartbeat,
        entity_gold=entity_gold,
        relationship_gold=relationship_gold,
        brand=brand,
    )
    activation_ready = not blockers
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t1303-release-manager-activation-preflight",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_ids": REQUIRED_TASK_IDS,
        "acceptance_ids": REQUIRED_ACCEPTANCE_IDS,
        "status": "RELEASE_MANAGER_ACTIVATION_BLOCKED"
        if not activation_ready
        else "RELEASE_MANAGER_ACTIVATION_READY",
        "activation_ready": activation_ready,
        "release_manager_activation_allowed": activation_ready,
        "relationship_publication_allowed": activation_ready,
        "public_brand_launch_allowed": activation_ready,
        "source_files": {
            "release_decision_contract": relative(release_decision_contract_path),
            "release_decision_contract_sha256": sha256_file(release_decision_contract_path),
            "signed_decision_bundle": relative(signed_decision_bundle_path),
            "signed_decision_bundle_sha256": sha256_file(signed_decision_bundle_path),
            "operator_soak_evidence": relative(operator_soak_evidence_path),
            "operator_soak_evidence_sha256": sha256_file(operator_soak_evidence_path),
            "operator_soak_heartbeat": relative(operator_soak_heartbeat_path),
            "operator_soak_heartbeat_sha256": sha256_file(operator_soak_heartbeat_path),
            "entity_gold_evaluation": relative(entity_gold_evaluation_path),
            "entity_gold_evaluation_sha256": sha256_file(entity_gold_evaluation_path),
            "relationship_gold_evaluation": relative(relationship_gold_evaluation_path),
            "relationship_gold_evaluation_sha256": sha256_file(relationship_gold_evaluation_path),
            "brand_preflight": relative(brand_preflight_path),
            "brand_preflight_sha256": sha256_file(brand_preflight_path),
        },
        "required_external_gates": REQUIRED_EXTERNAL_GATES,
        "gate_statuses": {
            "release_decision": release_decision,
            "operator_soak": soak,
            "operator_soak_background_heartbeat": soak_heartbeat,
            "entity_gold": entity_gold,
            "relationship_gold": relationship_gold,
            "brand": brand,
        },
        "missing_gates": blockers,
        "validation_policy": {
            "repository_fixtures_count_as_clearance": False,
            "release_manager_must_fail_closed_until_all_gates_ready": True,
            "a209_24h_must_be_release_ready": True,
            "a209_background_heartbeat_counts_as_release_ready": False,
            "production_gold_set_required": True,
        },
        "non_claims": [
            "This preflight does not certify legal, source-license, brand or market clearance.",
            "This preflight does not convert repository fixtures into production approval.",
            "This preflight does not replace A209 24h operator soak evidence.",
            "This preflight treats A209 background heartbeat as progress context only.",
            "This preflight does not activate a release manager while missing_gates is non-empty.",
        ],
    }


def validate_preflight(
    payload: dict[str, Any],
    *,
    release_decision_contract_path: Path = DEFAULT_RELEASE_DECISION_CONTRACT,
    signed_decision_bundle_path: Path = DEFAULT_SIGNED_DECISION_BUNDLE,
    operator_soak_evidence_path: Path = DEFAULT_OPERATOR_SOAK_EVIDENCE,
    operator_soak_heartbeat_path: Path = DEFAULT_OPERATOR_SOAK_HEARTBEAT,
    entity_gold_evaluation_path: Path = DEFAULT_ENTITY_GOLD_EVALUATION,
    relationship_gold_evaluation_path: Path = DEFAULT_RELATIONSHIP_GOLD_EVALUATION,
    brand_preflight_path: Path = DEFAULT_BRAND_PREFLIGHT,
) -> None:
    expected = build_preflight(
        release_decision_contract_path=release_decision_contract_path,
        signed_decision_bundle_path=signed_decision_bundle_path,
        operator_soak_evidence_path=operator_soak_evidence_path,
        operator_soak_heartbeat_path=operator_soak_heartbeat_path,
        entity_gold_evaluation_path=entity_gold_evaluation_path,
        relationship_gold_evaluation_path=relationship_gold_evaluation_path,
        brand_preflight_path=brand_preflight_path,
        generated_at=payload.get("generated_at"),
    )
    for key in (
        "schema_version",
        "artifact_id",
        "system_name",
        "task_ids",
        "acceptance_ids",
        "status",
        "activation_ready",
        "release_manager_activation_allowed",
        "relationship_publication_allowed",
        "public_brand_launch_allowed",
        "source_files",
        "required_external_gates",
        "gate_statuses",
        "missing_gates",
        "validation_policy",
    ):
        if payload.get(key) != expected.get(key):
            raise ValueError(f"release-manager preflight field drift: {key}")
    activation_ready = payload.get("activation_ready") is True
    missing_gates = payload.get("missing_gates") or []
    if activation_ready:
        if payload.get("status") != "RELEASE_MANAGER_ACTIVATION_READY":
            raise ValueError("ready preflight must report RELEASE_MANAGER_ACTIVATION_READY")
        if missing_gates:
            raise ValueError("ready preflight cannot list missing gates")
        if payload.get("release_manager_activation_allowed") is not True:
            raise ValueError("ready preflight must allow release-manager activation")
        if payload.get("relationship_publication_allowed") is not True:
            raise ValueError("ready preflight must allow relationship publication")
        if payload.get("public_brand_launch_allowed") is not True:
            raise ValueError("ready preflight must allow public brand launch")
    else:
        if payload.get("status") != "RELEASE_MANAGER_ACTIVATION_BLOCKED":
            raise ValueError("blocked preflight must report RELEASE_MANAGER_ACTIVATION_BLOCKED")
        if not missing_gates:
            raise ValueError("blocked preflight must list missing gates")
        if payload.get("release_manager_activation_allowed") is not False:
            raise ValueError("blocked preflight must not allow release-manager activation")


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--release-decision-contract",
        type=Path,
        default=DEFAULT_RELEASE_DECISION_CONTRACT,
    )
    parser.add_argument(
        "--signed-decision-bundle",
        type=Path,
        default=DEFAULT_SIGNED_DECISION_BUNDLE,
    )
    parser.add_argument(
        "--operator-soak-evidence",
        type=Path,
        default=DEFAULT_OPERATOR_SOAK_EVIDENCE,
    )
    parser.add_argument(
        "--operator-soak-heartbeat",
        type=Path,
        default=DEFAULT_OPERATOR_SOAK_HEARTBEAT,
    )
    parser.add_argument(
        "--entity-gold-evaluation",
        type=Path,
        default=DEFAULT_ENTITY_GOLD_EVALUATION,
    )
    parser.add_argument(
        "--relationship-gold-evaluation",
        type=Path,
        default=DEFAULT_RELATIONSHIP_GOLD_EVALUATION,
    )
    parser.add_argument("--brand-preflight", type=Path, default=DEFAULT_BRAND_PREFLIGHT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)


def generate(args: argparse.Namespace) -> None:
    payload = build_preflight(
        release_decision_contract_path=args.release_decision_contract,
        signed_decision_bundle_path=args.signed_decision_bundle,
        operator_soak_evidence_path=args.operator_soak_evidence,
        operator_soak_heartbeat_path=args.operator_soak_heartbeat,
        entity_gold_evaluation_path=args.entity_gold_evaluation,
        relationship_gold_evaluation_path=args.relationship_gold_evaluation,
        brand_preflight_path=args.brand_preflight,
    )
    validate_preflight(
        payload,
        release_decision_contract_path=args.release_decision_contract,
        signed_decision_bundle_path=args.signed_decision_bundle,
        operator_soak_evidence_path=args.operator_soak_evidence,
        operator_soak_heartbeat_path=args.operator_soak_heartbeat,
        entity_gold_evaluation_path=args.entity_gold_evaluation,
        relationship_gold_evaluation_path=args.relationship_gold_evaluation,
        brand_preflight_path=args.brand_preflight,
    )
    write_json(args.output, payload)
    print(json.dumps({"generated": True, "artifact": relative(args.output)}, indent=2))


def validate(args: argparse.Namespace) -> None:
    validate_preflight(
        read_json(args.output),
        release_decision_contract_path=args.release_decision_contract,
        signed_decision_bundle_path=args.signed_decision_bundle,
        operator_soak_evidence_path=args.operator_soak_evidence,
        operator_soak_heartbeat_path=args.operator_soak_heartbeat,
        entity_gold_evaluation_path=args.entity_gold_evaluation,
        relationship_gold_evaluation_path=args.relationship_gold_evaluation,
        brand_preflight_path=args.brand_preflight,
    )
    print(json.dumps({"valid": True, "artifact": relative(args.output)}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("generate", "validate"):
        child = sub.add_parser(command)
        add_common_args(child)
    args = parser.parse_args()
    if args.command == "generate":
        generate(args)
    else:
        validate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
