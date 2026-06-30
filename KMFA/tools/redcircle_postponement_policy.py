#!/usr/bin/env python3
"""Build KMFA S07-P3 Redcircle export postponement policy artifacts.

S07-P3 reserves Redcircle export templates and explicitly postpones automatic
connectors. Public artifacts contain only template ids, hashes, private refs,
controls, and evidence refs; they do not contain raw business rows or source
field plaintext.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "schema_maps" / "redcircle_postponement_manifest.json"
DEFAULT_OUTPUT_TEMPLATES = ROOT / "metadata" / "schema_maps" / "redcircle_reserved_export_templates.jsonl"
DEFAULT_OUTPUT_POLICY = ROOT / "metadata" / "schema_maps" / "redcircle_postponement_policy.yaml"
DEFAULT_OUTPUT_REGISTRY = ROOT / "metadata" / "imports" / "redcircle_export_source_registry.json"
DEFAULT_OUTPUT_CONNECTOR_POLICY = (
    ROOT
    / "stage_artifacts"
    / "S07_P3_redcircle_postponement_policy"
    / "machine"
    / "redcircle_connector_postponement_policy.json"
)
DEFAULT_OUTPUT_ROLLBACK_PLAN = (
    ROOT
    / "stage_artifacts"
    / "S07_P3_redcircle_postponement_policy"
    / "machine"
    / "redcircle_future_rollback_plan.jsonl"
)
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT
    / "stage_artifacts"
    / "S07_P3_redcircle_postponement_policy"
    / "machine"
    / "s07_p3_manifest.json"
)

HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
REQUIRED_REDCIRCLE_EXPORT_TYPES = (
    "operating",
    "contract",
    "collection",
    "finance",
)
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "source_header_text",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "original_filename",
    "bank_account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
    "contract_plaintext",
}


@dataclass(frozen=True)
class RedcircleTemplateSpec:
    export_type: str
    template_id: str
    source_ref: str
    source_file_private_ref: str
    template_section_refs: tuple[str, ...]


REDCIRCLE_TEMPLATE_SPECS = (
    RedcircleTemplateSpec(
        "operating",
        "TMPL-REDCIRCLE-OPERATING-001",
        "SRC-REDCIRCLE-OPERATING-RESERVED",
        "private://KMFA/S07-P3/redcircle/source/SRC-REDCIRCLE-OPERATING-RESERVED",
        ("section:operating-summary-ref", "section:project-portfolio-ref", "section:workflow-status-ref"),
    ),
    RedcircleTemplateSpec(
        "contract",
        "TMPL-REDCIRCLE-CONTRACT-001",
        "SRC-REDCIRCLE-CONTRACT-RESERVED",
        "private://KMFA/S07-P3/redcircle/source/SRC-REDCIRCLE-CONTRACT-RESERVED",
        ("section:contract-index-ref", "section:milestone-ref", "section:counterparty-link-ref"),
    ),
    RedcircleTemplateSpec(
        "collection",
        "TMPL-REDCIRCLE-COLLECTION-001",
        "SRC-REDCIRCLE-COLLECTION-RESERVED",
        "private://KMFA/S07-P3/redcircle/source/SRC-REDCIRCLE-COLLECTION-RESERVED",
        ("section:collection-status-ref", "section:invoice-link-ref", "section:follow-up-ref"),
    ),
    RedcircleTemplateSpec(
        "finance",
        "TMPL-REDCIRCLE-FINANCE-001",
        "SRC-REDCIRCLE-FINANCE-RESERVED",
        "private://KMFA/S07-P3/redcircle/source/SRC-REDCIRCLE-FINANCE-RESERVED",
        ("section:project-finance-ref", "section:cost-link-ref", "section:approval-flow-ref"),
    ),
)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def require_export_type(export_type: str) -> str:
    if export_type not in REQUIRED_REDCIRCLE_EXPORT_TYPES:
        raise ValueError(f"unknown Redcircle export type: {export_type!r}")
    return export_type


def future_controls() -> dict[str, bool]:
    return {
        "read_only_required": True,
        "hash_retention_required": True,
        "rollback_plan_required": True,
        "manual_approval_required": True,
        "source_header_plaintext_committed": False,
        "raw_business_values_committed": False,
        "raw_file_committed": False,
    }


def build_template_contract_hash(spec: RedcircleTemplateSpec) -> str:
    payload = {
        "stage_phase": "S07-P3",
        "export_type": spec.export_type,
        "template_id": spec.template_id,
        "template_section_refs": list(spec.template_section_refs),
        "automatic_connector_allowed": False,
        "future_ingestion_controls": future_controls(),
    }
    return sha256_text(canonical_json(payload))


def build_template_records(generated_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for spec in REDCIRCLE_TEMPLATE_SPECS:
        records.append(
            {
                "record_type": "redcircle_reserved_export_template",
                "schema_version": "kmfa.redcircle_reserved_export_template.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P3",
                "generated_at": generated_at,
                "template_id": spec.template_id,
                "template_status": "reserved_postponed",
                "export_type": spec.export_type,
                "source_ref": spec.source_ref,
                "source_file_private_ref": spec.source_file_private_ref,
                "template_contract_hash": build_template_contract_hash(spec),
                "template_section_refs": list(spec.template_section_refs),
                "manual_export_file_allowed": True,
                "automatic_connector_allowed": False,
                "d15_file_mvp_automatic_connector_allowed": False,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "future_ingestion_controls": future_controls(),
                "quality_state": {
                    "machine_candidate_quality_grade": "Q1_reserved_template",
                    "q4_human_confirmed": False,
                    "q5_calculation_baseline_allowed": False,
                    "formal_report_allowed": False,
                },
                "public_repo_safety": {
                    "raw_business_values_committed": False,
                    "normalized_business_values_committed": False,
                    "source_header_plaintext_committed": False,
                    "raw_file_committed": False,
                    "private_csv_committed": False,
                },
                "next_required_phase": "Stage 7 review before downstream lineage or fact layer use",
            }
        )
    return records


def build_connector_policy(generated_at: str) -> dict[str, Any]:
    return {
        "record_type": "redcircle_connector_postponement_policy",
        "schema_version": "kmfa.redcircle_connector_postponement_policy.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P3",
        "generated_at": generated_at,
        "connector_status": "postponed_until_after_file_mvp",
        "d15_file_mvp_automatic_connector_allowed": False,
        "external_connector_included": False,
        "manual_export_file_allowed": True,
        "covered_export_types": list(REQUIRED_REDCIRCLE_EXPORT_TYPES),
        "future_connector_controls": future_controls(),
        "hard_blocks": [
            "automatic_connector_before_stage7_review",
            "missing_read_only_contract",
            "missing_hash_retention",
            "missing_rollback_plan",
            "missing_manual_approval",
        ],
        "evidence_ref": "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/human/s07_p3_completion_record.md",
    }


def build_rollback_plan(generated_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for spec in REDCIRCLE_TEMPLATE_SPECS:
        records.append(
            {
                "record_type": "redcircle_future_rollback_plan",
                "schema_version": "kmfa.redcircle_future_rollback_plan.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P3",
                "generated_at": generated_at,
                "rollback_plan_id": f"RBK-{spec.template_id}",
                "export_type": spec.export_type,
                "source_ref": spec.source_ref,
                "rollback_status": "required_before_ingestion",
                "read_only_required": True,
                "hash_retention_required": True,
                "rollback_plan_required": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "rollback_trigger_refs": [
                    "trigger:source-hash-mismatch",
                    "trigger:template-contract-drift",
                    "trigger:authorization-revoked",
                    "trigger:connector-side-effect-detected",
                ],
                "rollback_actions": [
                    "disable_future_redcircle_ingestion",
                    "preserve_prior_hash_manifest",
                    "invalidate_downstream_derived_outputs",
                    "return_to_manual_export_file_mode",
                ],
            }
        )
    return records


def build_source_registry(templates: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "record_type": "redcircle_export_source_registry",
        "schema_version": "kmfa.redcircle_export_source_registry.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P3",
        "generated_at": generated_at,
        "registry_status": "reserved_templates_only_no_connector",
        "sources": [
            {
                "source_ref": template["source_ref"],
                "export_type": template["export_type"],
                "template_id": template["template_id"],
                "template_contract_hash": template["template_contract_hash"],
                "source_file_private_ref": template["source_file_private_ref"],
                "template_status": template["template_status"],
                "manual_export_file_allowed": True,
                "automatic_connector_allowed": False,
                "read_only_required": True,
                "hash_retention_required": True,
                "rollback_plan_required": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
            }
            for template in templates
        ],
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_committed": False,
            "private_csv_committed": False,
        },
    }


def build_manifest(
    templates: list[dict[str, Any]],
    connector_policy: dict[str, Any],
    rollback_plan: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "record_type": "s07_p3_redcircle_postponement_manifest",
        "schema_version": "kmfa.s07_p3_manifest.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P3",
        "generated_at": generated_at,
        "redcircle_export_types": list(REQUIRED_REDCIRCLE_EXPORT_TYPES),
        "summary": {
            "reserved_template_count": len(templates),
            "connector_policy_count": 1,
            "rollback_plan_count": len(rollback_plan),
            "automatic_connector_allowed_count": 0,
        },
        "stage_scope": {
            "finance_scope_included": False,
            "wps_scope_included": False,
            "redcircle_scope_included": True,
            "external_connector_included": False,
            "facts_layer_write_included": False,
            "formal_report_generation_included": False,
            "stage7_review_included": False,
            "github_upload_allowed": False,
        },
        "mvp_scope": {
            "d15_file_mvp_automatic_connector_allowed": False,
            "manual_export_file_allowed": True,
            "reserved_templates_only": True,
        },
        "future_required_controls": connector_policy["future_connector_controls"],
        "quality_gate": {
            "formal_report_allowed": False,
            "q5_calculation_baseline_allowed": False,
            "release_gate": "blocked_until_stage7_review",
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_committed": False,
            "private_csv_committed": False,
        },
        "template_records_ref": display_path(DEFAULT_OUTPUT_TEMPLATES),
        "connector_policy_ref": display_path(DEFAULT_OUTPUT_CONNECTOR_POLICY),
        "rollback_plan_ref": display_path(DEFAULT_OUTPUT_ROLLBACK_PLAN),
        "source_registry_ref": display_path(DEFAULT_OUTPUT_REGISTRY),
        "validator_ref": "KMFA/tools/check_s07_p3_redcircle_postponement.py",
        "completion_record_ref": (
            "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/human/s07_p3_completion_record.md"
        ),
        "test_results_ref": "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/human/test_results.md",
    }


def build_policy_yaml() -> str:
    lines = [
        'schema_version: "kmfa.redcircle_postponement_policy.v1"',
        'project_id: "KMFA"',
        'stage_phase: "S07-P3"',
        'policy_status: "reserved_templates_only_no_connector"',
        "required_export_types:",
    ]
    for export_type in REQUIRED_REDCIRCLE_EXPORT_TYPES:
        lines.append(f'  - "{export_type}"')
    lines.extend(
        [
            "mvp_scope:",
            "  d15_file_mvp_automatic_connector_allowed: false",
            "  manual_export_file_allowed: true",
            "future_connector_controls:",
            "  read_only_required: true",
            "  hash_retention_required: true",
            "  rollback_plan_required: true",
            "  manual_approval_required: true",
            "public_repo_policy:",
            "  raw_business_values_committed: false",
            "  normalized_business_values_committed: false",
            "  source_header_plaintext_committed: false",
            "  raw_file_committed: false",
            "  private_csv_committed: false",
            "out_of_scope:",
            "  automatic_connector_included: false",
            "  facts_layer_write_included: false",
            "  formal_report_generation_included: false",
            "  stage7_review_included: false",
            "  github_upload_allowed: false",
            "evidence_refs:",
            '  - "KMFA/tools/redcircle_postponement_policy.py"',
            '  - "KMFA/tools/check_s07_p3_redcircle_postponement.py"',
            '  - "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/human/s07_p3_completion_record.md"',
            "",
        ]
    )
    return "\n".join(lines)


def build_default_redcircle_postponement_policy(
    generated_at: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    timestamp = generated_at or utc_now()
    templates = build_template_records(timestamp)
    connector_policy = build_connector_policy(timestamp)
    rollback_plan = build_rollback_plan(timestamp)
    manifest = build_manifest(templates, connector_policy, rollback_plan, timestamp)
    return manifest, templates, connector_policy, rollback_plan


def classify_redcircle_ingestion_request(
    *,
    export_type: str,
    request_kind: str,
    source_ref: str,
) -> dict[str, Any]:
    required_export_type = require_export_type(export_type)
    if request_kind not in {"manual_export_file", "automatic_connector"}:
        raise ValueError(f"unknown Redcircle request kind: {request_kind!r}")
    is_connector = request_kind == "automatic_connector"
    return {
        "record_type": "redcircle_ingestion_request_plan",
        "schema_version": "kmfa.redcircle_ingestion_request_plan.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P3",
        "export_type": required_export_type,
        "source_ref": source_ref,
        "request_kind": request_kind,
        "request_ref_hash": sha256_text(f"S07-P3:{required_export_type}:{request_kind}:{source_ref}"),
        "ingestion_decision": "blocked_for_d15_file_mvp" if is_connector else "allowed_after_private_file_registration",
        "manual_export_file_allowed": not is_connector,
        "automatic_connector_allowed": False,
        "future_ingestion_controls": future_controls(),
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_committed": False,
            "private_csv_committed": False,
        },
    }


def walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(walk_keys(child))
    elif isinstance(value, list):
        for item in value:
            keys.extend(walk_keys(item))
    return keys


def validate_no_forbidden_public_keys(*artifacts: Any) -> None:
    for artifact in artifacts:
        forbidden_hits = sorted(FORBIDDEN_PUBLIC_KEYS.intersection(walk_keys(artifact)))
        if forbidden_hits:
            raise ValueError(f"forbidden public keys present: {forbidden_hits}")


def validate_redcircle_postponement_policy(
    manifest: dict[str, Any],
    templates: list[dict[str, Any]],
    connector_policy: dict[str, Any],
    rollback_plan: list[dict[str, Any]],
    *,
    registry: dict[str, Any] | None = None,
) -> None:
    validate_no_forbidden_public_keys(manifest, templates, connector_policy, rollback_plan, registry or {})
    if manifest.get("stage_phase") != "S07-P3":
        raise ValueError("manifest stage_phase must be S07-P3")
    if set(manifest.get("redcircle_export_types", [])) != set(REQUIRED_REDCIRCLE_EXPORT_TYPES):
        raise ValueError("manifest missing required Redcircle export types")
    if manifest.get("summary", {}).get("reserved_template_count") != len(REQUIRED_REDCIRCLE_EXPORT_TYPES):
        raise ValueError("reserved template count mismatch")
    if manifest.get("summary", {}).get("rollback_plan_count") != len(REQUIRED_REDCIRCLE_EXPORT_TYPES):
        raise ValueError("rollback plan count mismatch")
    if manifest.get("summary", {}).get("automatic_connector_allowed_count") != 0:
        raise ValueError("automatic connector allowed count must be zero")
    if manifest.get("stage_scope", {}).get("external_connector_included") is not False:
        raise ValueError("external connector must remain out of S07-P3 scope")
    if manifest.get("mvp_scope", {}).get("d15_file_mvp_automatic_connector_allowed") is not False:
        raise ValueError("D15 file MVP automatic connector must be blocked")
    if manifest.get("quality_gate", {}).get("formal_report_allowed") is not False:
        raise ValueError("formal report must remain blocked")
    if manifest.get("quality_gate", {}).get("q5_calculation_baseline_allowed") is not False:
        raise ValueError("Q5 calculation baseline must remain blocked")

    template_types = {str(template.get("export_type")) for template in templates}
    if template_types != set(REQUIRED_REDCIRCLE_EXPORT_TYPES):
        raise ValueError("template export type coverage mismatch")
    for template in templates:
        if template.get("template_status") != "reserved_postponed":
            raise ValueError("template must be reserved_postponed")
        if template.get("manual_export_file_allowed") is not True:
            raise ValueError("manual export file must remain allowed")
        if template.get("automatic_connector_allowed") is not False:
            raise ValueError("automatic connector must remain blocked")
        if not HASH_RE.match(str(template.get("template_contract_hash", ""))):
            raise ValueError("template contract hash missing or invalid")
        controls = template.get("future_ingestion_controls", {})
        for key in ("read_only_required", "hash_retention_required", "rollback_plan_required"):
            if controls.get(key) is not True:
                raise ValueError(f"template future control missing: {key}")

    if connector_policy.get("connector_status") != "postponed_until_after_file_mvp":
        raise ValueError("connector policy status mismatch")
    if connector_policy.get("d15_file_mvp_automatic_connector_allowed") is not False:
        raise ValueError("connector policy must block D15 automatic connector")
    controls = connector_policy.get("future_connector_controls", {})
    for key in ("read_only_required", "hash_retention_required", "rollback_plan_required", "manual_approval_required"):
        if controls.get(key) is not True:
            raise ValueError(f"connector future control missing: {key}")

    rollback_types = {str(item.get("export_type")) for item in rollback_plan}
    if rollback_types != set(REQUIRED_REDCIRCLE_EXPORT_TYPES):
        raise ValueError("rollback export type coverage mismatch")
    for item in rollback_plan:
        if item.get("rollback_status") != "required_before_ingestion":
            raise ValueError("rollback plan status mismatch")
        for key in ("read_only_required", "hash_retention_required", "rollback_plan_required"):
            if item.get(key) is not True:
                raise ValueError(f"rollback control missing: {key}")
        if item.get("raw_layer_write_allowed") is not False:
            raise ValueError("rollback plan must block raw layer writes")
        if item.get("raw_source_mutation_allowed") is not False:
            raise ValueError("rollback plan must block source mutation")

    if registry is not None:
        if registry.get("registry_status") != "reserved_templates_only_no_connector":
            raise ValueError("registry status mismatch")
        if len(registry.get("sources", [])) != len(REQUIRED_REDCIRCLE_EXPORT_TYPES):
            raise ValueError("registry source count mismatch")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_outputs(generated_at: str) -> dict[str, Any]:
    manifest, templates, connector_policy, rollback_plan = build_default_redcircle_postponement_policy(generated_at)
    registry = build_source_registry(templates, generated_at)
    validate_redcircle_postponement_policy(manifest, templates, connector_policy, rollback_plan, registry=registry)
    write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    write_jsonl(DEFAULT_OUTPUT_TEMPLATES, templates)
    write_json(DEFAULT_OUTPUT_CONNECTOR_POLICY, connector_policy)
    write_jsonl(DEFAULT_OUTPUT_ROLLBACK_PLAN, rollback_plan)
    write_json(DEFAULT_OUTPUT_REGISTRY, registry)
    write_json(DEFAULT_OUTPUT_STAGE_MANIFEST, manifest)
    DEFAULT_OUTPUT_POLICY.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_POLICY.write_text(build_policy_yaml(), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S07-P3 Redcircle postponement policy artifacts.")
    parser.add_argument("--generated-at", default="2026-06-30T18:00:00+10:00")
    args = parser.parse_args(argv)
    manifest = write_outputs(args.generated_at)
    print(
        "PASS: KMFA S07-P3 Redcircle postponement policy built "
        f"(templates={manifest['summary']['reserved_template_count']}, "
        f"rollback_plans={manifest['summary']['rollback_plan_count']}, "
        "d15_connector_allowed=false, future_controls=readonly_hash_rollback, formal_report_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
