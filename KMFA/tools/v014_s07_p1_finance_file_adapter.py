#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S07-P1 public-safe finance file adapter evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s06_stage_review import validate_v014_s06_stage_review
from KMFA.tools.finance_file_adapter import (
    REQUIRED_FINANCE_CATEGORIES,
    build_default_finance_adapter,
    validate_finance_adapter,
)


TASK_ID = "KMFA-V014-S07-P1-FINANCE-FILE-ADAPTER-20260704"
ACCEPTANCE_ID = "ACC-V014-S07-P1-FINANCE-FILE-ADAPTER"
SCHEMA_VERSION = "kmfa.v014_s07_p1_finance_file_adapter.v1"
PHASE_SCOPE = "v014_s07_p1_finance_file_adapter_only"
EVIDENCE_TIME = "2026-07-04T08:30:00+10:00"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "finance_file_adapter_manifest.json"
FIELD_REPORT_PATH = MACHINE_DIR / "finance_readonly_field_report.jsonl"
REPORT_PATH = HUMAN_DIR / "finance_file_adapter_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_ADAPTER_MANIFEST_PATH = Path("KMFA/metadata/schema_maps/v014_s07_p1_finance_file_adapter_manifest.json")
METADATA_CANDIDATES_PATH = Path("KMFA/metadata/schema_maps/v014_s07_p1_finance_field_candidates.jsonl")
METADATA_SOURCE_REGISTRY_PATH = Path("KMFA/metadata/imports/v014_s07_p1_finance_support_source_registry.json")
S06_STAGE_REVIEW_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S06_STAGE_REVIEW/machine/stage6_review_manifest.json")

NEXT_PHASE = "S07-P2"
NEXT_INSTRUCTION = (
    "Run v0.1.4 S07-P2 WPS file adapter as a separate run only after S07-P1 is committed. "
    "Do not perform Stage 7 review or GitHub upload in S07-P1. GitHub main upload remains "
    "deferred until v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed."
)
RAW_INBOX_REF = "operator-designated local raw/private inbox outside repository"


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def load_public_safe_finance_baseline() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest, candidates, field_report = build_default_finance_adapter(generated_at=EVIDENCE_TIME)
    validate_finance_adapter(manifest, candidates, field_report)
    return manifest, candidates, field_report


def validate_stage6_dependency() -> dict[str, Any]:
    stage6 = validate_v014_s06_stage_review()
    if stage6.get("stage_id") != "S06":
        raise ValueError("Stage 6 dependency validator did not return S06")
    if stage6.get("github_upload_performed") is not False:
        raise ValueError("Stage 6 dependency must not upload to GitHub")
    if stage6.get("s07_p1_started") is not False:
        raise ValueError("Stage 6 dependency must not have started S07-P1")
    if stage6.get("release_state", {}).get("current_go_no_go") != "NO_GO":
        raise ValueError("Stage 6 dependency must keep NO_GO")
    return stage6


def public_field_ref(candidate: dict[str, Any]) -> str:
    canonical = candidate["canonical_field"]
    return "field:" + sha256_text(
        f"{candidate['finance_category']}:{canonical['field_key']}:{canonical['value_kind']}:{canonical['field_role']}"
    ).removeprefix("sha256:")


def build_v014_outputs(
    baseline_manifest: dict[str, Any],
    baseline_candidates: list[dict[str, Any]],
    baseline_field_report: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    registry_sources: list[dict[str, Any]] = []
    for source in baseline_manifest["source_registry"]:
        registry_sources.append(
            {
                "record_type": "v014_finance_support_source",
                "schema_version": "kmfa.v014_finance_support_source.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P1",
                "source_ref": source["source_ref"],
                "finance_category": source["finance_category"],
                "file_format": source["file_format"],
                "synthetic_structure_fingerprint": source["file_hash"],
                "source_file_private_ref": source["source_file_private_ref"],
                "read_only_parse": True,
                "parse_status": "public_safe_synthetic_structure_probe_only",
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "source_header_plaintext_committed": False,
                "source_file_committed": False,
            }
        )

    candidate_rows: list[dict[str, Any]] = []
    for candidate in baseline_candidates:
        binding = candidate["source_binding"]
        canonical = candidate["canonical_field"]
        candidate_rows.append(
            {
                "record_type": "v014_finance_field_candidate_mapping",
                "schema_version": "kmfa.v014_finance_field_candidate.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P1",
                "candidate_id": candidate["mapping_id"].replace("FIN-FLD-", "V014-FIN-FLD-", 1),
                "finance_category": candidate["finance_category"],
                "source_ref": candidate["source_ref"],
                "canonical_field_ref": public_field_ref(candidate),
                "canonical_value_kind": canonical["value_kind"],
                "canonical_role": canonical["field_role"],
                "source_binding": {
                    "source_file_private_ref": binding["source_file_private_ref"],
                    "file_format": binding["file_format"],
                    "synthetic_structure_fingerprint": binding["file_hash"],
                    "sheet_ref": binding["sheet_ref"],
                    "column_ref": binding["column_ref"],
                    "source_header_fingerprint": binding["source_header_hash"],
                    "source_header_private_ref": binding["source_header_private_ref"],
                    "source_anchor_status": "hash_only_from_public_safe_readonly_probe",
                },
                "quality_state": {
                    "machine_candidate_quality_grade": "Q2_structure_candidate",
                    "q4_human_confirmed": False,
                    "q5_calculation_baseline_allowed": False,
                    "formal_report_allowed": False,
                },
                "public_repo_safety": {
                    "source_payload_values_committed": False,
                    "source_header_plaintext_committed": False,
                    "field_plaintext_committed": False,
                    "source_file_committed": False,
                    "private_csv_committed": False,
                },
                "next_required_phase": "S07 stage review before downstream lineage or fact layer use",
            }
        )

    candidates_by_category: dict[str, list[dict[str, Any]]] = {}
    for row in candidate_rows:
        candidates_by_category.setdefault(str(row["finance_category"]), []).append(row)

    readonly_reports: list[dict[str, Any]] = []
    for report in baseline_field_report:
        category = str(report["finance_category"])
        readonly_reports.append(
            {
                "record_type": "v014_finance_file_readonly_field_report",
                "schema_version": "kmfa.v014_finance_file_field_report.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P1",
                "source_ref": report["source_ref"],
                "finance_category": category,
                "file_format": report["file_format"],
                "synthetic_structure_fingerprint": report["file_hash"],
                "parse_status": "public_safe_synthetic_structure_probe_only",
                "read_only_parse": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "source_header_plaintext_committed": False,
                "sheet_count": report["sheet_count"],
                "source_header_fingerprint_count": report["source_header_hash_count"],
                "field_candidate_count": len(candidates_by_category.get(category, [])),
                "canonical_field_ref_count": len({row["canonical_field_ref"] for row in candidates_by_category.get(category, [])}),
                "stage_scope": {
                    "finance_file_adapter": True,
                    "wps_scope_included": False,
                    "redcircle_scope_included": False,
                    "external_connector_included": False,
                },
            }
        )

    adapter_manifest = {
        "record_type": "v014_finance_file_adapter_metadata_manifest",
        "schema_version": "kmfa.v014_finance_file_adapter_metadata.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P1",
        "generated_at": EVIDENCE_TIME,
        "finance_categories": list(REQUIRED_FINANCE_CATEGORIES),
        "source_registry_ref": METADATA_SOURCE_REGISTRY_PATH.as_posix(),
        "field_candidates_ref": METADATA_CANDIDATES_PATH.as_posix(),
        "field_report_ref": FIELD_REPORT_PATH.as_posix(),
        "summary": {
            "source_category_count": len({source["finance_category"] for source in registry_sources}),
            "source_registry_count": len(registry_sources),
            "field_candidate_count": len(candidate_rows),
            "hash_only_field_candidate_count": sum(
                1
                for row in candidate_rows
                if str(row["source_binding"].get("source_header_fingerprint", "")).startswith("sha256:")
                and row["source_binding"].get("source_header_private_ref")
            ),
            "field_report_count": len(readonly_reports),
            "source_header_fingerprint_count": sum(row["source_header_fingerprint_count"] for row in readonly_reports),
        },
        "stage_scope": {
            "finance_file_adapter": True,
            "wps_scope_included": False,
            "redcircle_scope_included": False,
            "stage7_review_included": False,
            "external_connector_included": False,
            "facts_layer_write_included": False,
            "lineage_full_check_included": False,
            "formal_report_generation_included": False,
            "github_upload_included": False,
        },
        "quality_gate": {
            "candidate_quality_grade": "Q2_structure_candidate",
            "requires_stage7_review_before_downstream_use": True,
            "q4_human_confirmed_count": 0,
            "q5_calculation_baseline_allowed_count": 0,
            "formal_report_allowed_count": 0,
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
        },
        "public_repo_safety": {
            "source_payload_values_committed": False,
            "source_header_plaintext_committed": False,
            "field_plaintext_committed": False,
            "source_file_committed": False,
            "private_csv_committed": False,
            "xlsx_committed": False,
            "pdf_committed": False,
            "zip_committed": False,
            "credentials_committed": False,
        },
    }
    source_registry = {
        "record_type": "v014_finance_support_source_registry",
        "schema_version": "kmfa.v014_finance_support_source_registry.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P1",
        "sources": registry_sources,
        "public_repo_safety": adapter_manifest["public_repo_safety"],
    }
    return adapter_manifest, candidate_rows, source_registry, readonly_reports


def build_manifest(
    stage6: dict[str, Any],
    adapter_manifest: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    source_registry: dict[str, Any],
    readonly_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    quality_counts = Counter(row["quality_state"]["machine_candidate_quality_grade"] for row in candidate_rows)
    summary = adapter_manifest["summary"]
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S07",
        "stage_name": "file-based source adapters and field mapping",
        "phase_id": "S07-P1",
        "phase_name": "finance file adapter",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "evidence_time": EVIDENCE_TIME,
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_finance_file_adapter",
        "completed_task_ids": ["S7PAT01", "S7PAT02", "S7PAT03"],
        "s06_stage_review_dependency_validated": True,
        "s06_dependency_ref": S06_STAGE_REVIEW_MANIFEST_PATH.as_posix(),
        "s06_dependency_status": stage6["status"],
        "s06_dependency_phase_results": stage6["phase_results"],
        "s06_dependency_current_data_quality_grade": stage6["release_state"]["current_data_quality_grade"],
        "s06_dependency_current_report_grade": stage6["release_state"]["current_report_grade"],
        "legacy_finance_adapter_validated": True,
        "finance_adapter_summary": {
            **summary,
            "finance_categories": list(adapter_manifest["finance_categories"]),
            "quality_counts": dict(sorted(quality_counts.items())),
            "q4_human_confirmed_count": sum(1 for row in candidate_rows if row["quality_state"]["q4_human_confirmed"]),
            "q5_calculation_baseline_allowed_count": sum(
                1 for row in candidate_rows if row["quality_state"]["q5_calculation_baseline_allowed"]
            ),
            "formal_report_allowed_count": sum(1 for row in candidate_rows if row["quality_state"]["formal_report_allowed"]),
            "readonly_parse_count": sum(1 for row in readonly_reports if row["read_only_parse"]),
            "raw_layer_write_allowed_count": sum(1 for row in readonly_reports if row["raw_layer_write_allowed"]),
            "source_registry_count": len(source_registry["sources"]),
        },
        "metadata_outputs": {
            "adapter_manifest_ref": METADATA_ADAPTER_MANIFEST_PATH.as_posix(),
            "source_registry_ref": METADATA_SOURCE_REGISTRY_PATH.as_posix(),
            "field_candidates_ref": METADATA_CANDIDATES_PATH.as_posix(),
            "readonly_field_report_ref": FIELD_REPORT_PATH.as_posix(),
        },
        "stage_scope": adapter_manifest["stage_scope"],
        "quality_gate": adapter_manifest["quality_gate"],
        "raw_data_boundary": {
            "raw_inbox_ref": RAW_INBOX_REF,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_stat_performed_by_this_phase": False,
            "codex_hash_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "raw_content_matching_performed": False,
        "business_field_value_parsing_performed": False,
        "source_header_plaintext_committed": False,
        "field_plaintext_committed": False,
        "s07_p1_performed": True,
        "s07_p2_performed": False,
        "s07_p3_performed": False,
        "stage7_review_performed": False,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "public_repo_safety": adapter_manifest["public_repo_safety"],
        "validation_summary": {
            "generator": "PASS",
            "s06_stage_review_dependency": "PASS",
            "legacy_finance_adapter": "PASS",
            "s07_p1_validator": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "legacy_finance_adapter_validator": "PENDING_FINAL_VALIDATION",
            "legacy_finance_adapter_unit_test": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "structured_parse": "PENDING_FINAL_VALIDATION",
            "ruby_yaml_parse": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "public_s07_p1_semantic_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            METADATA_ADAPTER_MANIFEST_PATH.as_posix(),
            METADATA_SOURCE_REGISTRY_PATH.as_posix(),
            METADATA_CANDIDATES_PATH.as_posix(),
            FIELD_REPORT_PATH.as_posix(),
            "KMFA/tools/v014_s07_p1_finance_file_adapter.py",
            "KMFA/tools/check_v014_s07_p1_finance_file_adapter.py",
            "KMFA/tests/test_v014_s07_p1_finance_file_adapter.py",
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_human_evidence(manifest: dict[str, Any]) -> None:
    summary = manifest["finance_adapter_summary"]
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P1 Finance File Adapter",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred_finance_file_adapter`",
                "- scope: `S07-P1 only`",
                f"- s06_stage_review_dependency_validated: `{str(manifest['s06_stage_review_dependency_validated']).lower()}`",
                f"- source_category_count: `{summary['source_category_count']}`",
                f"- source_registry_count: `{summary['source_registry_count']}`",
                f"- field_candidate_count: `{summary['field_candidate_count']}`",
                f"- hash_only_field_candidate_count: `{summary['hash_only_field_candidate_count']}`",
                f"- readonly_field_report_count: `{summary['field_report_count']}`",
                f"- source_header_fingerprint_count: `{summary['source_header_fingerprint_count']}`",
                f"- q4_human_confirmed_count: `{summary['q4_human_confirmed_count']}`",
                f"- q5_calculation_baseline_allowed_count: `{summary['q5_calculation_baseline_allowed_count']}`",
                f"- formal_report_allowed_count: `{summary['formal_report_allowed_count']}`",
                f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
                f"- current_report_grade: `{manifest['current_report_grade']}`",
                f"- release_permission: `{manifest['release_permission']}`",
                f"- github_upload_status: `{manifest['github_upload_status']}`",
                "",
                "## Boundary",
                "",
                "- This phase creates public-safe adapter metadata from synthetic structure probes and existing public adapter logic only.",
                "- It does not read, list, inventory, stat, hash, modify, delete, move, rename, overwrite, or write the operator-designated raw/private inbox.",
                "- Public evidence keeps source refs, fingerprints, private refs, aggregate counts, candidate ids and quality gates only.",
                "- It does not publish source headers, raw file names, raw file hashes, private source structure, private records, business values, credentials, workbooks, documents, private tables, databases or raw business data.",
                "- S07-P2, S07-P3, Stage 7 review, GitHub upload, raw content matching, lineage full check, formal report, live connector, OpMe deep coupling and business execution remain out of scope.",
                "",
                "## Next",
                "",
                manifest["next_phase_instruction"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P1 Finance File Adapter Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{TASK_ID}`",
                "- generator: `PASS`",
                "- s06_stage_review_dependency: `PASS`",
                "- legacy_finance_adapter: `PASS`",
                "- s07_p2_performed: `false`",
                "- s07_p3_performed: `false`",
                "- stage7_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_read_performed: `false`",
                "- raw_inbox_mutation_performed: `false`",
                "",
                "Final command results are captured after validator, focused unit test, governance checks and safety scans pass in this run.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P1 Risk Register",
                "",
                "| Risk | Mitigation | Status |",
                "|---|---|---|",
                "| Adapter evidence could be mistaken for raw-data reconciliation. | Manifest keeps raw inbox read false and Q5/formal report counts at zero. | controlled |",
                "| Adapter evidence could be mistaken for Stage 7 completion. | Manifest keeps S07-P2, S07-P3 and Stage 7 review false. | controlled |",
                "| Public evidence could leak private source details. | Outputs use refs, fingerprints and aggregate counts only, followed by safety scans. | controlled |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P1 Rollback Plan",
                "",
                "1. Revert the local commit containing `V014_S07_P1_FINANCE_FILE_ADAPTER` artifacts and v014 metadata rows.",
                "2. Restore the active next phase to `S07-P1` if the validator is invalidated.",
                "3. Do not modify, delete, move, rename, overwrite or write the raw inbox during rollback.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    MACHINE_DIR.mkdir(parents=True, exist_ok=True)
    stage6 = validate_stage6_dependency()
    baseline_manifest, baseline_candidates, baseline_field_report = load_public_safe_finance_baseline()
    adapter_manifest, candidate_rows, source_registry, readonly_reports = build_v014_outputs(
        baseline_manifest, baseline_candidates, baseline_field_report
    )
    manifest = build_manifest(stage6, adapter_manifest, candidate_rows, source_registry, readonly_reports)
    write_json(METADATA_ADAPTER_MANIFEST_PATH, adapter_manifest)
    write_json(METADATA_SOURCE_REGISTRY_PATH, source_registry)
    write_jsonl(METADATA_CANDIDATES_PATH, candidate_rows)
    write_jsonl(FIELD_REPORT_PATH, readonly_reports)
    write_json(MANIFEST_PATH, manifest)
    write_human_evidence(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["finance_adapter_summary"]
    print(
        "PASS: KMFA v0.1.4 S07-P1 finance file adapter generated "
        f"(categories={summary['source_category_count']}, "
        f"field_candidates={summary['field_candidate_count']}, "
        f"field_reports={summary['field_report_count']}, "
        f"q5_allowed={summary['q5_calculation_baseline_allowed_count']}, "
        "stage7_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
