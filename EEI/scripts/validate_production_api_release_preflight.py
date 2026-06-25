#!/usr/bin/env python3
"""Generate and validate the T1302/A203 production API release preflight.

The A203 API surface can be implemented and CI-proven before it is release-ready.
This preflight keeps that distinction explicit: production graph/scoring APIs
remain blocked until production-approved relationship edges, A202 clearance,
release-manager activation and A209 long-duration evidence are ready.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "eei-t1302-a203-production-api-release-preflight-v1"
DEFAULT_A203_CONTRACT = (
    ROOT / "artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json"
)
DEFAULT_RELEASE_DECISION_CONTRACT = (
    ROOT / "artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json"
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
DEFAULT_OUTPUT = (
    ROOT / "artifacts/tests/a203/t1302_production_api_release_preflight.json"
)

REQUIRED_SCORE_OBJECT_TYPES = [
    "entity",
    "theme",
    "facility",
    "event",
    "industry",
    "source_document",
    "score_result",
    "relationship_fact_candidate",
    "relationship",
]
REQUIRED_API_PATHS = [
    "/v1/explore",
    "/v1/paths",
    "/v1/catalogs",
    "/v1/scoring/explain/{objectType}/{objectId}",
    "/v1/evidence/{objectType}/{objectId}",
]
REQUIRED_TASK_IDS = ["T1301", "T1302", "T1303", "T1307"]
REQUIRED_ACCEPTANCE_IDS = ["A202", "A203", "A204", "A205", "A209"]


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


def a203_contract_status(payload: dict[str, Any]) -> dict[str, Any]:
    implemented_slice = payload.get("scope", {}).get("implemented_slice", [])
    api_contracts = payload.get("api_contracts", [])
    scoring_thresholds = payload.get("scoring_thresholds", {})
    publication_policy = payload.get("publication_policy", {})
    implemented_text = "\n".join(str(item) for item in implemented_slice)
    paths = {str(item.get("path")) for item in api_contracts if isinstance(item, dict)}
    object_type_coverage = {
        object_type: (
            object_type in scoring_thresholds
            or object_type in implemented_text
            or object_type.replace("_", " ") in implemented_text
        )
        for object_type in REQUIRED_SCORE_OBJECT_TYPES
    }
    return {
        "contract_status": payload.get("status"),
        "implemented_slice_count": len(implemented_slice),
        "api_path_coverage": {path: path in paths for path in REQUIRED_API_PATHS},
        "score_object_type_coverage": object_type_coverage,
        "relationship_fact_candidates_in_graph_edges": publication_policy.get(
            "relationship_fact_candidates_in_graph_edges"
        ),
        "publish_requires_source_threshold": publication_policy.get(
            "publish_requires_source_threshold"
        ),
        "publish_requires_human_review": publication_policy.get(
            "publish_requires_human_review"
        ),
        "minimum_independent_sources": publication_policy.get(
            "minimum_independent_sources"
        ),
    }


def release_decision_status(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "release_gate_closed_by_contract": payload.get(
            "release_gate_closed_by_contract"
        ),
        "relationship_publication_allowed": payload.get(
            "relationship_publication_allowed"
        ),
        "public_brand_launch_allowed": payload.get("public_brand_launch_allowed"),
    }


def release_manager_status(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "activation_ready": payload.get("activation_ready"),
        "release_manager_activation_allowed": payload.get(
            "release_manager_activation_allowed"
        ),
        "relationship_publication_allowed": payload.get(
            "relationship_publication_allowed"
        ),
        "missing_gate_ids": [
            row.get("gate_id")
            for row in payload.get("missing_gates", [])
            if isinstance(row, dict)
        ],
    }


def soak_status(payload: dict[str, Any]) -> dict[str, Any]:
    results = {
        str(row.get("label")): str(row.get("status"))
        for row in payload.get("results", [])
        if isinstance(row, dict)
    }
    return {
        "status": payload.get("status"),
        "release_gate_closed_by_validator": payload.get(
            "release_gate_closed_by_validator"
        ),
        "operator_4h": results.get("operator_4h", "MISSING"),
        "operator_24h": results.get("operator_24h", "MISSING"),
    }


def heartbeat_status(payload: dict[str, Any]) -> dict[str, Any]:
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


def missing_gates(
    *,
    a203: dict[str, Any],
    release_decision: dict[str, Any],
    release_manager: dict[str, Any],
    soak: dict[str, Any],
) -> list[dict[str, str]]:
    gates: list[dict[str, str]] = []
    if a203["contract_status"] not in {"DONE", "RELEASE_READY"}:
        gates.append(
            {
                "gate_id": "A203_contract_status",
                "reason": "A203 contract artifact is not marked DONE or release-ready",
            }
        )
    if not all(a203["api_path_coverage"].values()):
        gates.append(
            {
                "gate_id": "A203_api_path_coverage",
                "reason": "one or more required production API paths are absent",
            }
        )
    if not all(a203["score_object_type_coverage"].values()):
        gates.append(
            {
                "gate_id": "A203_score_object_family_coverage",
                "reason": "one or more MVP scoring object families are absent",
            }
        )
    if a203["relationship_fact_candidates_in_graph_edges"] is not False:
        gates.append(
            {
                "gate_id": "A203_candidate_publication_boundary",
                "reason": "relationship fact candidates must stay outside graph edges",
            }
        )
    if release_decision["relationship_publication_allowed"] is not True:
        gates.append(
            {
                "gate_id": "A202_relationship_publication_clearance",
                "reason": "real source/license/passage/owner/legal clearance is incomplete",
            }
        )
    if release_manager["release_manager_activation_allowed"] is not True:
        gates.append(
            {
                "gate_id": "A204_A205_release_manager_activation",
                "reason": "release-manager activation is blocked by external gates",
            }
        )
    if soak["release_gate_closed_by_validator"] is not True or soak["operator_24h"] != "PASS":
        gates.append(
            {
                "gate_id": "A209_24h_operator_soak",
                "reason": "24h operator soak evidence is missing or not release-ready",
            }
        )
    return gates


def build_preflight(
    *,
    a203_contract_path: Path = DEFAULT_A203_CONTRACT,
    release_decision_contract_path: Path = DEFAULT_RELEASE_DECISION_CONTRACT,
    release_manager_preflight_path: Path = DEFAULT_RELEASE_MANAGER_PREFLIGHT,
    operator_soak_evidence_path: Path = DEFAULT_OPERATOR_SOAK_EVIDENCE,
    operator_soak_heartbeat_path: Path = DEFAULT_OPERATOR_SOAK_HEARTBEAT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    a203 = a203_contract_status(read_json(a203_contract_path))
    release_decision = release_decision_status(read_json(release_decision_contract_path))
    release_manager = release_manager_status(read_json(release_manager_preflight_path))
    soak = soak_status(read_json(operator_soak_evidence_path))
    heartbeat = heartbeat_status(read_json(operator_soak_heartbeat_path))
    blockers = missing_gates(
        a203=a203,
        release_decision=release_decision,
        release_manager=release_manager,
        soak=soak,
    )
    release_ready = not blockers
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t1302-a203-production-api-release-preflight",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_ids": REQUIRED_TASK_IDS,
        "acceptance_ids": REQUIRED_ACCEPTANCE_IDS,
        "status": (
            "A203_PRODUCTION_API_RELEASE_READY"
            if release_ready
            else "A203_PRODUCTION_API_RELEASE_BLOCKED"
        ),
        "api_surface_ready": (
            all(a203["api_path_coverage"].values())
            and all(a203["score_object_type_coverage"].values())
            and a203["relationship_fact_candidates_in_graph_edges"] is False
        ),
        "release_ready": release_ready,
        "production_graph_publication_allowed": release_ready,
        "score_publication_allowed": release_ready,
        "source_files": {
            "a203_contract": relative(a203_contract_path),
            "a203_contract_sha256": sha256_file(a203_contract_path),
            "release_decision_contract": relative(release_decision_contract_path),
            "release_decision_contract_sha256": sha256_file(
                release_decision_contract_path
            ),
            "release_manager_preflight": relative(release_manager_preflight_path),
            "release_manager_preflight_sha256": sha256_file(
                release_manager_preflight_path
            ),
            "operator_soak_evidence": relative(operator_soak_evidence_path),
            "operator_soak_evidence_sha256": sha256_file(operator_soak_evidence_path),
            "operator_soak_heartbeat": relative(operator_soak_heartbeat_path),
            "operator_soak_heartbeat_sha256": sha256_file(operator_soak_heartbeat_path),
        },
        "gate_statuses": {
            "a203_contract": a203,
            "release_decision": release_decision,
            "release_manager": release_manager,
            "operator_soak": soak,
            "operator_soak_background_heartbeat": heartbeat,
        },
        "missing_gates": blockers,
        "validation_policy": {
            "api_surface_can_be_ready_before_release": True,
            "release_requires_a202_relationship_publication_clearance": True,
            "release_requires_release_manager_activation": True,
            "release_requires_a209_24h_soak": True,
            "a209_background_heartbeat_counts_as_release_ready": False,
            "repository_fixtures_count_as_production_edges": False,
        },
        "non_claims": [
            "This preflight does not publish relationship fact candidates into graph edges.",
            "This preflight does not certify source-license, passage, owner or legal clearance.",
            "This preflight does not replace release-manager activation.",
            "This preflight does not replace A209 24h operator soak evidence.",
            "This preflight does not close A203 while missing_gates is non-empty.",
        ],
    }


def validate_preflight(
    payload: dict[str, Any],
    *,
    a203_contract_path: Path = DEFAULT_A203_CONTRACT,
    release_decision_contract_path: Path = DEFAULT_RELEASE_DECISION_CONTRACT,
    release_manager_preflight_path: Path = DEFAULT_RELEASE_MANAGER_PREFLIGHT,
    operator_soak_evidence_path: Path = DEFAULT_OPERATOR_SOAK_EVIDENCE,
    operator_soak_heartbeat_path: Path = DEFAULT_OPERATOR_SOAK_HEARTBEAT,
) -> None:
    expected = build_preflight(
        a203_contract_path=a203_contract_path,
        release_decision_contract_path=release_decision_contract_path,
        release_manager_preflight_path=release_manager_preflight_path,
        operator_soak_evidence_path=operator_soak_evidence_path,
        operator_soak_heartbeat_path=operator_soak_heartbeat_path,
        generated_at=payload.get("generated_at"),
    )
    for key in (
        "schema_version",
        "artifact_id",
        "system_name",
        "task_ids",
        "acceptance_ids",
        "status",
        "api_surface_ready",
        "release_ready",
        "production_graph_publication_allowed",
        "score_publication_allowed",
        "source_files",
        "gate_statuses",
        "missing_gates",
        "validation_policy",
    ):
        if payload.get(key) != expected.get(key):
            raise ValueError(f"A203 production API preflight field drift: {key}")
    if payload.get("release_ready") is True:
        if payload.get("missing_gates"):
            raise ValueError("release-ready A203 preflight cannot list missing gates")
        if payload.get("production_graph_publication_allowed") is not True:
            raise ValueError("release-ready A203 preflight must allow graph publication")
    else:
        if payload.get("status") != "A203_PRODUCTION_API_RELEASE_BLOCKED":
            raise ValueError("blocked A203 preflight must report BLOCKED")
        if not payload.get("missing_gates"):
            raise ValueError("blocked A203 preflight must list missing gates")
        if payload.get("production_graph_publication_allowed") is not False:
            raise ValueError("blocked A203 preflight must not allow graph publication")


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--a203-contract", type=Path, default=DEFAULT_A203_CONTRACT)
    parser.add_argument(
        "--release-decision-contract",
        type=Path,
        default=DEFAULT_RELEASE_DECISION_CONTRACT,
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
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)


def generate(args: argparse.Namespace) -> None:
    payload = build_preflight(
        a203_contract_path=args.a203_contract,
        release_decision_contract_path=args.release_decision_contract,
        release_manager_preflight_path=args.release_manager_preflight,
        operator_soak_evidence_path=args.operator_soak_evidence,
        operator_soak_heartbeat_path=args.operator_soak_heartbeat,
    )
    validate_preflight(
        payload,
        a203_contract_path=args.a203_contract,
        release_decision_contract_path=args.release_decision_contract,
        release_manager_preflight_path=args.release_manager_preflight,
        operator_soak_evidence_path=args.operator_soak_evidence,
        operator_soak_heartbeat_path=args.operator_soak_heartbeat,
    )
    write_json(args.output, payload)
    print(json.dumps({"generated": True, "artifact": relative(args.output)}, indent=2))


def validate(args: argparse.Namespace) -> None:
    validate_preflight(
        read_json(args.output),
        a203_contract_path=args.a203_contract,
        release_decision_contract_path=args.release_decision_contract,
        release_manager_preflight_path=args.release_manager_preflight,
        operator_soak_evidence_path=args.operator_soak_evidence,
        operator_soak_heartbeat_path=args.operator_soak_heartbeat,
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
