#!/usr/bin/env python3
"""Generate and validate the A202 signed-intake preflight.

This preflight turns the operator-fillable A202 release-decision intake into a
hash-bound gate artifact. It is intentionally fail-closed: the committed default
uses the template and reports missing signed inputs. A future operator-supplied
signed intake can validate as A202-complete, but it still does not make the MVP
release ready without A210, A026/A027, A209 and release-manager activation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DECISIONS_PATH = ROOT / "scripts/validate_release_decision_bundle.py"
DECISIONS_SPEC = importlib.util.spec_from_file_location(
    "validate_release_decision_bundle",
    DECISIONS_PATH,
)
if DECISIONS_SPEC is None or DECISIONS_SPEC.loader is None:
    raise RuntimeError(f"cannot load {DECISIONS_PATH}")
decisions = importlib.util.module_from_spec(DECISIONS_SPEC)
DECISIONS_SPEC.loader.exec_module(decisions)

SCHEMA_VERSION = "eei-a202-signed-intake-preflight-v1"
DEFAULT_SIGNED_INTAKE = decisions.DEFAULT_INTAKE_TEMPLATE
DEFAULT_A202_PACKET = decisions.DEFAULT_A202_PACKET
DEFAULT_FACT_CANDIDATES = decisions.DEFAULT_FACT_CANDIDATES
DEFAULT_OUTPUT = ROOT / "artifacts/tests/a202/t1301_a202_signed_intake_preflight.json"

REQUIRED_TASK_IDS = ["T1301"]
REQUIRED_ACCEPTANCE_IDS = ["A202"]
MISSING_SIGNED_INPUTS = [
    "A202_source_license_reviews",
    "A202_passage_level_relationship_reviews",
    "A202_production_owner_signoffs",
    "A202_legal_release_clearance",
    "A202_final_attestation",
]
REMAINING_EXTERNAL_GATES_AFTER_A202 = [
    "A210_brand_clearance",
    "A026_A027_production_gold_labels",
    "A209_24h_operator_soak",
    "release_manager_activation",
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


def pending_input_rows() -> list[dict[str, str]]:
    return [
        {
            "input_id": "A202_source_license_reviews",
            "reason": "source-license review signatures are not supplied",
        },
        {
            "input_id": "A202_passage_level_relationship_reviews",
            "reason": "passage-level relationship review signatures are not supplied",
        },
        {
            "input_id": "A202_production_owner_signoffs",
            "reason": "production owner sign-off signatures are not supplied",
        },
        {
            "input_id": "A202_legal_release_clearance",
            "reason": "legal clearance or signed risk waiver is not supplied",
        },
        {
            "input_id": "A202_final_attestation",
            "reason": "final release-decision attestation is not supplied",
        },
    ]


def template_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "bundle_status": payload.get("bundle_status"),
        "source_license_reviews": len(payload.get("source_license_reviews", [])),
        "passage_reviews": len(payload.get("passage_level_relationship_reviews", [])),
        "owner_signoffs": len(payload.get("production_owner_signoffs", [])),
        "legal_clearance_status": (
            (payload.get("legal_release_clearance") or {}).get("clearance_status")
        ),
        "candidate_source_anchor_requirements": payload.get(
            "candidate_source_anchor_requirements"
        ),
    }


def build_preflight(
    *,
    signed_intake_path: Path = DEFAULT_SIGNED_INTAKE,
    a202_packet_path: Path = DEFAULT_A202_PACKET,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
    generated_at: str | None = None,
) -> dict[str, Any]:
    signed_intake = read_json(signed_intake_path)
    source_boundary = decisions.signed_intake_source_boundary(signed_intake_path)
    if signed_intake.get("bundle_status") == "TEMPLATE_ONLY":
        decisions.validate_intake_template(
            signed_intake,
            a202_packet_path=a202_packet_path,
            fact_candidates_path=fact_candidates_path,
        )
        status = "A202_SIGNED_INTAKE_MISSING"
        a202_clearance_complete = False
        relationship_publication_allowed = False
        summary = template_summary(signed_intake)
        missing_inputs = pending_input_rows()
    else:
        source_boundary = decisions.validate_signed_intake_source_path(
            signed_intake_path
        )
        summary = decisions.validate_signed_intake_bundle(
            signed_intake,
            a202_packet_path=a202_packet_path,
            fact_candidates_path=fact_candidates_path,
        )
        status = "A202_SIGNED_INTAKE_COMPLETE"
        a202_clearance_complete = True
        relationship_publication_allowed = True
        missing_inputs = []

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t1301-a202-signed-intake-preflight",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_ids": REQUIRED_TASK_IDS,
        "acceptance_ids": REQUIRED_ACCEPTANCE_IDS,
        "status": status,
        "a202_clearance_complete": a202_clearance_complete,
        "relationship_publication_allowed": relationship_publication_allowed,
        "release_gate_closed_by_preflight": False,
        "release_ready": False,
        "source_files": {
            "signed_intake": display_path(signed_intake_path),
            "signed_intake_sha256": sha256_file(signed_intake_path),
            "a202_operator_review_packet": display_path(a202_packet_path),
            "a202_operator_review_packet_sha256": sha256_file(a202_packet_path),
            "golden_vertical_fact_candidates": display_path(fact_candidates_path),
            "golden_vertical_fact_candidates_sha256": sha256_file(fact_candidates_path),
        },
        "signed_intake_source_boundary": source_boundary,
        "signed_intake_summary": summary,
        "missing_signed_inputs": missing_inputs,
        "remaining_external_gates_after_a202_clearance": (
            REMAINING_EXTERNAL_GATES_AFTER_A202
        ),
        "validation_policy": {
            "template_only_counts_as_clearance": False,
            "signed_intake_required_for_a202_closure": True,
            "signed_intake_source_must_be_operator_supplied": True,
            "repository_fixtures_and_templates_count_as_clearance": False,
            "signed_intake_must_cover_all_candidate_source_anchors": True,
            "signed_intake_must_include_counter_evidence_review": True,
            "signed_intake_alone_counts_as_release_ready": False,
            "release_gate_closed_by_preflight": False,
        },
        "operator_next_actions": operator_next_actions(a202_clearance_complete),
        "non_claims": [
            "This preflight does not create source-license approval.",
            "This preflight does not create passage-level relationship approval.",
            "This preflight does not create production owner approval.",
            "This preflight does not create legal release clearance.",
            "This preflight does not publish relationship facts or graph edges.",
            "This preflight does not close A202 by itself.",
            "This preflight does not close A209, A210, A026/A027 or release-manager activation.",
        ],
        "rollback": [
            "Regenerate this preflight from the signed intake or template source.",
            "Do not delete future operator-supplied signed intake files during rollback.",
            "Do not treat a committed template preflight as clearance evidence.",
        ],
    }


def operator_next_actions(a202_clearance_complete: bool) -> list[str]:
    if a202_clearance_complete:
        return [
            "Attach A210 signed brand clearance or risk waiver evidence.",
            "Attach A026/A027 production gold-label evidence that meets thresholds.",
            "Wait for A209 finalization to allow downstream release-gate refresh.",
            "Regenerate release-manager and MVP release-gate preflights after all gates are ready.",
        ]
    return [
        "Fill the A202 release-decision intake with real source-license reviews.",
        "Fill passage-level relationship reviews for GV-FACT-001 and GV-FACT-002.",
        "Attach production owner sign-offs with authority scope and signatures.",
        "Attach legal release clearance or signed risk waiver.",
        "Run validate-a202-signed-intake-preflight against the signed bundle.",
    ]


def validate_preflight(
    payload: dict[str, Any],
    *,
    signed_intake_path: Path = DEFAULT_SIGNED_INTAKE,
    a202_packet_path: Path = DEFAULT_A202_PACKET,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
) -> None:
    expected = build_preflight(
        signed_intake_path=signed_intake_path,
        a202_packet_path=a202_packet_path,
        fact_candidates_path=fact_candidates_path,
        generated_at=payload.get("generated_at"),
    )
    checked_fields = (
        "schema_version",
        "artifact_id",
        "system_name",
        "task_ids",
        "acceptance_ids",
        "status",
        "a202_clearance_complete",
        "relationship_publication_allowed",
        "release_gate_closed_by_preflight",
        "release_ready",
        "source_files",
        "signed_intake_summary",
        "signed_intake_source_boundary",
        "missing_signed_inputs",
        "remaining_external_gates_after_a202_clearance",
        "validation_policy",
        "operator_next_actions",
        "non_claims",
    )
    for key in checked_fields:
        if payload.get(key) != expected.get(key):
            raise ValueError(f"A202 signed-intake preflight drift: {key}")
    if payload.get("release_gate_closed_by_preflight") is not False:
        raise ValueError("A202 signed-intake preflight must not close release gates")
    if payload.get("release_ready") is not False:
        raise ValueError("A202 signed-intake preflight must not claim release readiness")
    if payload.get("a202_clearance_complete") is True and payload.get(
        "missing_signed_inputs"
    ):
        raise ValueError("complete A202 preflight cannot list missing signed inputs")
    if payload.get("a202_clearance_complete") is not True and not payload.get(
        "missing_signed_inputs"
    ):
        raise ValueError("incomplete A202 preflight must list missing signed inputs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"))
    parser.add_argument("--signed-intake", type=Path, default=DEFAULT_SIGNED_INTAKE)
    parser.add_argument("--a202-packet", type=Path, default=DEFAULT_A202_PACKET)
    parser.add_argument("--fact-candidates", type=Path, default=DEFAULT_FACT_CANDIDATES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "generate":
        payload = build_preflight(
            signed_intake_path=args.signed_intake,
            a202_packet_path=args.a202_packet,
            fact_candidates_path=args.fact_candidates,
        )
        validate_preflight(
            payload,
            signed_intake_path=args.signed_intake,
            a202_packet_path=args.a202_packet,
            fact_candidates_path=args.fact_candidates,
        )
        write_json(args.output, payload)
        if not args.quiet:
            print(json.dumps({"generated": True, "artifact": display_path(args.output)}))
    else:
        validate_preflight(
            read_json(args.output),
            signed_intake_path=args.signed_intake,
            a202_packet_path=args.a202_packet,
            fact_candidates_path=args.fact_candidates,
        )
        if not args.quiet:
            print(json.dumps({"valid": True, "artifact": display_path(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
