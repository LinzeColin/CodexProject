#!/usr/bin/env python3
"""Generate and validate the A202/A210 signed release decision bundle contract.

This contract is intentionally fail-closed. It defines the exact signed inputs
needed before selected live official-source evidence, owner approval, legal
clearance, and brand clearance can be treated as release evidence. Repository
fixtures may validate the schema, but they must not close A202 or A210.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "eei-a202-a210-release-decision-bundle-v1"
CONTRACT_SCHEMA_VERSION = "eei-a202-a210-release-decision-bundle-contract-v1"
DEFAULT_A202_PACKET = ROOT / "artifacts/tests/a202/t1301_operator_review_packet_contract.json"
DEFAULT_A210_PREFLIGHT = ROOT / "artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json"
DEFAULT_TEMPLATE = (
    ROOT / "tests/fixtures/release_decision_bundle/a202_a210_release_decision_bundle_template.json"
)
DEFAULT_SIGNED_CONTRACT_TEST = (
    ROOT
    / "tests/fixtures/release_decision_bundle/"
    "a202_a210_signed_decision_bundle_contract_test.json"
)
DEFAULT_OUTPUT = ROOT / "artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json"

REQUIRED_TASK_IDS = ["T1301", "T1309"]
REQUIRED_ACCEPTANCE_IDS = ["A202", "A210"]
REQUIRED_SECTIONS = {
    "source_license_reviews": [
        "anchor_id",
        "reviewer",
        "reviewed_at",
        "source_license_status",
        "allowed_use_scope",
        "evidence_uri",
        "signature",
    ],
    "passage_level_relationship_reviews": [
        "candidate_key",
        "supporting_anchor_ids",
        "supporting_passage_locator",
        "counter_evidence_reviewed",
        "decision",
        "reviewer",
        "reviewed_at",
        "signature",
    ],
    "production_owner_signoffs": [
        "candidate_key",
        "owner_actor",
        "owner_role",
        "authority_scope",
        "signed_at",
        "signature",
    ],
}
SIGNED_SOURCE_LICENSE_STATUSES = {"approved_for_public_release", "approved_for_internal_review"}
SIGNED_PASSAGE_DECISIONS = {"approved_for_publication"}
SIGNED_LEGAL_CLEARANCE_STATUSES = {"CLEARED", "RISK_WAIVER_ACCEPTED"}
SIGNED_BRAND_DECISIONS = {"CLEARED", "RISK_WAIVER_ACCEPTED"}


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing signed decision field: {key}")
    return value.strip()


def validate_common_bundle_shape(bundle: dict[str, Any]) -> None:
    if bundle.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    if bundle.get("system_name") != "EEI":
        raise ValueError("system_name must be EEI")
    if bundle.get("task_ids") != REQUIRED_TASK_IDS:
        raise ValueError(f"task_ids must be {REQUIRED_TASK_IDS}")
    if bundle.get("acceptance_ids") != REQUIRED_ACCEPTANCE_IDS:
        raise ValueError(f"acceptance_ids must be {REQUIRED_ACCEPTANCE_IDS}")
    decision_scope = bundle.get("decision_scope")
    if not isinstance(decision_scope, dict):
        raise ValueError("decision_scope must be present")
    for key in ("relationship_publication", "public_brand_launch", "release_clearance"):
        if decision_scope.get(key) is not False:
            raise ValueError(f"template decision_scope.{key} must remain false")
    for section, fields in REQUIRED_SECTIONS.items():
        entries = bundle.get(section)
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"{section} must be a non-empty list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"{section} entries must be objects")
            for field in fields:
                if field not in entry:
                    raise ValueError(f"{section} entry missing {field}")
    for section in ("legal_release_clearance", "brand_clearance_or_risk_waiver", "attestation"):
        if not isinstance(bundle.get(section), dict):
            raise ValueError(f"{section} must be present")


def validate_template_bundle(bundle: dict[str, Any]) -> None:
    validate_common_bundle_shape(bundle)
    if bundle.get("bundle_status") != "TEMPLATE_ONLY":
        raise ValueError("template bundle_status must be TEMPLATE_ONLY")
    if bundle.get("release_gate_closure_allowed") is not False:
        raise ValueError("template must not allow release gate closure")
    for entry in bundle["source_license_reviews"]:
        if entry.get("source_license_status") != "PENDING_REVIEW":
            raise ValueError("template source_license_status must remain PENDING_REVIEW")
    for entry in bundle["passage_level_relationship_reviews"]:
        if entry.get("decision") != "PENDING_REVIEW":
            raise ValueError("template passage review decision must remain PENDING_REVIEW")
    if bundle["legal_release_clearance"].get("clearance_status") != "PENDING_REVIEW":
        raise ValueError("template legal clearance must remain PENDING_REVIEW")
    if bundle["brand_clearance_or_risk_waiver"].get("decision") != "PENDING_REVIEW":
        raise ValueError("template brand decision must remain PENDING_REVIEW")


def validate_signed_decision_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    validate_common_bundle_shape(bundle)
    if bundle.get("bundle_status") == "TEMPLATE_ONLY":
        raise ValueError("template-only bundle is not signed release evidence")
    if bundle.get("bundle_status") != "SIGNED_DECISION_BUNDLE":
        raise ValueError("signed bundle_status must be SIGNED_DECISION_BUNDLE")
    if bundle.get("release_gate_closure_allowed") is not True:
        raise ValueError("signed bundle must explicitly allow release gate closure")

    for entry in bundle["source_license_reviews"]:
        for field in REQUIRED_SECTIONS["source_license_reviews"]:
            require_text(entry, field)
        if entry["source_license_status"] not in SIGNED_SOURCE_LICENSE_STATUSES:
            raise ValueError(f"unsupported source license status: {entry['source_license_status']}")
    for entry in bundle["passage_level_relationship_reviews"]:
        for field in REQUIRED_SECTIONS["passage_level_relationship_reviews"]:
            if field == "counter_evidence_reviewed":
                if entry.get(field) is not True:
                    raise ValueError("counter_evidence_reviewed must be true")
            elif field == "supporting_anchor_ids":
                if not isinstance(entry.get(field), list) or not entry[field]:
                    raise ValueError("supporting_anchor_ids must be non-empty")
            else:
                require_text(entry, field)
        if entry["decision"] not in SIGNED_PASSAGE_DECISIONS:
            raise ValueError(f"unsupported passage decision: {entry['decision']}")
    for entry in bundle["production_owner_signoffs"]:
        for field in REQUIRED_SECTIONS["production_owner_signoffs"]:
            require_text(entry, field)

    legal = bundle["legal_release_clearance"]
    for field in (
        "legal_reviewer",
        "clearance_status",
        "clearance_scope",
        "risk_waiver_id_or_opinion_ref",
        "signed_at",
        "signature",
    ):
        require_text(legal, field)
    if legal["clearance_status"] not in SIGNED_LEGAL_CLEARANCE_STATUSES:
        raise ValueError(f"unsupported legal clearance status: {legal['clearance_status']}")

    brand = bundle["brand_clearance_or_risk_waiver"]
    for field in ("decision", "scope", "evidence_uri", "signed_by", "signed_at", "signature"):
        require_text(brand, field)
    if brand["decision"] not in SIGNED_BRAND_DECISIONS:
        raise ValueError(f"unsupported brand decision: {brand['decision']}")

    attestation = bundle["attestation"]
    for field in ("signed_by", "signed_at", "signature"):
        require_text(attestation, field)
    return {
        "source_license_reviews": len(bundle["source_license_reviews"]),
        "passage_reviews": len(bundle["passage_level_relationship_reviews"]),
        "owner_signoffs": len(bundle["production_owner_signoffs"]),
        "legal_clearance_status": legal["clearance_status"],
        "brand_decision": brand["decision"],
    }


def gate_statuses(packet: dict[str, Any]) -> dict[str, str]:
    return {
        str(gate.get("gate_id")): str(gate.get("status"))
        for gate in packet.get("closure_gates", [])
        if isinstance(gate, dict)
    }


def build_contract(
    *,
    a202_packet_path: Path = DEFAULT_A202_PACKET,
    a210_preflight_path: Path = DEFAULT_A210_PREFLIGHT,
    template_path: Path = DEFAULT_TEMPLATE,
    signed_contract_test_path: Path = DEFAULT_SIGNED_CONTRACT_TEST,
    generated_at: str | None = None,
) -> dict[str, Any]:
    a202_packet = read_json(a202_packet_path)
    a210_preflight = read_json(a210_preflight_path)
    template = read_json(template_path)
    validate_template_bundle(template)
    signed_contract_test = read_json(signed_contract_test_path)
    signed_contract_test_summary = validate_signed_decision_bundle(signed_contract_test)
    a202_gates = gate_statuses(a202_packet)
    a210_current = a210_preflight.get("current_clearance_status") or {}
    return {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "artifact_id": "t1301-a202-a210-release-decision-bundle-contract",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_ids": REQUIRED_TASK_IDS,
        "acceptance_ids": REQUIRED_ACCEPTANCE_IDS,
        "status": "PENDING_SIGNED_DECISIONS",
        "release_gate_closed_by_contract": False,
        "relationship_publication_allowed": False,
        "public_brand_launch_allowed": False,
        "source_files": {
            "a202_operator_review_packet": relative(a202_packet_path),
            "a202_operator_review_packet_sha256": sha256_file(a202_packet_path),
            "a210_brand_preflight": relative(a210_preflight_path),
            "a210_brand_preflight_sha256": sha256_file(a210_preflight_path),
            "decision_bundle_template": relative(template_path),
            "decision_bundle_template_sha256": sha256_file(template_path),
            "signed_contract_test_bundle": relative(signed_contract_test_path),
            "signed_contract_test_bundle_sha256": sha256_file(signed_contract_test_path),
        },
        "signed_contract_test_summary": signed_contract_test_summary,
        "required_sections": REQUIRED_SECTIONS,
        "a202_gate_statuses": a202_gates,
        "a210_current_clearance_status": a210_current,
        "required_signed_inputs_before_closure": [
            "source license review for each selected live official-source anchor",
            "passage-level relationship review for every candidate intended for publication",
            "production owner sign-off with authority scope and signature",
            "legal release clearance or explicit signed risk waiver",
            "brand clearance or explicit signed risk waiver covering public launch surfaces",
            "A209 24h operator soak evidence must still be provided separately",
        ],
        "validation_policy": {
            "template_only_allowed_in_repository": True,
            "template_only_counts_as_clearance": False,
            "signed_bundle_required_for_a202_a210_closure": True,
            "contract_test_signatures_are_not_clearance": True,
            "signed_contract_test_counts_as_clearance": False,
            "production_owner_publication_requires_signed_bundle": True,
            "production_owner_publication_writes_operation_log": True,
            "default_publication_state": "fail_closed",
        },
        "non_claims": [
            "This contract does not certify legal clearance.",
            "This contract does not certify trademark or market clearance.",
            "This contract does not publish relationship facts or graph edges.",
            "This contract does not close A202, A209 or A210 without real signed evidence.",
        ],
    }


def validate_contract(
    contract: dict[str, Any],
    *,
    a202_packet_path: Path = DEFAULT_A202_PACKET,
    a210_preflight_path: Path = DEFAULT_A210_PREFLIGHT,
    template_path: Path = DEFAULT_TEMPLATE,
    signed_contract_test_path: Path = DEFAULT_SIGNED_CONTRACT_TEST,
) -> None:
    expected = build_contract(
        a202_packet_path=a202_packet_path,
        a210_preflight_path=a210_preflight_path,
        template_path=template_path,
        signed_contract_test_path=signed_contract_test_path,
        generated_at=contract.get("generated_at"),
    )
    for key in (
        "schema_version",
        "artifact_id",
        "system_name",
        "task_ids",
        "acceptance_ids",
        "status",
        "release_gate_closed_by_contract",
        "relationship_publication_allowed",
        "public_brand_launch_allowed",
        "source_files",
        "signed_contract_test_summary",
        "a202_gate_statuses",
        "a210_current_clearance_status",
    ):
        if contract.get(key) != expected.get(key):
            raise ValueError(f"contract field drift: {key}")
    if contract.get("release_gate_closed_by_contract") is not False:
        raise ValueError("contract must not close release gates")
    if contract.get("relationship_publication_allowed") is not False:
        raise ValueError("contract must not allow relationship publication")
    if contract.get("public_brand_launch_allowed") is not False:
        raise ValueError("contract must not allow public brand launch")


def generate(args: argparse.Namespace) -> None:
    contract = build_contract(
        a202_packet_path=args.a202_packet,
        a210_preflight_path=args.a210_preflight,
        template_path=args.template,
        signed_contract_test_path=args.signed_contract_test,
    )
    validate_contract(
        contract,
        a202_packet_path=args.a202_packet,
        a210_preflight_path=args.a210_preflight,
        template_path=args.template,
        signed_contract_test_path=args.signed_contract_test,
    )
    write_json(args.output, contract)
    print(json.dumps({"generated": True, "artifact": relative(args.output)}, indent=2))


def validate(args: argparse.Namespace) -> None:
    validate_contract(
        read_json(args.output),
        a202_packet_path=args.a202_packet,
        a210_preflight_path=args.a210_preflight,
        template_path=args.template,
        signed_contract_test_path=args.signed_contract_test,
    )
    print(json.dumps({"valid": True, "artifact": relative(args.output)}, indent=2))


def validate_bundle(args: argparse.Namespace) -> None:
    bundle = read_json(args.bundle)
    if args.template_only:
        validate_template_bundle(bundle)
        result = {"valid": True, "bundle": relative(args.bundle), "release_ready": False}
    else:
        summary = validate_signed_decision_bundle(bundle)
        result = {
            "valid": True,
            "bundle": relative(args.bundle),
            "signed_decision_complete": True,
            "release_ready": False,
            "remaining_external_gates": [
                "A209_24h_operator_soak",
                "release_manager_activation",
            ],
            **summary,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "validate"):
        child = sub.add_parser(name)
        child.add_argument("--a202-packet", type=Path, default=DEFAULT_A202_PACKET)
        child.add_argument("--a210-preflight", type=Path, default=DEFAULT_A210_PREFLIGHT)
        child.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
        child.add_argument(
            "--signed-contract-test",
            type=Path,
            default=DEFAULT_SIGNED_CONTRACT_TEST,
        )
        child.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    bundle = sub.add_parser("validate-bundle")
    bundle.add_argument("--bundle", type=Path, default=DEFAULT_TEMPLATE)
    bundle.add_argument("--template-only", action="store_true")
    args = parser.parse_args()
    if args.command == "generate":
        generate(args)
    elif args.command == "validate":
        validate(args)
    else:
        validate_bundle(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
