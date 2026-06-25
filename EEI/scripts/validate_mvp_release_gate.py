#!/usr/bin/env python3
"""Generate and validate the EEI MVP release-gate preflight.

This artifact is the final fail-closed release checklist for v0.1. It aggregates
the existing A202, A203, A204/A205, A209, A210 and A026/A027 gate contracts
without converting templates, fixtures or background progress into clearance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "eei-t1303-mvp-release-gate-preflight-v1"
DEFAULT_RELEASE_DECISION_CONTRACT = (
    ROOT / "artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json"
)
DEFAULT_PRODUCTION_API_PREFLIGHT = (
    ROOT / "artifacts/tests/a203/t1302_production_api_release_preflight.json"
)
DEFAULT_RELEASE_MANAGER_PREFLIGHT = (
    ROOT / "artifacts/tests/a205/t1303_release_manager_activation_preflight.json"
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
DEFAULT_OUTPUT = ROOT / "artifacts/tests/a205/t1303_mvp_release_gate_preflight.json"

REQUIRED_TASK_IDS = ["T1301", "T1302", "T1303", "T1307", "T1309", "T904"]
REQUIRED_ACCEPTANCE_IDS = ["A202", "A203", "A204", "A205", "A209", "A210", "A026", "A027"]
REQUIRED_GATE_IDS = [
    "A202_relationship_publication_clearance",
    "A203_production_api_release_preflight",
    "A204_A205_release_manager_activation",
    "A209_24h_operator_soak",
    "A210_brand_clearance_or_risk_waiver",
    "A026_entity_resolution_production_gold_set",
    "A027_relationship_extraction_production_gold_set",
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


def release_decision_status(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "release_gate_closed_by_contract": payload.get("release_gate_closed_by_contract"),
        "relationship_publication_allowed": payload.get("relationship_publication_allowed"),
        "public_brand_launch_allowed": payload.get("public_brand_launch_allowed"),
    }


def production_api_status(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "api_surface_ready": payload.get("api_surface_ready"),
        "release_ready": payload.get("release_ready"),
        "production_graph_publication_allowed": payload.get(
            "production_graph_publication_allowed"
        ),
        "score_publication_allowed": payload.get("score_publication_allowed"),
        "missing_gate_ids": [
            row.get("gate_id")
            for row in payload.get("missing_gates", [])
            if isinstance(row, dict)
        ],
    }


def release_manager_status(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "activation_ready": payload.get("activation_ready"),
        "release_manager_activation_allowed": payload.get(
            "release_manager_activation_allowed"
        ),
        "relationship_publication_allowed": payload.get("relationship_publication_allowed"),
        "public_brand_launch_allowed": payload.get("public_brand_launch_allowed"),
        "missing_gate_ids": [
            row.get("gate_id")
            for row in payload.get("missing_gates", [])
            if isinstance(row, dict)
        ],
    }


def soak_status(payload: dict[str, Any]) -> dict[str, Any]:
    results = {
        str(row.get("label")): row
        for row in payload.get("results", [])
        if isinstance(row, dict)
    }
    operator_24h = results.get("operator_24h", {})
    return {
        "status": payload.get("status"),
        "release_gate_closed_by_validator": payload.get("release_gate_closed_by_validator"),
        "operator_4h": results.get("operator_4h", {}).get("status", "MISSING"),
        "operator_24h": operator_24h.get("status", "MISSING"),
        "operator_24h_windows_completed": operator_24h.get("windows_completed"),
    }


def soak_heartbeat_status(payload: dict[str, Any]) -> dict[str, Any]:
    progress = payload.get("progress") if isinstance(payload.get("progress"), dict) else {}
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
        "production_gold_set": (payload.get("fixture_policy") or {}).get(
            "production_gold_set"
        ),
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
    production_api: dict[str, Any],
    release_manager: dict[str, Any],
    soak: dict[str, Any],
    brand: dict[str, Any],
    entity_gold: dict[str, Any],
    relationship_gold: dict[str, Any],
) -> list[dict[str, str]]:
    gates: list[dict[str, str]] = []
    if release_decision["relationship_publication_allowed"] is not True:
        gates.append(
            {
                "gate_id": "A202_relationship_publication_clearance",
                "reason": "source-license, passage, owner and legal clearance is incomplete",
            }
        )
    if (
        production_api["release_ready"] is not True
        or production_api["production_graph_publication_allowed"] is not True
        or production_api["score_publication_allowed"] is not True
    ):
        gates.append(
            {
                "gate_id": "A203_production_api_release_preflight",
                "reason": "production API preflight is not release-ready",
            }
        )
    if release_manager["release_manager_activation_allowed"] is not True:
        gates.append(
            {
                "gate_id": "A204_A205_release_manager_activation",
                "reason": "release-manager activation remains blocked",
            }
        )
    if soak["release_gate_closed_by_validator"] is not True or soak["operator_24h"] != "PASS":
        gates.append(
            {
                "gate_id": "A209_24h_operator_soak",
                "reason": "24h operator soak evidence is missing or not release-ready",
            }
        )
    if brand["public_release_allowed"] is not True or brand["a210_status"] != "DONE":
        gates.append(
            {
                "gate_id": "A210_brand_clearance_or_risk_waiver",
                "reason": "formal brand clearance or signed risk waiver is incomplete",
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
    return gates


def build_preflight(
    *,
    release_decision_contract_path: Path = DEFAULT_RELEASE_DECISION_CONTRACT,
    production_api_preflight_path: Path = DEFAULT_PRODUCTION_API_PREFLIGHT,
    release_manager_preflight_path: Path = DEFAULT_RELEASE_MANAGER_PREFLIGHT,
    operator_soak_evidence_path: Path = DEFAULT_OPERATOR_SOAK_EVIDENCE,
    operator_soak_heartbeat_path: Path = DEFAULT_OPERATOR_SOAK_HEARTBEAT,
    brand_preflight_path: Path = DEFAULT_BRAND_PREFLIGHT,
    entity_gold_evaluation_path: Path = DEFAULT_ENTITY_GOLD_EVALUATION,
    relationship_gold_evaluation_path: Path = DEFAULT_RELATIONSHIP_GOLD_EVALUATION,
    generated_at: str | None = None,
) -> dict[str, Any]:
    release_decision = release_decision_status(read_json(release_decision_contract_path))
    production_api = production_api_status(read_json(production_api_preflight_path))
    release_manager = release_manager_status(read_json(release_manager_preflight_path))
    soak = soak_status(read_json(operator_soak_evidence_path))
    soak_heartbeat = soak_heartbeat_status(read_json(operator_soak_heartbeat_path))
    brand = brand_status(read_json(brand_preflight_path))
    entity_gold = gold_status(read_json(entity_gold_evaluation_path), "A026")
    relationship_gold = gold_status(read_json(relationship_gold_evaluation_path), "A027")
    blockers = missing_gates(
        release_decision=release_decision,
        production_api=production_api,
        release_manager=release_manager,
        soak=soak,
        brand=brand,
        entity_gold=entity_gold,
        relationship_gold=relationship_gold,
    )
    release_ready = not blockers
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t1303-mvp-release-gate-preflight",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_ids": REQUIRED_TASK_IDS,
        "acceptance_ids": REQUIRED_ACCEPTANCE_IDS,
        "required_gate_ids": REQUIRED_GATE_IDS,
        "status": "MVP_RELEASE_READY" if release_ready else "MVP_RELEASE_BLOCKED",
        "release_ready": release_ready,
        "production_publication_allowed": release_ready,
        "score_publication_allowed": release_ready,
        "public_brand_launch_allowed": release_ready,
        "source_files": {
            "release_decision_contract": relative(release_decision_contract_path),
            "release_decision_contract_sha256": sha256_file(release_decision_contract_path),
            "production_api_preflight": relative(production_api_preflight_path),
            "production_api_preflight_sha256": sha256_file(production_api_preflight_path),
            "release_manager_preflight": relative(release_manager_preflight_path),
            "release_manager_preflight_sha256": sha256_file(release_manager_preflight_path),
            "operator_soak_evidence": relative(operator_soak_evidence_path),
            "operator_soak_evidence_sha256": sha256_file(operator_soak_evidence_path),
            "operator_soak_heartbeat": relative(operator_soak_heartbeat_path),
            "operator_soak_heartbeat_sha256": sha256_file(operator_soak_heartbeat_path),
            "brand_preflight": relative(brand_preflight_path),
            "brand_preflight_sha256": sha256_file(brand_preflight_path),
            "entity_gold_evaluation": relative(entity_gold_evaluation_path),
            "entity_gold_evaluation_sha256": sha256_file(entity_gold_evaluation_path),
            "relationship_gold_evaluation": relative(relationship_gold_evaluation_path),
            "relationship_gold_evaluation_sha256": sha256_file(
                relationship_gold_evaluation_path
            ),
        },
        "gate_statuses": {
            "release_decision": release_decision,
            "production_api": production_api,
            "release_manager": release_manager,
            "operator_soak": soak,
            "operator_soak_background_heartbeat": soak_heartbeat,
            "brand": brand,
            "entity_gold": entity_gold,
            "relationship_gold": relationship_gold,
        },
        "missing_gates": blockers,
        "operator_next_actions": [
            {
                "gate_id": row["gate_id"],
                "action": "supply real signed evidence or complete the referenced gate artifact",
            }
            for row in blockers
        ],
        "validation_policy": {
            "all_required_gate_ids_must_pass": True,
            "repository_fixtures_count_as_clearance": False,
            "templates_count_as_clearance": False,
            "a209_background_heartbeat_counts_as_release_ready": False,
            "release_manager_activation_must_be_allowed": True,
            "production_api_release_preflight_must_be_ready": True,
        },
        "non_claims": [
            "This preflight does not execute a release.",
            "This preflight does not certify legal, market or trademark clearance.",
            "This preflight does not convert repository fixtures into production approval.",
            "This preflight does not replace A209 24h operator soak evidence.",
        ],
    }


def validate_preflight(
    payload: dict[str, Any],
    *,
    release_decision_contract_path: Path = DEFAULT_RELEASE_DECISION_CONTRACT,
    production_api_preflight_path: Path = DEFAULT_PRODUCTION_API_PREFLIGHT,
    release_manager_preflight_path: Path = DEFAULT_RELEASE_MANAGER_PREFLIGHT,
    operator_soak_evidence_path: Path = DEFAULT_OPERATOR_SOAK_EVIDENCE,
    operator_soak_heartbeat_path: Path = DEFAULT_OPERATOR_SOAK_HEARTBEAT,
    brand_preflight_path: Path = DEFAULT_BRAND_PREFLIGHT,
    entity_gold_evaluation_path: Path = DEFAULT_ENTITY_GOLD_EVALUATION,
    relationship_gold_evaluation_path: Path = DEFAULT_RELATIONSHIP_GOLD_EVALUATION,
) -> None:
    expected = build_preflight(
        release_decision_contract_path=release_decision_contract_path,
        production_api_preflight_path=production_api_preflight_path,
        release_manager_preflight_path=release_manager_preflight_path,
        operator_soak_evidence_path=operator_soak_evidence_path,
        operator_soak_heartbeat_path=operator_soak_heartbeat_path,
        brand_preflight_path=brand_preflight_path,
        entity_gold_evaluation_path=entity_gold_evaluation_path,
        relationship_gold_evaluation_path=relationship_gold_evaluation_path,
        generated_at=payload.get("generated_at"),
    )
    checked_fields = (
        "schema_version",
        "artifact_id",
        "task_ids",
        "acceptance_ids",
        "required_gate_ids",
        "status",
        "release_ready",
        "production_publication_allowed",
        "score_publication_allowed",
        "public_brand_launch_allowed",
        "source_files",
        "gate_statuses",
        "missing_gates",
        "operator_next_actions",
        "validation_policy",
    )
    for key in checked_fields:
        if payload.get(key) != expected.get(key):
            raise ValueError(f"MVP release-gate preflight field drift: {key}")
    missing = payload.get("missing_gates") or []
    if payload.get("release_ready") is True:
        if payload.get("status") != "MVP_RELEASE_READY":
            raise ValueError("ready preflight must report MVP_RELEASE_READY")
        if missing:
            raise ValueError("ready preflight cannot contain missing gates")
        if payload.get("production_publication_allowed") is not True:
            raise ValueError("ready preflight must allow production publication")
    else:
        if payload.get("status") != "MVP_RELEASE_BLOCKED":
            raise ValueError("blocked preflight must report MVP_RELEASE_BLOCKED")
        if not missing:
            raise ValueError("blocked preflight must list missing gates")
        if payload.get("production_publication_allowed") is not False:
            raise ValueError("blocked preflight cannot allow production publication")


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--release-decision-contract",
        type=Path,
        default=DEFAULT_RELEASE_DECISION_CONTRACT,
    )
    parser.add_argument(
        "--production-api-preflight",
        type=Path,
        default=DEFAULT_PRODUCTION_API_PREFLIGHT,
    )
    parser.add_argument(
        "--release-manager-preflight",
        type=Path,
        default=DEFAULT_RELEASE_MANAGER_PREFLIGHT,
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
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)


def generate(args: argparse.Namespace) -> None:
    payload = build_preflight(
        release_decision_contract_path=args.release_decision_contract,
        production_api_preflight_path=args.production_api_preflight,
        release_manager_preflight_path=args.release_manager_preflight,
        operator_soak_evidence_path=args.operator_soak_evidence,
        operator_soak_heartbeat_path=args.operator_soak_heartbeat,
        brand_preflight_path=args.brand_preflight,
        entity_gold_evaluation_path=args.entity_gold_evaluation,
        relationship_gold_evaluation_path=args.relationship_gold_evaluation,
    )
    validate_preflight(
        payload,
        release_decision_contract_path=args.release_decision_contract,
        production_api_preflight_path=args.production_api_preflight,
        release_manager_preflight_path=args.release_manager_preflight,
        operator_soak_evidence_path=args.operator_soak_evidence,
        operator_soak_heartbeat_path=args.operator_soak_heartbeat,
        brand_preflight_path=args.brand_preflight,
        entity_gold_evaluation_path=args.entity_gold_evaluation,
        relationship_gold_evaluation_path=args.relationship_gold_evaluation,
    )
    write_json(args.output, payload)
    print(json.dumps({"generated": True, "artifact": relative(args.output)}, indent=2))


def validate(args: argparse.Namespace) -> None:
    validate_preflight(
        read_json(args.output),
        release_decision_contract_path=args.release_decision_contract,
        production_api_preflight_path=args.production_api_preflight,
        release_manager_preflight_path=args.release_manager_preflight,
        operator_soak_evidence_path=args.operator_soak_evidence,
        operator_soak_heartbeat_path=args.operator_soak_heartbeat,
        brand_preflight_path=args.brand_preflight,
        entity_gold_evaluation_path=args.entity_gold_evaluation,
        relationship_gold_evaluation_path=args.relationship_gold_evaluation,
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
