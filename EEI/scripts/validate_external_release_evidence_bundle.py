#!/usr/bin/env python3
"""Generate and validate the external release-evidence bundle preflight.

This preflight gives operators one contract for the external evidence still
blocking MVP release: A202 source/legal/owner decisions, A210 brand clearance,
A026/A027 production gold labels, and A209 final soak completion. It does not
close any of those gates by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "eei-external-release-evidence-bundle-preflight-v1"
DEFAULT_RELEASE_DECISION_CONTRACT = (
    ROOT / "artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json"
)
DEFAULT_BRAND_PREFLIGHT = (
    ROOT / "artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json"
)
DEFAULT_ENTITY_GOLD_EVALUATION = (
    ROOT / "artifacts/tests/a026/t904_entity_resolution_gold_evaluation_contract.json"
)
DEFAULT_RELATIONSHIP_GOLD_EVALUATION = (
    ROOT / "artifacts/tests/a027/t904_relationship_gold_evaluation_contract.json"
)
DEFAULT_OPERATOR_SOAK_FINALIZATION = (
    ROOT / "artifacts/tests/a209/t1307_operator_soak_finalization_preflight.json"
)
DEFAULT_OUTPUT = ROOT / "artifacts/tests/a205/t1303_external_release_evidence_bundle_preflight.json"

REQUIRED_TASK_IDS = ["T1301", "T1303", "T1307", "T1309", "T904"]
REQUIRED_ACCEPTANCE_IDS = ["A202", "A204", "A205", "A209", "A210", "A026", "A027"]
REQUIRED_EXTERNAL_INPUTS = [
    "A202_source_license_passage_owner_legal_release",
    "A210_brand_legal_market_clearance_or_risk_waiver",
    "A026_entity_resolution_production_gold_set",
    "A027_relationship_extraction_production_gold_set",
    "A209_24h_operator_soak_finalization",
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{display_path(path)} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def display_path(path: Path) -> str:
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


def release_decision_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "release_gate_closed_by_contract": payload.get("release_gate_closed_by_contract"),
        "relationship_publication_allowed": payload.get("relationship_publication_allowed"),
        "public_brand_launch_allowed": payload.get("public_brand_launch_allowed"),
    }


def brand_summary(payload: dict[str, Any]) -> dict[str, Any]:
    release_gate = (
        payload.get("release_gate") if isinstance(payload.get("release_gate"), dict) else {}
    )
    current = (
        payload.get("current_clearance_status")
        if isinstance(payload.get("current_clearance_status"), dict)
        else {}
    )
    return {
        "release_gate_status": release_gate.get("status"),
        "public_release_allowed": release_gate.get("public_release_allowed"),
        "a210_status": current.get("a210_status"),
        "formal_legal_clearance": current.get("formal_legal_clearance"),
        "market_clearance": current.get("market_clearance"),
        "signed_risk_waiver": current.get("signed_risk_waiver"),
        "owner_signoff": current.get("owner_signoff"),
    }


def gold_summary(payload: dict[str, Any], acceptance_id: str) -> dict[str, Any]:
    focus = (
        payload.get("focus_quality_result")
        if isinstance(payload.get("focus_quality_result"), dict)
        else {}
    )
    metrics = focus.get("metrics") if isinstance(focus.get("metrics"), dict) else {}
    fixture_policy = (
        payload.get("fixture_policy") if isinstance(payload.get("fixture_policy"), dict) else {}
    )
    return {
        "focus_acceptance_id": payload.get("focus_acceptance_id"),
        "expected_acceptance_id": acceptance_id,
        "status": focus.get("status"),
        "threshold_result": focus.get("threshold_result"),
        "release_gate_closure_allowed": focus.get("release_gate_closure_allowed"),
        "sample_count": metrics.get("sample_count"),
        "precision": metrics.get("precision"),
        "source_coverage_min": metrics.get("source_coverage_min"),
        "production_gold_set": fixture_policy.get("production_gold_set"),
    }


def soak_finalization_summary(payload: dict[str, Any]) -> dict[str, Any]:
    heartbeat = (
        (payload.get("source_statuses") or {}).get("heartbeat")
        if isinstance(payload.get("source_statuses"), dict)
        else {}
    )
    if not isinstance(heartbeat, dict):
        heartbeat = {}
    return {
        "status": payload.get("status"),
        "a209_evidence_ready_for_release_manager": payload.get(
            "a209_evidence_ready_for_release_manager"
        ),
        "downstream_release_gate_refresh_allowed": payload.get(
            "downstream_release_gate_refresh_allowed"
        ),
        "release_gate_closed_by_finalizer": payload.get("release_gate_closed_by_finalizer"),
        "windows_completed": heartbeat.get("windows_completed"),
        "target_windows": heartbeat.get("target_windows"),
        "windows_failed": heartbeat.get("windows_failed"),
        "progress_status": heartbeat.get("progress_status"),
    }


def missing_inputs(
    *,
    release_decision: dict[str, Any],
    brand: dict[str, Any],
    entity_gold: dict[str, Any],
    relationship_gold: dict[str, Any],
    soak_finalization: dict[str, Any],
) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    if release_decision.get("relationship_publication_allowed") is not True:
        missing.append(
            {
                "input_id": "A202_source_license_passage_owner_legal_release",
                "acceptance_id": "A202",
                "reason": "relationship publication clearance is not supplied",
            }
        )
    if brand.get("public_release_allowed") is not True or brand.get("a210_status") != "DONE":
        missing.append(
            {
                "input_id": "A210_brand_legal_market_clearance_or_risk_waiver",
                "acceptance_id": "A210",
                "reason": "brand public release clearance or risk waiver is not complete",
            }
        )
    if entity_gold.get("release_gate_closure_allowed") is not True:
        missing.append(
            {
                "input_id": "A026_entity_resolution_production_gold_set",
                "acceptance_id": "A026",
                "reason": "entity-resolution production gold threshold is not met",
            }
        )
    if relationship_gold.get("release_gate_closure_allowed") is not True:
        missing.append(
            {
                "input_id": "A027_relationship_extraction_production_gold_set",
                "acceptance_id": "A027",
                "reason": "relationship-extraction production gold threshold is not met",
            }
        )
    if soak_finalization.get("downstream_release_gate_refresh_allowed") is not True:
        progress = ""
        if soak_finalization.get("windows_completed") is not None:
            progress = (
                f" at {soak_finalization.get('windows_completed')}/"
                f"{soak_finalization.get('target_windows')} windows"
            )
        missing.append(
            {
                "input_id": "A209_24h_operator_soak_finalization",
                "acceptance_id": "A209",
                "reason": f"A209 finalization does not allow downstream refresh{progress}",
            }
        )
    return missing


def build_preflight(
    *,
    release_decision_contract_path: Path = DEFAULT_RELEASE_DECISION_CONTRACT,
    brand_preflight_path: Path = DEFAULT_BRAND_PREFLIGHT,
    entity_gold_evaluation_path: Path = DEFAULT_ENTITY_GOLD_EVALUATION,
    relationship_gold_evaluation_path: Path = DEFAULT_RELATIONSHIP_GOLD_EVALUATION,
    operator_soak_finalization_path: Path = DEFAULT_OPERATOR_SOAK_FINALIZATION,
    generated_at: str | None = None,
) -> dict[str, Any]:
    release_decision = release_decision_summary(read_json(release_decision_contract_path))
    brand = brand_summary(read_json(brand_preflight_path))
    entity_gold = gold_summary(read_json(entity_gold_evaluation_path), "A026")
    relationship_gold = gold_summary(read_json(relationship_gold_evaluation_path), "A027")
    soak_finalization = soak_finalization_summary(read_json(operator_soak_finalization_path))
    missing = missing_inputs(
        release_decision=release_decision,
        brand=brand,
        entity_gold=entity_gold,
        relationship_gold=relationship_gold,
        soak_finalization=soak_finalization,
    )
    ready = not missing
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t1303-external-release-evidence-bundle-preflight",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_ids": REQUIRED_TASK_IDS,
        "acceptance_ids": REQUIRED_ACCEPTANCE_IDS,
        "status": "EXTERNAL_RELEASE_EVIDENCE_BUNDLE_READY"
        if ready
        else "EXTERNAL_RELEASE_EVIDENCE_BUNDLE_BLOCKED",
        "external_release_evidence_ready": ready,
        "release_manager_preflight_refresh_allowed": ready,
        "mvp_release_gate_refresh_allowed": ready,
        "release_gate_closed_by_bundle_preflight": False,
        "required_external_inputs": REQUIRED_EXTERNAL_INPUTS,
        "source_files": {
            "release_decision_contract": display_path(release_decision_contract_path),
            "release_decision_contract_sha256": sha256_file(release_decision_contract_path),
            "brand_preflight": display_path(brand_preflight_path),
            "brand_preflight_sha256": sha256_file(brand_preflight_path),
            "entity_gold_evaluation": display_path(entity_gold_evaluation_path),
            "entity_gold_evaluation_sha256": sha256_file(entity_gold_evaluation_path),
            "relationship_gold_evaluation": display_path(relationship_gold_evaluation_path),
            "relationship_gold_evaluation_sha256": sha256_file(relationship_gold_evaluation_path),
            "operator_soak_finalization": display_path(operator_soak_finalization_path),
            "operator_soak_finalization_sha256": sha256_file(operator_soak_finalization_path),
        },
        "gate_statuses": {
            "release_decision": release_decision,
            "brand": brand,
            "entity_gold": entity_gold,
            "relationship_gold": relationship_gold,
            "operator_soak_finalization": soak_finalization,
        },
        "missing_external_inputs": missing,
        "operator_next_actions": operator_next_actions(ready),
        "validation_policy": {
            "repository_templates_count_as_clearance": False,
            "repository_fixtures_count_as_clearance": False,
            "a209_partial_heartbeat_counts_as_clearance": False,
            "all_external_inputs_required_before_release_manager_refresh": True,
        },
        "non_claims": [
            "This bundle preflight does not certify legal, source-license, brand "
            "or market clearance.",
            "This bundle preflight does not convert templates or fixtures into clearance.",
            "This bundle preflight does not close A202, A209, A210, A026 or A027.",
            "This bundle preflight does not activate release-manager or MVP release gates.",
        ],
        "rollback": [
            "Regenerate this preflight from the source gate artifacts.",
            "Do not delete operator-supplied signed evidence bundles during rollback.",
            "Do not delete live A209 checkpoint or log files during rollback.",
        ],
    }


def operator_next_actions(ready: bool) -> list[str]:
    if ready:
        return [
            "Regenerate release-manager activation and MVP release-gate preflights.",
            "Run make verify and root governance before release-manager activation.",
        ]
    return [
        "Attach real signed A202 source/license/passage/owner/legal evidence.",
        "Attach real signed A210 brand clearance or risk waiver evidence.",
        "Attach production A026/A027 gold-label evidence that meets thresholds.",
        "Wait for A209 finalization to allow downstream release-gate refresh.",
    ]


def validate_preflight(
    payload: dict[str, Any],
    *,
    release_decision_contract_path: Path = DEFAULT_RELEASE_DECISION_CONTRACT,
    brand_preflight_path: Path = DEFAULT_BRAND_PREFLIGHT,
    entity_gold_evaluation_path: Path = DEFAULT_ENTITY_GOLD_EVALUATION,
    relationship_gold_evaluation_path: Path = DEFAULT_RELATIONSHIP_GOLD_EVALUATION,
    operator_soak_finalization_path: Path = DEFAULT_OPERATOR_SOAK_FINALIZATION,
) -> None:
    expected = build_preflight(
        release_decision_contract_path=release_decision_contract_path,
        brand_preflight_path=brand_preflight_path,
        entity_gold_evaluation_path=entity_gold_evaluation_path,
        relationship_gold_evaluation_path=relationship_gold_evaluation_path,
        operator_soak_finalization_path=operator_soak_finalization_path,
        generated_at=payload.get("generated_at"),
    )
    checked_fields = (
        "schema_version",
        "artifact_id",
        "system_name",
        "task_ids",
        "acceptance_ids",
        "status",
        "external_release_evidence_ready",
        "release_manager_preflight_refresh_allowed",
        "mvp_release_gate_refresh_allowed",
        "release_gate_closed_by_bundle_preflight",
        "required_external_inputs",
        "source_files",
        "gate_statuses",
        "missing_external_inputs",
        "operator_next_actions",
        "validation_policy",
        "non_claims",
    )
    for key in checked_fields:
        if payload.get(key) != expected.get(key):
            raise ValueError(f"external release evidence bundle drift: {key}")
    ready = payload.get("external_release_evidence_ready") is True
    if ready and payload.get("missing_external_inputs"):
        raise ValueError("ready bundle cannot list missing external inputs")
    if ready and payload.get("release_manager_preflight_refresh_allowed") is not True:
        raise ValueError("ready bundle must allow release-manager preflight refresh")
    if not ready and payload.get("release_manager_preflight_refresh_allowed") is not False:
        raise ValueError("blocked bundle must not allow release-manager preflight refresh")
    if payload.get("release_gate_closed_by_bundle_preflight") is not False:
        raise ValueError("bundle preflight must not close release gates directly")


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--release-decision-contract",
        type=Path,
        default=DEFAULT_RELEASE_DECISION_CONTRACT,
    )
    parser.add_argument("--brand-preflight", type=Path, default=DEFAULT_BRAND_PREFLIGHT)
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
    parser.add_argument(
        "--operator-soak-finalization",
        type=Path,
        default=DEFAULT_OPERATOR_SOAK_FINALIZATION,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"))
    add_common_args(parser)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "generate":
        payload = build_preflight(
            release_decision_contract_path=args.release_decision_contract,
            brand_preflight_path=args.brand_preflight,
            entity_gold_evaluation_path=args.entity_gold_evaluation,
            relationship_gold_evaluation_path=args.relationship_gold_evaluation,
            operator_soak_finalization_path=args.operator_soak_finalization,
        )
        validate_preflight(
            payload,
            release_decision_contract_path=args.release_decision_contract,
            brand_preflight_path=args.brand_preflight,
            entity_gold_evaluation_path=args.entity_gold_evaluation,
            relationship_gold_evaluation_path=args.relationship_gold_evaluation,
            operator_soak_finalization_path=args.operator_soak_finalization,
        )
        write_json(args.output, payload)
        if not args.quiet:
            print(json.dumps({"generated": True, "artifact": display_path(args.output)}))
    else:
        validate_preflight(
            read_json(args.output),
            release_decision_contract_path=args.release_decision_contract,
            brand_preflight_path=args.brand_preflight,
            entity_gold_evaluation_path=args.entity_gold_evaluation,
            relationship_gold_evaluation_path=args.relationship_gold_evaluation,
            operator_soak_finalization_path=args.operator_soak_finalization,
        )
        if not args.quiet:
            print(json.dumps({"valid": True, "artifact": display_path(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
