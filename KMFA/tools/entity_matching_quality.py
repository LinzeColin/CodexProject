#!/usr/bin/env python3
"""Build KMFA S08-P3 public-safe entity matching quality evidence.

The quality harness stress-tests project/entity matching with same-name,
multi-entity, multi-account, and multi-period scenarios. Public outputs keep
refs, hashes, scores, risk signals, review states, and evidence refs only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "quality" / "entity_matching_quality_manifest.json"
DEFAULT_OUTPUT_CASES = ROOT / "metadata" / "quality" / "entity_matching_quality_cases.jsonl"
DEFAULT_OUTPUT_REVIEW_QUEUE = ROOT / "metadata" / "quality" / "entity_matching_review_queue.jsonl"
DEFAULT_OUTPUT_REPORT = (
    ROOT / "stage_artifacts" / "S08_P3_entity_matching_quality" / "machine" / "entity_matching_report.json"
)
DEFAULT_OUTPUT_REPORT_MD = (
    ROOT / "stage_artifacts" / "S08_P3_entity_matching_quality" / "human" / "entity_matching_report.md"
)
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S08_P3_entity_matching_quality" / "machine" / "s08_p3_manifest.json"
)

QUALITY_SCENARIOS = (
    "same_project_name",
    "multiple_company_entities",
    "multiple_accounts",
    "multiple_periods",
)

FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "raw_file_bytes",
    "original_filename",
    "private_csv",
    "bank_account_number",
    "account_number",
    "identity_document_number",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "password",
    "token",
    "api_key",
    "private_key",
}
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")


class EntityMatchingQualityError(ValueError):
    """Raised when S08-P3 entity matching quality evidence is invalid."""


def require_text(value: Any, field_name: str) -> str:
    if value is None:
        raise EntityMatchingQualityError(f"{field_name} is required")
    text = str(value).strip()
    if not text:
        raise EntityMatchingQualityError(f"{field_name} is required")
    return text


def _sha256_for(label: str) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _case(
    *,
    index: int,
    scenario_type: str,
    score_bps: int,
    risk_level: str,
    matched_components: list[str],
    mismatched_components: list[str],
    missing_components: list[str],
    risk_signals: list[str],
    manual_review_required: bool,
) -> dict[str, Any]:
    case_id = f"EMQ-S08P3-{index:03d}"
    return {
        "schema_version": "kmfa.entity_matching_quality_case.v1",
        "record_type": "entity_matching_quality_case",
        "project_id": "KMFA",
        "stage_phase": "S08-P3",
        "case_id": case_id,
        "scenario_type": scenario_type,
        "profile_ref": f"KMFA/metadata/schema_maps/project_identity_profiles.jsonl#{case_id}",
        "entity_ref": f"KMFA/metadata/schema_maps/business_entity_model_schema.json#{scenario_type}",
        "authority_profile_ref": f"profile_ref://KMFA/S08-P1/AUTH/{index:03d}",
        "candidate_profile_ref": f"profile_ref://KMFA/S08-P1/CAND/{index:03d}",
        "authority_entity_ref": f"entity_ref://KMFA/S08-P2/project/AUTH/{index:03d}",
        "candidate_entity_ref": f"entity_ref://KMFA/S08-P2/project/CAND/{index:03d}",
        "source_hash": _sha256_for(f"S08-P3:{scenario_type}:{index}"),
        "source_refs": [
            f"source_ref://KMFA/S08-P3/{scenario_type}/authority",
            f"source_ref://KMFA/S08-P3/{scenario_type}/candidate",
        ],
        "matched_components": matched_components,
        "mismatched_components": mismatched_components,
        "missing_components": missing_components,
        "risk_signals": risk_signals,
        "risk_level": risk_level,
        "score_bps": score_bps,
        "thresholds_bps": {
            "strong_auto_match": 8500,
            "human_review": 7000,
            "weak_candidate": 5000,
        },
        "manual_review_required": manual_review_required,
        "auto_merge_allowed": not manual_review_required,
        "quality_decision": "manual_review_required" if manual_review_required else "quality_control_passed",
        "raw_layer_write_allowed": False,
        "evidence_ref": "KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/test_results.md",
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "field_plaintext_committed": False,
            "raw_file_committed": False,
            "private_tabular_files_committed": False,
        },
    }


def build_default_entity_matching_quality(
    *, generated_at: str
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    generated_at_value = require_text(generated_at, "generated_at")
    cases = [
        _case(
            index=1,
            scenario_type="same_project_name",
            score_bps=7600,
            risk_level="high",
            matched_components=["project_name", "counterparty", "company_entity", "responsible_person"],
            mismatched_components=["contract_number", "occurrence_or_project_date", "amount_signature"],
            missing_components=["source_hash"],
            risk_signals=["same_name_with_conflicting_contract_ref", "same_name_with_period_or_amount_conflict"],
            manual_review_required=True,
        ),
        _case(
            index=2,
            scenario_type="multiple_company_entities",
            score_bps=6900,
            risk_level="high",
            matched_components=["project_name", "counterparty", "occurrence_or_project_date", "amount_signature"],
            mismatched_components=["company_entity", "contract_number"],
            missing_components=["responsible_person", "source_hash"],
            risk_signals=["company_entity_mismatch", "candidate_below_human_review_threshold"],
            manual_review_required=True,
        ),
        _case(
            index=3,
            scenario_type="multiple_accounts",
            score_bps=7300,
            risk_level="medium",
            matched_components=["contract_number", "project_name", "counterparty", "company_entity"],
            mismatched_components=["source_hash"],
            missing_components=["occurrence_or_project_date", "amount_signature", "responsible_person"],
            risk_signals=["account_ref_variance", "missing_period_amount_owner_components"],
            manual_review_required=True,
        ),
        _case(
            index=4,
            scenario_type="multiple_periods",
            score_bps=8800,
            risk_level="low",
            matched_components=[
                "contract_number",
                "project_name",
                "counterparty",
                "company_entity",
                "amount_signature",
                "responsible_person",
                "source_hash",
            ],
            mismatched_components=["occurrence_or_project_date"],
            missing_components=[],
            risk_signals=["period_ref_variance_checked"],
            manual_review_required=False,
        ),
    ]
    review_queue = [
        {
            "schema_version": "kmfa.entity_matching_quality_review_queue.v1",
            "record_type": "entity_matching_quality_review_queue_item",
            "queue_id": f"EMQ-REVIEW-S08P3-{index:03d}",
            "queue_type": "entity_matching_quality_manual_review",
            "case_id": case["case_id"],
            "scenario_type": case["scenario_type"],
            "risk_level": case["risk_level"],
            "score_bps": case["score_bps"],
            "risk_signals": list(case["risk_signals"]),
            "status": "pending_human_review",
            "auto_merge_allowed": False,
            "raw_layer_write_allowed": False,
            "evidence_ref": "KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/test_results.md",
        }
        for index, case in enumerate(cases, start=1)
        if case["manual_review_required"]
    ]
    report = {
        "schema_version": "kmfa.entity_matching_report.v1",
        "record_type": "entity_matching_report",
        "report_type": "entity_matching_report",
        "project_id": "KMFA",
        "stage_phase": "S08-P3",
        "generated_at": generated_at_value,
        "scenario_count": len(QUALITY_SCENARIOS),
        "quality_case_count": len(cases),
        "manual_review_queue_count": len(review_queue),
        "risk_summary": {
            "high": sum(1 for case in cases if case["risk_level"] == "high"),
            "medium": sum(1 for case in cases if case["risk_level"] == "medium"),
            "low": sum(1 for case in cases if case["risk_level"] == "low"),
        },
        "tested_scenarios": list(QUALITY_SCENARIOS),
        "cases_ref": "KMFA/metadata/quality/entity_matching_quality_cases.jsonl",
        "review_queue_ref": "KMFA/metadata/quality/entity_matching_review_queue.jsonl",
        "formal_report_allowed": False,
        "q5_calculation_baseline_allowed": False,
        "github_upload_allowed": False,
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "field_plaintext_committed": False,
            "raw_file_committed": False,
            "private_tabular_files_committed": False,
        },
    }
    manifest = {
        "schema_version": "kmfa.entity_matching_quality_manifest.v1",
        "record_type": "entity_matching_quality_manifest",
        "project_id": "KMFA",
        "stage_phase": "S08-P3",
        "generated_at": generated_at_value,
        "quality_scenarios": list(QUALITY_SCENARIOS),
        "summary": {
            "scenario_count": len(QUALITY_SCENARIOS),
            "quality_case_count": len(cases),
            "manual_review_queue_count": len(review_queue),
            "entity_matching_report_count": 1,
        },
        "stage_scope": {
            "s08_p1_project_composite_key_scope_included": False,
            "s08_p2_entity_model_scope_included": False,
            "s08_p3_matching_quality_scope_included": True,
            "stage8_review_scope_included": False,
            "fact_layer_scope_included": False,
            "lineage_full_check_scope_included": False,
            "formal_report_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
        },
        "quality_gate": {
            "formal_report_allowed": False,
            "q5_calculation_baseline_allowed": False,
            "github_upload_allowed": False,
            "phase_completion_upload_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
        },
        "artifact_refs": {
            "quality_cases": "KMFA/metadata/quality/entity_matching_quality_cases.jsonl",
            "review_queue": "KMFA/metadata/quality/entity_matching_review_queue.jsonl",
            "entity_matching_report": "KMFA/stage_artifacts/S08_P3_entity_matching_quality/machine/entity_matching_report.json",
            "completion_record": "KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/s08_p3_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/test_results.md",
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "field_plaintext_committed": False,
            "raw_file_committed": False,
            "private_tabular_files_committed": False,
        },
    }
    return manifest, cases, report, review_queue


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


def _require_false(container: dict[str, Any], path: str) -> None:
    for key, value in container.items():
        if value is not False:
            raise EntityMatchingQualityError(f"{path}.{key} must be false")


def validate_entity_matching_quality_artifacts(
    manifest: dict[str, Any],
    cases: list[dict[str, Any]],
    report: dict[str, Any],
    review_queue: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.entity_matching_quality_manifest.v1":
        raise EntityMatchingQualityError("invalid S08-P3 manifest schema_version")
    if report.get("schema_version") != "kmfa.entity_matching_report.v1":
        raise EntityMatchingQualityError("invalid S08-P3 entity_matching_report schema_version")
    if tuple(manifest.get("quality_scenarios", [])) != QUALITY_SCENARIOS:
        raise EntityMatchingQualityError("S08-P3 quality scenarios mismatch")
    if {case.get("scenario_type") for case in cases} != set(QUALITY_SCENARIOS):
        raise EntityMatchingQualityError("S08-P3 case scenario coverage mismatch")
    summary = manifest.get("summary", {})
    if summary.get("scenario_count") != len(QUALITY_SCENARIOS):
        raise EntityMatchingQualityError("S08-P3 scenario count mismatch")
    if summary.get("quality_case_count") != len(cases):
        raise EntityMatchingQualityError("S08-P3 quality case count mismatch")
    if summary.get("manual_review_queue_count") != len(review_queue):
        raise EntityMatchingQualityError("S08-P3 review queue count mismatch")
    if report.get("report_type") != "entity_matching_report":
        raise EntityMatchingQualityError("S08-P3 must output entity_matching_report")
    if report.get("quality_case_count") != len(cases):
        raise EntityMatchingQualityError("S08-P3 report case count mismatch")
    if report.get("manual_review_queue_count") != len(review_queue):
        raise EntityMatchingQualityError("S08-P3 report queue count mismatch")
    if manifest.get("stage_scope", {}).get("s08_p3_matching_quality_scope_included") is not True:
        raise EntityMatchingQualityError("S08-P3 scope must be included")
    for excluded_scope in (
        "stage8_review_scope_included",
        "fact_layer_scope_included",
        "lineage_full_check_scope_included",
        "formal_report_scope_included",
        "ui_scope_included",
        "external_connector_scope_included",
    ):
        if manifest.get("stage_scope", {}).get(excluded_scope) is not False:
            raise EntityMatchingQualityError(f"S08-P3 must exclude {excluded_scope}")
    _require_false(manifest.get("quality_gate", {}), "manifest.quality_gate")
    _require_false(manifest.get("public_repo_safety", {}), "manifest.public_repo_safety")
    _require_false(report.get("public_repo_safety", {}), "report.public_repo_safety")
    if report.get("formal_report_allowed") is not False or report.get("github_upload_allowed") is not False:
        raise EntityMatchingQualityError("S08-P3 report cannot allow formal report or GitHub upload")

    review_case_ids = {item.get("case_id") for item in review_queue}
    for case in cases:
        if case.get("source_hash") and not HASH_RE.match(case["source_hash"]):
            raise EntityMatchingQualityError(f"{case.get('case_id')} source_hash must be sha256")
        if case.get("raw_layer_write_allowed") is not False:
            raise EntityMatchingQualityError("S08-P3 case cannot allow raw layer writes")
        _require_false(case.get("public_repo_safety", {}), f"case.{case.get('case_id')}.public_repo_safety")
        if case.get("risk_level") in {"medium", "high"}:
            if case.get("manual_review_required") is not True:
                raise EntityMatchingQualityError(f"{case.get('case_id')} medium/high risk requires manual review")
            if case.get("auto_merge_allowed") is not False:
                raise EntityMatchingQualityError(f"{case.get('case_id')} cannot auto merge risky matches")
            if case.get("case_id") not in review_case_ids:
                raise EntityMatchingQualityError(f"{case.get('case_id')} missing review queue item")
    for queue_item in review_queue:
        if queue_item.get("queue_type") != "entity_matching_quality_manual_review":
            raise EntityMatchingQualityError("S08-P3 review queue type mismatch")
        if queue_item.get("auto_merge_allowed") is not False:
            raise EntityMatchingQualityError("S08-P3 review queue cannot auto merge")
        if queue_item.get("raw_layer_write_allowed") is not False:
            raise EntityMatchingQualityError("S08-P3 review queue cannot write raw layer")

    forbidden_hits = _walk_forbidden_keys([manifest, cases, report, review_queue])
    if forbidden_hits:
        raise EntityMatchingQualityError("forbidden public keys found: " + ", ".join(forbidden_hits))


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise EntityMatchingQualityError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise EntityMatchingQualityError(f"{path} contains a non-object JSONL record")
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


def render_report_markdown(report: dict[str, Any]) -> str:
    risk_summary = report["risk_summary"]
    return "\n".join(
        [
            "# S08-P3 Entity Matching Report",
            "",
            f"generated_at: `{report['generated_at']}`",
            f"quality_case_count: `{report['quality_case_count']}`",
            f"manual_review_queue_count: `{report['manual_review_queue_count']}`",
            f"risk_summary: `high={risk_summary['high']}; medium={risk_summary['medium']}; low={risk_summary['low']}`",
            "formal_report_allowed: `false`",
            "github_upload_allowed: `false`",
            "",
            "## Scope",
            "",
            "- Public-safe S08-P3 matching quality report only.",
            "- Same-name, multi-entity, multi-account, and multi-period scenarios are covered.",
            "- Medium/high mismatch risks enter manual review with auto_merge_allowed=false.",
            "- No raw business data, field plaintext, fact layer, lineage, UI, external connector, Stage 8 review, formal report, or GitHub upload is included.",
            "",
        ]
    )


def write_default_artifacts(generated_at: str) -> dict[str, Any]:
    manifest, cases, report, review_queue = build_default_entity_matching_quality(generated_at=generated_at)
    validate_entity_matching_quality_artifacts(manifest, cases, report, review_queue)
    write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    write_jsonl(DEFAULT_OUTPUT_CASES, cases)
    write_jsonl(DEFAULT_OUTPUT_REVIEW_QUEUE, review_queue)
    write_json(DEFAULT_OUTPUT_REPORT, report)
    DEFAULT_OUTPUT_REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_REPORT_MD.write_text(render_report_markdown(report), encoding="utf-8")
    stage_manifest = {
        "schema_version": "kmfa.s08_p3_manifest.v1",
        "record_type": "s08_p3_entity_matching_quality_manifest",
        "project_id": "KMFA",
        "stage_phase": "S08-P3",
        "generated_at": generated_at,
        "scenario_count": manifest["summary"]["scenario_count"],
        "quality_case_count": manifest["summary"]["quality_case_count"],
        "manual_review_queue_count": manifest["summary"]["manual_review_queue_count"],
        "entity_matching_report_count": manifest["summary"]["entity_matching_report_count"],
        "quality_manifest_ref": "KMFA/metadata/quality/entity_matching_quality_manifest.json",
        "quality_cases_ref": "KMFA/metadata/quality/entity_matching_quality_cases.jsonl",
        "review_queue_ref": "KMFA/metadata/quality/entity_matching_review_queue.jsonl",
        "entity_matching_report_ref": "KMFA/stage_artifacts/S08_P3_entity_matching_quality/machine/entity_matching_report.json",
        "entity_matching_report_human_ref": "KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/entity_matching_report.md",
        "completion_record_ref": "KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/s08_p3_completion_record.md",
        "test_results_ref": "KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/test_results.md",
        "validator_ref": "KMFA/tools/check_s08_p3_entity_matching_quality.py",
        "github_upload_allowed": False,
        "formal_report_allowed": False,
        "fact_layer_scope_included": False,
        "stage8_review_scope_included": False,
        "public_repo_safety": manifest["public_repo_safety"],
    }
    write_json(DEFAULT_OUTPUT_STAGE_MANIFEST, stage_manifest)
    return stage_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S08-P3 entity matching quality artifacts.")
    parser.add_argument("--generated-at", default="2026-06-30T22:00:00+10:00")
    args = parser.parse_args(argv)
    stage_manifest = write_default_artifacts(args.generated_at)
    print(
        "PASS: KMFA S08-P3 entity matching quality artifacts written "
        f"(scenarios={stage_manifest['scenario_count']}, "
        f"quality_cases={stage_manifest['quality_case_count']}, "
        f"manual_review_queue={stage_manifest['manual_review_queue_count']}, "
        "formal_report_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
