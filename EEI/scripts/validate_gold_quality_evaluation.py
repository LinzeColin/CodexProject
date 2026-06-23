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
LABEL_SCHEMA_VERSION = "eei-gold-quality-labels-v1"
DEFAULT_LABELS = ROOT / "tests/fixtures/gold_quality/golden_vertical_gold_labels_sample.json"
DEFAULT_A026_OUTPUT = (
    ROOT / "artifacts/tests/a026/t904_entity_resolution_gold_evaluation_contract.json"
)
DEFAULT_A027_OUTPUT = (
    ROOT / "artifacts/tests/a027/t904_relationship_gold_evaluation_contract.json"
)

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
        "release_boundary": {
            "gold_quality_pass_only_closes": ["A026", "A027"],
            "does_not_close": ["A202", "A209", "A210", "release_manager_activation"],
            "relationship_publication_allowed": False,
        },
    }


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
            required_text(entry, "labeler", case_id=case_id)
            required_text(entry, "labeled_at", case_id=case_id)
            evidence_refs = entry.get("evidence_refs")
            if not isinstance(evidence_refs, list) or not evidence_refs:
                raise ValueError(f"{case_id} evidence_refs must be non-empty")
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
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--a026-output", default=str(DEFAULT_A026_OUTPUT))
    validate_parser.add_argument("--a027-output", default=str(DEFAULT_A027_OUTPUT))
    validate_parser.set_defaults(func=validate)
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
