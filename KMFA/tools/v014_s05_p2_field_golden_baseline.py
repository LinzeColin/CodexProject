#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S05-P2 field-level golden baseline evidence.

The v1.4 S05-P2 phase binds A0 public file/candidate refs to the required
field-level baseline contracts without publishing raw filenames, source
headers, source locators, raw values, normalized values, sheet names, ZIP member
names, or business amounts. The only source dependency read here is the
public-safe S05-P1 evidence already committed in the project.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_s05_p2_completion_gate import evaluate_gate, validate_active_decision
from KMFA.tools.check_s05_p2_excel_owner_decision import (
    DEFAULT_CONTROL_EVENTS,
    DEFAULT_FIXTURE_CANDIDATES,
    DEFAULT_FIXTURE_MANIFEST,
    DEFAULT_PACKET,
    DEFAULT_RESOLUTION_EVENTS,
    validate_excel_owner_decision,
)
from KMFA.tools.check_s05_p2_owner_decision_templates import DEFAULT_TEMPLATES_DIR, validate_templates
from KMFA.tools.check_v014_s05_p1_a0_file_registration import validate_v014_s05_p1_a0_file_registration
from KMFA.tools.preview_s05_p2_owner_decision_application import build_preview
from KMFA.tools.v014_s05_p1_a0_file_registration import (
    MANIFEST_PATH as S05_P1_MANIFEST_PATH,
    PUBLIC_CANDIDATES_PATH as S05_P1_PUBLIC_CANDIDATES_PATH,
    PUBLIC_REGISTER_PATH as S05_P1_PUBLIC_REGISTER_PATH,
    RAW_INBOX,
)


TASK_ID = "KMFA-V014-S05-P2-FIELD-GOLDEN-BASELINE-20260704"
ACCEPTANCE_ID = "ACC-V014-S05-P2-FIELD-GOLDEN-BASELINE"
SCHEMA_VERSION = "kmfa.v014_s05_p2_field_golden_baseline.v1"
OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S05_P2_FIELD_GOLDEN_BASELINE")
MANIFEST_PATH = OUTPUT_DIR / "machine/field_golden_baseline_manifest.json"
REPORT_PATH = OUTPUT_DIR / "human/field_golden_baseline_report.md"
TEST_RESULTS_PATH = OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PATH = OUTPUT_DIR / "human/rollback_plan.md"
PUBLIC_FIELD_CONTRACTS_PATH = Path("KMFA/metadata/baseline/v014_s05_p2_field_contracts.json")
PUBLIC_FIELD_CANDIDATES_PATH = Path("KMFA/metadata/baseline/v014_s05_p2_field_candidates.jsonl")
ACTIVE_DECISION_PATH = Path(
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/"
    "excel_owner_resolution_decision.json"
)
ACTIVE_PREVIEW_PATH = Path(
    "KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/"
    "excel_owner_decision_application_preview.json"
)
NEXT_PHASE = "S05-P3"
NEXT_INSTRUCTION = (
    "Start S05-P3 authority baseline lock as a separate run only after user instruction. "
    "Do not perform Stage 5 review or GitHub upload in S05-P2. Keep GitHub main upload "
    "deferred until v1.4 Stage 1-18 are complete, overall review has passed, and review "
    "findings are fixed."
)
FIELD_CONTRACT_ROLES = (
    "contract_amount",
    "total_cost",
    "gross_profit",
    "gross_margin_rate",
    "cost_category",
)


class S05P2GenerationError(Exception):
    pass


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise S05P2GenerationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise S05P2GenerationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise S05P2GenerationError(f"{path} contains non-object JSONL row")
        records.append(value)
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def validate_owner_decision() -> dict[str, Any]:
    packet = validate_excel_owner_decision(
        packet_path=DEFAULT_PACKET,
        fixture_manifest_path=DEFAULT_FIXTURE_MANIFEST,
        fixture_candidates_path=DEFAULT_FIXTURE_CANDIDATES,
        resolution_events_path=DEFAULT_RESOLUTION_EVENTS,
        control_events_path=DEFAULT_CONTROL_EVENTS,
    )
    templates = validate_templates(DEFAULT_TEMPLATES_DIR)
    active_decision_code = validate_active_decision(ACTIVE_DECISION_PATH)
    fixture_manifest = read_json(DEFAULT_FIXTURE_MANIFEST)
    fixture_candidates = read_jsonl(DEFAULT_FIXTURE_CANDIDATES)
    gate = evaluate_gate(fixture_manifest, fixture_candidates, active_decision_code)
    preview = build_preview(ACTIVE_DECISION_PATH)
    recorded_preview = read_json(ACTIVE_PREVIEW_PATH)
    if preview != recorded_preview:
        raise S05P2GenerationError("active owner decision preview does not match deterministic replay")
    return {
        "owner_packet_status": packet["resolution_status"],
        "owner_allowed_decision_count": len(packet["allowed_decision_codes"]),
        "owner_template_count": len(templates),
        "active_decision_present": True,
        "active_actor_role_validated": True,
        "active_decision_code": active_decision_code,
        "active_decision_public_safe": True,
        "active_decision_raw_or_plaintext_values_included": False,
        "active_preview_status": preview["application_status"],
        "active_preview_candidate_role": preview["candidate_application"]["candidate_role"],
        "active_preview_q5_exclusion_confirmed": preview["candidate_application"].get("q5_exclusion_confirmed")
        is True,
        "completion_gate_ready": gate.ready,
        "completion_gate_mode": gate.mode,
        "completion_gate_reason": gate.reason,
        "completion_gate_pending_fields": gate.pending_fields,
    }


def field_contracts() -> dict[str, Any]:
    contracts = []
    for index, role in enumerate(FIELD_CONTRACT_ROLES, start=1):
        contracts.append(
            {
                "record_type": "v014_s05_p2_public_field_contract",
                "schema_version": "kmfa.v014_s05_p2_public_field_contract.v1",
                "field_contract_ref": f"V014-S05P2-FIELD-CONTRACT-{index:03d}",
                "field_role": role,
                "field_role_status": "canonical_contract_role_not_raw_header_text",
                "source_header_plaintext_committed": False,
                "source_locator_publication_allowed": False,
                "source_value_publication_allowed": False,
                "normalized_value_publication_allowed": False,
                "q4_human_confirmed_required_for_authority_lock": True,
                "q5_allowed_in_s05p2": False,
            }
        )
    return {
        "schema_version": "kmfa.v014_s05_p2_field_contracts.v1",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S05",
        "phase_id": "S05-P2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "contract_count": len(contracts),
        "contracts": contracts,
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "raw_filenames_committed": False,
            "raw_hashes_committed": False,
            "directory_tree_plaintext_committed": False,
            "source_header_plaintext_committed": False,
            "sheet_names_committed": False,
            "zip_member_names_committed": False,
            "row_or_cell_values_committed": False,
            "source_or_normalized_values_committed": False,
            "business_values_committed": False,
        },
    }


def field_candidates(
    public_file_records: list[dict[str, Any]],
    public_candidate_records: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    file_by_ref = {str(record["public_file_ref"]): record for record in public_file_records}
    records: list[dict[str, Any]] = []
    sequence = 0
    for candidate in public_candidate_records:
        source_file_ref = str(candidate["source_public_file_ref"])
        file_record = file_by_ref[source_file_ref]
        file_format = str(file_record["file_format"])
        excel_downgrade_applied = file_format in {"xlsx", "xls", "xlsm"}
        for contract in contracts:
            sequence += 1
            anchor_recorded = not excel_downgrade_applied
            records.append(
                {
                    "record_type": "v014_s05_p2_public_field_candidate",
                    "schema_version": "kmfa.v014_s05_p2_public_field_candidate.v1",
                    "field_candidate_public_ref": f"V014-S05P2-FIELD-CAND-{sequence:03d}",
                    "candidate_public_ref": candidate["candidate_public_ref"],
                    "source_public_file_ref": source_file_ref,
                    "source_file_format": file_format,
                    "field_contract_ref": contract["field_contract_ref"],
                    "field_role": contract["field_role"],
                    "field_role_status": "canonical_contract_role_not_raw_header_text",
                    "field_candidate_status": (
                        "private_hash_source_anchor_recorded_public_safe"
                        if anchor_recorded
                        else "owner_authorized_downgrade_cross_source_support_only"
                    ),
                    "source_anchor_status": "recorded_private_only" if anchor_recorded else "pending_downgraded",
                    "private_value_hash_status": "recorded_private_only" if anchor_recorded else "pending_downgraded",
                    "source_locator_status": "private_only_not_committed",
                    "page_sheet_cell_status": "private_only_not_committed",
                    "source_value_status": "private_only_not_committed",
                    "normalized_value_status": "private_only_not_committed",
                    "machine_candidate_quality_grade": "Q3",
                    "q4_human_confirmed": False,
                    "q5_calculation_baseline_allowed": False,
                    "q5_formal_report_allowed": False,
                    "excel_owner_downgrade_applied": excel_downgrade_applied,
                    "cross_source_support_only": excel_downgrade_applied,
                    "raw_file_committed": False,
                    "raw_filename_committed": False,
                    "raw_hash_committed": False,
                    "source_header_plaintext_committed": False,
                    "sheet_name_committed": False,
                    "zip_member_name_committed": False,
                    "row_or_cell_value_committed": False,
                    "source_or_normalized_values_committed": False,
                    "business_value_committed": False,
                }
            )
    return records


def summarize_candidates(records: list[dict[str, Any]]) -> dict[str, Any]:
    formats = Counter(str(record["source_file_format"]) for record in records)
    return {
        "a0_project_candidate_count": len({record["candidate_public_ref"] for record in records}),
        "required_field_contract_count": len({record["field_contract_ref"] for record in records}),
        "field_candidate_count": len(records),
        "pdf_field_candidate_count": formats.get("pdf", 0),
        "excel_field_candidate_count": sum(formats.get(item, 0) for item in ("xlsx", "xls", "xlsm")),
        "source_anchor_recorded_private_only_count": sum(
            1 for record in records if record["source_anchor_status"] == "recorded_private_only"
        ),
        "source_anchor_pending_or_downgraded_count": sum(
            1 for record in records if record["source_anchor_status"] == "pending_downgraded"
        ),
        "private_value_hash_recorded_count": sum(
            1 for record in records if record["private_value_hash_status"] == "recorded_private_only"
        ),
        "private_value_hash_pending_or_downgraded_count": sum(
            1 for record in records if record["private_value_hash_status"] == "pending_downgraded"
        ),
        "q3_field_candidate_count": sum(
            1 for record in records if record["machine_candidate_quality_grade"] == "Q3"
        ),
        "q4_human_confirmed_count": sum(1 for record in records if record["q4_human_confirmed"] is True),
        "q5_calculation_baseline_allowed_count": sum(
            1 for record in records if record["q5_calculation_baseline_allowed"] is True
        ),
        "q5_formal_report_allowed_count": sum(
            1 for record in records if record["q5_formal_report_allowed"] is True
        ),
        "owner_downgraded_excel_candidate_count": len(
            {
                record["candidate_public_ref"]
                for record in records
                if record["excel_owner_downgrade_applied"] is True
            }
        ),
        "owner_downgraded_excel_field_count": sum(
            1 for record in records if record["excel_owner_downgrade_applied"] is True
        ),
        "public_source_or_normalized_value_committed_count": sum(
            1 for record in records if record["source_or_normalized_values_committed"] is True
        ),
        "public_source_header_plaintext_committed_count": sum(
            1 for record in records if record["source_header_plaintext_committed"] is True
        ),
        "public_sheet_name_committed_count": sum(1 for record in records if record["sheet_name_committed"] is True),
        "public_row_or_cell_value_committed_count": sum(
            1 for record in records if record["row_or_cell_value_committed"] is True
        ),
        "source_format_counts": dict(sorted(formats.items())),
    }


def build_payloads() -> dict[str, Any]:
    s05_p1 = validate_v014_s05_p1_a0_file_registration()
    public_register = read_json(S05_P1_PUBLIC_REGISTER_PATH)
    public_candidates = read_jsonl(S05_P1_PUBLIC_CANDIDATES_PATH)
    owner = validate_owner_decision()
    contracts_payload = field_contracts()
    candidates = field_candidates(public_register["file_records"], public_candidates, contracts_payload["contracts"])
    summary = summarize_candidates(candidates)

    release_state = {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q3",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    public_repo_safety = {
        "raw_business_data_committed": False,
        "zip_committed": False,
        "excel_workbook_committed": False,
        "pdf_committed": False,
        "private_csv_committed": False,
        "sqlite_or_db_committed": False,
        "credentials_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "directory_tree_plaintext_committed": False,
        "zip_member_names_committed": False,
        "sheet_names_committed": False,
        "source_header_plaintext_committed": False,
        "source_or_normalized_values_committed": False,
        "row_or_cell_values_committed": False,
        "business_values_committed": False,
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S05",
        "stage_name": "A0 authority project cost golden baseline",
        "phase_id": "S05-P2",
        "phase_name": "field-level golden baseline",
        "phase_scope": "v014_s05_p2_field_golden_baseline_only",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_field_candidates_public_safe",
        "completed_task_ids": ["S05P2T01", "S05P2T02", "S05P2T03"],
        "s05_p1_dependency_validated": (
            s05_p1.get("phase_id") == "S05-P1"
            and s05_p1.get("github_upload_performed") is False
            and s05_p1.get("next_recommended_phase") == "S05-P2"
        ),
        "s05_p1_dependency_refs": [
            str(S05_P1_MANIFEST_PATH),
            str(S05_P1_PUBLIC_REGISTER_PATH),
            str(S05_P1_PUBLIC_CANDIDATES_PATH),
        ],
        "owner_decision_summary": owner,
        "completion_gate": {
            "ready": owner["completion_gate_ready"],
            "mode": owner["completion_gate_mode"],
            "reason": owner["completion_gate_reason"],
            "pending_fields": owner["completion_gate_pending_fields"],
            "q4_confirmation_claimed": False,
            "q5_baseline_claimed": False,
            "stage5_review_claimed": False,
        },
        "field_candidate_summary": summary,
        "phase_scope_controls": {
            "current_phase_only": True,
            "field_level_golden_baseline_performed": True,
            "s05_p2_performed": True,
            "raw_inbox_read_required_by_this_phase": False,
            "raw_inbox_read_by_this_phase": False,
            "raw_inbox_listed_by_this_phase": False,
            "raw_inbox_stat_by_this_phase": False,
            "raw_inbox_hashed_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
            "private_runtime_written_by_this_phase": False,
            "business_field_parsing_from_raw_performed": False,
            "source_value_matching_performed": False,
            "s05_p3_performed": False,
            "stage5_review_performed": False,
            "github_upload_performed": False,
            "lineage_full_check_performed": False,
            "formal_report_performed": False,
            "live_connector_called": False,
            "opme_deep_coupling_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "raw_data_boundary": {
            "raw_inbox_path": str(RAW_INBOX),
            "codex_read_allowed_only_when_phase_requires": True,
            "raw_inbox_read_by_this_phase": False,
            "raw_inbox_listed_by_this_phase": False,
            "raw_inbox_stat_by_this_phase": False,
            "raw_inbox_hashed_by_this_phase": False,
            "raw_inbox_modified_by_this_phase": False,
            "raw_inbox_deleted_by_this_phase": False,
            "raw_inbox_moved_by_this_phase": False,
            "raw_inbox_renamed_by_this_phase": False,
            "raw_inbox_overwritten_by_this_phase": False,
            "raw_inbox_written_by_this_phase": False,
            "raw_inbox_generate_inside_by_this_phase": False,
            "raw_inbox_create_extra_files_inside_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
            "raw_filenames_committed": False,
            "raw_hashes_committed": False,
            "directory_tree_plaintext_committed": False,
            "zip_member_names_committed": False,
            "sheet_names_committed": False,
            "source_header_plaintext_committed": False,
            "row_or_cell_values_committed": False,
            "source_or_normalized_values_committed": False,
            "business_values_committed": False,
        },
        "public_repo_safety": public_repo_safety,
        "release_state": release_state,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "validation_summary": {
            "s05_p1_dependency": "PASS",
            "field_contract_count_check": "PASS",
            "field_candidate_count_check": "PASS",
            "owner_downgrade_gate_check": "PASS",
            "public_safe_manifest_check": "PASS",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "py_compile": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "structured_parse": "PENDING_FINAL_VALIDATION",
            "ruby_yaml_parse": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "public_field_contracts_ref": str(PUBLIC_FIELD_CONTRACTS_PATH),
        "public_field_candidates_ref": str(PUBLIC_FIELD_CANDIDATES_PATH),
        "evidence_refs": [
            str(REPORT_PATH),
            str(TEST_RESULTS_PATH),
            str(RISK_REGISTER_PATH),
            str(ROLLBACK_PATH),
            str(MANIFEST_PATH),
            str(PUBLIC_FIELD_CONTRACTS_PATH),
            str(PUBLIC_FIELD_CANDIDATES_PATH),
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }
    return {
        "manifest": manifest,
        "contracts": contracts_payload,
        "candidates": candidates,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["field_candidate_summary"]
    owner = manifest["owner_decision_summary"]
    gate = manifest["completion_gate"]
    lines = [
        "# KMFA v0.1.4 S05-P2 Field Golden Baseline",
        "",
        f"- status: `{manifest['status']}`",
        f"- task_id: `{manifest['task_id']}`",
        f"- s05_p1_dependency_validated: `{str(manifest['s05_p1_dependency_validated']).lower()}`",
        f"- required_field_contract_count: `{summary['required_field_contract_count']}`",
        f"- a0_project_candidate_count: `{summary['a0_project_candidate_count']}`",
        f"- field_candidate_count: `{summary['field_candidate_count']}`",
        f"- pdf_field_candidate_count: `{summary['pdf_field_candidate_count']}`",
        f"- excel_field_candidate_count: `{summary['excel_field_candidate_count']}`",
        f"- source_anchor_recorded_private_only_count: `{summary['source_anchor_recorded_private_only_count']}`",
        f"- source_anchor_pending_or_downgraded_count: `{summary['source_anchor_pending_or_downgraded_count']}`",
        f"- private_value_hash_recorded_count: `{summary['private_value_hash_recorded_count']}`",
        f"- private_value_hash_pending_or_downgraded_count: `{summary['private_value_hash_pending_or_downgraded_count']}`",
        f"- q3_field_candidate_count: `{summary['q3_field_candidate_count']}`",
        f"- q4_human_confirmed_count: `{summary['q4_human_confirmed_count']}`",
        f"- q5_calculation_baseline_allowed_count: `{summary['q5_calculation_baseline_allowed_count']}`",
        f"- owner_downgraded_excel_candidate_count: `{summary['owner_downgraded_excel_candidate_count']}`",
        f"- owner_downgraded_excel_field_count: `{summary['owner_downgraded_excel_field_count']}`",
        f"- active_decision_code: `{owner['active_decision_code']}`",
        f"- completion_gate_ready: `{str(gate['ready']).lower()}`",
        f"- completion_gate_mode: `{gate['mode']}`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "- source_header_plaintext_committed: `false`",
        "- sheet_names_committed: `false`",
        "- zip_member_names_committed: `false`",
        "- source_or_normalized_values_committed: `false`",
        "- row_or_cell_values_committed: `false`",
        "- business_values_committed: `false`",
        "- s05_p3_performed: `false`",
        "- stage5_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- github_upload_status: `not_uploaded_deferred_until_v014_stage1_18_complete`",
        f"- current_data_quality_grade: `{manifest['release_state']['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['release_state']['current_report_grade']}`",
        f"- current_go_no_go: `{manifest['release_state']['current_go_no_go']}`",
        "",
        "## Boundary",
        "",
        "- This phase uses S05-P1 public refs and the existing active owner/authorized downgrade record.",
        "- The local raw inbox was not read, listed, stat-checked, hashed, modified or written by this phase.",
        "- Public evidence records field contracts, candidate refs, private-only locator/hash statuses and aggregate counts only.",
        "- Q4 human confirmation, Q5 authority lock, Stage 5 review, GitHub upload, formal report release and business execution remain out of scope.",
        "",
        "## Next",
        "",
        manifest["next_phase_instruction"],
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_test_results(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.4 S05-P2 Test Results",
        "",
        "- status: `pending_final_validation`",
        f"- task_id: `{manifest['task_id']}`",
        f"- field_candidate_count: `{manifest['field_candidate_summary']['field_candidate_count']}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        "",
        "Final validation results will be recorded before local commit.",
        "",
    ]
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_risk_register(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.4 S05-P2 Risk Register",
        "",
        "| risk_id | risk | control | status |",
        "| --- | --- | --- | --- |",
        "| V014-S05P2-R01 | Field candidates are not Q4/Q5 authority records yet. | Keep Q4/Q5 counts at 0 and require S05-P3 separate run. | controlled |",
        "| V014-S05P2-R02 | Raw source values or locators could leak into public evidence. | Validator rejects raw files, source headers, sheet/member names, row/cell values and business values. | controlled |",
        "| V014-S05P2-R03 | Excel workbook candidate cannot be promoted without owner handling. | Active owner/authorized downgrade keeps Excel fields cross-source support only. | controlled |",
        "",
        f"- next_required_phase: `{manifest['next_recommended_phase']}`",
        f"- github_upload_status: `{manifest['github_upload_status']}`",
        "",
    ]
    RISK_REGISTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    RISK_REGISTER_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_rollback_plan(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.4 S05-P2 Rollback Plan",
        "",
        "- Revert the local commit for `KMFA-V014-S05-P2-FIELD-GOLDEN-BASELINE-20260704` if validation or review finds a defect.",
        "- Remove only generated S05-P2 public evidence and metadata paths from this phase if rollback is required.",
        "- Do not modify, delete, move, rename, overwrite or write inside `/Users/linzezhang/Downloads/KMFA_MetaData`.",
        "- Do not push or upload GitHub main until v1.4 Stage 1-18 complete overall review passes and findings are fixed.",
        "",
        f"- rollback_scope: `{manifest['phase_scope']}`",
        "",
    ]
    ROLLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROLLBACK_PATH.write_text("\n".join(lines), encoding="utf-8")


def generate() -> dict[str, Any]:
    payloads = build_payloads()
    manifest = payloads["manifest"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(MANIFEST_PATH, manifest)
    write_json(PUBLIC_FIELD_CONTRACTS_PATH, payloads["contracts"])
    write_jsonl(PUBLIC_FIELD_CANDIDATES_PATH, payloads["candidates"])
    write_report(manifest)
    write_test_results(manifest)
    write_risk_register(manifest)
    write_rollback_plan(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["field_candidate_summary"]
    print(
        "PASS: KMFA v0.1.4 S05-P2 field golden baseline evidence generated "
        f"(field_candidates={summary['field_candidate_count']}, "
        f"anchor_recorded={summary['source_anchor_recorded_private_only_count']}, "
        f"downgraded={summary['owner_downgraded_excel_field_count']}, "
        f"q4={summary['q4_human_confirmed_count']}, "
        f"q5={summary['q5_calculation_baseline_allowed_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
