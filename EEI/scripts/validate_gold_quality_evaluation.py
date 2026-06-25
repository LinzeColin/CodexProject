#!/usr/bin/env python3
"""Generate and validate the A026/A027 gold-quality evaluation contract.

The repository fixture is intentionally small and fail-closed. It proves the
metric formula, source-coverage accounting, and acceptance wiring, but it must
not close A026 or A027 until a production gold set reaches the required sample
sizes and thresholds.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "eei-gold-quality-evaluation-contract-v1"
INTAKE_TEMPLATE_SCHEMA_VERSION = "eei-gold-quality-intake-template-v1"
LABEL_SCHEMA_VERSION = "eei-gold-quality-labels-v1"
DEFAULT_LABELS = ROOT / "tests/fixtures/gold_quality/golden_vertical_gold_labels_sample.json"
DEFAULT_A026_OUTPUT = (
    ROOT / "artifacts/tests/a026/t904_entity_resolution_gold_evaluation_contract.json"
)
DEFAULT_A027_OUTPUT = (
    ROOT / "artifacts/tests/a027/t904_relationship_gold_evaluation_contract.json"
)
DEFAULT_INTAKE_TEMPLATE_OUTPUT = (
    ROOT / "artifacts/tests/a026/t904_a026_a027_production_gold_label_intake_template.json"
)
DEFAULT_OPERATOR_PACKET_OUTPUT = (
    ROOT / "artifacts/tests/a026/t904_a026_a027_operator_labeling_packet.json"
)
DEFAULT_REVIEW_PACKET = ROOT / "artifacts/tests/a202/t1301_operator_review_packet_contract.json"
DEFAULT_FACT_CANDIDATES = ROOT / "data/golden_vertical_fact_candidates.json"

ENTITY_MIN_CASES = 50
ENTITY_MIN_PRECISION = 0.95
RELATIONSHIP_MIN_CASES = 100
RELATIONSHIP_MIN_PRECISION = 0.90
SOURCE_COVERAGE_MIN = 1.0

PRODUCTION_GOLD_REQUIRED_TEXT_FIELDS = (
    "evidence_id",
    "dataset_owner",
    "owner_role",
    "sampling_frame",
    "labeling_protocol_ref",
    "label_freeze_sha256",
    "reviewer",
    "reviewed_at",
    "reviewer_signature_hash",
    "source_license_review_ref",
    "passage_review_policy_ref",
)
PRODUCTION_GOLD_REQUIRED_LIST_FIELDS = (
    "source_document_refs",
    "labeler_qualification_refs",
)
PRODUCTION_GOLD_FORBIDDEN_REPOSITORY_REF_PREFIXES = (
    "data/",
    "tests/",
    "fixture://",
)
PRODUCTION_GOLD_FORBIDDEN_LABELERS = {
    "fixture_reviewer",
}


@dataclass(frozen=True)
class QualityStats:
    sample_count: int
    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int
    precision: float
    recall: float
    source_coverage_min: float
    source_coverage_avg: float


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


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def required_text(row: dict[str, Any], key: str, *, case_id: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{case_id} missing required text field {key}")
    return value.strip()


def required_list(row: dict[str, Any], key: str, *, case_id: str) -> list[str]:
    value = row.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{case_id} missing required non-empty list field {key}")
    result = [str(item).strip() for item in value if str(item).strip()]
    if len(result) != len(value):
        raise ValueError(f"{case_id} list field {key} must not contain empty values")
    return result


def reject_repository_fixture_refs(refs: list[str], *, case_id: str, field: str) -> None:
    for ref in refs:
        if ref.startswith(PRODUCTION_GOLD_FORBIDDEN_REPOSITORY_REF_PREFIXES):
            raise ValueError(
                f"{case_id} {field} must not use repository fixture reference {ref!r} "
                "for production_gold_set"
            )


def reject_fixture_labeler(labeler: str, *, case_id: str) -> None:
    normalized = labeler.strip().lower()
    if normalized in PRODUCTION_GOLD_FORBIDDEN_LABELERS or normalized.startswith("fixture_"):
        raise ValueError(
            f"{case_id} labeler {labeler!r} is not allowed for production_gold_set"
        )


def production_intake_policy() -> dict[str, Any]:
    return {
        "allow_flag_required": "--allow-production-gold-set",
        "required_text_fields": list(PRODUCTION_GOLD_REQUIRED_TEXT_FIELDS),
        "required_list_fields": list(PRODUCTION_GOLD_REQUIRED_LIST_FIELDS),
        "required_boolean_fields": {
            "excludes_repository_fixtures": True,
            "operator_supplied_labels": True,
            "synthetic_or_fixture_labels": False,
        },
        "forbidden_repository_ref_prefixes": list(
            PRODUCTION_GOLD_FORBIDDEN_REPOSITORY_REF_PREFIXES
        ),
        "forbidden_labelers": sorted(PRODUCTION_GOLD_FORBIDDEN_LABELERS),
        "release_boundary": {
            "gold_quality_pass_only_closes": ["A026", "A027"],
            "does_not_close": ["A202", "A209", "A210", "release_manager_activation"],
            "relationship_publication_allowed": False,
        },
    }


def production_gold_evidence_template() -> dict[str, Any]:
    return {
        **{field: "<required>" for field in PRODUCTION_GOLD_REQUIRED_TEXT_FIELDS},
        "source_document_refs": ["<required-source-document-ref>"],
        "labeler_qualification_refs": ["<required-labeler-qualification-ref>"],
        "excludes_repository_fixtures": True,
        "operator_supplied_labels": True,
        "synthetic_or_fixture_labels": False,
    }


def entity_resolution_case_template() -> dict[str, Any]:
    return {
        "case_id": "ENT-PROD-000",
        "labeler": "<required-labeler>",
        "labeled_at": "<required-utc-timestamp>",
        "expected_entity_id": "<required-or-empty-string-for-true-negative>",
        "predicted_entity_id": "<required-or-empty-string-for-no-prediction>",
        "evidence_refs": ["<required-evidence-ref>"],
        "source_coverage": {
            "required_source_ids": ["<required-source-id>"],
            "observed_source_ids": ["<observed-source-id>"],
            "counter_evidence_reviewed": True,
        },
    }


def relationship_case_template() -> dict[str, Any]:
    return {
        "case_id": "REL-PROD-000",
        "labeler": "<required-labeler>",
        "labeled_at": "<required-utc-timestamp>",
        "expected_relation_present": True,
        "predicted_relation_present": True,
        "expected_relationship_key": "<subject|predicate|object>",
        "predicted_relationship_key": "<subject|predicate|object-or-empty-string>",
        "evidence_refs": ["<required-evidence-ref>"],
        "source_coverage": {
            "required_source_ids": ["<required-source-id>"],
            "observed_source_ids": ["<observed-source-id>"],
            "counter_evidence_reviewed": True,
        },
    }


def build_intake_template(*, generated_at: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": INTAKE_TEMPLATE_SCHEMA_VERSION,
        "artifact_id": "t904-a026-a027-production-gold-label-intake-template",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "task_id": "T904",
        "acceptance_ids": ["A026", "A027"],
        "status": "TEMPLATE_ONLY",
        "release_gate_closure_allowed": False,
        "production_claim_allowed": False,
        "relationship_publication_allowed": False,
        "scope": "golden-vertical:nvidia",
        "thresholds": {
            "A026": {
                "minimum_cases": ENTITY_MIN_CASES,
                "minimum_precision": ENTITY_MIN_PRECISION,
                "minimum_source_coverage": SOURCE_COVERAGE_MIN,
            },
            "A027": {
                "minimum_cases": RELATIONSHIP_MIN_CASES,
                "minimum_precision": RELATIONSHIP_MIN_PRECISION,
                "minimum_source_coverage": SOURCE_COVERAGE_MIN,
            },
        },
        "production_gold_evidence_schema": production_intake_policy(),
        "label_payload_skeleton": {
            "schema_version": LABEL_SCHEMA_VERSION,
            "system_name": "EEI",
            "scope": "golden-vertical:nvidia",
            "dataset_id": "<operator-production-gold-dataset-id>",
            "fixture_policy": {
                "production_gold_set": True,
                "release_clearance": False,
                "relationship_publication": False,
            },
            "production_gold_evidence": production_gold_evidence_template(),
            "entity_resolution_cases": {
                "minimum_required_cases": ENTITY_MIN_CASES,
                "case_template": entity_resolution_case_template(),
            },
            "relationship_cases": {
                "minimum_required_cases": RELATIONSHIP_MIN_CASES,
                "case_template": relationship_case_template(),
            },
        },
        "validation_commands": {
            "generate_contract": (
                "python scripts/validate_gold_quality_evaluation.py generate "
                "--labels <operator-production-gold-labels.json> "
                "--allow-production-gold-set"
            ),
            "validate_contract": "python scripts/validate_gold_quality_evaluation.py validate",
            "release_manager_gate": (
                "python scripts/validate_release_manager_activation.py validate"
            ),
        },
        "non_claims": [
            "This template is not a production gold label set.",
            "This template does not close A026 or A027.",
            "This template does not close A202, A209, A210 or release-manager activation.",
            "Filled labels still require validate_gold_quality_evaluation.py with "
            "--allow-production-gold-set and complete production_gold_evidence.",
        ],
    }


def sha256_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def anchor_lookup(
    review_packet: dict[str, Any],
    fact_candidates: dict[str, Any],
) -> dict[str, dict]:
    anchors: dict[str, dict] = {}
    for anchor in review_packet.get("anchors", []):
        if isinstance(anchor, dict) and isinstance(anchor.get("anchor_id"), str):
            anchors[anchor["anchor_id"]] = anchor
    for snapshot in fact_candidates.get("source_snapshots", []):
        if isinstance(snapshot, dict) and isinstance(snapshot.get("anchor_id"), str):
            anchors[snapshot["anchor_id"]] = snapshot
    return anchors


def entity_terms_from_sources(
    review_packet: dict[str, Any],
    fact_candidates: dict[str, Any],
) -> list[dict[str, Any]]:
    anchors = anchor_lookup(review_packet, fact_candidates)
    terms: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    source_snapshots = fact_candidates.get("source_snapshots", [])
    for snapshot in source_snapshots:
        if not isinstance(snapshot, dict):
            continue
        anchor_id = str(snapshot.get("anchor_id") or "").strip()
        raw_terms = str(snapshot.get("expected_entities_or_stages") or "")
        for raw in raw_terms.split(";"):
            value = raw.strip()
            if not value:
                continue
            key = (value.lower(), anchor_id)
            if key in seen:
                continue
            seen.add(key)
            terms.append(
                {
                    "input_text": value,
                    "source_anchor_id": anchor_id,
                    "source_ref": f"data/golden_vertical_fact_candidates.json#{anchor_id}",
                    "official_publisher": snapshot.get("official_publisher"),
                    "source_title": snapshot.get("title"),
                    "source_url": snapshot.get("url") or snapshot.get("source_url"),
                }
            )
    for anchor in anchors.values():
        title = str(anchor.get("title") or "").strip()
        if not title:
            continue
        anchor_id = str(anchor.get("anchor_id") or "").strip()
        key = (title.lower(), anchor_id)
        if key in seen:
            continue
        seen.add(key)
        terms.append(
            {
                "input_text": title,
                "source_anchor_id": anchor_id,
                "source_ref": (
                    "artifacts/tests/a202/t1301_operator_review_packet_contract.json"
                    f"#{anchor_id}"
                ),
                "official_publisher": anchor.get("official_publisher"),
                "source_title": anchor.get("title"),
                "source_url": anchor.get("source_url"),
            }
        )
    if not terms:
        raise ValueError(
            "operator labeling packet requires at least one source-derived entity term"
        )
    return terms


def relationship_candidates_from_sources(
    review_packet: dict[str, Any],
    fact_candidates: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = review_packet.get("relationship_candidate_review_queue") or fact_candidates.get(
        "relationship_candidates"
    )
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("operator labeling packet requires relationship candidates")
    result = [candidate for candidate in candidates if isinstance(candidate, dict)]
    if not result:
        raise ValueError("operator labeling packet relationship candidates must be objects")
    return result


def build_entity_labeling_slots(
    review_packet: dict[str, Any],
    fact_candidates: dict[str, Any],
) -> list[dict[str, Any]]:
    terms = entity_terms_from_sources(review_packet, fact_candidates)
    slots: list[dict[str, Any]] = []
    for index in range(ENTITY_MIN_CASES):
        term = terms[index % len(terms)]
        slots.append(
            {
                "slot_id": f"ENT-PROD-SLOT-{index + 1:03d}",
                "label_status": "OPERATOR_TO_LABEL",
                "input_text": term["input_text"],
                "predicted_entity_id": "",
                "operator_expected_entity_id": "",
                "operator_true_negative": None,
                "required_evidence_refs": [term["source_ref"]],
                "source_coverage": {
                    "required_source_ids": [term["source_anchor_id"]],
                    "observed_source_ids": [],
                    "counter_evidence_reviewed": None,
                },
                "source_context": {
                    "official_publisher": term.get("official_publisher"),
                    "source_title": term.get("source_title"),
                    "source_url": term.get("source_url"),
                },
                "required_operator_fields": [
                    "labeler",
                    "labeled_at",
                    "expected_entity_id",
                    "predicted_entity_id",
                    "evidence_refs",
                    "source_coverage.counter_evidence_reviewed",
                ],
            }
        )
    return slots


def build_relationship_labeling_slots(
    review_packet: dict[str, Any],
    fact_candidates: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = relationship_candidates_from_sources(review_packet, fact_candidates)
    slots: list[dict[str, Any]] = []
    for index in range(RELATIONSHIP_MIN_CASES):
        candidate = candidates[index % len(candidates)]
        candidate_key = str(candidate.get("candidate_key") or f"candidate-{index + 1}")
        required_anchor_ids = candidate.get("required_source_anchor_ids") or [
            item
            for item in [
                candidate.get("source_anchor_id"),
                *(candidate.get("supporting_source_anchor_ids") or []),
            ]
            if item
        ]
        slots.append(
            {
                "slot_id": f"REL-PROD-SLOT-{index + 1:03d}",
                "candidate_key": candidate_key,
                "label_status": "OPERATOR_TO_LABEL",
                "subject_candidate_name": candidate.get("subject_candidate_name"),
                "relationship_type": candidate.get("relationship_type"),
                "object_candidate_name": candidate.get("object_candidate_name"),
                "predicted_relation_present": True,
                "predicted_relationship_key": candidate_key,
                "operator_expected_relation_present": None,
                "operator_expected_relationship_key": "",
                "required_evidence_refs": [
                    f"data/golden_vertical_fact_candidates.json#{candidate_key}",
                    "artifacts/tests/a202/t1301_operator_review_packet_contract.json",
                ],
                "required_source_anchor_ids": required_anchor_ids,
                "source_coverage": {
                    "required_source_ids": required_anchor_ids,
                    "observed_source_ids": [],
                    "counter_evidence_reviewed": None,
                },
                "support_excerpt": candidate.get("support_excerpt"),
                "counter_evidence_prompt": (
                    "Operator must review contrary official evidence before setting "
                    "counter_evidence_reviewed=true."
                ),
                "required_operator_fields": [
                    "labeler",
                    "labeled_at",
                    "expected_relation_present",
                    "predicted_relation_present",
                    "expected_relationship_key",
                    "predicted_relationship_key",
                    "evidence_refs",
                    "source_coverage.counter_evidence_reviewed",
                ],
            }
        )
    return slots


def build_operator_labeling_packet(
    *,
    review_packet_path: Path = DEFAULT_REVIEW_PACKET,
    fact_candidates_path: Path = DEFAULT_FACT_CANDIDATES,
    generated_at: str | None = None,
) -> dict[str, Any]:
    review_packet = read_json(review_packet_path)
    fact_candidates = read_json(fact_candidates_path)
    return {
        "schema_version": "eei-a026-a027-operator-labeling-packet-v1",
        "artifact_id": "t904-a026-a027-operator-labeling-packet",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "system_zh_name": "商域图谱",
        "task_id": "T904",
        "acceptance_ids": ["A026", "A027"],
        "status": "READY_FOR_OPERATOR_LABELING",
        "scope": "golden-vertical:nvidia",
        "production_gold_set": False,
        "release_gate_closure_allowed": False,
        "production_claim_allowed": False,
        "relationship_publication_allowed": False,
        "label_payload_generated": False,
        "thresholds": {
            "A026": {
                "minimum_cases": ENTITY_MIN_CASES,
                "minimum_precision": ENTITY_MIN_PRECISION,
                "minimum_source_coverage": SOURCE_COVERAGE_MIN,
            },
            "A027": {
                "minimum_cases": RELATIONSHIP_MIN_CASES,
                "minimum_precision": RELATIONSHIP_MIN_PRECISION,
                "minimum_source_coverage": SOURCE_COVERAGE_MIN,
            },
        },
        "source_files": {
            "a202_operator_review_packet": relative(review_packet_path),
            "a202_operator_review_packet_sha256": sha256_file(review_packet_path),
            "golden_vertical_fact_candidates": relative(fact_candidates_path),
            "golden_vertical_fact_candidates_sha256": sha256_file(fact_candidates_path),
            "gold_quality_intake_template": relative(DEFAULT_INTAKE_TEMPLATE_OUTPUT),
            "gold_quality_intake_template_sha256": (
                sha256_file(DEFAULT_INTAKE_TEMPLATE_OUTPUT)
                if DEFAULT_INTAKE_TEMPLATE_OUTPUT.exists()
                else None
            ),
        },
        "operator_payload_requirements": {
            "schema_version": LABEL_SCHEMA_VERSION,
            "production_gold_evidence": production_intake_policy(),
            "entity_resolution_cases_required": ENTITY_MIN_CASES,
            "relationship_cases_required": RELATIONSHIP_MIN_CASES,
            "forbidden": {
                "repository_fixture_refs": list(PRODUCTION_GOLD_FORBIDDEN_REPOSITORY_REF_PREFIXES),
                "fixture_labelers": sorted(PRODUCTION_GOLD_FORBIDDEN_LABELERS),
            },
        },
        "entity_resolution_labeling_slots": build_entity_labeling_slots(
            review_packet,
            fact_candidates,
        ),
        "relationship_labeling_slots": build_relationship_labeling_slots(
            review_packet,
            fact_candidates,
        ),
        "validation_commands": {
            "convert_completed_packet_to_labels": (
                "Fill this packet into an eei-gold-quality-labels-v1 JSON payload; "
                "this repository does not auto-convert incomplete slots."
            ),
            "generate_contract": (
                "python scripts/validate_gold_quality_evaluation.py generate "
                "--labels <operator-production-gold-labels.json> "
                "--allow-production-gold-set"
            ),
            "validate_contract": "python scripts/validate_gold_quality_evaluation.py validate",
        },
        "non_claims": [
            "This packet is an operator labeling worksheet, not a production gold label set.",
            "This packet does not close A026 or A027.",
            "Blank slots, repository fixtures, unsigned labels and unreviewed payloads "
            "do not count as production evidence.",
            "A202 source/legal/owner clearance, A209 24h soak and A210 brand clearance "
            "remain separate gates.",
        ],
    }


def validate_operator_labeling_packet(packet: dict[str, Any]) -> None:
    if packet.get("schema_version") != "eei-a026-a027-operator-labeling-packet-v1":
        raise ValueError("operator labeling packet schema_version drift")
    if packet.get("status") != "READY_FOR_OPERATOR_LABELING":
        raise ValueError("operator labeling packet status drift")
    for key in (
        "production_gold_set",
        "release_gate_closure_allowed",
        "production_claim_allowed",
        "relationship_publication_allowed",
        "label_payload_generated",
    ):
        if packet.get(key) is not False:
            raise ValueError(f"operator labeling packet {key} must be false")
    entity_slots = packet.get("entity_resolution_labeling_slots")
    relationship_slots = packet.get("relationship_labeling_slots")
    if not isinstance(entity_slots, list) or len(entity_slots) != ENTITY_MIN_CASES:
        raise ValueError("operator labeling packet must contain exactly 50 entity slots")
    if (
        not isinstance(relationship_slots, list)
        or len(relationship_slots) != RELATIONSHIP_MIN_CASES
    ):
        raise ValueError("operator labeling packet must contain exactly 100 relationship slots")
    if len({slot.get("slot_id") for slot in entity_slots}) != ENTITY_MIN_CASES:
        raise ValueError("entity slot ids must be unique")
    if len({slot.get("slot_id") for slot in relationship_slots}) != RELATIONSHIP_MIN_CASES:
        raise ValueError("relationship slot ids must be unique")
    for slot in entity_slots + relationship_slots:
        if slot.get("label_status") != "OPERATOR_TO_LABEL":
            raise ValueError("all labeling slots must remain OPERATOR_TO_LABEL")
        required_refs = slot.get("required_evidence_refs")
        if not isinstance(required_refs, list) or not required_refs:
            raise ValueError("labeling slots require evidence refs")
        coverage = slot.get("source_coverage")
        if not isinstance(coverage, dict) or not coverage.get("required_source_ids"):
            raise ValueError("labeling slots require source coverage")
        if coverage.get("counter_evidence_reviewed") is not None:
            raise ValueError("blank operator slots must not pre-claim counter-evidence review")


def validate_production_gold_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    evidence = payload.get("production_gold_evidence")
    if not isinstance(evidence, dict):
        raise ValueError("production_gold_evidence is required for production_gold_set")
    for field in PRODUCTION_GOLD_REQUIRED_TEXT_FIELDS:
        required_text(evidence, field, case_id="production_gold_evidence")
    for field in PRODUCTION_GOLD_REQUIRED_LIST_FIELDS:
        required_list(evidence, field, case_id="production_gold_evidence")
    if evidence.get("excludes_repository_fixtures") is not True:
        raise ValueError("production_gold_evidence.excludes_repository_fixtures must be true")
    if evidence.get("operator_supplied_labels") is not True:
        raise ValueError("production_gold_evidence.operator_supplied_labels must be true")
    if evidence.get("synthetic_or_fixture_labels") is not False:
        raise ValueError("production_gold_evidence.synthetic_or_fixture_labels must be false")
    reject_repository_fixture_refs(
        required_list(evidence, "source_document_refs", case_id="production_gold_evidence"),
        case_id="production_gold_evidence",
        field="source_document_refs",
    )
    reject_repository_fixture_refs(
        required_list(
            evidence,
            "labeler_qualification_refs",
            case_id="production_gold_evidence",
        ),
        case_id="production_gold_evidence",
        field="labeler_qualification_refs",
    )
    return evidence


def source_coverage(row: dict[str, Any], *, case_id: str) -> float:
    coverage = row.get("source_coverage")
    if not isinstance(coverage, dict):
        raise ValueError(f"{case_id} missing source_coverage")
    required = coverage.get("required_source_ids")
    observed = coverage.get("observed_source_ids")
    if not isinstance(required, list) or not required:
        raise ValueError(f"{case_id} source_coverage.required_source_ids must be non-empty")
    if not isinstance(observed, list):
        raise ValueError(f"{case_id} source_coverage.observed_source_ids must be a list")
    if coverage.get("counter_evidence_reviewed") is not True:
        raise ValueError(f"{case_id} counter_evidence_reviewed must be true")
    required_set = {str(item) for item in required}
    observed_set = {str(item) for item in observed}
    return len(required_set & observed_set) / len(required_set)


def validate_label_payload(
    payload: dict[str, Any],
    *,
    allow_production_gold_set: bool = False,
) -> None:
    if payload.get("schema_version") != LABEL_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {LABEL_SCHEMA_VERSION}")
    if payload.get("system_name") != "EEI":
        raise ValueError("system_name must be EEI")
    fixture_policy = payload.get("fixture_policy")
    if not isinstance(fixture_policy, dict):
        raise ValueError("fixture_policy must be present")
    production_gold_set = fixture_policy.get("production_gold_set") is True
    if production_gold_set and not allow_production_gold_set:
        raise ValueError("production_gold_set requires --allow-production-gold-set")
    for key in ("release_clearance", "relationship_publication"):
        if fixture_policy.get(key) is not False:
            raise ValueError(f"fixture_policy.{key} must remain false for gold-quality evidence")
    if production_gold_set:
        validate_production_gold_evidence(payload)
    elif fixture_policy.get("production_gold_set") is not False:
        raise ValueError("fixture_policy.production_gold_set must be boolean false or true")
    for section in ("entity_resolution_cases", "relationship_cases"):
        entries = payload.get(section)
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"{section} must be a non-empty list")
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"{section} entries must be objects")
            case_id = required_text(entry, "case_id", case_id=section)
            if case_id in seen:
                raise ValueError(f"duplicate case_id: {case_id}")
            seen.add(case_id)
            labeler = required_text(entry, "labeler", case_id=case_id)
            required_text(entry, "labeled_at", case_id=case_id)
            evidence_refs = entry.get("evidence_refs")
            if not isinstance(evidence_refs, list) or not evidence_refs:
                raise ValueError(f"{case_id} evidence_refs must be non-empty")
            evidence_refs = [str(ref).strip() for ref in evidence_refs if str(ref).strip()]
            if not evidence_refs:
                raise ValueError(f"{case_id} evidence_refs must be non-empty")
            if production_gold_set:
                reject_fixture_labeler(labeler, case_id=case_id)
                reject_repository_fixture_refs(
                    evidence_refs,
                    case_id=case_id,
                    field="evidence_refs",
                )
            source_coverage(entry, case_id=case_id)


def entity_stats(cases: list[dict[str, Any]]) -> QualityStats:
    true_positive = 0
    false_positive = 0
    false_negative = 0
    true_negative = 0
    coverages: list[float] = []
    for row in cases:
        case_id = required_text(row, "case_id", case_id="entity_resolution_case")
        expected = row.get("expected_entity_id")
        predicted = row.get("predicted_entity_id")
        expected_text = expected if isinstance(expected, str) and expected.strip() else None
        predicted_text = predicted if isinstance(predicted, str) and predicted.strip() else None
        if expected_text and predicted_text == expected_text:
            true_positive += 1
        elif expected_text and predicted_text:
            false_positive += 1
            false_negative += 1
        elif expected_text and not predicted_text:
            false_negative += 1
        elif predicted_text:
            false_positive += 1
        else:
            true_negative += 1
        coverages.append(source_coverage(row, case_id=case_id))
    prediction_count = true_positive + false_positive
    expected_count = true_positive + false_negative
    return QualityStats(
        sample_count=len(cases),
        true_positive=true_positive,
        false_positive=false_positive,
        false_negative=false_negative,
        true_negative=true_negative,
        precision=ratio(true_positive, prediction_count),
        recall=ratio(true_positive, expected_count),
        source_coverage_min=min(coverages),
        source_coverage_avg=sum(coverages) / len(coverages),
    )


def relationship_stats(cases: list[dict[str, Any]]) -> QualityStats:
    true_positive = 0
    false_positive = 0
    false_negative = 0
    true_negative = 0
    coverages: list[float] = []
    for row in cases:
        case_id = required_text(row, "case_id", case_id="relationship_case")
        expected_present = row.get("expected_relation_present")
        predicted_present = row.get("predicted_relation_present")
        if not isinstance(expected_present, bool) or not isinstance(predicted_present, bool):
            raise ValueError(
                f"{case_id} expected_relation_present and predicted_relation_present "
                "must be booleans"
            )
        expected_key = row.get("expected_relationship_key")
        predicted_key = row.get("predicted_relationship_key")
        expected_key = (
            expected_key if isinstance(expected_key, str) and expected_key.strip() else None
        )
        predicted_key = (
            predicted_key if isinstance(predicted_key, str) and predicted_key.strip() else None
        )
        matched_positive = expected_present and predicted_present and expected_key == predicted_key
        if matched_positive:
            true_positive += 1
        elif not expected_present and not predicted_present:
            true_negative += 1
        else:
            if predicted_present:
                false_positive += 1
            if expected_present:
                false_negative += 1
        coverages.append(source_coverage(row, case_id=case_id))
    prediction_count = true_positive + false_positive
    expected_count = true_positive + false_negative
    return QualityStats(
        sample_count=len(cases),
        true_positive=true_positive,
        false_positive=false_positive,
        false_negative=false_negative,
        true_negative=true_negative,
        precision=ratio(true_positive, prediction_count),
        recall=ratio(true_positive, expected_count),
        source_coverage_min=min(coverages),
        source_coverage_avg=sum(coverages) / len(coverages),
    )


def blockers(
    stats: QualityStats,
    *,
    min_cases: int,
    min_precision: float,
    production_gold_set: bool,
) -> list[str]:
    result: list[str] = []
    if stats.sample_count < min_cases:
        result.append(f"sample_count {stats.sample_count} < required {min_cases}")
    if stats.precision < min_precision:
        result.append(f"precision {stats.precision:.4f} < required {min_precision:.4f}")
    if stats.source_coverage_min < SOURCE_COVERAGE_MIN:
        result.append(
            f"source_coverage_min {stats.source_coverage_min:.4f} "
            f"< required {SOURCE_COVERAGE_MIN:.4f}"
        )
    if not production_gold_set:
        result.append("repository fixture is not production_gold_set")
    return result


def stats_payload(stats: QualityStats) -> dict[str, Any]:
    return {
        "sample_count": stats.sample_count,
        "true_positive": stats.true_positive,
        "false_positive": stats.false_positive,
        "false_negative": stats.false_negative,
        "true_negative": stats.true_negative,
        "precision": round(stats.precision, 6),
        "recall": round(stats.recall, 6),
        "source_coverage_min": round(stats.source_coverage_min, 6),
        "source_coverage_avg": round(stats.source_coverage_avg, 6),
    }


def acceptance_payload(
    *,
    acceptance_id: str,
    stats: QualityStats,
    min_cases: int,
    min_precision: float,
    production_gold_set: bool,
) -> dict[str, Any]:
    closure_blockers = blockers(
        stats,
        min_cases=min_cases,
        min_precision=min_precision,
        production_gold_set=production_gold_set,
    )
    return {
        "acceptance_id": acceptance_id,
        "status": "DONE" if not closure_blockers else "IN_PROGRESS",
        "threshold_result": "PASS" if not closure_blockers else "FAIL_CLOSED",
        "release_gate_closure_allowed": not closure_blockers,
        "thresholds": {
            "minimum_cases": min_cases,
            "minimum_precision": min_precision,
            "minimum_source_coverage": SOURCE_COVERAGE_MIN,
            "recall_is_reported_not_release_threshold": True,
        },
        "metrics": stats_payload(stats),
        "closure_blockers": closure_blockers,
    }


def build_contract(
    labels_path: Path = DEFAULT_LABELS,
    *,
    generated_at: str | None = None,
    allow_production_gold_set: bool = False,
) -> dict[str, Any]:
    labels = read_json(labels_path)
    validate_label_payload(labels, allow_production_gold_set=allow_production_gold_set)
    production_gold_set = bool(labels["fixture_policy"].get("production_gold_set"))
    entity = entity_stats(labels["entity_resolution_cases"])
    relationship = relationship_stats(labels["relationship_cases"])
    a026 = acceptance_payload(
        acceptance_id="A026",
        stats=entity,
        min_cases=ENTITY_MIN_CASES,
        min_precision=ENTITY_MIN_PRECISION,
        production_gold_set=production_gold_set,
    )
    a027 = acceptance_payload(
        acceptance_id="A027",
        stats=relationship,
        min_cases=RELATIONSHIP_MIN_CASES,
        min_precision=RELATIONSHIP_MIN_PRECISION,
        production_gold_set=production_gold_set,
    )
    release_allowed = (
        a026["release_gate_closure_allowed"] is True
        and a027["release_gate_closure_allowed"] is True
    )
    status = "GOLD_EVALUATION_PASS" if release_allowed else "GOLD_EVALUATION_FAIL_CLOSED"
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": "t904-a026-a027-gold-quality-evaluation-contract",
        "generated_at": generated_at or utc_now(),
        "system_name": "EEI",
        "system_en_name": "Enterprise Ecosystem Intelligence",
        "task_id": "T904",
        "task_ids": ["T904", "T1301"],
        "acceptance_ids": ["A026", "A027", "A202"],
        "scope": labels["scope"],
        "dataset_id": labels["dataset_id"],
        "status": status,
        "release_gate_closure_allowed": release_allowed,
        "relationship_publication_allowed": False,
        "production_claim_allowed": release_allowed,
        "source_files": {
            "gold_labels": relative(labels_path),
        },
        "fixture_policy": labels["fixture_policy"],
        "production_gold_evidence": (
            labels.get("production_gold_evidence") if production_gold_set else None
        ),
        "production_intake_policy": production_intake_policy(),
        "quality_results": {
            "A026": a026,
            "A027": a027,
        },
        "source_coverage": {
            "minimum_required": SOURCE_COVERAGE_MIN,
            "entity_resolution_min": a026["metrics"]["source_coverage_min"],
            "relationship_min": a027["metrics"]["source_coverage_min"],
        },
        "manual_review_requirements": [
            "A026 requires at least 50 human-labeled entity-resolution cases "
            "and precision >= 95.00%.",
            "A027 requires at least 100 human-labeled relationship cases "
            "and precision >= 90.00%.",
            "Recall and source coverage must be reported for every run.",
            "Repository fixtures are not production gold-set evidence.",
            "Production gold labels require --allow-production-gold-set and "
            "production_gold_evidence with owner, sampling, labeler, source-license, "
            "passage-review and signature metadata.",
        ],
    }


def focus_payload(contract: dict[str, Any], acceptance_id: str) -> dict[str, Any]:
    if acceptance_id not in contract["quality_results"]:
        raise ValueError(f"unknown acceptance_id: {acceptance_id}")
    payload = dict(contract)
    payload["artifact_id"] = f"t904-{acceptance_id.lower()}-gold-quality-evaluation-contract"
    payload["focus_acceptance_id"] = acceptance_id
    payload["focus_quality_result"] = contract["quality_results"][acceptance_id]
    return payload


def validate_contract(contract: dict[str, Any], *, focus_acceptance_id: str | None = None) -> None:
    if contract.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    if contract.get("system_name") != "EEI":
        raise ValueError("system_name must be EEI")
    if contract.get("task_id") != "T904":
        raise ValueError("task_id must be T904")
    results = contract.get("quality_results")
    if not isinstance(results, dict):
        raise ValueError("quality_results must be present")
    for acceptance_id, min_cases, min_precision in [
        ("A026", ENTITY_MIN_CASES, ENTITY_MIN_PRECISION),
        ("A027", RELATIONSHIP_MIN_CASES, RELATIONSHIP_MIN_PRECISION),
    ]:
        result = results.get(acceptance_id)
        if not isinstance(result, dict):
            raise ValueError(f"missing quality result for {acceptance_id}")
        thresholds = result.get("thresholds")
        metrics = result.get("metrics")
        blockers_value = result.get("closure_blockers")
        if not isinstance(thresholds, dict) or not isinstance(metrics, dict):
            raise ValueError(f"{acceptance_id} must include thresholds and metrics")
        if thresholds.get("minimum_cases") != min_cases:
            raise ValueError(f"{acceptance_id} minimum_cases drift")
        if abs(float(thresholds.get("minimum_precision")) - min_precision) > 0.000001:
            raise ValueError(f"{acceptance_id} minimum_precision drift")
        if not isinstance(blockers_value, list):
            raise ValueError(f"{acceptance_id} closure_blockers must be a list")
        release_allowed = result.get("release_gate_closure_allowed") is True
        if release_allowed and blockers_value:
            raise ValueError(f"{acceptance_id} cannot allow closure while blockers exist")
        if not release_allowed and not blockers_value:
            raise ValueError(f"{acceptance_id} fail-closed result must list blockers")
    release_allowed = contract.get("release_gate_closure_allowed") is True
    if release_allowed:
        if (contract.get("fixture_policy") or {}).get("production_gold_set") is not True:
            raise ValueError("release closure requires production_gold_set=true")
        if not isinstance(contract.get("production_gold_evidence"), dict):
            raise ValueError("release closure requires production_gold_evidence")
        if any(
            contract["quality_results"][acceptance_id]["release_gate_closure_allowed"] is not True
            for acceptance_id in ("A026", "A027")
        ):
            raise ValueError("contract cannot allow release when A026 or A027 is blocked")
    if focus_acceptance_id and contract.get("focus_acceptance_id") != focus_acceptance_id:
        raise ValueError(f"artifact focus_acceptance_id must be {focus_acceptance_id}")


def validate_intake_template(template: dict[str, Any]) -> None:
    if template.get("schema_version") != INTAKE_TEMPLATE_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {INTAKE_TEMPLATE_SCHEMA_VERSION}")
    if template.get("system_name") != "EEI":
        raise ValueError("system_name must be EEI")
    if template.get("task_id") != "T904":
        raise ValueError("task_id must be T904")
    if template.get("status") != "TEMPLATE_ONLY":
        raise ValueError("intake template status must be TEMPLATE_ONLY")
    if template.get("release_gate_closure_allowed") is not False:
        raise ValueError("intake template must not close release gates")
    if template.get("production_claim_allowed") is not False:
        raise ValueError("intake template must not allow production claims")
    if template.get("relationship_publication_allowed") is not False:
        raise ValueError("intake template must not allow relationship publication")
    if template.get("acceptance_ids") != ["A026", "A027"]:
        raise ValueError("intake template acceptance_ids drift")

    thresholds = template.get("thresholds")
    if not isinstance(thresholds, dict):
        raise ValueError("intake template thresholds missing")
    expected_thresholds = {
        "A026": {
            "minimum_cases": ENTITY_MIN_CASES,
            "minimum_precision": ENTITY_MIN_PRECISION,
            "minimum_source_coverage": SOURCE_COVERAGE_MIN,
        },
        "A027": {
            "minimum_cases": RELATIONSHIP_MIN_CASES,
            "minimum_precision": RELATIONSHIP_MIN_PRECISION,
            "minimum_source_coverage": SOURCE_COVERAGE_MIN,
        },
    }
    if thresholds != expected_thresholds:
        raise ValueError("intake template thresholds drift")

    evidence_schema = template.get("production_gold_evidence_schema")
    if evidence_schema != production_intake_policy():
        raise ValueError("production_gold_evidence_schema drift")
    skeleton = template.get("label_payload_skeleton")
    if not isinstance(skeleton, dict):
        raise ValueError("label_payload_skeleton missing")
    if skeleton.get("schema_version") != LABEL_SCHEMA_VERSION:
        raise ValueError("label_payload_skeleton schema version drift")
    if (skeleton.get("fixture_policy") or {}).get("production_gold_set") is not True:
        raise ValueError("template skeleton must target production_gold_set=true")
    if skeleton.get("production_gold_evidence") != production_gold_evidence_template():
        raise ValueError("production_gold_evidence template drift")
    entity_cases = skeleton.get("entity_resolution_cases")
    relationship_cases = skeleton.get("relationship_cases")
    if not isinstance(entity_cases, dict) or not isinstance(relationship_cases, dict):
        raise ValueError("case templates missing")
    if entity_cases.get("minimum_required_cases") != ENTITY_MIN_CASES:
        raise ValueError("entity case count drift")
    if relationship_cases.get("minimum_required_cases") != RELATIONSHIP_MIN_CASES:
        raise ValueError("relationship case count drift")
    if entity_cases.get("case_template") != entity_resolution_case_template():
        raise ValueError("entity case template drift")
    if relationship_cases.get("case_template") != relationship_case_template():
        raise ValueError("relationship case template drift")


def generate_template(args: argparse.Namespace) -> int:
    output = Path(args.output)
    template = build_intake_template()
    validate_intake_template(template)
    write_json(output, template)
    print(
        json.dumps(
            {
                "generated": True,
                "status": template["status"],
                "release_gate_closure_allowed": template["release_gate_closure_allowed"],
                "output": relative(output),
                "a026_minimum_cases": ENTITY_MIN_CASES,
                "a027_minimum_cases": RELATIONSHIP_MIN_CASES,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def validate_template(args: argparse.Namespace) -> int:
    output = Path(args.output)
    template = read_json(output)
    validate_intake_template(template)
    print(
        json.dumps(
            {
                "valid": True,
                "status": template["status"],
                "release_gate_closure_allowed": template["release_gate_closure_allowed"],
                "output": relative(output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def generate_packet(args: argparse.Namespace) -> int:
    output = Path(args.output)
    packet = build_operator_labeling_packet(
        review_packet_path=Path(args.review_packet),
        fact_candidates_path=Path(args.fact_candidates),
    )
    validate_operator_labeling_packet(packet)
    write_json(output, packet)
    print(
        json.dumps(
            {
                "generated": True,
                "status": packet["status"],
                "release_gate_closure_allowed": packet["release_gate_closure_allowed"],
                "output": relative(output),
                "entity_slots": len(packet["entity_resolution_labeling_slots"]),
                "relationship_slots": len(packet["relationship_labeling_slots"]),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def validate_packet(args: argparse.Namespace) -> int:
    output = Path(args.output)
    packet = read_json(output)
    validate_operator_labeling_packet(packet)
    print(
        json.dumps(
            {
                "valid": True,
                "status": packet["status"],
                "release_gate_closure_allowed": packet["release_gate_closure_allowed"],
                "output": relative(output),
                "entity_slots": len(packet["entity_resolution_labeling_slots"]),
                "relationship_slots": len(packet["relationship_labeling_slots"]),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def generate(args: argparse.Namespace) -> int:
    labels = Path(args.labels)
    contract = build_contract(
        labels,
        allow_production_gold_set=bool(args.allow_production_gold_set),
    )
    write_json(Path(args.a026_output), focus_payload(contract, "A026"))
    write_json(Path(args.a027_output), focus_payload(contract, "A027"))
    print(
        json.dumps(
            {
                "generated": True,
                "status": contract["status"],
                "release_gate_closure_allowed": contract["release_gate_closure_allowed"],
                "a026_output": relative(Path(args.a026_output)),
                "a027_output": relative(Path(args.a027_output)),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def validate(args: argparse.Namespace) -> int:
    a026 = read_json(Path(args.a026_output))
    a027 = read_json(Path(args.a027_output))
    validate_contract(a026, focus_acceptance_id="A026")
    validate_contract(a027, focus_acceptance_id="A027")
    if a026["quality_results"] != a027["quality_results"]:
        raise ValueError("A026 and A027 artifacts must share one quality_results payload")
    print(
        json.dumps(
            {
                "valid": True,
                "a026_status": a026["quality_results"]["A026"]["status"],
                "a027_status": a027["quality_results"]["A027"]["status"],
                "release_gate_closure_allowed": a026["release_gate_closure_allowed"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--labels", default=str(DEFAULT_LABELS))
    generate_parser.add_argument("--a026-output", default=str(DEFAULT_A026_OUTPUT))
    generate_parser.add_argument("--a027-output", default=str(DEFAULT_A027_OUTPUT))
    generate_parser.add_argument(
        "--allow-production-gold-set",
        action="store_true",
        help=(
            "Permit operator-supplied production gold labels when the payload "
            "contains complete production_gold_evidence metadata."
        ),
    )
    generate_parser.set_defaults(func=generate)
    generate_template_parser = subparsers.add_parser("generate-template")
    generate_template_parser.add_argument(
        "--output",
        default=str(DEFAULT_INTAKE_TEMPLATE_OUTPUT),
    )
    generate_template_parser.set_defaults(func=generate_template)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--a026-output", default=str(DEFAULT_A026_OUTPUT))
    validate_parser.add_argument("--a027-output", default=str(DEFAULT_A027_OUTPUT))
    validate_parser.set_defaults(func=validate)
    validate_template_parser = subparsers.add_parser("validate-template")
    validate_template_parser.add_argument(
        "--output",
        default=str(DEFAULT_INTAKE_TEMPLATE_OUTPUT),
    )
    validate_template_parser.set_defaults(func=validate_template)
    generate_packet_parser = subparsers.add_parser("generate-packet")
    generate_packet_parser.add_argument("--output", default=str(DEFAULT_OPERATOR_PACKET_OUTPUT))
    generate_packet_parser.add_argument("--review-packet", default=str(DEFAULT_REVIEW_PACKET))
    generate_packet_parser.add_argument("--fact-candidates", default=str(DEFAULT_FACT_CANDIDATES))
    generate_packet_parser.set_defaults(func=generate_packet)
    validate_packet_parser = subparsers.add_parser("validate-packet")
    validate_packet_parser.add_argument("--output", default=str(DEFAULT_OPERATOR_PACKET_OUTPUT))
    validate_packet_parser.set_defaults(func=validate_packet)
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
