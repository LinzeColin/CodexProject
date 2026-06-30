#!/usr/bin/env python3
"""Build KMFA S08-P1 public-safe project composite key metadata.

The matcher combines contract number, project name, counterparty, company
entity, date, amount signature, responsible person, and source hash. Public
outputs keep hashes, private refs, scores, statuses, and evidence refs only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "schema_maps" / "project_composite_key_manifest.json"
DEFAULT_OUTPUT_PROFILES = ROOT / "metadata" / "schema_maps" / "project_identity_profiles.jsonl"
DEFAULT_OUTPUT_MATCHES = ROOT / "metadata" / "schema_maps" / "project_composite_key_matches.jsonl"
DEFAULT_OUTPUT_REVIEW_QUEUE = ROOT / "metadata" / "quality" / "project_identity_review_queue.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S08_P1_project_composite_key" / "machine" / "s08_p1_manifest.json"
)

REQUIRED_COMPONENTS = (
    "contract_number",
    "project_name",
    "counterparty",
    "company_entity",
    "occurrence_or_project_date",
    "amount_signature",
    "responsible_person",
    "source_hash",
)

MATCHING_WEIGHTS_BPS = {
    "contract_number": 2000,
    "project_name": 1800,
    "counterparty": 1500,
    "company_entity": 1000,
    "occurrence_or_project_date": 1200,
    "amount_signature": 1200,
    "responsible_person": 600,
    "source_hash": 700,
}

THRESHOLDS_BPS = {
    "strong_auto_match": 8500,
    "human_review": 7000,
    "weak_candidate": 5000,
}

HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")

FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "contract_number_plaintext",
    "project_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "responsible_person_plaintext",
    "amount_value",
    "bank_account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
}


class ProjectCompositeKeyError(ValueError):
    """Raised when S08-P1 composite key metadata is invalid."""


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ProjectCompositeKeyError(f"{field_name} is required")
    text = str(value).strip()
    if not text:
        raise ProjectCompositeKeyError(f"{field_name} is required")
    return text


def component_hash(component: str, value: str) -> str:
    if component == "source_hash" and HASH_RE.match(value):
        return value
    return sha256_text(f"{component}:{value}")


def build_identity_profile(
    *,
    profile_id: str,
    source_ref: str,
    components: dict[str, str],
    private_ref_prefix: str,
) -> dict[str, Any]:
    """Build a hash-only identity profile from private component values."""

    profile_id_value = require_text(profile_id, "profile_id")
    source_ref_value = require_text(source_ref, "source_ref")
    private_ref_prefix_value = require_text(private_ref_prefix, "private_ref_prefix").rstrip("/")
    component_records: list[dict[str, Any]] = []
    missing_components: list[str] = []
    for component in REQUIRED_COMPONENTS:
        weight_bps = MATCHING_WEIGHTS_BPS[component]
        value = components.get(component)
        if value is None or str(value).strip() == "":
            missing_components.append(component)
            component_records.append(
                {
                    "component": component,
                    "component_status": "missing_requires_review",
                    "weight_bps": weight_bps,
                    "component_hash": None,
                    "component_private_ref": f"{private_ref_prefix_value}/{component}",
                }
            )
            continue
        text = require_text(value, component)
        component_records.append(
            {
                "component": component,
                "component_status": "present_hash_only",
                "weight_bps": weight_bps,
                "component_hash": component_hash(component, text),
                "component_private_ref": f"{private_ref_prefix_value}/{component}",
            }
        )
    return {
        "schema_version": "kmfa.project_identity_profile.v1",
        "record_type": "project_identity_profile",
        "project_id": "KMFA",
        "stage_phase": "S08-P1",
        "profile_id": profile_id_value,
        "source_ref": source_ref_value,
        "required_component_count": len(REQUIRED_COMPONENTS),
        "present_component_count": len(REQUIRED_COMPONENTS) - len(missing_components),
        "missing_components": missing_components,
        "components": component_records,
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "plaintext_identity_values_committed": False,
            "private_csv_committed": False,
            "raw_file_committed": False,
        },
    }


def _component_index(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["component"]: record for record in profile.get("components", [])}


def _queue_id(authority_profile_id: str, candidate_profile_id: str, score_bps: int) -> str:
    digest = hashlib.sha256(f"{authority_profile_id}:{candidate_profile_id}:{score_bps}".encode("utf-8")).hexdigest()
    return "PMQ-" + digest[:12].upper()


def score_project_match(
    authority_profile: dict[str, Any],
    candidate_profile: dict[str, Any],
    *,
    evidence_ref: str,
) -> dict[str, Any]:
    """Score two public-safe identity profiles with weighted component hashes."""

    authority_components = _component_index(authority_profile)
    candidate_components = _component_index(candidate_profile)
    matched_components: list[str] = []
    mismatched_components: list[str] = []
    missing_components: list[str] = []
    for component in REQUIRED_COMPONENTS:
        authority_record = authority_components.get(component)
        candidate_record = candidate_components.get(component)
        authority_hash = authority_record.get("component_hash") if authority_record else None
        candidate_hash = candidate_record.get("component_hash") if candidate_record else None
        if not authority_hash or not candidate_hash:
            missing_components.append(component)
        elif authority_hash == candidate_hash:
            matched_components.append(component)
        else:
            mismatched_components.append(component)

    matched_weight_bps = sum(MATCHING_WEIGHTS_BPS[component] for component in matched_components)
    score_bps = matched_weight_bps
    manual_review_required = score_bps < THRESHOLDS_BPS["strong_auto_match"]
    if manual_review_required:
        decision = "human_review_required"
        if score_bps < THRESHOLDS_BPS["weak_candidate"]:
            review_reason = "score_below_weak_candidate_threshold"
        else:
            review_reason = "score_below_strong_threshold"
    else:
        decision = "strong_auto_match"
        review_reason = "score_at_or_above_strong_threshold"

    result: dict[str, Any] = {
        "schema_version": "kmfa.project_composite_key_match.v1",
        "record_type": "project_composite_key_match",
        "project_id": "KMFA",
        "stage_phase": "S08-P1",
        "authority_profile_id": authority_profile["profile_id"],
        "candidate_profile_id": candidate_profile["profile_id"],
        "matched_components": matched_components,
        "mismatched_components": mismatched_components,
        "missing_components": missing_components,
        "matched_weight_bps": matched_weight_bps,
        "score_bps": score_bps,
        "thresholds_bps": dict(THRESHOLDS_BPS),
        "match_decision": decision,
        "manual_review_required": manual_review_required,
        "review_reason": review_reason,
        "blocked_by_missing_single_field": False,
        "auto_merge_allowed": not manual_review_required,
        "evidence_ref": require_text(evidence_ref, "evidence_ref"),
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "plaintext_identity_values_committed": False,
        },
    }
    if manual_review_required:
        result["manual_review_queue_record"] = {
            "schema_version": "kmfa.project_identity_review_queue.v1",
            "record_type": "project_identity_review_queue_item",
            "queue_id": _queue_id(authority_profile["profile_id"], candidate_profile["profile_id"], score_bps),
            "queue_type": "project_identity_manual_review",
            "status": "pending_human_review",
            "authority_profile_id": authority_profile["profile_id"],
            "candidate_profile_id": candidate_profile["profile_id"],
            "score_bps": score_bps,
            "review_reason": review_reason,
            "missing_components": missing_components,
            "mismatched_components": mismatched_components,
            "auto_merge_allowed": False,
            "raw_layer_write_allowed": False,
            "evidence_ref": evidence_ref,
        }
    return result


def build_default_project_composite_key(
    *, generated_at: str
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    authority_components = {
        "contract_number": "KMFA-HT-2026-001",
        "project_name": "SYNTHETIC_PROJECT_ALPHA",
        "counterparty": "SYNTHETIC_COUNTERPARTY_ALPHA",
        "company_entity": "SYNTHETIC_ENTITY_ALPHA",
        "occurrence_or_project_date": "2026-06-30",
        "amount_signature": "amount-cents:12345600",
        "responsible_person": "SYNTHETIC_OWNER_ALPHA",
        "source_hash": "sha256:" + "a" * 64,
    }
    strong_components = dict(authority_components)
    missing_contract_components = dict(authority_components)
    missing_contract_components.pop("contract_number")
    weak_components = {
        "project_name": authority_components["project_name"],
        "counterparty": authority_components["counterparty"],
        "company_entity": authority_components["company_entity"],
        "occurrence_or_project_date": authority_components["occurrence_or_project_date"],
    }
    authority = build_identity_profile(
        profile_id="IDP-S08P1-AUTHORITY-001",
        source_ref="SRC-S08P1-AUTHORITY-001",
        components=authority_components,
        private_ref_prefix="private://KMFA/S08-P1/authority/IDP-S08P1-AUTHORITY-001",
    )
    strong = build_identity_profile(
        profile_id="IDP-S08P1-CANDIDATE-STRONG-001",
        source_ref="SRC-S08P1-CANDIDATE-STRONG-001",
        components=strong_components,
        private_ref_prefix="private://KMFA/S08-P1/candidate/IDP-S08P1-CANDIDATE-STRONG-001",
    )
    missing_contract = build_identity_profile(
        profile_id="IDP-S08P1-CANDIDATE-MISSING-CONTRACT-001",
        source_ref="SRC-S08P1-CANDIDATE-MISSING-CONTRACT-001",
        components=missing_contract_components,
        private_ref_prefix="private://KMFA/S08-P1/candidate/IDP-S08P1-CANDIDATE-MISSING-CONTRACT-001",
    )
    weak = build_identity_profile(
        profile_id="IDP-S08P1-CANDIDATE-WEAK-001",
        source_ref="SRC-S08P1-CANDIDATE-WEAK-001",
        components=weak_components,
        private_ref_prefix="private://KMFA/S08-P1/candidate/IDP-S08P1-CANDIDATE-WEAK-001",
    )
    evidence_ref = "KMFA/stage_artifacts/S08_P1_project_composite_key/human/test_results.md"
    match_results = [
        score_project_match(authority, strong, evidence_ref=evidence_ref),
        score_project_match(authority, missing_contract, evidence_ref=evidence_ref),
        score_project_match(authority, weak, evidence_ref=evidence_ref),
    ]
    review_queue = [result["manual_review_queue_record"] for result in match_results if result["manual_review_required"]]
    profiles = [authority, strong, missing_contract, weak]
    manifest = {
        "schema_version": "kmfa.project_composite_key_manifest.v1",
        "record_type": "s08_p1_project_composite_key_manifest",
        "project_id": "KMFA",
        "stage_phase": "S08-P1",
        "generated_at": require_text(generated_at, "generated_at"),
        "required_components": list(REQUIRED_COMPONENTS),
        "matching_weights_bps": dict(MATCHING_WEIGHTS_BPS),
        "thresholds_bps": dict(THRESHOLDS_BPS),
        "summary": {
            "profile_count": len(profiles),
            "match_result_count": len(match_results),
            "manual_review_queue_count": len(review_queue),
            "strong_auto_match_count": sum(
                1 for result in match_results if result["match_decision"] == "strong_auto_match"
            ),
        },
        "stage_scope": {
            "s08_p1_scope_included": True,
            "s08_p2_entity_model_scope_included": False,
            "s08_p3_matching_quality_scope_included": False,
            "fact_layer_scope_included": False,
            "lineage_full_check_scope_included": False,
            "report_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
        },
        "quality_gate": {
            "formal_report_allowed": False,
            "q5_calculation_baseline_allowed": False,
            "github_upload_allowed": False,
            "phase_completion_upload_allowed": False,
            "missing_single_component_blocks_all_matching": False,
            "below_strong_threshold_enters_manual_review": True,
        },
        "artifact_refs": {
            "profiles": "KMFA/metadata/schema_maps/project_identity_profiles.jsonl",
            "match_results": "KMFA/metadata/schema_maps/project_composite_key_matches.jsonl",
            "manual_review_queue": "KMFA/metadata/quality/project_identity_review_queue.jsonl",
            "completion_record": "KMFA/stage_artifacts/S08_P1_project_composite_key/human/s08_p1_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S08_P1_project_composite_key/human/test_results.md",
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "plaintext_identity_values_committed": False,
            "private_csv_committed": False,
            "raw_file_committed": False,
        },
    }
    return manifest, profiles, match_results, review_queue


def _walk_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(_walk_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_walk_forbidden_keys(child, f"{path}[{index}]"))
    return hits


def validate_project_composite_key_artifacts(
    manifest: dict[str, Any],
    profiles: list[dict[str, Any]],
    match_results: list[dict[str, Any]],
    review_queue: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.project_composite_key_manifest.v1":
        raise ProjectCompositeKeyError("invalid S08-P1 manifest schema_version")
    if tuple(manifest.get("required_components", [])) != REQUIRED_COMPONENTS:
        raise ProjectCompositeKeyError("S08-P1 required components mismatch")
    if manifest.get("matching_weights_bps") != MATCHING_WEIGHTS_BPS:
        raise ProjectCompositeKeyError("S08-P1 matching weights mismatch")
    if sum(MATCHING_WEIGHTS_BPS.values()) != 10000:
        raise ProjectCompositeKeyError("S08-P1 matching weights must sum to 10000 bps")
    if manifest.get("thresholds_bps") != THRESHOLDS_BPS:
        raise ProjectCompositeKeyError("S08-P1 thresholds mismatch")
    if manifest.get("quality_gate", {}).get("github_upload_allowed") is not False:
        raise ProjectCompositeKeyError("S08-P1 phase must not allow GitHub upload")
    if manifest.get("quality_gate", {}).get("formal_report_allowed") is not False:
        raise ProjectCompositeKeyError("S08-P1 must not allow formal reports")
    if manifest.get("stage_scope", {}).get("s08_p2_entity_model_scope_included") is not False:
        raise ProjectCompositeKeyError("S08-P1 must not include S08-P2 entity model")
    if manifest.get("stage_scope", {}).get("fact_layer_scope_included") is not False:
        raise ProjectCompositeKeyError("S08-P1 must not include fact layer")
    if len(profiles) != manifest.get("summary", {}).get("profile_count"):
        raise ProjectCompositeKeyError("S08-P1 profile count mismatch")
    if len(match_results) != manifest.get("summary", {}).get("match_result_count"):
        raise ProjectCompositeKeyError("S08-P1 match result count mismatch")
    if len(review_queue) != manifest.get("summary", {}).get("manual_review_queue_count"):
        raise ProjectCompositeKeyError("S08-P1 review queue count mismatch")
    if not any(result.get("match_decision") == "strong_auto_match" for result in match_results):
        raise ProjectCompositeKeyError("S08-P1 requires at least one strong auto match evidence")
    if not any(result.get("match_decision") == "human_review_required" for result in match_results):
        raise ProjectCompositeKeyError("S08-P1 requires human review evidence")
    for profile in profiles:
        components = _component_index(profile)
        if tuple(components) != REQUIRED_COMPONENTS:
            raise ProjectCompositeKeyError(f"profile {profile.get('profile_id')} missing component records")
        for component, record in components.items():
            if record.get("weight_bps") != MATCHING_WEIGHTS_BPS[component]:
                raise ProjectCompositeKeyError(f"profile {profile.get('profile_id')} has invalid weight for {component}")
            component_hash_value = record.get("component_hash")
            if component_hash_value is not None and not HASH_RE.match(component_hash_value):
                raise ProjectCompositeKeyError(f"profile {profile.get('profile_id')} has invalid hash for {component}")
    for result in match_results:
        if not 0 <= int(result.get("score_bps", -1)) <= 10000:
            raise ProjectCompositeKeyError("S08-P1 match score outside 0..10000")
        if result.get("score_bps", 0) < THRESHOLDS_BPS["strong_auto_match"] and not result.get(
            "manual_review_required"
        ):
            raise ProjectCompositeKeyError("S08-P1 below-strong score must require manual review")
        if result.get("missing_components") and result.get("blocked_by_missing_single_field") is not False:
            raise ProjectCompositeKeyError("S08-P1 missing fields must not create total block")
    for item in review_queue:
        if item.get("queue_type") != "project_identity_manual_review":
            raise ProjectCompositeKeyError("S08-P1 review queue type mismatch")
        if item.get("auto_merge_allowed") is not False:
            raise ProjectCompositeKeyError("S08-P1 review queue cannot allow auto merge")
    forbidden_hits = _walk_forbidden_keys([manifest, profiles, match_results, review_queue])
    if forbidden_hits:
        raise ProjectCompositeKeyError("forbidden public keys found: " + ", ".join(forbidden_hits))


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ProjectCompositeKeyError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ProjectCompositeKeyError(f"{path} contains a non-object JSONL record")
                records.append(value)
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def write_default_artifacts(generated_at: str) -> dict[str, Any]:
    manifest, profiles, match_results, review_queue = build_default_project_composite_key(generated_at=generated_at)
    validate_project_composite_key_artifacts(manifest, profiles, match_results, review_queue)
    write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    write_jsonl(DEFAULT_OUTPUT_PROFILES, profiles)
    write_jsonl(DEFAULT_OUTPUT_MATCHES, match_results)
    write_jsonl(DEFAULT_OUTPUT_REVIEW_QUEUE, review_queue)
    stage_manifest = {
        "schema_version": "kmfa.s08_p1_manifest.v1",
        "record_type": "s08_p1_project_composite_key_manifest",
        "project_id": "KMFA",
        "stage_phase": "S08-P1",
        "generated_at": generated_at,
        "required_component_count": len(REQUIRED_COMPONENTS),
        "profile_count": len(profiles),
        "match_result_count": len(match_results),
        "manual_review_queue_count": len(review_queue),
        "strong_auto_match_count": manifest["summary"]["strong_auto_match_count"],
        "manifest_ref": "KMFA/metadata/schema_maps/project_composite_key_manifest.json",
        "profiles_ref": "KMFA/metadata/schema_maps/project_identity_profiles.jsonl",
        "match_results_ref": "KMFA/metadata/schema_maps/project_composite_key_matches.jsonl",
        "manual_review_queue_ref": "KMFA/metadata/quality/project_identity_review_queue.jsonl",
        "completion_record_ref": "KMFA/stage_artifacts/S08_P1_project_composite_key/human/s08_p1_completion_record.md",
        "test_results_ref": "KMFA/stage_artifacts/S08_P1_project_composite_key/human/test_results.md",
        "validator_ref": "KMFA/tools/check_s08_p1_project_composite_key.py",
        "github_upload_allowed": False,
        "formal_report_allowed": False,
        "fact_layer_scope_included": False,
        "public_repo_safety": manifest["public_repo_safety"],
    }
    write_json(DEFAULT_OUTPUT_STAGE_MANIFEST, stage_manifest)
    return stage_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S08-P1 project composite key artifacts.")
    parser.add_argument("--generated-at", default="2026-06-30T20:00:00+10:00")
    args = parser.parse_args(argv)
    stage_manifest = write_default_artifacts(args.generated_at)
    print(
        "PASS: KMFA S08-P1 project composite key artifacts written "
        f"(profiles={stage_manifest['profile_count']}, "
        f"matches={stage_manifest['match_result_count']}, "
        f"manual_review_queue={stage_manifest['manual_review_queue_count']}, "
        "formal_report_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
