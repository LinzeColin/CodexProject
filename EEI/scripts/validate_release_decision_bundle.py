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
INTAKE_SCHEMA_VERSION = "eei-a202-release-decision-intake-v1"
DEFAULT_A202_PACKET = ROOT / "artifacts/tests/a202/t1301_operator_review_packet_contract.json"
DEFAULT_A210_PREFLIGHT = ROOT / "artifacts/tests/a210/t1309_brand_clearance_preflight_contract.json"
DEFAULT_INTAKE_TEMPLATE = (
    ROOT / "artifacts/tests/a202/t1301_a202_release_decision_intake_template.json"
)
DEFAULT_TEMPLATE = (
    ROOT / "tests/fixtures/release_decision_bundle/a202_a210_release_decision_bundle_template.json"
)
DEFAULT_SIGNED_CONTRACT_TEST = (
    ROOT
    / "tests/fixtures/release_decision_bundle/"
    "a202_a210_signed_decision_bundle_contract_test.json"
)
DEFAULT_FACT_CANDIDATES = ROOT / "data/golden_vertical_fact_candidates.json"
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
SIGNED_A202_INTAKE_STATUS = "SIGNED_A202_RELEASE_DECISION_INTAKE"
SIGNED_INTAKE_ALLOWED_REPO_PREFIXES = (
    "artifacts/operator_inputs/",
    "operator_inputs/",
    "work/operator_inputs/",
)
SIGNED_INTAKE_DISALLOWED_REPO_PREFIXES = (
    "artifacts/tests/",
    "data/",
    "tests/",
    "docs/",
    "config/",
    "brand/",
)
EXACT_SIGNED_COVERAGE_REJECTION_PREFIXES = (
    "source_license_reviews duplicate candidate source anchors",
    "source_license_reviews reference unknown candidate source anchors",
    "passage reviews duplicate relationship candidates",
    "production_owner_signoffs duplicate relationship candidates",
    "production_owner_signoffs reference unknown relationship candidates",
    "production_owner_signoffs missing relationship candidates",
)


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


def signed_intake_source_boundary(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    root = ROOT.resolve()
    try:
        repo_relative = resolved.relative_to(root).as_posix()
    except ValueError:
        return {
            "path": resolved.as_posix(),
            "source_kind": "external_operator_file",
            "repository_relative": None,
            "closure_allowed": True,
            "reason": "signed intake is outside the repository fixture/template tree",
        }
    if resolved == DEFAULT_INTAKE_TEMPLATE.resolve():
        return {
            "path": repo_relative,
            "source_kind": "repository_template",
            "repository_relative": repo_relative,
            "closure_allowed": False,
            "reason": "default intake template is not signed operator evidence",
        }
    if repo_relative.startswith(SIGNED_INTAKE_ALLOWED_REPO_PREFIXES):
        return {
            "path": repo_relative,
            "source_kind": "repository_operator_input",
            "repository_relative": repo_relative,
            "closure_allowed": True,
            "reason": "signed intake is under an approved operator input directory",
        }
    if repo_relative.startswith(SIGNED_INTAKE_DISALLOWED_REPO_PREFIXES):
        return {
            "path": repo_relative,
            "source_kind": "repository_fixture_or_source",
            "repository_relative": repo_relative,
            "closure_allowed": False,
            "reason": "repository fixtures, templates, configs, docs and data cannot close A202",
        }
    return {
        "path": repo_relative,
        "source_kind": "repository_unapproved_path",
        "repository_relative": repo_relative,
        "closure_allowed": False,
        "reason": "signed intake must be outside the repository or under artifacts/operator_inputs",
    }


def validate_signed_intake_source_path(path: Path) -> dict[str, Any]:
    boundary = signed_intake_source_boundary(path)
    if boundary["closure_allowed"] is not True:
        raise ValueError(
            "A202 signed intake must be operator-supplied, not "
            f"{boundary['source_kind']}: {boundary['path']}"
        )
    return boundary


def require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing signed decision field: {key}")
    return value.strip()


def candidate_source_anchor_requirements(
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
) -> dict[str, list[str]]:
    payload = read_json(fact_candidates_path)
    snapshots = payload.get("source_snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise ValueError("fact candidates must contain source_snapshots")
    source_anchor_ids = {
        require_text(snapshot, "anchor_id")
        for snapshot in snapshots
        if isinstance(snapshot, dict)
    }
    candidates = payload.get("relationship_candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("fact candidates must contain relationship_candidates")
    requirements: dict[str, list[str]] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("relationship_candidates entries must be objects")
        candidate_key = require_text(candidate, "candidate_key")
        if candidate_key in requirements:
            raise ValueError(f"duplicate relationship candidate: {candidate_key}")
        primary_anchor_id = require_text(candidate, "source_anchor_id")
        supporting_anchor_ids = candidate.get("supporting_source_anchor_ids")
        if not isinstance(supporting_anchor_ids, list):
            raise ValueError(f"{candidate_key} supporting_source_anchor_ids must be a list")
        required_anchor_ids = [primary_anchor_id]
        for anchor_id in supporting_anchor_ids:
            if not isinstance(anchor_id, str) or not anchor_id.strip():
                raise ValueError(f"{candidate_key} supporting_source_anchor_ids must be text")
            required_anchor_ids.append(anchor_id.strip())
        unknown_anchors = sorted(set(required_anchor_ids) - source_anchor_ids)
        if unknown_anchors:
            raise ValueError(
                f"{candidate_key} references unknown source anchors: "
                + ", ".join(unknown_anchors)
            )
        requirements[candidate_key] = list(dict.fromkeys(required_anchor_ids))
    return requirements


def fact_candidate_payloads(
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payload = read_json(fact_candidates_path)
    snapshots = payload.get("source_snapshots")
    candidates = payload.get("relationship_candidates")
    if not isinstance(snapshots, list) or not isinstance(candidates, list):
        raise ValueError(
            "fact candidates must contain source_snapshots and relationship_candidates"
        )
    snapshot_map: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            raise ValueError("source_snapshots entries must be objects")
        anchor_id = require_text(snapshot, "anchor_id")
        snapshot_map[anchor_id] = snapshot
    candidate_map: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("relationship_candidates entries must be objects")
        candidate_key = require_text(candidate, "candidate_key")
        candidate_map[candidate_key] = candidate
    return snapshot_map, candidate_map


def build_intake_template(
    *,
    a202_packet_path: Path = DEFAULT_A202_PACKET,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
    generated_at: str | None = None,
) -> dict[str, Any]:
    requirements = candidate_source_anchor_requirements(fact_candidates_path)
    snapshots, candidates = fact_candidate_payloads(fact_candidates_path)
    required_anchor_ids = sorted(
        {anchor_id for anchor_ids in requirements.values() for anchor_id in anchor_ids}
    )
    return {
        "schema_version": INTAKE_SCHEMA_VERSION,
        "artifact_id": "t1301-a202-release-decision-intake-template",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_ids": ["T1301"],
        "acceptance_ids": ["A202"],
        "bundle_status": "TEMPLATE_ONLY",
        "release_gate_closure_allowed": False,
        "relationship_publication_allowed": False,
        "template_counts_as_clearance": False,
        "source_files": {
            "a202_operator_review_packet": relative(a202_packet_path),
            "a202_operator_review_packet_sha256": sha256_file(a202_packet_path),
            "golden_vertical_fact_candidates": relative(fact_candidates_path),
            "golden_vertical_fact_candidates_sha256": sha256_file(fact_candidates_path),
        },
        "decision_scope": {
            "source_public_reuse": False,
            "relationship_fact_publication": False,
            "graph_edge_publication": False,
            "production_owner_activation": False,
            "legal_release_clearance": False,
        },
        "candidate_source_anchor_requirements": requirements,
        "source_license_reviews": [
            {
                "anchor_id": anchor_id,
                "source_title": str(snapshots[anchor_id].get("title", "")),
                "official_publisher": str(snapshots[anchor_id].get("official_publisher", "")),
                "source_url": str(snapshots[anchor_id].get("url", "")),
                "source_license_status": "PENDING_REVIEW",
                "allowed_use_scope": "",
                "evidence_uri": "",
                "reviewer": "",
                "reviewed_at": "",
                "signature": "",
            }
            for anchor_id in required_anchor_ids
        ],
        "passage_level_relationship_reviews": [
            {
                "candidate_key": candidate_key,
                "subject_candidate_name": str(
                    candidates[candidate_key].get("subject_candidate_name", "")
                ),
                "object_candidate_name": str(
                    candidates[candidate_key].get("object_candidate_name", "")
                ),
                "relationship_type": str(candidates[candidate_key].get("relationship_type", "")),
                "required_anchor_ids": required_anchor_ids,
                "supporting_anchor_ids": required_anchor_ids,
                "supporting_passage_locator": "",
                "counter_evidence_reviewed": None,
                "decision": "PENDING_REVIEW",
                "reviewer": "",
                "reviewed_at": "",
                "signature": "",
            }
            for candidate_key, required_anchor_ids in sorted(requirements.items())
        ],
        "production_owner_signoffs": [
            {
                "candidate_key": candidate_key,
                "owner_actor": "",
                "owner_role": "",
                "authority_scope": "",
                "signed_at": "",
                "signature": "",
            }
            for candidate_key in sorted(requirements)
        ],
        "legal_release_clearance": {
            "legal_reviewer": "",
            "clearance_status": "PENDING_REVIEW",
            "clearance_scope": "",
            "risk_waiver_id_or_opinion_ref": "",
            "signed_at": "",
            "signature": "",
        },
        "attestation": {
            "signed_by": "",
            "signed_at": "",
            "signature": "",
        },
        "validation_policy": {
            "template_only_counts_as_clearance": False,
            "signed_intake_required_for_a202_closure": True,
            "signed_intake_must_cover_all_candidate_source_anchors": True,
            "signed_intake_must_include_counter_evidence_review": True,
            "signed_intake_counts_as_release_ready": False,
            "a209_24h_operator_soak_required_separately": True,
            "a210_brand_clearance_required_separately": True,
        },
        "non_claims": [
            "This template is not source-license approval.",
            "This template is not passage-level relationship approval.",
            "This template is not production owner approval.",
            "This template is not legal release clearance.",
            "This template does not publish relationship facts or graph edges.",
            "This template does not close A202, A209, A210 or release-manager activation.",
        ],
    }


def validate_candidate_source_anchor_coverage(
    bundle: dict[str, Any],
    *,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
    require_passage_anchor_coverage: bool,
) -> dict[str, Any]:
    requirements = candidate_source_anchor_requirements(fact_candidates_path)
    required_source_anchors = {
        anchor_id
        for required_anchor_ids in requirements.values()
        for anchor_id in required_anchor_ids
    }
    reviewed_source_anchor_list = [
        require_text(entry, "anchor_id")
        for entry in bundle["source_license_reviews"]
        if isinstance(entry, dict)
    ]
    duplicate_source_reviews = sorted(
        anchor_id
        for anchor_id in set(reviewed_source_anchor_list)
        if reviewed_source_anchor_list.count(anchor_id) > 1
    )
    if duplicate_source_reviews:
        raise ValueError(
            f"{EXACT_SIGNED_COVERAGE_REJECTION_PREFIXES[0]}: "
            + ", ".join(duplicate_source_reviews)
        )
    reviewed_source_anchors = set(reviewed_source_anchor_list)
    unknown_source_reviews = sorted(reviewed_source_anchors - required_source_anchors)
    if unknown_source_reviews:
        raise ValueError(
            f"{EXACT_SIGNED_COVERAGE_REJECTION_PREFIXES[1]}: "
            + ", ".join(unknown_source_reviews)
        )
    missing_source_reviews = sorted(required_source_anchors - reviewed_source_anchors)
    if missing_source_reviews:
        raise ValueError(
            "source_license_reviews missing candidate source anchors: "
            + ", ".join(missing_source_reviews)
        )

    passage_review_entries: list[tuple[str, dict[str, Any]]] = [
        (require_text(entry, "candidate_key"), entry)
        for entry in bundle["passage_level_relationship_reviews"]
        if isinstance(entry, dict)
    ]
    passage_review_keys = [candidate_key for candidate_key, _ in passage_review_entries]
    duplicate_passage_reviews = sorted(
        candidate_key
        for candidate_key in set(passage_review_keys)
        if passage_review_keys.count(candidate_key) > 1
    )
    if duplicate_passage_reviews:
        raise ValueError(
            f"{EXACT_SIGNED_COVERAGE_REJECTION_PREFIXES[2]}: "
            + ", ".join(duplicate_passage_reviews)
        )
    passage_reviews = dict(passage_review_entries)
    unknown_candidates = sorted(set(passage_reviews) - set(requirements))
    missing_candidates = sorted(set(requirements) - set(passage_reviews))
    if unknown_candidates:
        raise ValueError(
            "passage reviews reference unknown relationship candidates: "
            + ", ".join(unknown_candidates)
        )
    if missing_candidates:
        raise ValueError(
            "passage reviews missing relationship candidates: "
            + ", ".join(missing_candidates)
        )

    coverage: dict[str, Any] = {}
    for candidate_key, required_anchor_ids in sorted(requirements.items()):
        review = passage_reviews[candidate_key]
        supporting_anchor_ids = [
            str(anchor_id).strip()
            for anchor_id in review.get("supporting_anchor_ids", [])
            if isinstance(anchor_id, str) and str(anchor_id).strip()
        ]
        missing_passage_anchors = sorted(set(required_anchor_ids) - set(supporting_anchor_ids))
        if require_passage_anchor_coverage and missing_passage_anchors:
            raise ValueError(
                f"{candidate_key} passage review missing candidate source anchors: "
                + ", ".join(missing_passage_anchors)
            )
        unlicensed_supporting_anchors = sorted(
            set(supporting_anchor_ids) - reviewed_source_anchors
        )
        if require_passage_anchor_coverage and unlicensed_supporting_anchors:
            raise ValueError(
                f"{candidate_key} references anchors without source-license review: "
                + ", ".join(unlicensed_supporting_anchors)
            )
        coverage[candidate_key] = {
            "required_anchor_ids": required_anchor_ids,
            "supporting_anchor_ids": supporting_anchor_ids,
            "missing_passage_anchor_ids": missing_passage_anchors,
        }
    return {
        "fact_candidates": relative(fact_candidates_path),
        "required_source_anchor_ids": sorted(required_source_anchors),
        "candidate_source_anchor_coverage": coverage,
    }


def validate_candidate_owner_signoff_coverage(
    bundle: dict[str, Any],
    *,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
) -> dict[str, Any]:
    requirements = candidate_source_anchor_requirements(fact_candidates_path)
    owner_signoff_candidates = [
        require_text(entry, "candidate_key")
        for entry in bundle["production_owner_signoffs"]
        if isinstance(entry, dict)
    ]
    duplicate_signoffs = sorted(
        candidate_key
        for candidate_key in set(owner_signoff_candidates)
        if owner_signoff_candidates.count(candidate_key) > 1
    )
    if duplicate_signoffs:
        raise ValueError(
            f"{EXACT_SIGNED_COVERAGE_REJECTION_PREFIXES[3]}: "
            + ", ".join(duplicate_signoffs)
        )
    signed_candidates = set(owner_signoff_candidates)
    unknown_signoffs = sorted(signed_candidates - set(requirements))
    if unknown_signoffs:
        raise ValueError(
            f"{EXACT_SIGNED_COVERAGE_REJECTION_PREFIXES[4]}: "
            + ", ".join(unknown_signoffs)
        )
    missing_signoffs = sorted(set(requirements) - signed_candidates)
    if missing_signoffs:
        raise ValueError(
            f"{EXACT_SIGNED_COVERAGE_REJECTION_PREFIXES[5]}: "
            + ", ".join(missing_signoffs)
        )
    return {
        "owner_signoff_candidate_keys": sorted(signed_candidates),
    }


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


def validate_template_bundle(
    bundle: dict[str, Any],
    *,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
) -> None:
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
    validate_candidate_source_anchor_coverage(
        bundle,
        fact_candidates_path=fact_candidates_path,
        require_passage_anchor_coverage=False,
    )
    validate_candidate_owner_signoff_coverage(
        bundle,
        fact_candidates_path=fact_candidates_path,
    )


def validate_signed_decision_bundle(
    bundle: dict[str, Any],
    *,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
) -> dict[str, Any]:
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
    candidate_anchor_summary = validate_candidate_source_anchor_coverage(
        bundle,
        fact_candidates_path=fact_candidates_path,
        require_passage_anchor_coverage=True,
    )
    owner_signoff_summary = validate_candidate_owner_signoff_coverage(
        bundle,
        fact_candidates_path=fact_candidates_path,
    )
    return {
        "source_license_reviews": len(bundle["source_license_reviews"]),
        "passage_reviews": len(bundle["passage_level_relationship_reviews"]),
        "owner_signoffs": len(bundle["production_owner_signoffs"]),
        "legal_clearance_status": legal["clearance_status"],
        "brand_decision": brand["decision"],
        **candidate_anchor_summary,
        **owner_signoff_summary,
    }


def validate_intake_template(
    payload: dict[str, Any],
    *,
    a202_packet_path: Path = DEFAULT_A202_PACKET,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
) -> None:
    expected = build_intake_template(
        a202_packet_path=a202_packet_path,
        fact_candidates_path=fact_candidates_path,
        generated_at=payload.get("generated_at"),
    )
    if payload != expected:
        raise ValueError("A202 intake template drift")
    if payload.get("bundle_status") != "TEMPLATE_ONLY":
        raise ValueError("A202 intake template bundle_status must be TEMPLATE_ONLY")
    if payload.get("release_gate_closure_allowed") is not False:
        raise ValueError("A202 intake template must not allow gate closure")
    if payload.get("relationship_publication_allowed") is not False:
        raise ValueError("A202 intake template must not allow relationship publication")
    if payload.get("template_counts_as_clearance") is not False:
        raise ValueError("A202 intake template must not count as clearance")


def validate_signed_intake_bundle(
    payload: dict[str, Any],
    *,
    a202_packet_path: Path = DEFAULT_A202_PACKET,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
) -> dict[str, Any]:
    expected_template = build_intake_template(
        a202_packet_path=a202_packet_path,
        fact_candidates_path=fact_candidates_path,
        generated_at=payload.get("generated_at"),
    )
    for key in (
        "schema_version",
        "artifact_id",
        "system_name",
        "system_en_name",
        "system_zh_name",
        "task_ids",
        "acceptance_ids",
        "source_files",
        "decision_scope",
        "candidate_source_anchor_requirements",
    ):
        if payload.get(key) != expected_template.get(key):
            raise ValueError(f"A202 signed intake field drift: {key}")
    if payload.get("bundle_status") == "TEMPLATE_ONLY":
        raise ValueError("A202 intake template is not signed release evidence")
    if payload.get("bundle_status") != SIGNED_A202_INTAKE_STATUS:
        raise ValueError(f"A202 signed intake bundle_status must be {SIGNED_A202_INTAKE_STATUS}")
    if payload.get("release_gate_closure_allowed") is not True:
        raise ValueError("A202 signed intake must explicitly allow A202 gate closure")
    if payload.get("relationship_publication_allowed") is not True:
        raise ValueError("A202 signed intake must explicitly allow relationship publication")
    for entry in payload["source_license_reviews"]:
        for field in REQUIRED_SECTIONS["source_license_reviews"]:
            require_text(entry, field)
        if entry["source_license_status"] not in SIGNED_SOURCE_LICENSE_STATUSES:
            raise ValueError(f"unsupported source license status: {entry['source_license_status']}")
    for entry in payload["passage_level_relationship_reviews"]:
        if entry.get("required_anchor_ids") != (
            expected_template["candidate_source_anchor_requirements"][entry["candidate_key"]]
        ):
            raise ValueError(f"{entry['candidate_key']} required_anchor_ids drift")
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
    for entry in payload["production_owner_signoffs"]:
        for field in REQUIRED_SECTIONS["production_owner_signoffs"]:
            require_text(entry, field)
    legal = payload["legal_release_clearance"]
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
    attestation = payload["attestation"]
    for field in ("signed_by", "signed_at", "signature"):
        require_text(attestation, field)
    coverage = validate_candidate_source_anchor_coverage(
        payload,
        fact_candidates_path=fact_candidates_path,
        require_passage_anchor_coverage=True,
    )
    owner_signoff_summary = validate_candidate_owner_signoff_coverage(
        payload,
        fact_candidates_path=fact_candidates_path,
    )
    return {
        "source_license_reviews": len(payload["source_license_reviews"]),
        "passage_reviews": len(payload["passage_level_relationship_reviews"]),
        "owner_signoffs": len(payload["production_owner_signoffs"]),
        "legal_clearance_status": legal["clearance_status"],
        **coverage,
        **owner_signoff_summary,
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
    intake_template_path: Path = DEFAULT_INTAKE_TEMPLATE,
    template_path: Path = DEFAULT_TEMPLATE,
    signed_contract_test_path: Path = DEFAULT_SIGNED_CONTRACT_TEST,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
    generated_at: str | None = None,
) -> dict[str, Any]:
    a202_packet = read_json(a202_packet_path)
    a210_preflight = read_json(a210_preflight_path)
    intake_template = read_json(intake_template_path)
    validate_intake_template(
        intake_template,
        a202_packet_path=a202_packet_path,
        fact_candidates_path=fact_candidates_path,
    )
    template = read_json(template_path)
    validate_template_bundle(template, fact_candidates_path=fact_candidates_path)
    signed_contract_test = read_json(signed_contract_test_path)
    signed_contract_test_summary = validate_signed_decision_bundle(
        signed_contract_test,
        fact_candidates_path=fact_candidates_path,
    )
    a202_gates = gate_statuses(a202_packet)
    a210_current = a210_preflight.get("current_clearance_status") or {}
    candidate_anchor_requirements = candidate_source_anchor_requirements(fact_candidates_path)
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
            "a202_release_decision_intake_template": relative(intake_template_path),
            "a202_release_decision_intake_template_sha256": sha256_file(intake_template_path),
            "decision_bundle_template": relative(template_path),
            "decision_bundle_template_sha256": sha256_file(template_path),
            "signed_contract_test_bundle": relative(signed_contract_test_path),
            "signed_contract_test_bundle_sha256": sha256_file(signed_contract_test_path),
            "golden_vertical_fact_candidates": relative(fact_candidates_path),
            "golden_vertical_fact_candidates_sha256": sha256_file(fact_candidates_path),
        },
        "signed_contract_test_summary": signed_contract_test_summary,
        "candidate_source_anchor_requirements": candidate_anchor_requirements,
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
            "a202_intake_template_counts_as_clearance": False,
            "signed_bundle_required_for_a202_a210_closure": True,
            "signed_a202_intake_required_for_source_owner_legal_closure": True,
            "contract_test_signatures_are_not_clearance": True,
            "signed_contract_test_counts_as_clearance": False,
            "production_owner_publication_requires_signed_bundle": True,
            "publication_passage_reviews_must_cover_candidate_source_anchors": True,
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
    intake_template_path: Path = DEFAULT_INTAKE_TEMPLATE,
    template_path: Path = DEFAULT_TEMPLATE,
    signed_contract_test_path: Path = DEFAULT_SIGNED_CONTRACT_TEST,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
) -> None:
    expected = build_contract(
        a202_packet_path=a202_packet_path,
        a210_preflight_path=a210_preflight_path,
        intake_template_path=intake_template_path,
        template_path=template_path,
        signed_contract_test_path=signed_contract_test_path,
        fact_candidates_path=fact_candidates_path,
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
        "candidate_source_anchor_requirements",
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
        intake_template_path=args.intake_template,
        template_path=args.template,
        signed_contract_test_path=args.signed_contract_test,
        fact_candidates_path=args.fact_candidates,
    )
    validate_contract(
        contract,
        a202_packet_path=args.a202_packet,
        a210_preflight_path=args.a210_preflight,
        intake_template_path=args.intake_template,
        template_path=args.template,
        signed_contract_test_path=args.signed_contract_test,
        fact_candidates_path=args.fact_candidates,
    )
    write_json(args.output, contract)
    print(json.dumps({"generated": True, "artifact": relative(args.output)}, indent=2))


def validate(args: argparse.Namespace) -> None:
    validate_contract(
        read_json(args.output),
        a202_packet_path=args.a202_packet,
        a210_preflight_path=args.a210_preflight,
        intake_template_path=args.intake_template,
        template_path=args.template,
        signed_contract_test_path=args.signed_contract_test,
        fact_candidates_path=args.fact_candidates,
    )
    print(json.dumps({"valid": True, "artifact": relative(args.output)}, indent=2))


def generate_template(args: argparse.Namespace) -> None:
    payload = build_intake_template(
        a202_packet_path=args.a202_packet,
        fact_candidates_path=args.fact_candidates,
    )
    validate_intake_template(
        payload,
        a202_packet_path=args.a202_packet,
        fact_candidates_path=args.fact_candidates,
    )
    write_json(args.output, payload)
    print(
        json.dumps(
            {
                "generated": True,
                "artifact": relative(args.output),
                "status": payload["bundle_status"],
                "release_gate_closure_allowed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def validate_template(args: argparse.Namespace) -> None:
    validate_intake_template(
        read_json(args.output),
        a202_packet_path=args.a202_packet,
        fact_candidates_path=args.fact_candidates,
    )
    print(
        json.dumps(
            {
                "valid": True,
                "artifact": relative(args.output),
                "release_gate_closure_allowed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def validate_signed_intake(args: argparse.Namespace) -> None:
    source_boundary = validate_signed_intake_source_path(args.bundle)
    summary = validate_signed_intake_bundle(
        read_json(args.bundle),
        a202_packet_path=args.a202_packet,
        fact_candidates_path=args.fact_candidates,
    )
    print(
        json.dumps(
            {
                "valid": True,
                "bundle": relative(args.bundle),
                "a202_clearance_complete": True,
                "release_ready": False,
                "signed_intake_source_boundary": source_boundary,
                "remaining_external_gates": [
                    "A210_brand_clearance",
                    "A026_A027_production_gold_labels",
                    "A209_24h_operator_soak",
                    "release_manager_activation",
                ],
                **summary,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


def validate_bundle(args: argparse.Namespace) -> None:
    bundle = read_json(args.bundle)
    fact_candidates_path = getattr(args, "fact_candidates", DEFAULT_FACT_CANDIDATES)
    if args.template_only:
        validate_template_bundle(bundle, fact_candidates_path=fact_candidates_path)
        result = {"valid": True, "bundle": relative(args.bundle), "release_ready": False}
    else:
        summary = validate_signed_decision_bundle(
            bundle,
            fact_candidates_path=fact_candidates_path,
        )
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
        child.add_argument("--intake-template", type=Path, default=DEFAULT_INTAKE_TEMPLATE)
        child.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
        child.add_argument(
            "--signed-contract-test",
            type=Path,
            default=DEFAULT_SIGNED_CONTRACT_TEST,
        )
        child.add_argument("--fact-candidates", type=Path, default=DEFAULT_FACT_CANDIDATES)
        child.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    for name in ("generate-template", "validate-template"):
        child = sub.add_parser(name)
        child.add_argument("--a202-packet", type=Path, default=DEFAULT_A202_PACKET)
        child.add_argument("--fact-candidates", type=Path, default=DEFAULT_FACT_CANDIDATES)
        child.add_argument("--output", type=Path, default=DEFAULT_INTAKE_TEMPLATE)
    signed_intake = sub.add_parser("validate-signed-intake")
    signed_intake.add_argument("--bundle", type=Path, default=DEFAULT_INTAKE_TEMPLATE)
    signed_intake.add_argument("--a202-packet", type=Path, default=DEFAULT_A202_PACKET)
    signed_intake.add_argument("--fact-candidates", type=Path, default=DEFAULT_FACT_CANDIDATES)
    bundle = sub.add_parser("validate-bundle")
    bundle.add_argument("--bundle", type=Path, default=DEFAULT_TEMPLATE)
    bundle.add_argument("--fact-candidates", type=Path, default=DEFAULT_FACT_CANDIDATES)
    bundle.add_argument("--template-only", action="store_true")
    args = parser.parse_args()
    if args.command == "generate":
        generate(args)
    elif args.command == "validate":
        validate(args)
    elif args.command == "generate-template":
        generate_template(args)
    elif args.command == "validate-template":
        validate_template(args)
    elif args.command == "validate-signed-intake":
        validate_signed_intake(args)
    else:
        validate_bundle(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
