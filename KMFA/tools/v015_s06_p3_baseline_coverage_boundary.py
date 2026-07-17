#!/usr/bin/env python3
"""Build the private fixture and public-safe boundary facts for v1.5 S06-P3.

The locked S06-P2 golden record remains the only business-value authority.
This module creates an immutable private regression fixture, routes every
unconfirmed item without guessing, and publishes aggregate coverage only.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import v015_s06_p2_golden_baseline_lock as p2


RUN_PHASE_ID = "V015_S06_P3_BASELINE_COVERAGE_BOUNDARY"
ROADMAP_PHASE_ID = "S06-P3"
TASK_ID = "KMFA-V015-S06-P3-BASELINE-COVERAGE-BOUNDARY-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S06-P3-BASELINE-COVERAGE-BOUNDARY"
VERSION = "1.5.0-dev-s06p3"

PRIVATE_SCHEMA = "kmfa.private.v015.s06p3.baseline_coverage_boundary.v1"
FIXTURE_SCHEMA = "kmfa.private.v015.s06p3.regression_fixture.v1"
QUEUE_SCHEMA = "kmfa.private.v015.s06p3.open_item_queue.v1"
COVERAGE_SCHEMA = "kmfa.private.v015.s06p3.sample_coverage.v1"
PUBLIC_SCHEMA = "kmfa.v015.s06p3.baseline_coverage_boundary_public_safe.v1"

PRIVATE_OUTPUT_DIR = Path(
    "KMFA/.codex_private_runtime/v015_s06_p3_baseline_coverage_boundary"
)
PRIVATE_FIXTURE_PATH = PRIVATE_OUTPUT_DIR / "private_regression_fixture.json"
PRIVATE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_open_item_queue.json"
PRIVATE_COVERAGE_PATH = PRIVATE_OUTPUT_DIR / "private_sample_coverage.json"
PRIVATE_SUMMARY_PATH = PRIVATE_OUTPUT_DIR / "private_phase_summary.json"


class BoundaryError(RuntimeError):
    """Stable fail-closed S06-P3 error."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundaryError(message)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    payload = value if isinstance(value, bytes) else _canonical_bytes(value)
    return hashlib.sha256(payload).hexdigest()


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BoundaryError(f"private JSON unavailable or invalid: {path.name}") from error
    _require(isinstance(value, dict), f"private JSON object required: {path.name}")
    return value


def _private_write_once(path: Path, value: dict[str, Any]) -> None:
    expected = _dump(value)
    if path.exists():
        _require(path.read_text(encoding="utf-8") == expected, f"immutable private evidence drift: {path.name}")
        os.chmod(path, 0o600)
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, expected.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chmod(path, 0o600)


def _dependencies() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    packet = _json(p2.PRIVATE_PACKET_PATH)
    signoff = _json(p2.PRIVATE_SIGNOFF_PATH)
    authorization = _json(p2.PRIVATE_AUTHORIZATION_PATH)
    p2.validate_candidate_packet(packet)
    p2.validate_authorization_record(authorization)
    accepted = p2.validate_signoff(signoff, packet)
    ledger = p2._read_ledger()
    _require(len(ledger) == 1, "S06-P3 requires exactly one locked S06-P2 golden version")
    record = ledger[0]
    _require(record.get("locked") is True, "S06-P2 golden version is not locked")
    _require(record.get("accepted_field_count") == 92, "S06-P2 accepted field count mismatch")
    _require(record.get("resolved_candidate_count") == 157, "S06-P2 resolution count mismatch")
    _require(record.get("project_count") == 8, "S06-P2 project count mismatch")
    _require(record.get("money_difference_cents") == 0, "S06-P2 money difference is non-zero")
    _require(len(accepted) == 92, "S06-P2 accepted decision set mismatch")
    _require(len(signoff.get("decision_rows", [])) == 157, "S06-P2 decision set is incomplete")
    return packet, signoff, authorization, ledger


def build_fixture(ledger_record: dict[str, Any]) -> dict[str, Any]:
    body = {
        "schema_version": FIXTURE_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": RUN_PHASE_ID,
        "fixture_version": "S06P3-FIXTURE-0001",
        "source_phase_id": p2.RUN_PHASE_ID,
        "source_baseline_version": ledger_record["baseline_version"],
        "source_golden_record_hash": ledger_record["record_hash"],
        "source_signoff_digest": ledger_record["signoff_digest"],
        "project_count": ledger_record["project_count"],
        "accepted_field_count": ledger_record["accepted_field_count"],
        "money_difference_cents": ledger_record["money_difference_cents"],
        "project_summaries": ledger_record["project_summaries"],
        "immutable": True,
        "overwrite_allowed": False,
        "public_sensitive_value_count": 0,
    }
    return {**body, "fixture_digest": _sha256(body)}


def _joined_decisions(packet: dict[str, Any], signoff: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = {row["candidate_id"]: row for row in packet["candidate_records"]}
    joined: list[dict[str, Any]] = []
    for decision in signoff["decision_rows"]:
        candidate = candidates.get(decision["candidate_id"])
        _require(candidate is not None, "decision references unknown candidate")
        joined.append({**candidate, **decision})
    return joined


def _rejected_route(reason: str) -> tuple[str, str, str, str]:
    if "无法与八个项目精确绑定" in reason:
        return (
            "AMBIGUOUS", "OPEN", "PROJECT_BINDING_UNAVAILABLE",
            "ADD_AUTHORIZED_PROJECT_BINDING_OR_EXPLICIT_EXCLUSION_IN_NEW_GOLDEN_VERSION",
        )
    if "未选为本项目权威字段" in reason:
        return (
            "NOT_APPLICABLE", "ROUTED_EXCLUSION", "NO_EFFECT_ON_LOCKED_BASELINE",
            "KEEP_EXCLUDED_UNLESS_A_NEW_GOLDEN_VERSION_CHANGES_AUTHORITY",
        )
    if "不一致" in reason and "重算" in reason:
        return (
            "CONFLICT", "ROUTED_DERIVATION", "SOURCE_DISPLAY_NOT_AUTHORITATIVE",
            "KEEP_DERIVED_VALUE_FROM_CONFIRMED_REVENUE_AND_COST",
        )
    raise BoundaryError("unclassified rejected candidate reason")


def build_open_queue(packet: dict[str, Any], signoff: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for row in _joined_decisions(packet, signoff):
        if row["decision"] == "REJECT":
            category, status, impact, resolution = _rejected_route(row["rejection_reason"])
            items.append({
                "item_id": "S06P3-OPEN-" + _sha256({"candidate": row["candidate_id"], "kind": "REJECT"})[:24].upper(),
                "candidate_id": row["candidate_id"],
                "field_family": row["field_family"],
                "source_ref": row["source_ref"],
                "source_locator": row["source_locator"],
                "category": category,
                "status": status,
                "impact": impact,
                "resolution_path": resolution,
                "guessing_used": False,
            })
        elif row.get("tax_status") == "SOURCE_NOT_STATED":
            items.append({
                "item_id": "S06P3-OPEN-" + _sha256({"candidate": row["candidate_id"], "kind": "TAX"})[:24].upper(),
                "candidate_id": row["candidate_id"],
                "field_family": row["field_family"],
                "project_ref": row["project_ref"],
                "source_ref": row["source_ref"],
                "source_locator": row["confirmed_source_locator"],
                "category": "MISSING",
                "status": "OPEN",
                "impact": "TAX_TREATMENT_UNCONFIRMED",
                "resolution_path": "ADD_AUTHORIZED_TAX_BASIS_IN_NEW_GOLDEN_VERSION",
                "guessing_used": False,
            })
    items.sort(key=lambda item: item["item_id"])
    category_counts = Counter(item["category"] for item in items)
    status_counts = Counter(item["status"] for item in items)
    body = {
        "schema_version": QUEUE_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": RUN_PHASE_ID,
        "item_count": len(items),
        "category_counts": dict(sorted(category_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "impact_present_count": sum(bool(item["impact"]) for item in items),
        "resolution_path_present_count": sum(bool(item["resolution_path"]) for item in items),
        "guessing_used": False,
        "items": items,
    }
    return {**body, "queue_digest": _sha256(body)}


def build_coverage(ledger_record: dict[str, Any], queue: dict[str, Any]) -> dict[str, Any]:
    summaries = ledger_record["project_summaries"]
    profit_count = sum(row["gross_profit_cents"] > 0 for row in summaries)
    loss_count = sum(row["gross_profit_cents"] < 0 for row in summaries)
    zero_cost_categories = sum(
        category["amount_cents"] == 0
        for row in summaries for category in row["category_costs"]
    )
    conflict_count = queue["category_counts"].get("CONFLICT", 0)
    criteria = [
        {"scenario": "PROFITABLE", "status": "COVERED", "evidence_count": profit_count},
        {"scenario": "LOSS", "status": "COVERED", "evidence_count": loss_count},
        {"scenario": "ZERO_OR_NEGATIVE_COST", "status": "COVERED", "evidence_count": zero_cost_categories},
        {"scenario": "CROSS_PERIOD", "status": "MISSING", "evidence_count": 0},
        {"scenario": "CONFLICT_TEMPLATE", "status": "COVERED", "evidence_count": conflict_count},
    ]
    _require(profit_count > 0 and loss_count > 0 and zero_cost_categories > 0 and conflict_count > 0,
             "required observed sample scenarios are incomplete")
    future_samples = [{
        "sample_id": "S06P3-SAMPLE-CROSS-PERIOD-001",
        "scenario": "CROSS_PERIOD",
        "status": "REGISTERED_FOR_FUTURE_SOURCE_EXPANSION",
        "impact": "PERIOD_BOUNDARY_REGRESSION_NOT_PROVEN_BY_CURRENT_GOLDEN_SET",
        "resolution_path": "ADD_AUTHORIZED_CROSS_PERIOD_PROJECT_IN_A_NEW_GOLDEN_VERSION",
        "guessing_used": False,
    }]
    body = {
        "schema_version": COVERAGE_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": RUN_PHASE_ID,
        "required_scenario_count": 5,
        "covered_scenario_count": 4,
        "missing_scenario_count": 1,
        "criteria": criteria,
        "sample_expansion_required": True,
        "future_sample_count": len(future_samples),
        "future_samples": future_samples,
        "phase_task_acceptance_allowed_with_registered_sample_gap": True,
        "guessing_used": False,
    }
    return {**body, "coverage_digest": _sha256(body)}


def build_private_outputs() -> dict[str, Any]:
    packet, signoff, _, ledger = _dependencies()
    fixture = build_fixture(ledger[-1])
    queue = build_open_queue(packet, signoff)
    coverage = build_coverage(ledger[-1], queue)
    summary_body = {
        "schema_version": PRIVATE_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": RUN_PHASE_ID,
        "fixture_digest": fixture["fixture_digest"],
        "queue_digest": queue["queue_digest"],
        "coverage_digest": coverage["coverage_digest"],
        "private_files": [path.name for path in (PRIVATE_FIXTURE_PATH, PRIVATE_QUEUE_PATH, PRIVATE_COVERAGE_PATH)],
        "raw_mutation_performed": False,
    }
    summary = {**summary_body, "summary_digest": _sha256(summary_body)}
    PRIVATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(PRIVATE_OUTPUT_DIR, 0o700)
    for path, value in (
        (PRIVATE_FIXTURE_PATH, fixture), (PRIVATE_QUEUE_PATH, queue),
        (PRIVATE_COVERAGE_PATH, coverage), (PRIVATE_SUMMARY_PATH, summary),
    ):
        _private_write_once(path, value)
    return public_projection(fixture, queue, coverage)


def validate_private_outputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    _require(PRIVATE_OUTPUT_DIR.is_dir(), "private S06-P3 directory missing")
    _require(stat.S_IMODE(PRIVATE_OUTPUT_DIR.stat().st_mode) == 0o700, "private directory must be 0700")
    fixture = _json(PRIVATE_FIXTURE_PATH)
    queue = _json(PRIVATE_QUEUE_PATH)
    coverage = _json(PRIVATE_COVERAGE_PATH)
    summary = _json(PRIVATE_SUMMARY_PATH)
    for path in (PRIVATE_FIXTURE_PATH, PRIVATE_QUEUE_PATH, PRIVATE_COVERAGE_PATH, PRIVATE_SUMMARY_PATH):
        _require(stat.S_IMODE(path.stat().st_mode) == 0o600, f"private file must be 0600: {path.name}")
    for value, digest_key in ((fixture, "fixture_digest"), (queue, "queue_digest"), (coverage, "coverage_digest"), (summary, "summary_digest")):
        body = {key: item for key, item in value.items() if key != digest_key}
        _require(value.get(digest_key) == _sha256(body), f"private digest mismatch: {digest_key}")
    packet, signoff, _, ledger = _dependencies()
    _require(fixture == build_fixture(ledger[-1]), "fixture differs from locked golden version")
    _require(queue == build_open_queue(packet, signoff), "open queue differs from source decisions")
    _require(coverage == build_coverage(ledger[-1], queue), "sample coverage differs from fixture")
    return fixture, queue, coverage


def public_projection(
    fixture: dict[str, Any], queue: dict[str, Any], coverage: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S06",
        "phase_id": RUN_PHASE_ID,
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "fixture_version_count": 1,
        "fixture_project_count": fixture["project_count"],
        "fixture_accepted_field_count": fixture["accepted_field_count"],
        "fixture_money_difference_cents": fixture["money_difference_cents"],
        "fixture_hash_recorded_private": True,
        "fixture_consistent_with_golden": True,
        "fixture_immutable": fixture["immutable"],
        "fixture_overwrite_allowed": fixture["overwrite_allowed"],
        "open_item_count": queue["item_count"],
        "open_item_category_counts": queue["category_counts"],
        "open_item_status_counts": queue["status_counts"],
        "open_item_impact_coverage_bps": 10000,
        "open_item_resolution_path_coverage_bps": 10000,
        "required_scenario_count": coverage["required_scenario_count"],
        "covered_scenario_count": coverage["covered_scenario_count"],
        "missing_scenario_count": coverage["missing_scenario_count"],
        "coverage_disposition_count": coverage["covered_scenario_count"] + coverage["future_sample_count"],
        "coverage_matrix": coverage["criteria"],
        "sample_expansion_required": coverage["sample_expansion_required"],
        "future_sample_count": coverage["future_sample_count"],
        "future_sample_scenarios": [row["scenario"] for row in coverage["future_samples"]],
        "empirical_coverage_complete": False,
        "registered_gap_satisfies_stop_condition": True,
        "coverage_acceptance_basis": "FOUR_OBSERVED_PLUS_ONE_REGISTERED_FUTURE_SAMPLE_PER_STOP_CONDITION",
        "downstream_cross_period_claim_allowed": False,
        "tax_normalization_allowed": False,
        "open_items_may_be_treated_as_resolved": False,
        "golden_scope": "SOURCE_DISPLAY_CENTS_WITH_EXPLICIT_UNCONFIRMED_BOUNDARIES",
        "guessing_used": False,
        "raw_mutation_performed": False,
        "public_project_identity_count": 0,
        "public_money_value_count": 0,
        "public_source_locator_count": 0,
        "public_private_fixture_hash_count": 0,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION",
        "s06_stage_review_entry_allowed": False,
        "s06_stage_review_started": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


def current_public_projection() -> dict[str, Any]:
    fixture, queue, coverage = validate_private_outputs()
    return public_projection(fixture, queue, coverage)


def main(argv: Iterable[str] | None = None) -> int:
    parser = __import__("argparse").ArgumentParser(description="KMFA v1.5 S06-P3 baseline boundary")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--build-private", action="store_true")
    action.add_argument("--public-summary", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    projection = build_private_outputs() if args.build_private else current_public_projection()
    print(_dump(projection), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
